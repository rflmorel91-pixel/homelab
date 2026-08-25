from sqlalchemy import select

from app.models import AdminAuditLog, Lead, User


def create_lead(db_session):
    lead = Lead(
        product_id=1,
        business_name="Lead Test Services",
        contact_name="Lead Prospect",
        email="protected-lead@example.com",
        service_type="Handyman",
        status="new",
    )
    db_session.add(lead)
    db_session.commit()
    db_session.refresh(lead)
    return lead


def get_default_user(db_session):
    user = db_session.scalar(
        select(User).where(
            User.email == "default-test-user@example.com"
        )
    )

    assert user is not None
    return user


def test_platform_admin_can_list_leads(
    client,
    db_session,
):
    user = get_default_user(db_session)
    user.is_platform_admin = True
    db_session.commit()

    lead = create_lead(db_session)

    response = client.get("/api/v1/leads/")

    assert response.status_code == 200

    payload = response.json()

    assert any(
        item["id"] == lead.id
        and item["email"] == "protected-lead@example.com"
        and item["product_id"] == lead.product_id
        and item["product_slug"] == "jobflow"
        and item["product_name"] == "JobFlow"
        for item in payload
    )


def test_non_platform_admin_cannot_list_leads(
    client,
    db_session,
):
    create_lead(db_session)

    response = client.get("/api/v1/leads/")

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "Platform operator access required"
    )


def test_unauthenticated_user_cannot_list_leads(
    raw_client,
    db_session,
):
    create_lead(db_session)

    response = raw_client.get("/api/v1/leads/")

    assert response.status_code == 401


def make_platform_admin(db_session):
    user = get_default_user(db_session)
    user.is_platform_admin = True
    db_session.commit()
    return user


