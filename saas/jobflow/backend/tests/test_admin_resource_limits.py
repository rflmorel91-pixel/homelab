from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import func, select

from app.models import AdminAuditLog, Tenant, TenantMembership, TenantResourceLimit
from tests.test_admin import make_platform_admin
from tests.test_prestamodesk_administration import add_member, headers, ADMIN
from tests.test_prestamodesk_collections import create_tenant
from tests.test_prestamodesk_loans import (
    LOANS_URL, create_borrower, loan_payload,
)

EMPTY = {"active_memberships": None, "active_loans": None}
PLAN = {"active_memberships": 3, "active_loans": 100}
ACTION = "tenant.resource_limits_changed"


def setup(db):
    operator = make_platform_admin(db)
    tenant = create_tenant(
        db, client_number=990, slug="operator-resource-limits",
    )
    db.commit()
    return tenant, operator, f"/api/v1/admin/tenants/{tenant.id}/resource-limits"


def payload(limits=PLAN, expected=EMPTY):
    return {
        "expected_limits": dict(expected),
        "limits": dict(limits),
        "reason": "Synthetic approved capacity assignment",
    }


def audit_count(db):
    return db.scalar(select(func.count(AdminAuditLog.id)).where(
        AdminAuditLog.action == ACTION,
    ))


def test_get_does_not_assign_limits(client, db_session):
    tenant, _, url = setup(db_session)
    response = client.get(url)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {"tenant_id": tenant.id, "limits": EMPTY}
    assert db_session.scalar(select(func.count(TenantResourceLimit.tenant_id))) == 0
    assert audit_count(db_session) == 0


def test_assignment_is_audited_and_noop_is_idempotent(client, db_session):
    tenant, operator, url = setup(db_session)
    response = client.put(url, json=payload())
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["limits"] == PLAN
    assert client.get(url).json()["limits"] == PLAN

    event = db_session.scalar(select(AdminAuditLog).where(
        AdminAuditLog.action == ACTION,
    ))
    assert event.operator_user_id == operator.id
    assert event.tenant_id == tenant.id
    assert event.before_data == {"limits": EMPTY}
    assert event.after_data == {
        "limits": PLAN, "reason": payload()["reason"],
    }

    same = client.put(url, json=payload(expected=PLAN))
    assert same.status_code == 200
    assert audit_count(db_session) == 1


def test_stale_update_is_rejected(client, db_session):
    _, _, url = setup(db_session)
    assert client.put(url, json=payload()).status_code == 200
    stale = client.put(url, json=payload(
        {"active_memberships": 5, "active_loans": 200},
    ))
    assert stale.status_code == 409
    assert client.get(url).json()["limits"] == PLAN
    assert audit_count(db_session) == 1


def test_removal_is_explicit_and_preserves_other_resources(client, db_session):
    tenant, _, url = setup(db_session)
    db_session.add(TenantResourceLimit(
        tenant_id=tenant.id, resource_key="future.resource", maximum_count=7,
    ))
    db_session.commit()
    assert client.put(url, json=payload()).status_code == 200
    removed = client.put(url, json=payload(EMPTY, PLAN))
    assert removed.status_code == 200
    assert client.get(url).json()["limits"] == EMPTY
    assert db_session.get(
        TenantResourceLimit, (tenant.id, "future.resource"),
    ).maximum_count == 7
    assert audit_count(db_session) == 2


@pytest.mark.parametrize("bad", [-1, True, 1.5, "3", 2147483648])
def test_invalid_counts_are_rejected(client, db_session, bad):
    _, _, url = setup(db_session)
    body = payload()
    body["limits"]["active_memberships"] = bad
    assert client.put(url, json=body).status_code == 422
    assert client.get(url).json()["limits"] == EMPTY
    assert audit_count(db_session) == 0


@pytest.mark.parametrize("case", ["missing_expected", "missing_field", "extra", "blank_reason"])
def test_incomplete_or_ambiguous_changes_are_rejected(client, db_session, case):
    _, _, url = setup(db_session)
    body = payload()
    if case == "missing_expected":
        del body["expected_limits"]
    elif case == "missing_field":
        del body["limits"]["active_loans"]
    elif case == "extra":
        body["limits"]["unknown_resource"] = 4
    else:
        body["reason"] = " " * 20
    assert client.put(url, json=body).status_code == 422
    assert client.get(url).json()["limits"] == EMPTY


@pytest.mark.parametrize(
    "role", ["owner", "administrator", "supervisor", "collector", "cashier", "member"],
)
def test_customer_roles_cannot_view_or_assign_limits(client, db_session, role):
    tenant = create_tenant(
        db_session, client_number=991, slug="customer-limit-denial",
    )
    user, _ = add_member(db_session, tenant, role, role)
    url = f"/api/v1/admin/tenants/{tenant.id}/resource-limits"
    h = headers(user, tenant)
    assert client.get(url, headers=h).status_code == 403
    assert client.put(url, headers=h, json=payload()).status_code == 403
    assert audit_count(db_session) == 0


def test_unauthenticated_requests_are_denied(raw_client):
    url = "/api/v1/admin/tenants/999/resource-limits"
    assert raw_client.get(url).status_code == 401
    assert raw_client.put(url, json=payload()).status_code == 401


def test_missing_and_wrong_product_tenants_are_rejected(client, db_session):
    make_platform_admin(db_session)
    missing = "/api/v1/admin/tenants/999999/resource-limits"
    assert client.get(missing).status_code == 404
    assert client.put(missing, json=payload()).status_code == 404

    # The client fixture's tenant belongs to JobFlow.
    tenant = db_session.scalar(select(Tenant).order_by(Tenant.id))
    url = f"/api/v1/admin/tenants/{tenant.id}/resource-limits"
    assert client.get(url).status_code == 422
    assert client.put(url, json=payload()).status_code == 422
    assert audit_count(db_session) == 0


def test_zero_limits_block_additions_without_removing_access(client, db_session):
    tenant, _, url = setup(db_session)
    owner, membership = add_member(db_session, tenant, "owner", "limited-owner")
    borrower = create_borrower(db_session, tenant)
    h = headers(owner, tenant)
    zero = {"active_memberships": 0, "active_loans": 0}
    assert client.put(url, json=payload(zero)).status_code == 200

    assert client.get(ADMIN + "/team", headers=h).status_code == 200
    assert client.post(
        LOANS_URL, headers=h, json=loan_payload(borrower.id),
    ).status_code == 409
    assert client.post(ADMIN + "/invitations", headers=h, json={
        "display_name": "Blocked",
        "email": "blocked-resource-limit@example.test",
        "role": "cashier",
    }).status_code == 409

    db_session.refresh(membership)
    assert membership.is_active
    assert client.put(url, json=payload(EMPTY, zero)).status_code == 200
    assert client.post(
        LOANS_URL, headers=h, json=loan_payload(borrower.id),
    ).status_code == 201


def test_competing_assignments_cannot_overwrite_reviewed_values(client, db_session):
    _, _, url = setup(db_session)
    db_session.rollback()
    barrier = Barrier(2)
    offers = [
        PLAN,
        {"active_memberships": 5, "active_loans": 200},
    ]

    def submit(limits):
        barrier.wait(timeout=10)
        return client.put(url, json=payload(limits)).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(submit, limits) for limits in offers]
        results = [future.result(timeout=25) for future in futures]
    assert sorted(results) == [200, 409]
    assert client.get(url).json()["limits"] in offers
    db_session.expire_all()
    assert audit_count(db_session) == 1
