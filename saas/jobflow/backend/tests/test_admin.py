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


def test_platform_admin_can_add_tenant_membership(
    client,
    db_session,
):
    from app.models import Tenant, TenantMembership, User

    make_platform_admin(db_session)

    tenant = db_session.scalar(select(Tenant))
    assert tenant is not None

    user = User(
        email="admin-membership-test@example.com",
        display_name="Admin Membership Test",
        password_hash="unused",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    response = client.post(
        f"/api/v1/admin/tenants/{tenant.id}/memberships",
        json={
            "user_id": user.id,
            "role": "member",
        },
    )

    assert response.status_code == 201
    payload = response.json()

    assert payload["user_id"] == user.id
    assert payload["tenant_id"] == tenant.id
    assert payload["role"] == "member"

    membership = db_session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant.id,
            TenantMembership.user_id == user.id,
        )
    )
    assert membership is not None


def test_admin_cannot_add_duplicate_tenant_membership(
    client,
    db_session,
):
    from app.models import Tenant

    user = make_platform_admin(db_session)

    tenant = db_session.scalar(select(Tenant))
    assert tenant is not None

    response = client.post(
        f"/api/v1/admin/tenants/{tenant.id}/memberships",
        json={
            "user_id": user.id,
            "role": "member",
        },
    )

    assert response.status_code == 409


def test_platform_admin_can_change_membership_role(
    client,
    db_session,
):
    from app.models import TenantMembership

    make_platform_admin(db_session)

    membership = db_session.scalar(
        select(TenantMembership)
    )
    assert membership is not None

    response = client.put(
        f"/api/v1/admin/memberships/{membership.id}",
        json={"role": "member"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "member"


def test_admin_rejects_invalid_membership_role(
    client,
    db_session,
):
    from app.models import TenantMembership

    make_platform_admin(db_session)

    membership = db_session.scalar(
        select(TenantMembership)
    )
    assert membership is not None

    response = client.put(
        f"/api/v1/admin/memberships/{membership.id}",
        json={"role": "superuser"},
    )

    assert response.status_code == 422


def test_platform_admin_can_remove_membership(
    client,
    db_session,
):
    from app.models import TenantMembership

    make_platform_admin(db_session)

    membership = db_session.scalar(
        select(TenantMembership)
    )
    assert membership is not None
    membership_id = membership.id

    response = client.delete(
        f"/api/v1/admin/memberships/{membership_id}"
    )

    assert response.status_code == 204

    db_session.expire_all()

    assert db_session.get(
        TenantMembership,
        membership_id,
    ) is None


def test_admin_cannot_demote_last_tenant_owner(
    client,
    db_session,
):
    from app.models import TenantMembership

    make_platform_admin(db_session)

    membership = db_session.scalar(
        select(TenantMembership)
    )
    assert membership is not None

    membership.role = "owner"
    db_session.commit()

    response = client.put(
        f"/api/v1/admin/memberships/{membership.id}",
        json={"role": "member"},
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "Tenant must retain at least one owner"
    )


def test_admin_cannot_remove_last_tenant_owner(
    client,
    db_session,
):
    from app.models import TenantMembership

    make_platform_admin(db_session)

    membership = db_session.scalar(
        select(TenantMembership)
    )
    assert membership is not None

    membership.role = "owner"
    db_session.commit()

    response = client.delete(
        f"/api/v1/admin/memberships/{membership.id}"
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "Tenant must retain at least one owner"
    )


def test_admin_can_demote_owner_when_another_owner_exists(
    client,
    db_session,
):
    from app.models import TenantMembership, User

    make_platform_admin(db_session)

    membership = db_session.scalar(
        select(TenantMembership)
    )
    assert membership is not None

    membership.role = "owner"

    second_user = User(
        email="second-owner@example.com",
        display_name="Second Owner",
        password_hash="unused",
        is_active=True,
    )
    db_session.add(second_user)
    db_session.flush()

    second_owner = TenantMembership(
        tenant_id=membership.tenant_id,
        user_id=second_user.id,
        role="owner",
    )
    db_session.add(second_owner)
    db_session.commit()

    response = client.put(
        f"/api/v1/admin/memberships/{membership.id}",
        json={"role": "member"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "member"


def test_admin_can_remove_owner_when_another_owner_exists(
    client,
    db_session,
):
    from app.models import TenantMembership, User

    make_platform_admin(db_session)

    membership = db_session.scalar(
        select(TenantMembership)
    )
    assert membership is not None

    membership.role = "owner"

    second_user = User(
        email="removal-owner@example.com",
        display_name="Removal Owner",
        password_hash="unused",
        is_active=True,
    )
    db_session.add(second_user)
    db_session.flush()

    second_owner = TenantMembership(
        tenant_id=membership.tenant_id,
        user_id=second_user.id,
        role="owner",
    )
    db_session.add(second_owner)
    db_session.commit()

    membership_id = membership.id

    response = client.delete(
        f"/api/v1/admin/memberships/{membership_id}"
    )

    assert response.status_code == 204

    db_session.expire_all()

    assert db_session.get(
        TenantMembership,
        membership_id,
    ) is None
