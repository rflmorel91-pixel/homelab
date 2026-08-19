from sqlalchemy import select

from app.models import User


def get_default_user(db_session):
    user = db_session.scalar(
        select(User).where(
            User.email == "default-test-user@example.com"
        )
    )

    assert user is not None
    return user


def test_platform_admin_can_view_admin_overview(
    client,
    db_session,
):
    user = get_default_user(db_session)
    user.is_platform_admin = True
    db_session.commit()

    response = client.get("/api/v1/admin/overview")

    assert response.status_code == 200

    payload = response.json()

    assert payload["counts"]["users"] >= 1
    assert payload["counts"]["tenants"] >= 1
    assert payload["counts"]["memberships"] >= 1

    assert any(
        item["email"] == "default-test-user@example.com"
        for item in payload["users"]
    )


def test_non_platform_admin_cannot_view_admin_overview(
    client,
):
    response = client.get("/api/v1/admin/overview")

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "Platform operator access required"
    )


def test_unauthenticated_user_cannot_view_admin_overview(
    raw_client,
):
    response = raw_client.get("/api/v1/admin/overview")

    assert response.status_code == 401


def make_platform_admin(db_session):
    user = get_default_user(db_session)
    user.is_platform_admin = True
    db_session.commit()
    return user


def test_platform_admin_can_view_tenant_detail(
    client,
    db_session,
):
    make_platform_admin(db_session)

    overview = client.get("/api/v1/admin/overview")
    assert overview.status_code == 200

    tenant_id = overview.json()["tenants"][0]["id"]

    response = client.get(
        f"/api/v1/admin/tenants/{tenant_id}"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["tenant"]["id"] == tenant_id
    assert payload["counts"]["memberships"] >= 1
    assert "customers" in payload["counts"]
    assert "jobs" in payload["counts"]


def test_platform_admin_can_view_user_detail(
    client,
    db_session,
):
    user = make_platform_admin(db_session)

    response = client.get(
        f"/api/v1/admin/users/{user.id}"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["user"]["id"] == user.id
    assert payload["user"]["is_platform_admin"] is True
    assert len(payload["memberships"]) >= 1


def test_admin_tenant_detail_returns_404(
    client,
    db_session,
):
    make_platform_admin(db_session)

    response = client.get(
        "/api/v1/admin/tenants/999999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Tenant not found"


def test_admin_user_detail_returns_404(
    client,
    db_session,
):
    make_platform_admin(db_session)

    response = client.get(
        "/api/v1/admin/users/999999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
