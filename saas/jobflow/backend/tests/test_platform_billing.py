import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import (
    AdminAuditLog,
    BillingAccount,
    BillingOffer,
    Product,
    Tenant,
    User,
)


def get_tenant(db_session):
    tenant = db_session.scalar(
        select(Tenant)
        .where(
            Tenant.client_number.is_not(None)
        )
        .order_by(Tenant.id)
    )

    if tenant is None:
        product = db_session.scalar(
            select(Product).where(
                Product.slug == "jobflow"
            )
        )

        assert product is not None

        tenant = Tenant(
            product_id=product.id,
            client_number=1,
            name="Billing Test Client",
            slug="billing-test-client",
            status="active",
            timezone_name="UTC",
        )

        db_session.add(tenant)
        db_session.commit()
        db_session.refresh(tenant)

    return tenant


def test_billing_account_is_tenant_owned(
    db_session,
):
    tenant = get_tenant(db_session)

    account = BillingAccount(
        tenant_id=tenant.id,
        billing_mode="subscription",
        provider="manual",
        status="pending",
        currency="USD",
    )

    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    assert account.id is not None
    assert account.tenant_id == tenant.id
    assert account.billing_mode == "subscription"
    assert account.provider == "manual"
    assert account.status == "pending"
    assert account.currency == "USD"
    assert account.provider_customer_id is None
    assert account.provider_subscription_id is None
    assert account.created_at is not None
    assert account.updated_at is not None


def test_tenant_has_only_one_billing_account(
    db_session,
):
    tenant = get_tenant(db_session)

    db_session.add_all(
        [
            BillingAccount(
                tenant_id=tenant.id,
                billing_mode="manual",
                provider="manual",
                status="pending",
                currency="USD",
            ),
            BillingAccount(
                tenant_id=tenant.id,
                billing_mode="subscription",
                provider="manual",
                status="active",
                currency="USD",
            ),
        ]
    )

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_billing_account_references_tenant(
    db_session,
):
    table = BillingAccount.__table__

    foreign_keys = {
        foreign_key.target_fullname
        for foreign_key
        in table.columns["tenant_id"].foreign_keys
    }

    assert foreign_keys == {
        "tenants.id",
    }


def make_platform_admin(
    db_session,
):
    user = db_session.scalar(
        select(User).where(
            User.email
            == "default-test-user@example.com"
        )
    )

    assert user is not None

    user.is_platform_admin = True
    db_session.commit()

    return user


def test_admin_tenant_detail_has_billing_account(
    client,
    db_session,
):
    make_platform_admin(db_session)

    tenant = get_tenant(db_session)

    response = client.get(
        f"/api/v1/admin/tenants/{tenant.id}"
    )

    assert response.status_code == 200
    assert (
        response.json()["billing_account"]
        is None
    )


