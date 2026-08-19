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


def make_platform_admin(db_session):
    user = get_default_user(db_session)
    user.is_platform_admin = True
    db_session.commit()
    return user


def test_platform_admin_can_update_lead_status(
    client,
    db_session,
):
    make_platform_admin(db_session)
    lead = create_lead(db_session)

    response = client.put(
        f"/api/v1/leads/{lead.id}",
        json={
            "status": "contacted",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "contacted"

    db_session.refresh(lead)
    assert lead.status == "contacted"


def test_lead_status_progression(
    client,
    db_session,
):
    make_platform_admin(db_session)
    lead = create_lead(db_session)

    for status in (
        "contacted",
        "qualified",
        "converted",
    ):
        response = client.put(
            f"/api/v1/leads/{lead.id}",
            json={
                "status": status,
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == status


def test_lead_can_be_closed_after_contact(
    client,
    db_session,
):
    make_platform_admin(db_session)
    lead = create_lead(db_session)

    response = client.put(
        f"/api/v1/leads/{lead.id}",
        json={
            "status": "contacted",
        },
    )

    assert response.status_code == 200

    response = client.put(
        f"/api/v1/leads/{lead.id}",
        json={
            "status": "closed",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "closed"


def test_invalid_lead_status_transition_is_rejected(
    client,
    db_session,
):
    make_platform_admin(db_session)
    lead = create_lead(db_session)

    response = client.put(
        f"/api/v1/leads/{lead.id}",
        json={
            "status": "converted",
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Invalid lead status transition: new -> converted"
    )


def test_non_platform_admin_cannot_update_lead(
    client,
    db_session,
):
    lead = create_lead(db_session)

    response = client.put(
        f"/api/v1/leads/{lead.id}",
        json={
            "status": "contacted",
        },
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "Platform operator access required"
    )


def test_update_unknown_lead_returns_404(
    client,
    db_session,
):
    make_platform_admin(db_session)

    response = client.put(
        "/api/v1/leads/999999",
        json={
            "status": "contacted",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Lead not found"


def test_lead_update_rejects_extra_fields(
    client,
    db_session,
):
    make_platform_admin(db_session)
    lead = create_lead(db_session)

    response = client.put(
        f"/api/v1/leads/{lead.id}",
        json={
            "status": "contacted",
            "email": "override@example.com",
        },
    )

    assert response.status_code == 422
