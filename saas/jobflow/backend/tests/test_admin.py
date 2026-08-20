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

    assert payload["counts"]["products"] >= 1
    assert payload["counts"]["users"] >= 1
    assert payload["counts"]["tenants"] >= 1
    assert payload["counts"]["memberships"] >= 1

    assert any(
        product["slug"] == "jobflow"
        and product["workspace_key"] == "jobflow"
        and product["tenant_count"] >= 1
        for product in payload["products"]
    )

    assert all(
        "product_id" in tenant
        for tenant in payload["tenants"]
    )

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
    assert set(payload["counts"]) == {"memberships"}


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


def test_admin_overview_includes_operational_user_counts(
    client,
    db_session,
):
    from app.models import User

    make_platform_admin(db_session)

    inactive_user = User(
        email="inactive-admin-overview@example.com",
        display_name="Inactive Overview User",
        password_hash="unused",
        is_active=False,
        is_platform_admin=False,
    )

    db_session.add(inactive_user)
    db_session.commit()

    response = client.get("/api/v1/admin/overview")

    assert response.status_code == 200

    counts = response.json()["counts"]

    assert counts["users"] >= 2
    assert counts["active_users"] >= 1
    assert counts["active_users"] < counts["users"]
    assert counts["platform_admins"] >= 1


