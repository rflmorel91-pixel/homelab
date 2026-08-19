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
