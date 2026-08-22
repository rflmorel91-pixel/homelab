from datetime import timedelta

from sqlalchemy import select

from app.api.invitations import utc_now_naive
from app.models import (
    AdminAuditLog,
    Lead,
    Product,
    User,
    UserInvitation,
)
from app.security import (
    hash_invitation_token,
    verify_password,
)


def make_platform_admin(db_session):
    user = db_session.scalar(
        select(User).where(
            User.email == "default-test-user@example.com"
        )
    )
    assert user is not None

    user.is_platform_admin = True
    db_session.commit()

    return user


def create_lead(
    db_session,
    *,
    status="qualified",
    email="invited.user@example.com",
):
    product = db_session.scalar(
        select(Product).order_by(Product.id)
    )
    assert product is not None

    lead = Lead(
        product_id=product.id,
        business_name="Invited Business",
        contact_name="Invited User",
        email=email,
        phone=None,
        service_type="Pilot",
        message=None,
        status=status,
    )
    db_session.add(lead)
    db_session.commit()
    db_session.refresh(lead)

    return lead, product


def create_invitation(client, db_session):
    make_platform_admin(db_session)
    lead, product = create_lead(db_session)

    response = client.post(
        "/api/v1/admin/user-invitations",
        json={
            "lead_id": lead.id,
        },
    )

    assert response.status_code == 201

    return response, lead, product


def token_from_activation_path(path):
    return path.split("token=", 1)[1]


def test_platform_admin_creates_lead_linked_hashed_invitation(
    client,
    db_session,
):
    response, lead, product = create_invitation(
        client,
        db_session,
    )
    body = response.json()

    assert body["lead"]["id"] == lead.id
    assert body["lead"]["business_name"] == lead.business_name
    assert body["product"]["id"] == product.id
    assert body["product"]["name"] == product.name
    assert body["product"]["slug"] == product.slug
    assert body["email"] == lead.email
    assert body["display_name"] == lead.contact_name
    assert response.headers["cache-control"] == "no-store"

    assert body["activation_path"].startswith(
        "/accept-invitation#token="
    )
    assert "?token=" not in body["activation_path"]

    token = token_from_activation_path(
        body["activation_path"]
    )

    invitation = db_session.get(
        UserInvitation,
        body["id"],
    )
    assert invitation is not None
    assert invitation.lead_id == lead.id
    assert invitation.token_hash == hash_invitation_token(token)
    assert invitation.token_hash != token
    assert invitation.accepted_at is None
    assert invitation.accepted_user_id is None

    audit = db_session.scalar(
        select(AdminAuditLog).where(
            AdminAuditLog.action
            == "user.invitation_created"
        )
    )
    assert audit is not None
    assert audit.after_data["lead_id"] == lead.id
    assert audit.after_data["product_id"] == product.id
    assert audit.after_data["product_slug"] == product.slug
    assert "token" not in str(audit.after_data).lower()


def test_non_platform_admin_cannot_create_invitation(
    client,
    db_session,
):
    lead, _ = create_lead(db_session)

    response = client.post(
        "/api/v1/admin/user-invitations",
        json={"lead_id": lead.id},
    )

    assert response.status_code == 403


