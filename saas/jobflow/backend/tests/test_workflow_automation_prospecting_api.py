from sqlalchemy import select

from app.models import AdminAuditLog, User
from app.products.workflow_automation.models import (
    ProspectCandidate,
    ProspectingCampaign,
)


def make_operator(db_session):
    user = db_session.scalar(
        select(User).where(
            User.email
            == "default-test-user@example.com"
        )
    )

    assert user is not None

    user.is_platform_admin = True
    db_session.commit()

    return user


def create_candidate(
    db_session,
    operator,
):
    campaign = ProspectingCampaign(
        name="Review Test Campaign",
        geography="New York State",
        segments=[
            "small_it_provider",
        ],
        status="completed",
        max_candidates=5,
        minimum_score=70,
        model="test-model",
        created_by_user_id=operator.id,
    )

    db_session.add(campaign)
    db_session.flush()

    candidate = ProspectCandidate(
        campaign_id=campaign.id,
        business_name="Review Test IT",
        website_url=(
            "https://review-test.example"
        ),
        normalized_domain=(
            "review-test.example"
        ),
        segment="small_it_provider",
        location="Buffalo, New York",
        contact_name=None,
        email=(
            "hello@review-test.example"
        ),
        phone=None,
        evidence=[
            {
                "url": (
                    "https://review-test.example"
                ),
                "fact": (
                    "Public business website."
                ),
            }
        ],
        fit_score=84,
        score_reasons=[
            "Small IT provider",
            "Clear operational workflows",
        ],
        disqualifiers=[],
        outreach_subject=(
            "Workflow question"
        ),
        outreach_body=(
            "Draft for Rafael review."
        ),
        review_status="pending",
    )

    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)

    return candidate


def test_operator_can_create_campaign(
    client,
    db_session,
):
    operator = make_operator(db_session)

    response = client.post(
        "/api/v1/products/"
        "workflow-automation/"
        "prospecting/campaigns",
        json={
            "name": (
                "New York Product #6 Prospects"
            ),
            "geography": "New York State",
            "segments": [
                "small_it_provider",
                "home_service_business",
            ],
            "max_candidates": 10,
            "minimum_score": 70,
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["status"] == "draft"
    assert payload["geography"] == (
        "New York State"
    )
    assert payload["model"]
    assert payload["created_by_user_id"] == (
        operator.id
    )

    audit = db_session.scalar(
        select(AdminAuditLog).where(
            AdminAuditLog.action
            == (
                "workflow_automation."
                "campaign_created"
            )
        )
    )

    assert audit is not None


def test_non_operator_cannot_create_campaign(
    client,
):
    response = client.post(
        "/api/v1/products/"
        "workflow-automation/"
        "prospecting/campaigns",
        json={
            "name": "Unauthorized Campaign",
        },
    )

    assert response.status_code == 403


def test_operator_can_list_and_approve_candidate(
    client,
    db_session,
):
    operator = make_operator(db_session)

    candidate = create_candidate(
        db_session,
        operator,
    )

    response = client.get(
        "/api/v1/products/"
        "workflow-automation/"
        "prospecting/candidates",
        params={
            "review_status": "pending",
        },
    )

    assert response.status_code == 200
    assert response.json()[0]["id"] == (
        candidate.id
    )

    response = client.put(
        "/api/v1/products/"
        "workflow-automation/"
        f"prospecting/candidates/"
        f"{candidate.id}/review",
        json={
            "decision": "approved",
            "outreach_subject": (
                "Edited workflow question"
            ),
            "outreach_body": (
                "Edited by Rafael before approval."
            ),
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["review_status"] == (
        "approved"
    )
    assert payload["outreach_subject"] == (
        "Edited workflow question"
    )
    assert payload["reviewed_by_user_id"] == (
        operator.id
    )

    audit = db_session.scalar(
        select(AdminAuditLog).where(
            AdminAuditLog.action
            == (
                "workflow_automation."
                "candidate_reviewed"
            )
        )
    )

    assert audit is not None


def test_candidate_cannot_be_reviewed_twice(
    client,
    db_session,
):
    operator = make_operator(db_session)

    candidate = create_candidate(
        db_session,
        operator,
    )

    candidate.review_status = "rejected"
    db_session.commit()

    response = client.put(
        "/api/v1/products/"
        "workflow-automation/"
        f"prospecting/candidates/"
        f"{candidate.id}/review",
        json={
            "decision": "approved",
        },
    )

    assert response.status_code == 409
