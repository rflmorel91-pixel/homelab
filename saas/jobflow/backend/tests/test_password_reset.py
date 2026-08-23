from datetime import timedelta
from urllib.parse import parse_qs, urlsplit

from sqlalchemy import select

from app.api import password_reset
from app.models import (
    PasswordResetToken,
    Product,
    Tenant,
    TenantMembership,
    User,
)
from app.security import (
    hash_invitation_token,
    hash_password,
)


def create_reset_account(
    db_session,
    *,
    email="reset-user@example.com",
):
    product = db_session.scalar(
        select(Product).where(
            Product.slug == "renewaldesk"
        )
    )
    assert product is not None

    user = User(
        email=email,
        display_name="Reset User",
        password_hash=hash_password(
            "original-password"
        ),
        is_active=True,
        is_platform_admin=False,
    )
    tenant = Tenant(
        product_id=product.id,
        client_number=990,
        name="Password Reset Client",
        slug="password-reset-client",
        status="active",
    )

    db_session.add_all([user, tenant])
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(tenant)

    membership = TenantMembership(
        tenant_id=tenant.id,
        user_id=user.id,
        role="member",
    )
    db_session.add(membership)
    db_session.commit()

    return user


def request_reset(
    raw_client,
    monkeypatch,
    db_session,
):
    sent = {}

    def fake_send_password_reset_email(**kwargs):
        sent.update(kwargs)

    monkeypatch.setenv(
        "PLATFORM_PUBLIC_BASE_URL",
        "https://jobflow.fieldlookers.com",
    )
    monkeypatch.setattr(
        password_reset,
        "send_password_reset_email",
        fake_send_password_reset_email,
    )

    user = create_reset_account(db_session)

    response = raw_client.post(
        "/api/v1/auth/password-reset/request",
        json={
            "email": user.email,
            "product_slug": "renewaldesk",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "accepted",
        "message": (
            "If an eligible account exists, "
            "a password reset email has been sent."
        ),
    }

    assert sent["to_email"] == user.email
    assert sent["product_name"] == "RenewalDesk"

    reset_url = sent["reset_url"]

    assert reset_url.startswith(
        "https://jobflow.fieldlookers.com/"
        "reset-password#"
    )

    fragment = parse_qs(
        urlsplit(reset_url).fragment
    )
    token = fragment["token"][0]

    assert fragment["product"] == ["renewaldesk"]

    record = db_session.scalar(
        select(PasswordResetToken)
    )
    assert record is not None
    assert record.token_hash == (
        hash_invitation_token(token)
    )
    assert token not in record.token_hash
    assert record.used_at is None

    return user, token, record


def test_password_reset_request_is_enumeration_safe(
    raw_client,
    monkeypatch,
    db_session,
):
    sent = []

    monkeypatch.setenv(
        "PLATFORM_PUBLIC_BASE_URL",
        "https://jobflow.fieldlookers.com",
    )
    monkeypatch.setattr(
        password_reset,
        "send_password_reset_email",
        lambda **kwargs: sent.append(kwargs),
    )

    response = raw_client.post(
        "/api/v1/auth/password-reset/request",
        json={
            "email": "missing@example.com",
            "product_slug": "renewaldesk",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert sent == []
    assert db_session.scalar(
        select(PasswordResetToken)
    ) is None


def test_password_reset_updates_password_and_is_single_use(
    raw_client,
    monkeypatch,
    db_session,
):
    user, token, _ = request_reset(
        raw_client,
        monkeypatch,
        db_session,
    )

    response = raw_client.post(
        "/api/v1/auth/password-reset/confirm",
        json={
            "token": token,
            "password": "replacement-password",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "password_updated",
        "product": {
            "slug": "renewaldesk",
            "workspace_route": "/renewaldesk/app",
        },
    }

    old_login = raw_client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "original-password",
        },
    )
    assert old_login.status_code == 401

    new_login = raw_client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "replacement-password",
        },
    )
    assert new_login.status_code == 200

    reused = raw_client.post(
        "/api/v1/auth/password-reset/confirm",
        json={
            "token": token,
            "password": "another-password",
        },
    )

    assert reused.status_code == 400
    assert reused.json()["detail"] == (
        "Reset link is invalid or expired"
    )


def test_password_reset_rejects_expired_token(
    raw_client,
    monkeypatch,
    db_session,
):
    _, token, record = request_reset(
        raw_client,
        monkeypatch,
        db_session,
    )

    record.expires_at = (
        password_reset.utc_now_naive()
        - timedelta(minutes=1)
    )
    db_session.commit()

    response = raw_client.post(
        "/api/v1/auth/password-reset/confirm",
        json={
            "token": token,
            "password": "replacement-password",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Reset link is invalid or expired"
    )
