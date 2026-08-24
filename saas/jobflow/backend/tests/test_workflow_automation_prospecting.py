from sqlalchemy import select

from app.database import Base
from app.models import Product, User
from app.platform import discover_product_models
from app.products.workflow_automation.models import (
    ProspectCandidate,
    ProspectingCampaign,
)


def get_operator(db_session):
    operator = db_session.scalar(
        select(User).where(
            User.email
            == "default-test-user@example.com"
        )
    )

    if operator is None:
        operator = User(
            email=(
                "prospecting-operator@example.com"
            ),
            display_name=(
                "Prospecting Operator"
            ),
            is_active=True,
            is_platform_admin=True,
        )

        db_session.add(operator)
        db_session.commit()
        db_session.refresh(operator)

    return operator


def test_workflow_automation_models_are_discovered():
    discovered = discover_product_models()

    assert "workflow_automation" in discovered
    assert (
        "workflow_automation_"
        "prospecting_campaigns"
        in Base.metadata.tables
    )
    assert (
        "workflow_automation_"
        "prospect_candidates"
        in Base.metadata.tables
    )


def test_prospecting_records_are_product_owned(
    db_session,
):
    operator = get_operator(db_session)

    product = db_session.scalar(
        select(Product).where(
            Product.slug
            == "workflow-automation"
        )
    )

    if product is None:
        product = Product(
            name=(
                "Workflow Automation Package"
            ),
            slug="workflow-automation",
            status="active",
            workspace_key=(
                "workflow-automation"
            ),
        )

        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)

    campaign = ProspectingCampaign(
        name="New York Initial Campaign",
        geography="New York State",
        segments=[
            "small_it_provider",
        ],
        status="draft",
        max_candidates=10,
        minimum_score=70,
        model="test-model",
        created_by_user_id=operator.id,
    )

    db_session.add(campaign)
    db_session.flush()

    candidate = ProspectCandidate(
        campaign_id=campaign.id,
        business_name="Example IT Services",
        website_url=(
            "https://example-it.test"
        ),
        normalized_domain=(
            "example-it.test"
        ),
        segment="small_it_provider",
        location="Albany, New York",
        contact_name="Example Owner",
        email="owner@example-it.test",
        phone=None,
        evidence=[
            {
                "url": (
                    "https://example-it.test"
                ),
                "fact": (
                    "Provides managed IT services "
                    "to small businesses."
                ),
            }
        ],
        fit_score=82,
        score_reasons=[
            "Small team",
            "Manual client operations likely",
        ],
        disqualifiers=[],
        outreach_subject=(
            "A workflow question for "
            "Example IT Services"
        ),
        outreach_body=(
            "Draft for Rafael review."
        ),
        review_status="pending",
    )

    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)

    assert candidate.id is not None
    assert candidate.lead_id is None
    assert candidate.review_status == "pending"
    assert candidate.fit_score == 82
    assert (
        candidate.normalized_domain
        == "example-it.test"
    )
