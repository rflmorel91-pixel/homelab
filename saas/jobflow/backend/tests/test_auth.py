from datetime import datetime, timedelta, timezone

import jwt

from app.models import User
from app.security import (
    JWT_ALGORITHM,
    JWT_SECRET,
    decode_access_token,
    hash_password,
)


def create_login_user(
    db_session,
    *,
    email="login@example.com",
    password="correct-password",
    is_active=True,
):
    user = User(
        email=email,
        display_name="Login Test User",
        password_hash=hash_password(password),
        is_active=is_active,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def test_login_returns_access_token(raw_client, db_session):
    user = create_login_user(db_session)

    response = raw_client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "correct-password",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["token_type"] == "bearer"
    assert decode_access_token(body["access_token"]) == user.id


def test_login_rejects_wrong_password(raw_client, db_session):
    user = create_login_user(db_session)

    response = raw_client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_rejects_unknown_email(raw_client):
    response = raw_client.post(
        "/api/v1/auth/login",
        json={
            "email": "missing@example.com",
            "password": "correct-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_rejects_inactive_user(raw_client, db_session):
    user = create_login_user(
        db_session,
        email="inactive@example.com",
        is_active=False,
    )

    response = raw_client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "correct-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_token_accesses_protected_tenant_resource(
    raw_client,
    db_session,
):
    from app.models import Tenant, TenantMembership

    user = create_login_user(
        db_session,
        email="integration@example.com",
        password="integration-password",
    )

    tenant = Tenant(

        product_id=1,
        name="Integration Tenant",
        slug="integration-tenant",
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    membership = TenantMembership(
        tenant_id=tenant.id,
        user_id=user.id,
        role="member",
    )
    db_session.add(membership)
    db_session.commit()

    login_response = raw_client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "integration-password",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = raw_client.get(
        "/api/v1/customers/",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": str(tenant.id),
        },
    )

    assert response.status_code == 200
    assert response.json() == []


def test_expired_access_token_returns_401(raw_client, db_session):
    user = create_login_user(
        db_session,
        email="expired-token@example.com",
    )

    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub": str(user.id),
            "iat": now - timedelta(minutes=31),
            "exp": now - timedelta(minutes=1),
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )

    response = raw_client.get(
        "/api/v1/customers/",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": "1",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_login_sets_secure_httponly_cookie(raw_client, db_session):
    user = create_login_user(
        db_session,
        email="cookie@example.com",
        password="cookie-password",
    )

    response = raw_client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "cookie-password",
        },
    )

    assert response.status_code == 200

    set_cookie = response.headers["set-cookie"]

    assert "jobflow_access_token=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "Secure" in set_cookie
    assert "SameSite=strict" in set_cookie
    assert "Max-Age=1800" in set_cookie


def test_cookie_authenticates_protected_tenant_resource(
    raw_client,
    db_session,
):
    from app.models import Tenant, TenantMembership

    user = create_login_user(
        db_session,
        email="cookie-auth@example.com",
        password="cookie-auth-password",
    )

    tenant = Tenant(

        product_id=1,
        name="Cookie Auth Tenant",
        slug="cookie-auth-tenant",
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    db_session.add(
        TenantMembership(
            tenant_id=tenant.id,
            user_id=user.id,
            role="member",
        )
    )
    db_session.commit()

    login_response = raw_client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "cookie-auth-password",
        },
    )

    assert login_response.status_code == 200

    response = raw_client.get(
        "/api/v1/customers/",
        headers={
            "X-Tenant-ID": str(tenant.id),
        },
    )

    assert response.status_code == 200
    assert response.json() == []


def test_logout_clears_authentication_cookie(raw_client, db_session):
    user = create_login_user(
        db_session,
        email="logout@example.com",
        password="logout-password",
    )

    login_response = raw_client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "logout-password",
        },
    )

    assert login_response.status_code == 200
    assert "jobflow_access_token" in raw_client.cookies

    logout_response = raw_client.post(
        "/api/v1/auth/logout",
    )

    assert logout_response.status_code == 200
    assert logout_response.json() == {
        "status": "signed_out",
    }

    assert "jobflow_access_token" not in raw_client.cookies

    set_cookie = logout_response.headers["set-cookie"]

    assert "jobflow_access_token=" in set_cookie
    assert "Max-Age=0" in set_cookie
