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


def test_login_returns_status_without_token(raw_client, db_session):
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

    assert body == {"status": "signed_in"}
    token = response.cookies["jobflow_access_token"]
    assert decode_access_token(token) == user.id
    assert token not in response.text


def test_login_normalizes_email(
    raw_client,
    db_session,
):
    user = create_login_user(
        db_session,
        email="MixedCase@example.com",
    )

    response = raw_client.post(
        "/api/v1/auth/login",
        json={
            "email": "  MIXEDCASE@EXAMPLE.COM  ",
            "password": "correct-password",
        },
    )

    assert response.status_code == 200
    assert decode_access_token(
        response.cookies["jobflow_access_token"]
    ) == user.id


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


def test_cookie_login_logout_protected_resource_cycle(
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

    assert login_response.json() == {"status": "signed_in"}
    assert "Authorization" not in raw_client.headers

    response = raw_client.get(
        "/api/v1/customers/",
        headers={"X-Tenant-ID": str(tenant.id)},
    )
    assert response.status_code == 200
    assert response.json() == []

    logout_response = raw_client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 200
    assert "jobflow_access_token" not in raw_client.cookies

    denied = raw_client.get(
        "/api/v1/customers/",
        headers={"X-Tenant-ID": str(tenant.id)},
    )
    assert denied.status_code == 401
    assert denied.json() == {"detail": "Authentication required"}


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
    assert "HttpOnly" in set_cookie
    assert "Secure" in set_cookie
    assert "SameSite=strict" in set_cookie
    assert "Path=/" in set_cookie


def test_authenticated_user_discovers_product_client_access(
    raw_client,
    db_session,
):
    from sqlalchemy import select

    from app.models import (
        Product,
        Tenant,
        TenantMembership,
    )

    user = create_login_user(
        db_session,
        email="product-access@example.com",
        password="product-access-password",
    )

    product = db_session.scalar(
        select(Product).where(
            Product.slug == "renewaldesk"
        )
    )
    assert product is not None

    client_tenant = Tenant(
        product_id=product.id,
        client_number=1,
        name="Product Access Client",
        slug="product-access-client",
    )

    validation_tenant = Tenant(
        product_id=product.id,
        name="Product Access Validation",
        slug="product-access-validation",
    )

    db_session.add_all([
        client_tenant,
        validation_tenant,
    ])
    db_session.commit()
    db_session.refresh(client_tenant)
    db_session.refresh(validation_tenant)

    db_session.add_all([
        TenantMembership(
            tenant_id=client_tenant.id,
            user_id=user.id,
            role="owner",
        ),
        TenantMembership(
            tenant_id=validation_tenant.id,
            user_id=user.id,
            role="member",
        ),
    ])
    db_session.commit()

    login_response = raw_client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "product-access-password",
        },
    )
    assert login_response.status_code == 200

    response = raw_client.get(
        "/api/v1/auth/products/renewaldesk/access"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["product"]["slug"] == "renewaldesk"
    assert (
        payload["product"]["landing_route"]
        == "/renewaldesk"
    )
    assert (
        payload["product"]["workspace_route"]
        == "/renewaldesk/app"
    )

    assert payload["clients"] == [
        {
            "tenant_id": client_tenant.id,
            "client_number": 1,
            "name": client_tenant.name,
            "slug": client_tenant.slug,
            "status": "active",
            "role": "owner",
        }
    ]


def test_product_access_returns_empty_without_membership(
    raw_client,
    db_session,
):
    user = create_login_user(
        db_session,
        email="no-product-access@example.com",
        password="no-product-access-password",
    )

    login_response = raw_client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "no-product-access-password",
        },
    )
    assert login_response.status_code == 200

    response = raw_client.get(
        "/api/v1/auth/products/renewaldesk/access"
    )

    assert response.status_code == 200
    assert response.json()["clients"] == []


def test_product_access_requires_authentication(raw_client):
    response = raw_client.get(
        "/api/v1/auth/products/renewaldesk/access"
    )

    assert response.status_code == 401


def test_product_access_rejects_unknown_product(
    raw_client,
    db_session,
):
    user = create_login_user(
        db_session,
        email="unknown-product@example.com",
        password="unknown-product-password",
    )

    login_response = raw_client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "unknown-product-password",
        },
    )
    assert login_response.status_code == 200

    response = raw_client.get(
        "/api/v1/auth/products/not-a-product/access"
    )

    assert response.status_code == 404
