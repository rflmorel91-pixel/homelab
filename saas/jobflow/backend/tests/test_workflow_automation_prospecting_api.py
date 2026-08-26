from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models import (
    AdminAuditLog,
    Lead,
    User,
)
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

    lead = Lead(
        product_id=1,
        business_name="Review Test IT",
        contact_name="Business contact",
        email="hello@review-test.example",
        phone=None,
        service_type=(
            "Small IT provider partnership"
        ),
        message="Agent review test",
        status="new",
    )

    db_session.add(lead)
    db_session.flush()

    candidate = ProspectCandidate(
        campaign_id=campaign.id,
        lead_id=lead.id,
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
                "New York Workflow Automation Package Prospects"
            ),
            "geography": "New York State",
            "segments": [
                "small_it_provider",
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


def test_operator_queues_campaign_run(
    client,
    db_session,
    monkeypatch,
):
    operator = make_operator(db_session)

    campaign = ProspectingCampaign(
        name="Queued Campaign",
        geography="New York State",
        segments=["small_it_provider"],
        status="draft",
        max_candidates=3,
        minimum_score=75,
        model="test-model",
        created_by_user_id=operator.id,
    )

    db_session.add(campaign)
    db_session.commit()
    db_session.refresh(campaign)

    calls = []

    def fake_background_run(campaign_id):
        calls.append(campaign_id)

    monkeypatch.setattr(
        "app.products.workflow_automation."
        "prospecting_api."
        "run_campaign_in_background",
        fake_background_run,
    )

    monkeypatch.setenv(
        "OPENAI_API_KEY",
        "test-key",
    )

    response = client.post(
        "/api/v1/products/"
        "workflow-automation/"
        f"prospecting/campaigns/"
        f"{campaign.id}/run"
    )

    assert response.status_code == 202
    assert response.json() == {
        "campaign_id": campaign.id,
        "status": "queued",
    }
    assert calls == [campaign.id]

    db_session.expire_all()

    queued = db_session.get(
        ProspectingCampaign,
        campaign.id,
    )

    assert queued.status == "queued"
    assert queued.started_at is None


def test_campaign_cannot_be_queued_twice(
    client,
    db_session,
    monkeypatch,
):
    operator = make_operator(db_session)

    campaign = ProspectingCampaign(
        name="Already Queued Campaign",
        geography="New York State",
        segments=["small_it_provider"],
        status="queued",
        max_candidates=3,
        minimum_score=75,
        model="test-model",
        created_by_user_id=operator.id,
    )

    db_session.add(campaign)
    db_session.commit()
    db_session.refresh(campaign)

    monkeypatch.setenv(
        "OPENAI_API_KEY",
        "test-key",
    )

    response = client.post(
        "/api/v1/products/"
        "workflow-automation/"
        f"prospecting/campaigns/"
        f"{campaign.id}/run"
    )

    assert response.status_code == 409


def test_rejecting_candidate_closes_new_lead(
    client,
    db_session,
):
    operator = make_operator(db_session)

    candidate = create_candidate(
        db_session,
        operator,
    )

    response = client.put(
        "/api/v1/products/"
        "workflow-automation/"
        f"prospecting/candidates/"
        f"{candidate.id}/review",
        json={
            "decision": "rejected",
        },
    )

    assert response.status_code == 200

    db_session.expire_all()

    lead = db_session.get(
        Lead,
        candidate.lead_id,
    )

    assert lead.status == "closed"

def test_operator_can_add_manual_candidate(
    client,
    db_session,
    monkeypatch,
):
    operator = make_operator(db_session)

    campaign = ProspectingCampaign(
        name="Manual Prospect Campaign",
        geography="United States",
        segments=["small_it_provider"],
        status="draft",
        max_candidates=10,
        minimum_score=70,
        model="manual-research",
        created_by_user_id=operator.id,
    )

    db_session.add(campaign)
    db_session.commit()
    db_session.refresh(campaign)

    monkeypatch.setenv(
        "FIELDLOOKERS_OUTREACH_POSTAL_ADDRESS",
        "Verified Business Address",
    )

    response = client.post(
        "/api/v1/products/"
        "workflow-automation/"
        "prospecting/candidates",
        json={
            "campaign_id": campaign.id,
            "business_name": "Manual IT Partner",
            "website_url": (
                "https://manual-partner.example"
            ),
            "segment": "small_it_provider",
            "location": "United States",
            "contact_name": None,
            "email": (
                "INQUIRIES@MANUAL-PARTNER.EXAMPLE"
            ),
            "phone": None,
            "evidence": [
                {
                    "url": (
                        "https://manual-partner.example"
                    ),
                    "fact": (
                        "Public website documents "
                        "client implementation work."
                    ),
                }
            ],
            "fit_score": 88,
            "score_reasons": [
                "Small IT provider",
                "Public implementation evidence",
            ],
            "disqualifiers": [],
            "outreach_subject": (
                "Overflow implementation capacity"
            ),
            "outreach_body": (
                "Personalized body for review."
            ),
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["review_status"] == "pending"
    assert payload["normalized_domain"] == (
        "manual-partner.example"
    )
    assert payload["email"] == (
        "inquiries@manual-partner.example"
    )
    assert "Personalized body for review." in (
        payload["outreach_body"]
    )
    assert "Verified Business Address" in (
        payload["outreach_body"]
    )
    assert "unsubscribe" in (
        payload["outreach_body"]
    )

    lead = db_session.get(
        Lead,
        payload["lead_id"],
    )

    assert lead is not None
    assert lead.status == "new"

    audit = db_session.scalar(
        select(AdminAuditLog).where(
            AdminAuditLog.action
            == (
                "workflow_automation."
                "manual_candidate_created"
            )
        )
    )

    assert audit is not None


def test_manual_candidate_requires_business_email(
    client,
    db_session,
):
    operator = make_operator(db_session)

    campaign = ProspectingCampaign(
        name="Manual Email Validation",
        geography="United States",
        segments=["small_it_provider"],
        status="draft",
        max_candidates=10,
        minimum_score=70,
        model="manual-research",
        created_by_user_id=operator.id,
    )

    db_session.add(campaign)
    db_session.commit()
    db_session.refresh(campaign)

    response = client.post(
        "/api/v1/products/"
        "workflow-automation/"
        "prospecting/candidates",
        json={
            "campaign_id": campaign.id,
            "business_name": "Invalid Email MSP",
            "website_url": "https://invalid-msp.example",
            "segment": "small_it_provider",
            "location": "United States",
            "email": "person@gmail.com",
            "evidence": [
                {
                    "url": "https://invalid-msp.example",
                    "fact": "Public MSP website.",
                }
            ],
            "fit_score": 80,
            "score_reasons": [
                "Small IT provider",
            ],
            "disqualifiers": [],
            "outreach_subject": "Test subject",
            "outreach_body": "Test body",
        },
    )

    assert response.status_code == 422


def test_manual_candidate_rejects_duplicate_domain(
    client,
    db_session,
):
    operator = make_operator(db_session)

    existing = create_candidate(
        db_session,
        operator,
    )

    campaign = ProspectingCampaign(
        name="Duplicate Validation",
        geography="United States",
        segments=["small_it_provider"],
        status="draft",
        max_candidates=10,
        minimum_score=70,
        model="manual-research",
        created_by_user_id=operator.id,
    )

    db_session.add(campaign)
    db_session.commit()
    db_session.refresh(campaign)

    response = client.post(
        "/api/v1/products/"
        "workflow-automation/"
        "prospecting/candidates",
        json={
            "campaign_id": campaign.id,
            "business_name": "Duplicate MSP",
            "website_url": existing.website_url,
            "segment": "small_it_provider",
            "location": "United States",
            "email": existing.email,
            "evidence": [
                {
                    "url": existing.website_url,
                    "fact": "Duplicate evidence.",
                }
            ],
            "fit_score": 80,
            "score_reasons": [
                "Small IT provider",
            ],
            "disqualifiers": [],
            "outreach_subject": "Duplicate",
            "outreach_body": "Duplicate",
        },
    )

    assert response.status_code == 409


def test_only_approved_candidate_can_be_marked_sent(
    client,
    db_session,
):
    operator = make_operator(db_session)
    candidate = create_candidate(
        db_session,
        operator,
    )

    endpoint = (
        "/api/v1/products/"
        "workflow-automation/"
        f"prospecting/candidates/{candidate.id}/"
        "outreach/sent"
    )
    payload = {
        "channel": "email",
        "sent_at": "2026-08-25T19:00:00-04:00",
    }

    response = client.post(
        endpoint,
        json=payload,
    )

    assert response.status_code == 409

    candidate.review_status = "rejected"
    db_session.commit()

    response = client.post(
        endpoint,
        json=payload,
    )

    assert response.status_code == 409


def test_operator_records_sent_outreach(
    client,
    db_session,
):
    operator = make_operator(db_session)
    candidate = create_candidate(
        db_session,
        operator,
    )
    candidate.review_status = "approved"
    db_session.commit()

    response = client.post(
        "/api/v1/products/"
        "workflow-automation/"
        f"prospecting/candidates/{candidate.id}/"
        "outreach/sent",
        json={
            "channel": "email",
            "sent_at": (
                "2026-08-25T19:51:00-04:00"
            ),
            "follow_up_due_at": (
                "2026-09-01T09:00:00-04:00"
            ),
            "notes": (
                "Manually sent through Outlook."
            ),
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["outreach_channel"] == "email"
    assert payload["outreach_sent_at"] is not None
    assert payload["follow_up_due_at"] is not None
    assert payload["operator_notes"] == (
        "Manually sent through Outlook."
    )

    db_session.expire_all()

    lead = db_session.get(
        Lead,
        candidate.lead_id,
    )

    assert lead.status == "contacted"

    audit = db_session.scalar(
        select(AdminAuditLog).where(
            AdminAuditLog.action
            == (
                "workflow_automation."
                "outreach_sent"
            )
        )
    )

    assert audit is not None


def test_operator_records_follow_up(
    client,
    db_session,
):
    operator = make_operator(db_session)
    candidate = create_candidate(
        db_session,
        operator,
    )
    candidate.review_status = "approved"
    db_session.commit()

    sent_response = client.post(
        "/api/v1/products/"
        "workflow-automation/"
        f"prospecting/candidates/{candidate.id}/"
        "outreach/sent",
        json={
            "channel": "email",
            "sent_at": (
                "2026-08-25T19:00:00-04:00"
            ),
            "follow_up_due_at": (
                "2026-09-01T09:00:00-04:00"
            ),
        },
    )

    assert sent_response.status_code == 200

    response = client.post(
        "/api/v1/products/"
        "workflow-automation/"
        f"prospecting/candidates/{candidate.id}/"
        "outreach/follow-up",
        json={
            "completed_at": (
                "2026-09-01T09:15:00-04:00"
            ),
            "notes": (
                "One manual follow-up sent."
            ),
        },
    )

    assert response.status_code == 200
    assert (
        response.json()[
            "follow_up_completed_at"
        ]
        is not None
    )

    audit = db_session.scalar(
        select(AdminAuditLog).where(
            AdminAuditLog.action
            == (
                "workflow_automation."
                "follow_up_recorded"
            )
        )
    )

    assert audit is not None


def test_unsubscribe_reply_suppresses_candidate(
    client,
    db_session,
):
    operator = make_operator(db_session)
    candidate = create_candidate(
        db_session,
        operator,
    )
    candidate.review_status = "approved"
    db_session.commit()

    sent_response = client.post(
        "/api/v1/products/"
        "workflow-automation/"
        f"prospecting/candidates/{candidate.id}/"
        "outreach/sent",
        json={
            "channel": "email",
            "sent_at": (
                "2026-08-25T19:00:00-04:00"
            ),
        },
    )

    assert sent_response.status_code == 200

    response = client.post(
        "/api/v1/products/"
        "workflow-automation/"
        f"prospecting/candidates/{candidate.id}/"
        "outreach/reply",
        json={
            "received_at": (
                "2026-08-25T22:08:00-04:00"
            ),
            "outcome": "unsubscribe",
            "notes": "Explicit unsubscribe reply.",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["reply_outcome"] == (
        "unsubscribe"
    )
    assert payload["suppressed_at"] is not None
    assert payload["suppression_reason"] == (
        "Unsubscribe request"
    )

    db_session.expire_all()

    lead = db_session.get(
        Lead,
        candidate.lead_id,
    )

    assert lead.status == "closed"

    follow_up_response = client.post(
        "/api/v1/products/"
        "workflow-automation/"
        f"prospecting/candidates/{candidate.id}/"
        "outreach/follow-up",
        json={
            "completed_at": (
                "2026-09-01T09:00:00-04:00"
            ),
        },
    )

    assert follow_up_response.status_code == 409

    audit = db_session.scalar(
        select(AdminAuditLog).where(
            AdminAuditLog.action
            == (
                "workflow_automation."
                "reply_recorded"
            )
        )
    )

    assert audit is not None


def test_operator_can_suppress_before_send(
    client,
    db_session,
):
    operator = make_operator(db_session)
    candidate = create_candidate(
        db_session,
        operator,
    )
    candidate.review_status = "approved"
    db_session.commit()

    response = client.post(
        "/api/v1/products/"
        "workflow-automation/"
        f"prospecting/candidates/{candidate.id}/"
        "outreach/suppression",
        json={
            "suppressed_at": (
                "2026-08-26T09:00:00-04:00"
            ),
            "reason": "Do not contact request",
            "notes": "Recorded by operator.",
        },
    )

    assert response.status_code == 200
    assert response.json()["suppressed_at"] is not None

    sent_response = client.post(
        "/api/v1/products/"
        "workflow-automation/"
        f"prospecting/candidates/{candidate.id}/"
        "outreach/sent",
        json={
            "channel": "email",
            "sent_at": (
                "2026-08-26T10:00:00-04:00"
            ),
        },
    )

    assert sent_response.status_code == 409

    audit = db_session.scalar(
        select(AdminAuditLog).where(
            AdminAuditLog.action
            == (
                "workflow_automation."
                "candidate_suppressed"
            )
        )
    )

    assert audit is not None


def test_due_follow_ups_are_ordered_and_filtered(
    client,
    db_session,
):
    operator = make_operator(db_session)
    candidate = create_candidate(
        db_session,
        operator,
    )

    second_lead = Lead(
        product_id=1,
        business_name="Earlier Follow-Up IT",
        contact_name="Earlier contact",
        email="hello@earlier-follow-up.example",
        phone=None,
        service_type="Small IT provider partnership",
        message="Earlier follow-up test",
        status="new",
    )
    db_session.add(second_lead)
    db_session.flush()

    earlier_candidate = ProspectCandidate(
        campaign_id=candidate.campaign_id,
        lead_id=second_lead.id,
        business_name="Earlier Follow-Up IT",
        website_url="https://earlier-follow-up.example",
        normalized_domain="earlier-follow-up.example",
        segment="small_it_provider",
        location="Albany, New York",
        contact_name="Earlier contact",
        email="hello@earlier-follow-up.example",
        phone=None,
        evidence=[],
        fit_score=80,
        score_reasons=["Small IT provider"],
        disqualifiers=[],
        outreach_subject="Earlier workflow question",
        outreach_body="Earlier approved draft.",
        review_status="approved",
    )
    db_session.add(earlier_candidate)

    now = datetime.now(
        timezone.utc
    ).replace(tzinfo=None)

    candidate.review_status = "approved"
    candidate.outreach_sent_at = (
        now - timedelta(days=7)
    )
    candidate.follow_up_due_at = (
        now + timedelta(days=2)
    )

    earlier_candidate.outreach_sent_at = (
        now - timedelta(days=8)
    )
    earlier_candidate.follow_up_due_at = (
        now - timedelta(days=1)
    )
    db_session.commit()

    endpoint = (
        "/api/v1/products/"
        "workflow-automation/"
        "prospecting/follow-ups/due"
    )

    response = client.get(endpoint)

    assert response.status_code == 200
    assert [
        item["candidate_id"]
        for item in response.json()
    ] == [
        earlier_candidate.id,
        candidate.id,
    ]

    earlier_candidate.follow_up_completed_at = now
    db_session.commit()

    assert [
        item["candidate_id"]
        for item in client.get(endpoint).json()
    ] == [candidate.id]

    candidate.reply_received_at = now
    candidate.reply_outcome = "interested"
    db_session.commit()
    assert client.get(endpoint).json() == []

    candidate.reply_received_at = None
    candidate.reply_outcome = None
    candidate.suppressed_at = now
    candidate.suppression_reason = "Unsubscribe request"
    db_session.commit()
    assert client.get(endpoint).json() == []

    candidate.suppressed_at = None
    candidate.suppression_reason = None

    lead = db_session.get(
        Lead,
        candidate.lead_id,
    )
    assert lead is not None
    lead.status = "closed"
    db_session.commit()

    assert client.get(endpoint).json() == []


def test_due_follow_ups_require_operator(
    client,
    db_session,
):
    operator = make_operator(db_session)
    operator.is_platform_admin = False
    db_session.commit()

    response = client.get(
        "/api/v1/products/"
        "workflow-automation/"
        "prospecting/follow-ups/due"
    )

    assert response.status_code == 403
