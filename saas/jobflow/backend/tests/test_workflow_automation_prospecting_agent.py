from sqlalchemy import select

from app.models import (
    AdminAuditLog,
    Lead,
    Product,
    User,
)
from app.products.workflow_automation.models import (
    ProspectCandidate,
    ProspectingCampaign,
)
from app.products.workflow_automation.prospecting_agent import (
    evidence_matches_source,
    run_campaign,
)
from app.products.workflow_automation.prospecting_schemas import (
    DiscoveredCandidate,
)


class FakeProvider:
    def __init__(self, candidates):
        self.candidates = candidates

    def discover(self, campaign):
        return self.candidates


class FailingProvider:
    def discover(self, campaign):
        raise RuntimeError(
            "Simulated provider failure"
        )


def setup_records(db_session):
    operator = User(
        email="agent-operator@example.com",
        display_name="Agent Operator",
        is_active=True,
        is_platform_admin=True,
    )

    product = Product(
        name="Workflow Automation Package",
        slug="workflow-automation",
        status="active",
        workspace_key="workflow-automation",
    )

    db_session.add_all([
        operator,
        product,
    ])
    db_session.commit()
    db_session.refresh(operator)

    campaign = ProspectingCampaign(
        name="Agent Test Campaign",
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
    db_session.commit()
    db_session.refresh(campaign)

    return campaign


def candidate(
    *,
    name,
    domain,
    email,
    score,
    disqualifiers=None,
):
    return DiscoveredCandidate(
        business_name=name,
        website_url=f"https://{domain}",
        segment="small_it_provider",
        location="Albany, New York",
        contact_name=None,
        email=email,
        phone=None,
        evidence=[
            {
                "url": f"https://{domain}",
                "fact": (
                    "Public business evidence."
                ),
            }
        ],
        fit_score=score,
        score_reasons=[
            "Small IT provider",
        ],
        disqualifiers=(
            disqualifiers or []
        ),
        outreach_subject=(
            f"Workflow question for {name}"
        ),
        outreach_body=(
            "Draft for Rafael approval."
        ),
    )


def test_campaign_saves_only_qualified_leads(
    db_session,
):
    campaign = setup_records(db_session)

    provider = FakeProvider([
        candidate(
            name="Qualified IT",
            domain="qualified-it.example",
            email=(
                "hello@qualified-it.example"
            ),
            score=84,
        ),
        candidate(
            name="Low Score IT",
            domain="low-score.example",
            email=(
                "hello@low-score.example"
            ),
            score=50,
        ),
        candidate(
            name="Wrong Email Domain",
            domain="wrong-domain.example",
            email="hello@unrelated.example",
            score=90,
        ),
    ])

    result = run_campaign(
        db=db_session,
        campaign=campaign,
        provider=provider,
    )

    assert result == {
        "campaign_id": campaign.id,
        "status": "completed",
        "discovered_count": 3,
        "saved_count": 1,
        "skipped_count": 2,
    }

    leads = list(
        db_session.scalars(
            select(Lead)
        )
    )

    candidates = list(
        db_session.scalars(
            select(ProspectCandidate)
        )
    )

    assert len(leads) == 1
    assert len(candidates) == 1
    assert leads[0].business_name == (
        "Qualified IT"
    )
    assert leads[0].status == "new"
    assert candidates[0].lead_id == (
        leads[0].id
    )
    assert candidates[0].review_status == (
        "pending"
    )

    audit = db_session.scalar(
        select(AdminAuditLog).where(
            AdminAuditLog.action
            == (
                "workflow_automation."
                "campaign_completed"
            )
        )
    )

    assert audit is not None
    assert audit.after_data[
        "skip_reasons"
    ]["below_minimum_score"] == 1
    assert audit.after_data[
        "skip_reasons"
    ]["invalid_business_email"] == 1


def test_campaign_deduplicates_domains(
    db_session,
):
    first = setup_records(db_session)

    item = candidate(
        name="Duplicate IT",
        domain="duplicate-it.example",
        email="hello@duplicate-it.example",
        score=88,
    )

    first_result = run_campaign(
        db=db_session,
        campaign=first,
        provider=FakeProvider([item]),
    )

    operator = db_session.scalar(
        select(User).where(
            User.email
            == "agent-operator@example.com"
        )
    )

    second = ProspectingCampaign(
        name="Second Campaign",
        geography="New York State",
        segments=["small_it_provider"],
        status="draft",
        max_candidates=10,
        minimum_score=70,
        model="test-model",
        created_by_user_id=operator.id,
    )

    db_session.add(second)
    db_session.commit()
    db_session.refresh(second)

    second_result = run_campaign(
        db=db_session,
        campaign=second,
        provider=FakeProvider([item]),
    )

    assert first_result["saved_count"] == 1
    assert second_result["saved_count"] == 0
    assert second_result["skipped_count"] == 1


def test_campaign_records_provider_failure(
    db_session,
):
    campaign = setup_records(db_session)

    try:
        run_campaign(
            db=db_session,
            campaign=campaign,
            provider=FailingProvider(),
        )
    except RuntimeError:
        pass
    else:
        raise AssertionError(
            "Provider failure was not raised"
        )

    db_session.expire_all()

    failed = db_session.get(
        ProspectingCampaign,
        campaign.id,
    )

    assert failed.status == "failed"
    assert (
        "Simulated provider failure"
        in failed.error_message
    )


def test_evidence_accepts_canonical_url_variations():
    assert evidence_matches_source(
        "https://example.com/contact",
        (
            "https://www.example.com/contact/"
            "?utm_source=search"
        ),
    )


def test_evidence_accepts_verified_source_domain():
    assert evidence_matches_source(
        "https://example.com/contact-us",
        "https://example.com/about",
    )


def test_evidence_rejects_unverified_domain():
    assert not evidence_matches_source(
        "https://invented.example/contact",
        "https://verified.example/about",
    )
