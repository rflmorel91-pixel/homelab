from sqlalchemy import select

from app.models import Lead


def test_public_lead_can_be_created_without_auth(
    raw_client,
    db_session,
):
    response = raw_client.post(
        "/api/v1/public/leads",
        json={
            "business_name": "Morel Home Services",
            "contact_name": "Rafael Morel",
            "email": "pilot@example.com",
            "phone": "555-2000",
            "service_type": "Handyman",
            "message": (
                "Looking for a simpler way to manage jobs "
                "and customer requests."
            ),
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "received"
    assert response.json()["lead_id"] > 0

    lead = db_session.scalar(
        select(Lead).where(
            Lead.email == "pilot@example.com"
        )
    )

    assert lead is not None
    assert lead.business_name == "Morel Home Services"
    assert lead.contact_name == "Rafael Morel"
    assert lead.service_type == "Handyman"
    assert lead.status == "new"


def test_public_lead_optional_fields_can_be_omitted(
    raw_client,
    db_session,
):
    response = raw_client.post(
        "/api/v1/public/leads",
        json={
            "business_name": "Simple Landscaping",
            "contact_name": "Test Prospect",
            "email": "simple@example.com",
            "service_type": "Landscaping",
        },
    )

    assert response.status_code == 201

    lead = db_session.scalar(
        select(Lead).where(
            Lead.email == "simple@example.com"
        )
    )

    assert lead is not None
    assert lead.phone is None
    assert lead.message is None
    assert lead.status == "new"


def test_public_lead_rejects_server_controlled_fields(
    raw_client,
    db_session,
):
    response = raw_client.post(
        "/api/v1/public/leads",
        json={
            "business_name": "Malicious Prospect",
            "contact_name": "Bad Actor",
            "email": "bad@example.com",
            "service_type": "Testing",
            "status": "converted",
            "id": 999,
        },
    )

    assert response.status_code == 422

    assert db_session.scalar(
        select(Lead).where(
            Lead.email == "bad@example.com"
        )
    ) is None


def test_public_lead_rejects_blank_required_fields(
    raw_client,
    db_session,
):
    response = raw_client.post(
        "/api/v1/public/leads",
        json={
            "business_name": "   ",
            "contact_name": "Test Prospect",
            "email": "test@example.com",
            "service_type": "Handyman",
        },
    )

    assert response.status_code == 422

    assert db_session.scalar(
        select(Lead).where(
            Lead.email == "test@example.com"
        )
    ) is None