def test_platform_admin_can_create_billing_account(
    client,
    db_session,
):
    operator = make_platform_admin(
        db_session
    )
    tenant = get_tenant(db_session)

    response = client.put(
        (
            f"/api/v1/admin/tenants/"
            f"{tenant.id}/billing"
        ),
        json={
            "billing_mode": "subscription",
            "provider": "manual",
            "status": "pending",
            "currency": "usd",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["tenant_id"] == tenant.id
    assert payload["billing_mode"] == (
        "subscription"
    )
    assert payload["provider"] == "manual"
    assert payload["status"] == "pending"
    assert payload["currency"] == "USD"
    assert (
        payload["provider_customer_id"]
        is None
    )
    assert (
        payload["provider_subscription_id"]
        is None
    )

    account = db_session.scalar(
        select(BillingAccount).where(
            BillingAccount.tenant_id
            == tenant.id
        )
    )

    assert account is not None

    audit = db_session.scalar(
        select(AdminAuditLog).where(
            AdminAuditLog.action
            == "billing_account.created"
        )
    )

    assert audit is not None
    assert (
        audit.operator_user_id
        == operator.id
    )
    assert audit.tenant_id == tenant.id
    assert audit.before_data is None
    assert audit.after_data["status"] == (
        "pending"
    )


def test_platform_admin_can_update_billing_account(
    client,
    db_session,
):
    make_platform_admin(db_session)
    tenant = get_tenant(db_session)

    first = client.put(
        (
            f"/api/v1/admin/tenants/"
            f"{tenant.id}/billing"
        ),
        json={
            "billing_mode": "manual",
            "provider": "manual",
            "status": "pending",
            "currency": "USD",
        },
    )

    assert first.status_code == 200

    response = client.put(
        (
            f"/api/v1/admin/tenants/"
            f"{tenant.id}/billing"
        ),
        json={
            "billing_mode": "fixed_scope",
            "provider": "manual",
            "status": "active",
            "currency": "USD",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["id"] == first.json()["id"]
    assert payload["billing_mode"] == (
        "fixed_scope"
    )
    assert payload["status"] == "active"

    accounts = db_session.scalars(
        select(BillingAccount).where(
            BillingAccount.tenant_id
            == tenant.id
        )
    ).all()

    assert len(accounts) == 1

    audit = db_session.scalar(
        select(AdminAuditLog).where(
            AdminAuditLog.action
            == "billing_account.updated"
        )
    )

    assert audit is not None
    assert audit.before_data["status"] == (
        "pending"
    )
    assert audit.after_data["status"] == (
        "active"
    )


def test_non_platform_admin_cannot_manage_billing(
    client,
    db_session,
):
    tenant = get_tenant(db_session)

    response = client.put(
        (
            f"/api/v1/admin/tenants/"
            f"{tenant.id}/billing"
        ),
        json={
            "billing_mode": "manual",
            "provider": "manual",
            "status": "pending",
            "currency": "USD",
        },
    )

    assert response.status_code == 403


def test_admin_rejects_invalid_billing_values(
    client,
    db_session,
):
    make_platform_admin(db_session)
    tenant = get_tenant(db_session)

    response = client.put(
        (
            f"/api/v1/admin/tenants/"
            f"{tenant.id}/billing"
        ),
        json={
            "billing_mode": "unknown",
            "provider": "stripe",
            "status": "unpaid",
            "currency": "dollars",
        },
    )

    assert response.status_code == 422


def test_billing_update_returns_404_for_missing_tenant(
    client,
    db_session,
):
    make_platform_admin(db_session)

    response = client.put(
        "/api/v1/admin/tenants/999999/billing",
        json={
            "billing_mode": "manual",
            "provider": "manual",
            "status": "pending",
            "currency": "USD",
        },
    )

    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "Tenant not found"
    )


def test_platform_admin_can_view_billing_directory(
    client,
    db_session,
):
    make_platform_admin(db_session)
    tenant = get_tenant(db_session)

    response = client.get(
        "/api/v1/admin/billing"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["counts"]["tenants"] >= 1
    assert payload["counts"]["configured"] == 0
    assert (
        payload["counts"]["unconfigured"]
        == payload["counts"]["clients"]
    )

    row = next(
        item
        for item in payload["accounts"]
        if item["tenant"]["id"] == tenant.id
    )

    assert row["product"]["slug"] == (
        "jobflow"
    )
    assert row["access_kind"] in {
        "client",
        "validation_workspace",
    }
    assert row["billing_account"] is None


def test_billing_directory_reports_account_status(
    client,
    db_session,
):
    make_platform_admin(db_session)
    tenant = get_tenant(db_session)

    update = client.put(
        (
            f"/api/v1/admin/tenants/"
            f"{tenant.id}/billing"
        ),
        json={
            "billing_mode": "subscription",
            "provider": "manual",
            "status": "active",
            "currency": "USD",
        },
    )

    assert update.status_code == 200

    response = client.get(
        "/api/v1/admin/billing"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["counts"]["configured"] == 1
    assert payload["counts"]["active"] == 1
    assert (
        payload["counts"]["unconfigured"]
        == payload["counts"]["clients"] - 1
    )

    row = next(
        item
        for item in payload["accounts"]
        if item["tenant"]["id"] == tenant.id
    )

    assert (
        row["billing_account"]["status"]
        == "active"
    )
    assert (
        row["billing_account"]["provider"]
        == "manual"
    )


def test_non_platform_admin_cannot_view_billing_directory(
    client,
):
    response = client.get(
        "/api/v1/admin/billing"
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_view_billing_directory(
    raw_client,
):
    response = raw_client.get(
        "/api/v1/admin/billing"
    )

    assert response.status_code == 401


def test_unchanged_billing_update_is_not_audited(
    client,
    db_session,
):
    make_platform_admin(db_session)
    tenant = get_tenant(db_session)

    payload = {
        "billing_mode": "subscription",
        "provider": "manual",
        "status": "pending",
        "currency": "USD",
    }

    first = client.put(
        (
            f"/api/v1/admin/tenants/"
            f"{tenant.id}/billing"
        ),
        json=payload,
    )

    assert first.status_code == 200

    second = client.put(
        (
            f"/api/v1/admin/tenants/"
            f"{tenant.id}/billing"
        ),
        json=payload,
    )

    assert second.status_code == 200
    assert second.json()["id"] == (
        first.json()["id"]
    )

    updated_events = db_session.scalars(
        select(AdminAuditLog).where(
            AdminAuditLog.action
            == "billing_account.updated"
        )
    ).all()

    assert updated_events == []


def test_validation_workspace_cannot_be_billed(
    client,
    db_session,
):
    make_platform_admin(db_session)

    validation_workspace = db_session.scalar(
        select(Tenant)
        .where(
            Tenant.client_number.is_(None)
        )
        .order_by(Tenant.id)
    )

    assert validation_workspace is not None

    response = client.put(
        (
            f"/api/v1/admin/tenants/"
            f"{validation_workspace.id}/billing"
        ),
        json={
            "billing_mode": "manual",
            "provider": "manual",
            "status": "pending",
            "currency": "USD",
        },
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == (
            "Validation workspaces "
            "cannot have billing accounts"
        )
    )



def make_billing_offer_for_tenant(
    db_session,
    tenant,
    *,
    status="active",
    product_id=None,
    code_suffix="default",
):
    offer = BillingOffer(
        product_id=(
            tenant.product_id
            if product_id is None
            else product_id
        ),
        code=(
            f"billing-assignment-{tenant.id}-"
            f"{code_suffix}"
        ),
        name="Billing Assignment Test Offer",
        description="Test billing assignment.",
        status=status,
        charge_type="one_time",
        currency="USD",
        minimum_amount_cents=9900,
        maximum_amount_cents=9900,
        billing_interval=None,
        service_period_days=30,
    )

    db_session.add(offer)
    db_session.commit()
    db_session.refresh(offer)

    return offer


def billing_assignment_payload(
    offer_id,
    *,
    currency="USD",
    status="pending",
):
    return {
        "billing_offer_id": offer_id,
        "billing_mode": "fixed_scope",
        "provider": "manual",
        "status": status,
        "currency": currency,
        "billing_contact_name":
            "  Billing Contact  ",
        "billing_contact_email":
            "  BILLING@EXAMPLE.COM  ",
        "provider_customer_id": None,
        "provider_subscription_id": None,
    }


def test_billing_account_references_offer():
    table = BillingAccount.__table__

    foreign_keys = {
        foreign_key.target_fullname
        for foreign_key
        in table.columns[
            "billing_offer_id"
        ].foreign_keys
    }

    assert foreign_keys == {
        "platform_billing_offers.id",
    }


def test_tenant_detail_returns_product_offers(
    client,
    db_session,
):
    make_platform_admin(db_session)
    tenant = get_tenant(db_session)

    offer = make_billing_offer_for_tenant(
        db_session,
        tenant,
        code_suffix="tenant-detail",
    )

    response = client.get(
        f"/api/v1/admin/tenants/{tenant.id}"
    )

    assert response.status_code == 200

    returned_offer = next(
        item
        for item
        in response.json()["billing_offers"]
        if item["id"] == offer.id
    )

    assert returned_offer["product_id"] == (
        tenant.product_id
    )
    assert returned_offer["status"] == "active"


def test_platform_admin_assigns_active_offer(
    client,
    db_session,
):
    make_platform_admin(db_session)
    tenant = get_tenant(db_session)

    offer = make_billing_offer_for_tenant(
        db_session,
        tenant,
        code_suffix="active",
    )

    response = client.put(
        (
            f"/api/v1/admin/tenants/"
            f"{tenant.id}/billing"
        ),
        json=billing_assignment_payload(
            offer.id
        ),
    )

    assert response.status_code == 200
    assert (
        response.json()["billing_offer_id"]
        == offer.id
    )
    assert (
        response.json()["billing_contact_name"]
        == "Billing Contact"
    )
    assert (
        response.json()["billing_contact_email"]
        == "billing@example.com"
    )

    account = db_session.scalar(
        select(BillingAccount).where(
            BillingAccount.tenant_id
            == tenant.id
        )
    )

    assert account is not None
    assert account.billing_offer_id == offer.id

    audit = db_session.scalar(
        select(AdminAuditLog).where(
            AdminAuditLog.action
            == "billing_account.created"
        )
    )

    assert audit is not None
    assert (
        audit.after_data["billing_offer_id"]
        == offer.id
    )


def test_billing_rejects_missing_offer(
    client,
    db_session,
):
    make_platform_admin(db_session)
    tenant = get_tenant(db_session)

    response = client.put(
        (
            f"/api/v1/admin/tenants/"
            f"{tenant.id}/billing"
        ),
        json=billing_assignment_payload(
            999999
        ),
    )

    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "Billing offer not found"
    )


def test_billing_rejects_cross_product_offer(
    client,
    db_session,
):
    make_platform_admin(db_session)
    tenant = get_tenant(db_session)

    other_product = db_session.scalar(
        select(Product)
        .where(
            Product.id != tenant.product_id
        )
        .order_by(Product.id)
    )

    assert other_product is not None

    offer = make_billing_offer_for_tenant(
        db_session,
        tenant,
        product_id=other_product.id,
        code_suffix="cross-product",
    )

    response = client.put(
        (
            f"/api/v1/admin/tenants/"
            f"{tenant.id}/billing"
        ),
        json=billing_assignment_payload(
            offer.id
        ),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Billing offer does not belong "
        "to the tenant product"
    )


def test_billing_rejects_inactive_offer(
    client,
    db_session,
):
    make_platform_admin(db_session)
    tenant = get_tenant(db_session)

    offer = make_billing_offer_for_tenant(
        db_session,
        tenant,
        status="draft",
        code_suffix="draft",
    )

    response = client.put(
        (
            f"/api/v1/admin/tenants/"
            f"{tenant.id}/billing"
        ),
        json=billing_assignment_payload(
            offer.id
        ),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Only active billing offers "
        "can be assigned"
    )


def test_billing_preserves_archived_assigned_offer(
    client,
    db_session,
):
    make_platform_admin(db_session)
    tenant = get_tenant(db_session)

    offer = make_billing_offer_for_tenant(
        db_session,
        tenant,
        code_suffix="archive",
    )

    first = client.put(
        (
            f"/api/v1/admin/tenants/"
            f"{tenant.id}/billing"
        ),
        json=billing_assignment_payload(
            offer.id
        ),
    )

    assert first.status_code == 200

    offer.status = "archived"
    db_session.commit()

    second = client.put(
        (
            f"/api/v1/admin/tenants/"
            f"{tenant.id}/billing"
        ),
        json=billing_assignment_payload(
            offer.id,
            status="active",
        ),
    )

    assert second.status_code == 200
    assert (
        second.json()["billing_offer_id"]
        == offer.id
    )
    assert second.json()["status"] == "active"


def test_billing_offer_currency_must_match(
    client,
    db_session,
):
    make_platform_admin(db_session)
    tenant = get_tenant(db_session)

    offer = make_billing_offer_for_tenant(
        db_session,
        tenant,
        code_suffix="currency",
    )

    response = client.put(
        (
            f"/api/v1/admin/tenants/"
            f"{tenant.id}/billing"
        ),
        json=billing_assignment_payload(
            offer.id,
            currency="EUR",
        ),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Billing account currency must "
        "match the selected offer"
    )



def test_assigned_offer_requires_billing_contact(
    client,
    db_session,
):
    make_platform_admin(db_session)
    tenant = get_tenant(db_session)

    offer = make_billing_offer_for_tenant(
        db_session,
        tenant,
        code_suffix="missing-contact",
    )

    payload = billing_assignment_payload(
        offer.id
    )
    payload["billing_contact_name"] = None
    payload["billing_contact_email"] = None

    response = client.put(
        (
            f"/api/v1/admin/tenants/"
            f"{tenant.id}/billing"
        ),
        json=payload,
    )

    assert response.status_code == 422
