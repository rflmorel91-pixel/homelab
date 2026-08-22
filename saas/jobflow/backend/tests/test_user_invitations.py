from datetime import timedelta

from sqlalchemy import select

from app.api.invitations import utc_now_naive
from app.models import (
    AdminAuditLog,
    Lead,
    Product,
    Tenant,
    TenantMembership,
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



def create_commercial_client(db_session):
    product = db_session.scalar(
        select(Product).order_by(Product.id)
    )
    assert product is not None

    tenant = Tenant(
        product_id=product.id,
        client_number=1,
        name="Invited Client",
        slug="invited-client",
        status="active",
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    return tenant, product


def test_platform_admin_creates_client_user_invitation(
    client,
    db_session,
):
    make_platform_admin(db_session)
    tenant, product = create_commercial_client(
        db_session
    )

    response = client.post(
        (
            f"/api/v1/admin/tenants/{tenant.id}"
            "/user-invitations"
        ),
        json={
            "display_name": "Client Member",
            "email": "CLIENT.MEMBER@example.com",
            "role": "member",
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["product"]["id"] == product.id
    assert payload["client"]["id"] == tenant.id
    assert payload["client"]["client_number"] == 1
    assert payload["email"] == "client.member@example.com"
    assert payload["role"] == "member"
    assert payload["activation_path"].startswith(
        "/accept-invitation#token="
    )

    invitation = db_session.get(
        UserInvitation,
        payload["id"],
    )

    assert invitation is not None
    assert invitation.lead_id is None
    assert invitation.tenant_id == tenant.id
    assert invitation.role == "member"


def test_client_invitation_acceptance_creates_membership(
    client,
    db_session,
):
    make_platform_admin(db_session)
    tenant, _ = create_commercial_client(
        db_session
    )

    create_response = client.post(
        (
            f"/api/v1/admin/tenants/{tenant.id}"
            "/user-invitations"
        ),
        json={
            "display_name": "New Client Owner",
            "email": "new-owner@example.com",
            "role": "owner",
        },
    )
    assert create_response.status_code == 201

    token = token_from_activation_path(
        create_response.json()["activation_path"]
    )

    accept_response = client.post(
        "/api/v1/auth/invitations/accept",
        json={
            "token": token,
            "password": "secure-client-password",
        },
    )

    assert accept_response.status_code == 200

    payload = accept_response.json()

    assert payload["status"] == "activated"
    assert payload["client"]["id"] == tenant.id
    assert payload["client"]["client_number"] == 1
    assert payload["client"]["role"] == "owner"

    user = db_session.scalar(
        select(User).where(
            User.email == "new-owner@example.com"
        )
    )
    assert user is not None
    assert verify_password(
        "secure-client-password",
        user.password_hash,
    )

    membership = db_session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant.id,
            TenantMembership.user_id == user.id,
        )
    )

    assert membership is not None
    assert membership.role == "owner"


def test_cannot_invite_user_to_validation_workspace(
    client,
    db_session,
):
    make_platform_admin(db_session)

    tenant = db_session.scalar(
        select(Tenant).where(
            Tenant.client_number.is_(None)
        )
    )
    assert tenant is not None

    response = client.post(
        (
            f"/api/v1/admin/tenants/{tenant.id}"
            "/user-invitations"
        ),
        json={
            "display_name": "Invalid Invite",
            "email": "invalid@example.com",
            "role": "member",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Client invitations require a "
        "commercial client workspace"
    )


def test_cannot_create_duplicate_active_client_invitation(
    client,
    db_session,
):
    make_platform_admin(db_session)
    tenant, _ = create_commercial_client(
        db_session
    )

    path = (
        f"/api/v1/admin/tenants/{tenant.id}"
        "/user-invitations"
    )
    request = {
        "display_name": "Duplicate Invite",
        "email": "duplicate@example.com",
        "role": "member",
    }

    first = client.post(path, json=request)
    second = client.post(path, json=request)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"] == (
        "An active invitation already exists "
        "for this client and email"
    )



def test_platform_admin_lists_client_invitations_without_token(
    client,
    db_session,
):
    make_platform_admin(db_session)
    tenant, _ = create_commercial_client(
        db_session
    )

    create_response = client.post(
        (
            f"/api/v1/admin/tenants/{tenant.id}"
            "/user-invitations"
        ),
        json={
            "display_name": "Pending Member",
            "email": "pending-member@example.com",
            "role": "member",
        },
    )
    assert create_response.status_code == 201

    response = client.get(
        (
            f"/api/v1/admin/tenants/{tenant.id}"
            "/user-invitations"
        )
    )

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"

    payload = response.json()

    assert len(payload["invitations"]) == 1

    invitation = payload["invitations"][0]

    assert invitation["email"] == "pending-member@example.com"
    assert invitation["role"] == "member"
    assert invitation["status"] == "pending"
    assert "token" not in str(payload).lower()
    assert "activation_path" not in str(payload)


def test_platform_admin_revokes_pending_client_invitation(
    client,
    db_session,
):
    make_platform_admin(db_session)
    tenant, _ = create_commercial_client(
        db_session
    )

    create_response = client.post(
        (
            f"/api/v1/admin/tenants/{tenant.id}"
            "/user-invitations"
        ),
        json={
            "display_name": "Revoked Member",
            "email": "revoked-member@example.com",
            "role": "member",
        },
    )
    assert create_response.status_code == 201

    invitation_id = create_response.json()["id"]

    response = client.post(
        (
            f"/api/v1/admin/tenants/{tenant.id}"
            f"/user-invitations/{invitation_id}/revoke"
        )
    )

    assert response.status_code == 200
    assert response.json()["status"] == "revoked"

    invitation = db_session.get(
        UserInvitation,
        invitation_id,
    )

    assert invitation is not None
    assert invitation.revoked_at is not None

    audit = db_session.scalar(
        select(AdminAuditLog).where(
            AdminAuditLog.action
            == "client_user.invitation_revoked"
        )
    )

    assert audit is not None
    assert audit.tenant_id == tenant.id
    assert "token" not in str(audit.after_data).lower()


def test_revoked_client_invitation_cannot_be_accepted(
    client,
    db_session,
):
    make_platform_admin(db_session)
    tenant, _ = create_commercial_client(
        db_session
    )

    create_response = client.post(
        (
            f"/api/v1/admin/tenants/{tenant.id}"
            "/user-invitations"
        ),
        json={
            "display_name": "Blocked Member",
            "email": "blocked-member@example.com",
            "role": "member",
        },
    )
    assert create_response.status_code == 201

    token = token_from_activation_path(
        create_response.json()["activation_path"]
    )
    invitation_id = create_response.json()["id"]

    revoke_response = client.post(
        (
            f"/api/v1/admin/tenants/{tenant.id}"
            f"/user-invitations/{invitation_id}/revoke"
        )
    )
    assert revoke_response.status_code == 200

    accept_response = client.post(
        "/api/v1/auth/invitations/accept",
        json={
            "token": token,
            "password": "revoked-client-password",
        },
    )

    assert accept_response.status_code == 400
    assert accept_response.json()["detail"] == (
        "Invitation is invalid or expired"
    )