def test_cannot_invite_unknown_lead(
    client,
    db_session,
):
    make_platform_admin(db_session)

    response = client.post(
        "/api/v1/admin/user-invitations",
        json={"lead_id": 999999},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Lead not found"


def test_cannot_invite_unqualified_lead(
    client,
    db_session,
):
    make_platform_admin(db_session)
    lead, _ = create_lead(
        db_session,
        status="contacted",
    )

    response = client.post(
        "/api/v1/admin/user-invitations",
        json={"lead_id": lead.id},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Invitation requires a qualified, "
        "unprovisioned lead"
    )


def test_cannot_invite_existing_user(
    client,
    db_session,
):
    make_platform_admin(db_session)
    lead, _ = create_lead(
        db_session,
        email="default-test-user@example.com",
    )

    response = client.post(
        "/api/v1/admin/user-invitations",
        json={"lead_id": lead.id},
    )

    assert response.status_code == 409


def test_cannot_create_duplicate_active_invitation(
    client,
    db_session,
):
    response, lead, _ = create_invitation(
        client,
        db_session,
    )
    assert response.status_code == 201

    duplicate = client.post(
        "/api/v1/admin/user-invitations",
        json={"lead_id": lead.id},
    )

    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == (
        "An active invitation already exists for this lead"
    )


def test_invitation_acceptance_creates_login_user(
    client,
    raw_client,
    db_session,
):
    invitation_response, lead, _ = create_invitation(
        client,
        db_session,
    )
    token = token_from_activation_path(
        invitation_response.json()["activation_path"]
    )

    response = raw_client.post(
        "/api/v1/auth/invitations/accept",
        json={
            "token": token,
            "password": "a-secure-customer-password",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "activated"
    assert payload["product"]["id"] == lead.product_id
    assert payload["product"]["slug"] == "jobflow"
    assert payload["product"]["landing_route"] == "/"
    assert payload["product"]["workspace_route"] == "/app"
    assert response.headers["cache-control"] == "no-store"

    user = db_session.scalar(
        select(User).where(
            User.email == lead.email
        )
    )
    assert user is not None
    assert user.is_active is True
    assert user.is_platform_admin is False
    assert verify_password(
        "a-secure-customer-password",
        user.password_hash,
    )

    invitation = db_session.scalar(
        select(UserInvitation).where(
            UserInvitation.lead_id == lead.id
        )
    )
    assert invitation is not None
    assert invitation.accepted_at is not None
    assert invitation.accepted_user_id == user.id

    login_response = raw_client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "a-secure-customer-password",
        },
    )
    assert login_response.status_code == 200


def test_invitation_is_single_use(
    client,
    raw_client,
    db_session,
):
    invitation_response, _, _ = create_invitation(
        client,
        db_session,
    )
    token = token_from_activation_path(
        invitation_response.json()["activation_path"]
    )
    payload = {
        "token": token,
        "password": "a-secure-customer-password",
    }

    first = raw_client.post(
        "/api/v1/auth/invitations/accept",
        json=payload,
    )
    second = raw_client.post(
        "/api/v1/auth/invitations/accept",
        json=payload,
    )

    assert first.status_code == 200
    assert second.status_code == 400


def test_expired_invitation_is_rejected(
    client,
    raw_client,
    db_session,
):
    invitation_response, _, _ = create_invitation(
        client,
        db_session,
    )
    token = token_from_activation_path(
        invitation_response.json()["activation_path"]
    )

    invitation = db_session.get(
        UserInvitation,
        invitation_response.json()["id"],
    )
    invitation.expires_at = (
        utc_now_naive() - timedelta(minutes=1)
    )
    db_session.commit()

    response = raw_client.post(
        "/api/v1/auth/invitations/accept",
        json={
            "token": token,
            "password": "a-secure-customer-password",
        },
    )

    assert response.status_code == 400


def test_revoked_invitation_is_rejected(
    client,
    raw_client,
    db_session,
):
    invitation_response, _, _ = create_invitation(
        client,
        db_session,
    )
    token = token_from_activation_path(
        invitation_response.json()["activation_path"]
    )

    invitation = db_session.get(
        UserInvitation,
        invitation_response.json()["id"],
    )
    invitation.revoked_at = utc_now_naive()
    db_session.commit()

    response = raw_client.post(
        "/api/v1/auth/invitations/accept",
        json={
            "token": token,
            "password": "a-secure-customer-password",
        },
    )

    assert response.status_code == 400


def test_invitation_rejects_short_password(
    client,
    raw_client,
    db_session,
):
    invitation_response, _, _ = create_invitation(
        client,
        db_session,
    )
    token = token_from_activation_path(
        invitation_response.json()["activation_path"]
    )

    response = raw_client.post(
        "/api/v1/auth/invitations/accept",
        json={
            "token": token,
            "password": "too-short",
        },
    )

    assert response.status_code == 422
