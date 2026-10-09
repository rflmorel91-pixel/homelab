import pytest
from sqlalchemy import select

from app.models import AdminAuditLog, Product, TenantMembership, User
from app.security import create_access_token
from tests.test_prestamodesk_collections import create_tenant, create_loan, BASE_URL

ADMIN = BASE_URL + "/administration"


def add_member(db, tenant, role, suffix, active=True):
    user = User(email=f"admin-suite-{suffix}@example.test", display_name=f"Team {suffix}", is_active=True)
    db.add(user)
    db.flush()
    membership = TenantMembership(tenant_id=tenant.id, user_id=user.id, role=role, is_active=active)
    db.add(membership)
    db.commit()
    return user, membership


def headers(user, tenant):
    return {"Authorization": f"Bearer {create_access_token(user.id)}", "X-Tenant-ID": str(tenant.id)}


@pytest.mark.parametrize("role,allowed", [("owner", True), ("administrator", True), ("supervisor", False),
                                           ("collector", False), ("cashier", False), ("member", False), ("unknown", False)])
def test_administration_access_matrix(raw_client, db_session, role, allowed):
    tenant = create_tenant(db_session, client_number=950, slug="admin-role-matrix")
    user, _ = add_member(db_session, tenant, role, role)
    response = raw_client.get(ADMIN + "/team", headers=headers(user, tenant))
    assert response.status_code == (200 if allowed else 403)
    if allowed:
        assert response.headers["cache-control"] == "no-store"
        assert {r["role"] for r in response.json()["roles"]} == {"owner", "administrator", "supervisor", "collector", "cashier", "member"}


@pytest.mark.parametrize("role", ["owner", "administrator"])
def test_administrator_cannot_manage_privileged_roles(raw_client, db_session, role):
    tenant = create_tenant(db_session, client_number=951, slug="admin-escalation")
    admin, admin_membership = add_member(db_session, tenant, "administrator", "admin")
    _, privileged = add_member(db_session, tenant, role, "privileged")
    _, worker = add_member(db_session, tenant, "cashier", "worker")
    h = headers(admin, tenant)
    assert raw_client.put(f"{ADMIN}/memberships/{worker.id}/role", headers=h, json={"role": role}).status_code == 403
    assert raw_client.put(f"{ADMIN}/memberships/{privileged.id}/role", headers=h, json={"role": "cashier"}).status_code == 403
    assert raw_client.put(f"{ADMIN}/memberships/{privileged.id}/status", headers=h, json={"is_active": False}).status_code == 403
    assert raw_client.put(f"{ADMIN}/memberships/{admin_membership.id}/role", headers=h, json={"role": "owner"}).status_code == 403
    assert raw_client.post(ADMIN + "/invitations", headers=h, json={"display_name": "Privileged", "email": "privileged-new@example.test", "role": role}).status_code == 403
    assert raw_client.get("/api/v1/client/team", headers=h).status_code == 403
    db_session.refresh(worker)
    assert worker.role == "cashier"


def test_role_changes_audited_and_foreign_tenants_denied(raw_client, db_session):
    tenant = create_tenant(db_session, client_number=952, slug="admin-own-team")
    other = create_tenant(db_session, client_number=953, slug="admin-other-team")
    admin, _ = add_member(db_session, tenant, "administrator", "manager")
    _, worker = add_member(db_session, tenant, "cashier", "worker")
    _, foreign = add_member(db_session, other, "cashier", "foreign")
    h = headers(admin, tenant)
    assert raw_client.put(f"{ADMIN}/memberships/{foreign.id}/role", headers=h, json={"role": "supervisor"}).status_code == 404
    assert raw_client.put(f"{ADMIN}/memberships/{foreign.id}/status", headers=h, json={"is_active": False}).status_code == 404
    response = raw_client.put(f"{ADMIN}/memberships/{worker.id}/role", headers=h, json={"role": "supervisor"})
    assert response.status_code == 200
    audit = raw_client.get(ADMIN + "/audit", headers=h).json()
    assert len(audit) == 1
    assert audit[0]["before"]["role"] == "cashier"
    assert audit[0]["after"]["role"] == "supervisor"
    assert audit[0]["actor_user_id"] == admin.id