def test_platform_admin_can_deactivate_another_user(
    client,
    db_session,
):
    from app.models import User

    make_platform_admin(db_session)

    user = User(
        email="deactivate-user@example.com",
        display_name="Deactivate User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    response = client.put(
        f"/api/v1/admin/users/{user.id}",
        json={"is_active": False},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["id"] == user.id
    assert payload["is_active"] is False

    db_session.expire_all()

    updated = db_session.get(User, user.id)
    assert updated is not None
    assert updated.is_active is False


def test_platform_admin_can_grant_platform_admin(
    client,
    db_session,
):
    from app.models import User

    make_platform_admin(db_session)

    user = User(
        email="promote-admin@example.com",
        display_name="Promote Admin",
        is_active=True,
        is_platform_admin=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    response = client.put(
        f"/api/v1/admin/users/{user.id}",
        json={"is_platform_admin": True},
    )

    assert response.status_code == 200
    assert response.json()["is_platform_admin"] is True


def test_platform_admin_can_revoke_another_platform_admin(
    client,
    db_session,
):
    from app.models import User

    make_platform_admin(db_session)

    user = User(
        email="revoke-admin@example.com",
        display_name="Revoke Admin",
        is_active=True,
        is_platform_admin=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    response = client.put(
        f"/api/v1/admin/users/{user.id}",
        json={"is_platform_admin": False},
    )

    assert response.status_code == 200
    assert response.json()["is_platform_admin"] is False


def test_platform_admin_cannot_deactivate_self(
    client,
    db_session,
):
    user = make_platform_admin(db_session)

    response = client.put(
        f"/api/v1/admin/users/{user.id}",
        json={"is_active": False},
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "Current operator cannot deactivate themselves"
    )


def test_platform_admin_cannot_revoke_self(
    client,
    db_session,
):
    user = make_platform_admin(db_session)

    response = client.put(
        f"/api/v1/admin/users/{user.id}",
        json={"is_platform_admin": False},
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "Current operator cannot revoke their own platform access"
    )


def test_admin_user_update_returns_404(
    client,
    db_session,
):
    make_platform_admin(db_session)

    response = client.put(
        "/api/v1/admin/users/999999",
        json={"is_active": False},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_user_admin_change_creates_audit_log(
    client,
    db_session,
):
    from app.models import AdminAuditLog, User

    operator = make_platform_admin(db_session)

    user = User(
        email="audit-user@example.com",
        display_name="Audit User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    response = client.put(
        f"/api/v1/admin/users/{user.id}",
        json={"is_active": False},
    )

    assert response.status_code == 200

    db_session.expire_all()

    audit = db_session.scalar(
        select(AdminAuditLog).where(
            AdminAuditLog.action
            == "user.deactivated"
        )
    )

    assert audit is not None
    assert audit.operator_user_id == operator.id
    assert audit.target_type == "user"
    assert audit.target_id == user.id
    assert audit.before_data == {
        "is_active": True,
    }
    assert audit.after_data == {
        "is_active": False,
    }


def test_membership_role_change_creates_audit_log(
    client,
    db_session,
):
    from app.models import AdminAuditLog, TenantMembership

    operator = make_platform_admin(db_session)

    membership = db_session.scalar(
        select(TenantMembership)
    )
    assert membership is not None

    membership.role = "member"
    db_session.commit()

    response = client.put(
        f"/api/v1/admin/memberships/{membership.id}",
        json={"role": "owner"},
    )

    assert response.status_code == 200

    db_session.expire_all()

    audit = db_session.scalar(
        select(AdminAuditLog).where(
            AdminAuditLog.action
            == "membership.role_changed"
        )
    )

    assert audit is not None
    assert audit.operator_user_id == operator.id
    assert audit.target_type == "membership"
    assert audit.target_id == membership.id
    assert audit.tenant_id == membership.tenant_id
    assert audit.before_data == {"role": "member"}
    assert audit.after_data == {"role": "owner"}


def test_platform_admin_can_view_audit_log(
    client,
    db_session,
):
    from app.models import AdminAuditLog, User

    operator = make_platform_admin(db_session)

    target = User(
        email="audit-log-target@example.com",
        display_name="Audit Log Target",
        is_active=True,
    )
    db_session.add(target)
    db_session.commit()
    db_session.refresh(target)

    response = client.put(
        f"/api/v1/admin/users/{target.id}",
        json={"is_active": False},
    )

    assert response.status_code == 200

    response = client.get(
        "/api/v1/admin/audit-log"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["count"] >= 1
    assert len(payload["events"]) >= 1

    event = payload["events"][0]

    assert event["operator_user_id"] == operator.id
    assert event["action"] == "user.deactivated"
    assert event["target_type"] == "user"
    assert event["target_id"] == target.id
    assert event["before_data"] == {
        "is_active": True,
    }
    assert event["after_data"] == {
        "is_active": False,
    }


def test_non_platform_admin_cannot_view_audit_log(
    client,
):
    response = client.get(
        "/api/v1/admin/audit-log"
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_view_audit_log(
    raw_client,
):
    response = raw_client.get(
        "/api/v1/admin/audit-log"
    )

    assert response.status_code == 401


def test_platform_admin_can_suspend_tenant(
    client,
    db_session,
):
    from app.models import AdminAuditLog, Tenant

    operator = make_platform_admin(db_session)

    tenant = db_session.scalar(select(Tenant))
    assert tenant is not None
    assert tenant.status == "active"

    response = client.post(
        f"/api/v1/admin/tenants/{tenant.id}/suspend"
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "suspended"
    assert payload["suspended_at"] is not None

    db_session.expire_all()

    tenant = db_session.get(Tenant, tenant.id)
    assert tenant is not None
    assert tenant.status == "suspended"
    assert tenant.suspended_at is not None

    audit = db_session.scalar(
        select(AdminAuditLog).where(
            AdminAuditLog.action == "tenant.suspended",
            AdminAuditLog.target_id == tenant.id,
        )
    )

    assert audit is not None
    assert audit.operator_user_id == operator.id
    assert audit.tenant_id == tenant.id
    assert audit.before_data == {
        "status": "active",
        "suspended_at": None,
    }
    assert audit.after_data["status"] == "suspended"
    assert audit.after_data["suspended_at"] is not None


def test_suspending_suspended_tenant_is_rejected(
    client,
    db_session,
):
    from app.models import Tenant

    make_platform_admin(db_session)

    tenant = db_session.scalar(select(Tenant))
    assert tenant is not None

    tenant.status = "suspended"
    db_session.commit()

    response = client.post(
        f"/api/v1/admin/tenants/{tenant.id}/suspend"
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "Tenant is already suspended"
    )


def test_platform_admin_can_reactivate_tenant(
    client,
    db_session,
):
    from datetime import datetime, timezone

    from app.models import AdminAuditLog, Tenant

    operator = make_platform_admin(db_session)

    tenant = db_session.scalar(select(Tenant))
    assert tenant is not None

    tenant.status = "suspended"
    tenant.suspended_at = datetime.now(timezone.utc)
    db_session.commit()

    response = client.post(
        f"/api/v1/admin/tenants/{tenant.id}/reactivate"
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "active"
    assert payload["suspended_at"] is None

    db_session.expire_all()

    tenant = db_session.get(Tenant, tenant.id)
    assert tenant is not None
    assert tenant.status == "active"
    assert tenant.suspended_at is None

    audit = db_session.scalar(
        select(AdminAuditLog).where(
            AdminAuditLog.action == "tenant.reactivated",
            AdminAuditLog.target_id == tenant.id,
        )
    )

    assert audit is not None
    assert audit.operator_user_id == operator.id
    assert audit.tenant_id == tenant.id
    assert audit.before_data["status"] == "suspended"
    assert audit.after_data == {
        "status": "active",
        "suspended_at": None,
    }


def test_reactivating_active_tenant_is_rejected(
    client,
    db_session,
):
    from app.models import Tenant

    make_platform_admin(db_session)

    tenant = db_session.scalar(select(Tenant))
    assert tenant is not None
    assert tenant.status == "active"

    response = client.post(
        f"/api/v1/admin/tenants/{tenant.id}/reactivate"
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "Tenant is already active"
    )


def test_non_platform_admin_cannot_suspend_tenant(
    client,
    db_session,
):
    from app.models import Tenant

    tenant = db_session.scalar(select(Tenant))
    assert tenant is not None

    response = client.post(
        f"/api/v1/admin/tenants/{tenant.id}/suspend"
    )

    assert response.status_code == 403
