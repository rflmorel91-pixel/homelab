from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import func, select

from app.models import TenantMembership, TenantResourceLimit, User, UserInvitation
from app.platform.membership_limits import ACTIVE_MEMBERSHIP_RESOURCE
from tests.test_prestamodesk_administration import ADMIN, add_member, headers
from tests.test_prestamodesk_collections import create_tenant

ACCEPT = "/api/v1/auth/invitations/accept"
PASSWORD = "Synthetic-limit-password-2026!"


def setup(db, slug="membership-limits", number=980):
    tenant = create_tenant(db, client_number=number, slug=slug)
    owner, _ = add_member(db, tenant, "owner", slug + "-owner")
    return tenant, owner, headers(owner, tenant)


def assign(db, tenant, maximum):
    db.add(TenantResourceLimit(
        tenant_id=tenant.id,
        resource_key=ACTIVE_MEMBERSHIP_RESOURCE,
        maximum_count=maximum,
    ))
    db.commit()


def invite(client, owner_headers, suffix):
    return client.post(ADMIN + "/invitations", headers=owner_headers, json={
        "display_name": "Synthetic invite",
        "email": f"limit-{suffix}@example.test",
        "role": "cashier",
    })


def accept(client, invitation):
    return client.post(ACCEPT, json={
        "token": invitation["activation_path"].split("#token=")[1],
        "password": PASSWORD,
    })


def active_count(db, tenant_id):
    db.expire_all()
    return db.scalar(select(func.count(TenantMembership.id)).where(
        TenantMembership.tenant_id == tenant_id,
        TenantMembership.is_active.is_(True),
    ))


def test_unassigned_pilot_keeps_existing_behavior(raw_client, db_session):
    tenant, _, h = setup(db_session)
    for index in range(3):
        invitation = invite(raw_client, h, str(index))
        assert invitation.status_code == 201
        assert accept(raw_client, invitation.json()).status_code == 200
    assert active_count(db_session, tenant.id) == 4


def test_full_limit_blocks_all_invitation_entry_points(raw_client, db_session):
    tenant, _, h = setup(db_session)
    operator = User(
        email="limit-operator@example.test", display_name="Synthetic operator",
        is_active=True, is_platform_admin=True,
    )
    db_session.add(operator)
    db_session.commit()
    assign(db_session, tenant, 1)

    routes = [
        (ADMIN + "/invitations", h),
        ("/api/v1/client/user-invitations", h),
        (f"/api/v1/admin/tenants/{tenant.id}/user-invitations",
         headers(operator, tenant)),
    ]
    for index, (url, request_headers) in enumerate(routes):
        response = raw_client.post(url, headers=request_headers, json={
            "display_name": "Synthetic blocked invite",
            "email": f"blocked-{index}@example.test",
            "role": "member",
        })
        assert response.status_code == 409, response.text
    assert db_session.scalar(select(func.count(UserInvitation.id))) == 0
    assert raw_client.get(ADMIN + "/team", headers=h).status_code == 200


def test_acceptance_rechecks_limit_and_rolls_back_user(raw_client, db_session):
    tenant, _, h = setup(db_session)
    invitation = invite(raw_client, h, "blocked-accept")
    assert invitation.status_code == 201
    assign(db_session, tenant, 1)

    response = accept(raw_client, invitation.json())
    assert response.status_code == 409
    db_session.expire_all()
    assert db_session.scalar(select(User.id).where(
        User.email == "limit-blocked-accept@example.test",
    )) is None
    record = db_session.get(UserInvitation, invitation.json()["id"])
    assert record.accepted_at is None
    assert record.accepted_user_id is None
    assert active_count(db_session, tenant.id) == 1


def test_platform_admin_additions_obey_limit(raw_client, db_session):
    tenant, _, _ = setup(db_session)
    operator = User(
        email="capacity-operator@example.test", display_name="Synthetic operator",
        is_active=True, is_platform_admin=True,
    )
    targets = [
        User(email=f"capacity-target-{i}@example.test",
             display_name="Synthetic target", is_active=True)
        for i in range(2)
    ]
    db_session.add_all([operator, *targets])
    db_session.commit()
    assign(db_session, tenant, 2)

    results = [
        raw_client.post(
            f"/api/v1/admin/tenants/{tenant.id}/memberships",
            headers=headers(operator, tenant),
            json={"user_id": target.id, "role": "cashier"},
        ).status_code
        for target in targets
    ]
    assert results == [201, 409]
    assert active_count(db_session, tenant.id) == 2


def test_reactivation_blocks_but_suspension_frees_slot(raw_client, db_session):
    tenant, _, h = setup(db_session)
    _, worker = add_member(db_session, tenant, "cashier", "active-worker")
    _, inactive = add_member(
        db_session, tenant, "cashier", "inactive-worker", active=False,
    )
    worker_id, inactive_id = worker.id, inactive.id
    assign(db_session, tenant, 2)

    def status(membership_id, active):
        return raw_client.put(
            f"{ADMIN}/memberships/{membership_id}/status",
            headers=h, json={"is_active": active},
        )

    assert status(inactive_id, True).status_code == 409
    assert status(worker_id, False).status_code == 200
    assert status(inactive_id, True).status_code == 200
    assert status(inactive_id, True).status_code == 200
    assert active_count(db_session, tenant.id) == 2


def test_limit_is_tenant_scoped_and_counts_inactive_accounts(
    raw_client, db_session,
):
    tenant, _, h = setup(db_session)
    user, _ = add_member(db_session, tenant, "cashier", "inactive-account")
    user.is_active = False
    db_session.commit()
    assign(db_session, tenant, 2)
    assert invite(raw_client, h, "over-capacity").status_code == 409

    other, _, other_headers = setup(
        db_session, slug="other-membership-limits", number=981,
    )
    invitation = invite(raw_client, other_headers, "other-tenant")
    assert invitation.status_code == 201
    assert accept(raw_client, invitation.json()).status_code == 200
    assert active_count(db_session, other.id) == 2


@pytest.mark.parametrize("competitor", ["invitation", "reactivation"])
def test_competing_activations_cannot_take_same_slot(
    raw_client, db_session, competitor,
):
    tenant, _, h = setup(db_session)
    first = invite(raw_client, h, "race-first")
    assert first.status_code == 201
    first_body = first.json()

    if competitor == "invitation":
        second = invite(raw_client, h, "race-second")
        assert second.status_code == 201
        second_body = second.json()
        second_action = lambda: accept(raw_client, second_body)
    else:
        _, member = add_member(
            db_session, tenant, "cashier", "race-inactive", active=False,
        )
        member_id = member.id
        second_action = lambda: raw_client.put(
            f"{ADMIN}/memberships/{member_id}/status",
            headers=h, json={"is_active": True},
        )

    # Pending invitations do not reserve capacity.
    assign(db_session, tenant, 2)
    tenant_id = tenant.id
    db_session.rollback()
    barrier = Barrier(2)

    def run(action):
        barrier.wait(timeout=10)
        return action().status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(run, lambda: accept(raw_client, first_body)),
            pool.submit(run, second_action),
        ]
        results = [future.result(timeout=30) for future in futures]

    assert sorted(results) == [200, 409]
    assert active_count(db_session, tenant_id) == 2

    # Failed acceptance must not leave a newly created account behind.
    for email in ("limit-race-first@example.test", "limit-race-second@example.test"):
        user = db_session.scalar(select(User).where(User.email == email))
        if user is not None:
            assert db_session.scalar(select(TenantMembership.id).where(
                TenantMembership.tenant_id == tenant_id,
                TenantMembership.user_id == user.id,
            )) is not None