def test_suspension_is_tenant_scoped_and_immediate(raw_client, db_session):
    tenant = create_tenant(db_session, client_number=954, slug="suspend-here")
    other = create_tenant(db_session, client_number=955, slug="retain-there")
    owner, _ = add_member(db_session, tenant, "owner", "owner")
    user, worker = add_member(db_session, tenant, "cashier", "multi-tenant")
    db_session.add(TenantMembership(tenant_id=other.id, user_id=user.id, role="cashier"))
    db_session.commit()
    response = raw_client.put(f"{ADMIN}/memberships/{worker.id}/status", headers=headers(owner, tenant), json={"is_active": False})
    assert response.status_code == 200
    assert raw_client.get(BASE_URL + "/cashier/loans", headers=headers(user, tenant)).status_code == 403
    assert raw_client.get(BASE_URL + "/cashier/loans", headers=headers(user, other)).status_code == 200
    access = raw_client.get("/api/v1/auth/products/prestamodesk/access", headers=headers(user, tenant)).json()
    assert [c["tenant_id"] for c in access["clients"]] == [other.id]
    db_session.refresh(user)
    assert user.is_active
    assert raw_client.put(f"{ADMIN}/memberships/{worker.id}/status", headers=headers(owner, tenant), json={"is_active": True}).status_code == 200
    assert raw_client.get(BASE_URL + "/cashier/loans", headers=headers(user, tenant)).status_code == 200


def test_owner_protection_and_legacy_team_guard(raw_client, db_session):
    tenant = create_tenant(db_session, client_number=956, slug="protect-owner")
    owner, membership = add_member(db_session, tenant, "owner", "only-owner")
    h = headers(owner, tenant)
    assert raw_client.put(f"{ADMIN}/memberships/{membership.id}/status", headers=h, json={"is_active": False}).status_code == 409
    assert raw_client.put(f"{ADMIN}/memberships/{membership.id}/role", headers=h, json={"role": "administrator"}).status_code == 409
    assert raw_client.delete(f"/api/v1/client/team/memberships/{membership.id}", headers=h).status_code == 409
    # A suspended owner must not count as a usable replacement owner.
    add_member(db_session, tenant, "owner", "suspended-owner", active=False)
    assert raw_client.put(f"{ADMIN}/memberships/{membership.id}/role", headers=h, json={"role": "administrator"}).status_code == 409


@pytest.mark.parametrize("role", ["administrator", "supervisor", "cashier"])
def test_new_role_invitation_acceptance(raw_client, db_session, role):
    tenant = create_tenant(db_session, client_number=957, slug="new-role-invite")
    owner, _ = add_member(db_session, tenant, "owner", "inviter")
    response = raw_client.post(ADMIN + "/invitations", headers=headers(owner, tenant), json={
        "display_name": "New Role", "email": f"invited-{role}@example.test", "role": role,
    })
    assert response.status_code == 201, response.text
    token = response.json()["activation_path"].split("#token=")[1]
    accepted = raw_client.post("/api/v1/auth/invitations/accept", json={"token": token, "password": "Strong-test-password-2026!"})
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["client"]["role"] == role
    # The new roles must remain unavailable for other products.
    from app.membership_roles import membership_role_allowed_for_product
    assert not membership_role_allowed_for_product(role=role, product_slug="renewaldesk")


def test_administrator_can_invite_revoke_and_cannot_revoke_owner_invite(raw_client, db_session):
    tenant = create_tenant(db_session, client_number=958, slug="admin-invites")
    owner, _ = add_member(db_session, tenant, "owner", "inviter-owner")
    admin, _ = add_member(db_session, tenant, "administrator", "inviter-admin")
    privileged = raw_client.post(ADMIN + "/invitations", headers=headers(owner, tenant), json={"display_name": "Owner", "email": "new-owner@example.test", "role": "owner"}).json()
    assert raw_client.post(f"{ADMIN}/invitations/{privileged['id']}/revoke", headers=headers(admin, tenant)).status_code == 403
    ordinary = raw_client.post(ADMIN + "/invitations", headers=headers(admin, tenant), json={"display_name": "Cashier", "email": "new-cashier@example.test", "role": "cashier"})
    assert ordinary.status_code == 201
    assert raw_client.post(f"{ADMIN}/invitations/{ordinary.json()['id']}/revoke", headers=headers(admin, tenant)).status_code == 200
    assert raw_client.post("/api/v1/auth/invitations/accept", json={"token": ordinary.json()["activation_path"].split("#token=")[1], "password": "Strong-test-password-2026!"}).status_code == 400


@pytest.mark.parametrize("role,operations,cashier,collections", [
    ("owner", 200, 200, 200), ("administrator", 200, 200, 200),
    ("supervisor", 403, 403, 200), ("cashier", 403, 200, 403),
    ("collector", 403, 403, 200), ("member", 403, 200, 403), ("unknown", 403, 403, 403),
])
def test_product_endpoint_permissions(raw_client, db_session, role, operations, cashier, collections):
    tenant = create_tenant(db_session, client_number=959, slug="product-permissions")
    user, _ = add_member(db_session, tenant, role, role)
    h = headers(user, tenant)
    assert raw_client.get(BASE_URL + "/borrowers", headers=h).status_code == operations
    assert raw_client.get(BASE_URL + "/loans", headers=h).status_code == (200 if role == "member" else operations)
    assert raw_client.get(BASE_URL + "/cashier/loans", headers=h).status_code == cashier
    assert raw_client.get(BASE_URL + "/collections/portfolio", headers=h).status_code == collections
    assert raw_client.post(BASE_URL + "/loans", headers=h, json={}).status_code == (422 if operations == 200 else 403)
    assert raw_client.get(BASE_URL + "/cashier/closing-preview", headers=h).status_code == (200 if role in {"member", "cashier"} else 403)


