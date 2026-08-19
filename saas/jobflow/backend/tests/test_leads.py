from sqlalchemy import select

from app.models import Lead, User


def create_lead(db_session):
    lead = Lead(
        business_name="Lead Test Services",
        contact_name="Lead Prospect",
        email="protected-lead@example.com",
        service_type="Handyman",
        status="new",
    )
    db_session.add(lead)
    db_session.commit()
    db_session.refresh(lead)
    return lead


def get_default_user(db_session):
    user = db_session.scalar(
        select(User).where(
            User.email == "default-test-user@example.com"
        )
    )

    assert user is not None
    return user


def test_platform_admin_can_list_leads(
    client,
    db_session,
):
    user = get_default_user(db_session)
    user.is_platform_admin = True
    db_session.commit()

    lead = create_lead(db_session)

    response = client.get("/api/v1/leads/")

    assert response.status_code == 200

    payload = response.json()

    assert any(
        item["id"] == lead.id
        and item["email"] == "protected-lead@example.com"
        for item in payload
    )


def test_non_platform_admin_cannot_list_leads(
    client,
    db_session,
):
    create_lead(db_session)

    response = client.get("/api/v1/leads/")

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "Platform operator access required"
    )


def test_unauthenticated_user_cannot_list_leads(
    raw_client,
    db_session,
):
    create_lead(db_session)

    response = raw_client.get("/api/v1/leads/")

    assert response.status_code == 401