def test_platform_admin_can_update_lead_status(
    client,
    db_session,
):
    operator = make_platform_admin(db_session)
    lead = create_lead(db_session)

    response = client.put(
        f"/api/v1/leads/{lead.id}",
        json={
            "status": "contacted",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "contacted"

    db_session.refresh(lead)
    assert lead.status == "contacted"

    audit = db_session.scalar(
        select(AdminAuditLog).where(
            AdminAuditLog.action
            == "lead.status_changed",
            AdminAuditLog.target_type == "lead",
            AdminAuditLog.target_id == lead.id,
        )
    )

    assert audit is not None
    assert audit.operator_user_id == operator.id
    assert audit.tenant_id is None
    assert audit.before_data == {
        "status": "new",
    }
    assert audit.after_data == {
        "status": "contacted",
    }


def test_unchanged_lead_status_does_not_create_audit(
    client,
    db_session,
):
    make_platform_admin(db_session)
    lead = create_lead(db_session)

    response = client.put(
        f"/api/v1/leads/{lead.id}",
        json={
            "status": "new",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "new"

    audit = db_session.scalar(
        select(AdminAuditLog).where(
            AdminAuditLog.action
            == "lead.status_changed",
            AdminAuditLog.target_type == "lead",
            AdminAuditLog.target_id == lead.id,
        )
    )

    assert audit is None


def test_lead_status_progression_stops_at_qualified(
    client,
    db_session,
):
    make_platform_admin(db_session)
    lead = create_lead(db_session)

    for status in (
        "contacted",
        "qualified",
    ):
        response = client.put(
            f"/api/v1/leads/{lead.id}",
            json={
                "status": status,
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == status


def test_qualified_lead_cannot_be_manually_converted(
    client,
    db_session,
):
    make_platform_admin(db_session)
    lead = create_lead(db_session)

    for status in ("contacted", "qualified"):
        response = client.put(
            f"/api/v1/leads/{lead.id}",
            json={"status": status},
        )
        assert response.status_code == 200

    response = client.put(
        f"/api/v1/leads/{lead.id}",
        json={"status": "converted"},
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Invalid lead status transition: qualified -> converted"
    )


def test_lead_can_be_closed_after_contact(
    client,
    db_session,
):
    make_platform_admin(db_session)
    lead = create_lead(db_session)

    response = client.put(
        f"/api/v1/leads/{lead.id}",
        json={
            "status": "contacted",
        },
    )

    assert response.status_code == 200

    response = client.put(
        f"/api/v1/leads/{lead.id}",
        json={
            "status": "closed",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "closed"


def test_new_lead_can_be_closed_without_contact(
    client,
    db_session,
):
    make_platform_admin(db_session)
    lead = create_lead(db_session)

    response = client.put(
        f"/api/v1/leads/{lead.id}",
        json={
            "status": "closed",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "closed"

    db_session.refresh(lead)
    assert lead.status == "closed"


def test_invalid_lead_status_transition_is_rejected(
    client,
    db_session,
):
    make_platform_admin(db_session)
    lead = create_lead(db_session)

    response = client.put(
        f"/api/v1/leads/{lead.id}",
        json={
            "status": "converted",
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Invalid lead status transition: new -> converted"
    )


def test_non_platform_admin_cannot_update_lead(
    client,
    db_session,
):
    lead = create_lead(db_session)

    response = client.put(
        f"/api/v1/leads/{lead.id}",
        json={
            "status": "contacted",
        },
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "Platform operator access required"
    )


def test_update_unknown_lead_returns_404(
    client,
    db_session,
):
    make_platform_admin(db_session)

    response = client.put(
        "/api/v1/leads/999999",
        json={
            "status": "contacted",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Lead not found"


def test_lead_update_rejects_extra_fields(
    client,
    db_session,
):
    make_platform_admin(db_session)
    lead = create_lead(db_session)

    response = client.put(
        f"/api/v1/leads/{lead.id}",
        json={
            "status": "contacted",
            "email": "override@example.com",
        },
    )

    assert response.status_code == 422


def make_qualified_lead(client, db_session):
    lead = create_lead(db_session)

    for status in ("contacted", "qualified"):
        response = client.put(
            f"/api/v1/leads/{lead.id}",
            json={"status": status},
        )
        assert response.status_code == 200

    db_session.refresh(lead)
    return lead


def create_owner_user(
    db_session,
    *,
    email="tenant-owner@example.com",
    active=True,
):
    user = User(
        email=email,
        display_name="Tenant Owner",
        is_active=active,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def accept_owner_invitation(
    db_session,
    *,
    lead,
    owner,
    operator,
):
    from app.models import UserInvitation
    from app.security import hash_invitation_token
    from datetime import timedelta
    from app.api.invitations import utc_now_naive

    now = utc_now_naive()

    invitation = UserInvitation(
        lead_id=lead.id,
        email=owner.email,
        display_name=owner.display_name,
        token_hash=hash_invitation_token(
            f"accepted-invitation-{lead.id}-{owner.id}"
        ),
        created_by_user_id=operator.id,
        accepted_user_id=owner.id,
        expires_at=now + timedelta(hours=72),
        accepted_at=now,
    )
    db_session.add(invitation)
    db_session.commit()
    db_session.refresh(invitation)

    return invitation


def test_platform_admin_can_provision_qualified_lead(
    client,
    db_session,
):
    from app.models import (
        AdminAuditLog,
        Tenant,
        TenantMembership,
    )

    operator = make_platform_admin(db_session)
    lead = make_qualified_lead(client, db_session)
    owner = create_owner_user(db_session)
    accept_owner_invitation(
        db_session,
        lead=lead,
        owner=owner,
        operator=operator,
    )

    response = client.post(
        f"/api/v1/leads/{lead.id}/provision",
        json={
            "owner_user_id": owner.id,
            "tenant_slug": "lead-test-services",
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["lead_id"] == lead.id
    assert payload["tenant"]["client_number"] == 1
    assert payload["tenant"]["name"] == lead.business_name
    assert payload["tenant"]["slug"] == "lead-test-services"
    assert payload["tenant"]["status"] == "active"
    assert payload["owner"]["user_id"] == owner.id
    assert payload["owner"]["role"] == "owner"

    db_session.expire_all()

    tenant = db_session.get(
        Tenant,
        payload["tenant"]["id"],
    )
    assert tenant is not None
    assert tenant.client_number == 1

    listed_leads = client.get("/api/v1/leads/")
    assert listed_leads.status_code == 200

    listed_lead = next(
        item
        for item in listed_leads.json()
        if item["id"] == lead.id
    )
    assert listed_lead["converted_client_number"] == 1

    updated_lead = db_session.get(Lead, lead.id)
    assert updated_lead is not None
    assert updated_lead.status == "converted"
    assert updated_lead.converted_tenant_id == tenant.id
    assert updated_lead.converted_at is not None

    membership = db_session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant.id,
            TenantMembership.user_id == owner.id,
        )
    )
    assert membership is not None
    assert membership.role == "owner"

    audit = db_session.scalar(
        select(AdminAuditLog).where(
            AdminAuditLog.action == "tenant.provisioned",
            AdminAuditLog.target_id == tenant.id,
        )
    )
    assert audit is not None
    assert audit.operator_user_id == operator.id
    assert audit.tenant_id == tenant.id
    assert audit.after_data["lead_id"] == lead.id
    assert audit.after_data["owner_user_id"] == owner.id
    assert audit.after_data["client_number"] == 1


def test_only_qualified_lead_can_be_provisioned(
    client,
    db_session,
):
    make_platform_admin(db_session)
    lead = create_lead(db_session)
    owner = create_owner_user(db_session)

    response = client.post(
        f"/api/v1/leads/{lead.id}/provision",
        json={
            "owner_user_id": owner.id,
            "tenant_slug": "not-qualified",
        },
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "Lead must be qualified before provisioning"
    )


def test_lead_cannot_be_provisioned_twice(
    client,
    db_session,
):
    operator = make_platform_admin(db_session)
    lead = make_qualified_lead(client, db_session)
    owner = create_owner_user(db_session)
    accept_owner_invitation(
        db_session,
        lead=lead,
        owner=owner,
        operator=operator,
    )

    first = client.post(
        f"/api/v1/leads/{lead.id}/provision",
        json={
            "owner_user_id": owner.id,
            "tenant_slug": "duplicate-provision",
        },
    )
    assert first.status_code == 201

    second = client.post(
        f"/api/v1/leads/{lead.id}/provision",
        json={
            "owner_user_id": owner.id,
            "tenant_slug": "duplicate-provision-2",
        },
    )

    assert second.status_code == 409
    assert (
        second.json()["detail"]
        == "Lead has already been provisioned"
    )


def test_provision_rejects_owner_without_lead_invitation(
    client,
    db_session,
):
    make_platform_admin(db_session)
    lead = make_qualified_lead(client, db_session)
    owner = create_owner_user(db_session)

    response = client.post(
        f"/api/v1/leads/{lead.id}/provision",
        json={
            "owner_user_id": owner.id,
            "tenant_slug": "uninvited-owner",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Owner must accept the invitation "
        "for this lead before provisioning"
    )


def test_provision_rejects_inactive_owner(
    client,
    db_session,
):
    make_platform_admin(db_session)
    lead = make_qualified_lead(client, db_session)
    owner = create_owner_user(
        db_session,
        email="inactive-owner@example.com",
        active=False,
    )

    response = client.post(
        f"/api/v1/leads/{lead.id}/provision",
        json={
            "owner_user_id": owner.id,
            "tenant_slug": "inactive-owner",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Owner user must be active"


def test_provision_rejects_unknown_owner(
    client,
    db_session,
):
    make_platform_admin(db_session)
    lead = make_qualified_lead(client, db_session)

    response = client.post(
        f"/api/v1/leads/{lead.id}/provision",
        json={
            "owner_user_id": 999999,
            "tenant_slug": "unknown-owner",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Owner user not found"


def test_provision_rejects_duplicate_tenant_slug(
    client,
    db_session,
):
    from app.models import Tenant

    operator = make_platform_admin(db_session)
    lead = make_qualified_lead(client, db_session)
    owner = create_owner_user(db_session)
    accept_owner_invitation(
        db_session,
        lead=lead,
        owner=owner,
        operator=operator,
    )

    tenant = Tenant(

        product_id=1,
        name="Existing Tenant",
        slug="existing-tenant",
    )
    db_session.add(tenant)
    db_session.commit()

    response = client.post(
        f"/api/v1/leads/{lead.id}/provision",
        json={
            "owner_user_id": owner.id,
            "tenant_slug": "existing-tenant",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Tenant slug already exists"

    db_session.expire_all()
    lead = db_session.get(Lead, lead.id)
    assert lead.status == "qualified"
    assert lead.converted_tenant_id is None


def test_non_platform_admin_cannot_provision_lead(
    client,
    db_session,
):
    lead = create_lead(db_session)
    owner = create_owner_user(db_session)

    response = client.post(
        f"/api/v1/leads/{lead.id}/provision",
        json={
            "owner_user_id": owner.id,
            "tenant_slug": "forbidden-provision",
        },
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_provision_lead(
    raw_client,
):
    response = raw_client.post(
        "/api/v1/leads/1/provision",
        json={
            "owner_user_id": 1,
            "tenant_slug": "unauthenticated",
        },
    )

    assert response.status_code == 401


def test_provisioning_options_include_only_accepted_lead_owner(
    client,
    db_session,
):
    operator = make_platform_admin(db_session)
    lead = make_qualified_lead(client, db_session)

    owner = create_owner_user(
        db_session,
        email="provision-option@example.com",
    )

    unrelated = create_owner_user(
        db_session,
        email="unrelated-option@example.com",
    )

    accept_owner_invitation(
        db_session,
        lead=lead,
        owner=owner,
        operator=operator,
    )

    response = client.get(
        "/api/v1/leads/provisioning-options"
    )

    assert response.status_code == 200

    owners = response.json()["owners"]

    assert any(
        item["lead_id"] == lead.id
        and item["user_id"] == owner.id
        and item["email"]
        == "provision-option@example.com"
        for item in owners
    )

    assert all(
        item["user_id"] != unrelated.id
        for item in owners
    )

    assert all(
        item["user_id"] != operator.id
        for item in owners
    )


def test_inactive_accepted_owner_is_not_provisioning_option(
    client,
    db_session,
):
    operator = make_platform_admin(db_session)
    lead = make_qualified_lead(client, db_session)

    inactive = create_owner_user(
        db_session,
        email="inactive-option@example.com",
        active=False,
    )

    accept_owner_invitation(
        db_session,
        lead=lead,
        owner=inactive,
        operator=operator,
    )

    response = client.get(
        "/api/v1/leads/provisioning-options"
    )

    assert response.status_code == 200

    assert all(
        item["user_id"] != inactive.id
        for item in response.json()["owners"]
    )


def test_platform_admin_can_reopen_orphaned_legacy_conversion(
    client,
    db_session,
):
    from app.models import AdminAuditLog

    operator = make_platform_admin(db_session)

    lead = Lead(

        product_id=1,
        business_name="Legacy Converted Lead",
        contact_name="Legacy Contact",
        email="legacy-converted@example.com",
        service_type="Handyman",
        status="converted",
    )
    db_session.add(lead)
    db_session.commit()
    db_session.refresh(lead)

    response = client.post(
        f"/api/v1/leads/{lead.id}/reopen-conversion"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "qualified"

    db_session.expire_all()

    updated = db_session.get(Lead, lead.id)

    assert updated is not None
    assert updated.status == "qualified"
    assert updated.converted_tenant_id is None
    assert updated.converted_at is None

    audit = db_session.scalar(
        select(AdminAuditLog).where(
            AdminAuditLog.action
            == "lead.legacy_conversion_reopened",
            AdminAuditLog.target_id == lead.id,
        )
    )

    assert audit is not None
    assert audit.operator_user_id == operator.id
    assert audit.target_type == "lead"
    assert audit.before_data == {
        "status": "converted",
        "converted_tenant_id": None,
        "converted_at": None,
    }
    assert audit.after_data == {
        "status": "qualified",
    }


def test_linked_converted_lead_cannot_be_reopened(
    client,
    db_session,
):
    from app.models import Tenant

    make_platform_admin(db_session)

    tenant = Tenant(

        product_id=1,
        name="Real Provisioned Tenant",
        slug="real-provisioned-tenant",
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    lead = Lead(

        product_id=1,
        business_name="Real Converted Lead",
        contact_name="Real Contact",
        email="real-converted@example.com",
        service_type="Handyman",
        status="converted",
        converted_tenant_id=tenant.id,
    )
    db_session.add(lead)
    db_session.commit()
    db_session.refresh(lead)

    response = client.post(
        f"/api/v1/leads/{lead.id}/reopen-conversion"
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "Provisioned lead conversion cannot be reopened"
    )


def test_non_converted_lead_cannot_be_reopened(
    client,
    db_session,
):
    make_platform_admin(db_session)
    lead = create_lead(db_session)

    response = client.post(
        f"/api/v1/leads/{lead.id}/reopen-conversion"
    )

    assert response.status_code == 409