def test_assignments_block_suspension_and_role_change(raw_client, db_session):
    tenant = create_tenant(db_session, client_number=960, slug="assigned-staff")
    owner, _ = add_member(db_session, tenant, "owner", "owner")
    supervisor, _ = add_member(db_session, tenant, "supervisor", "supervisor")
    collector, membership = add_member(db_session, tenant, "collector", "collector")
    _, loan, _ = create_loan(db_session, tenant=tenant, suffix=901)
    assigned = raw_client.post(f"{BASE_URL}/collections/loans/{loan.id}/assignment", headers=headers(supervisor, tenant), json={"collector_user_id": collector.id})
    assert assigned.status_code == 200, assigned.text
    h = headers(owner, tenant)
    assert raw_client.put(f"{ADMIN}/memberships/{membership.id}/status", headers=h, json={"is_active": False}).status_code == 409
    assert raw_client.put(f"{ADMIN}/memberships/{membership.id}/role", headers=h, json={"role": "cashier"}).status_code == 409
    assert raw_client.put(f"/api/v1/client/team/memberships/{membership.id}", headers=h, json={"role": "cashier"}).status_code == 409
    assert raw_client.delete(f"/api/v1/client/team/memberships/{membership.id}", headers=h).status_code == 409
    released = raw_client.post(f"{BASE_URL}/collections/loans/{loan.id}/assignment/release", headers=headers(supervisor, tenant), json={"reason": "Staff change"})
    assert released.status_code == 200
    assert raw_client.put(f"{ADMIN}/memberships/{membership.id}/status", headers=h, json={"is_active": False}).status_code == 200
    assert raw_client.post(f"{BASE_URL}/collections/loans/{loan.id}/assignment", headers=headers(supervisor, tenant), json={"collector_user_id": collector.id}).status_code == 404
    events = raw_client.get(ADMIN + "/audit", headers=h).json()
    assert {e["action"] for e in events} >= {"collections.assignment_created", "collections.assignment_released", "client_team.status_changed"}


@pytest.mark.parametrize("role,expected", [("cashier", 201), ("administrator", 201), ("supervisor", 403), ("collector", 403)])
def test_payment_recording_is_separate_from_collections(raw_client, db_session, role, expected):
    tenant = create_tenant(db_session, client_number=961, slug="payment-responsibility")
    user, _ = add_member(db_session, tenant, role, role)
    _, _, installment = create_loan(db_session, tenant=tenant, suffix=902)
    response = raw_client.post(BASE_URL + "/payments", headers=headers(user, tenant), json={
        "installment_id": installment.id, "amount": "100.00", "payment_method": "cash",
    })
    assert response.status_code == expected, response.text
    if expected == 201:
        assert response.json()["recorded_by_user_id"] == user.id


def test_member_workspace_read_contract_preserves_management_boundaries(raw_client, db_session):
    tenant = create_tenant(db_session, client_number=965, slug="member-workspace-contract")
    other = create_tenant(db_session, client_number=966, slug="member-workspace-other")
    _, loan, _ = create_loan(db_session, tenant=tenant, suffix=965)
    _, other_loan, _ = create_loan(db_session, tenant=other, suffix=966)
    member, _ = add_member(db_session, tenant, "member", "workspace-contract")
    h = headers(member, tenant)
    assert raw_client.get(BASE_URL + "/loans", headers=h).status_code == 200
    assert raw_client.get(BASE_URL + f"/loans/{loan.id}", headers=h).status_code == 200
    cashier = raw_client.get(BASE_URL + "/cashier/loans", headers=h)
    assert cashier.status_code == 200
    assert [item["id"] for item in cashier.json()] == [loan.id]
    assert cashier.json()[0]["borrower_full_name"] == "Cliente Cobros 965"
    for path in ("/borrowers", "/prospects", "/applications", "/prospects/public-page", "/late-fee-policy"):
        assert raw_client.get(BASE_URL + path, headers=h).status_code == 403
    assert raw_client.get(BASE_URL + f"/loans/{other_loan.id}", headers=h).status_code == 404
    assert raw_client.get(BASE_URL + "/cashier/loans", headers=headers(member, other)).status_code == 403
