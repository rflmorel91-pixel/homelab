from app.models import User
from app.security import decode_access_token, hash_password


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
