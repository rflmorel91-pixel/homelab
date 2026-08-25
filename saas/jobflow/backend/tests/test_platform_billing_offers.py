import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import (
    AdminAuditLog,
    BillingOffer,
    Product,
    User,
)


def get_product(db_session):
    product = db_session.scalar(
        select(Product).where(
            Product.slug == "jobflow"
        )
    )

    assert product is not None
    return product


def test_one_time_offer_supports_service_period(
    db_session,
):
    product = get_product(db_session)

    offer = BillingOffer(
        product_id=product.id,
        code="pilot-30-day",
        name="30-day pilot",
        description=(
            "Pilot access, onboarding, "
            "and pilot review."
        ),
        status="active",
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

    assert offer.id is not None
    assert offer.product_id == product.id
    assert offer.status == "active"
    assert offer.charge_type == "one_time"
    assert offer.minimum_amount_cents == 9900
    assert offer.maximum_amount_cents == 9900
    assert offer.billing_interval is None
    assert offer.service_period_days == 30
    assert offer.created_at is not None
    assert offer.updated_at is not None


def test_custom_quote_supports_price_range(
    db_session,
):
    product = get_product(db_session)

    offer = BillingOffer(
        product_id=product.id,
        code="fixed-scope-workflow",
        name="Workflow Automation Package",
        status="draft",
        charge_type="custom_quote",
        currency="USD",
        minimum_amount_cents=50000,
        maximum_amount_cents=200000,
    )

    db_session.add(offer)
    db_session.commit()
    db_session.refresh(offer)

    assert offer.minimum_amount_cents == 50000
    assert offer.maximum_amount_cents == 200000
    assert offer.billing_interval is None
    assert offer.service_period_days is None


def test_subscription_offer_supports_interval(
    db_session,
):
    product = get_product(db_session)

    offer = BillingOffer(
        product_id=product.id,
        code="standard-monthly",
        name="Standard Monthly",
        status="draft",
        charge_type="subscription",
        currency="USD",
        minimum_amount_cents=4900,
        maximum_amount_cents=4900,
        billing_interval="month",
    )

    db_session.add(offer)
    db_session.commit()
    db_session.refresh(offer)

    assert offer.charge_type == "subscription"
    assert offer.billing_interval == "month"


def test_offer_code_is_unique_per_product(
    db_session,
):
    product = get_product(db_session)

    first = BillingOffer(
        product_id=product.id,
        code="duplicate",
        name="First",
        status="draft",
        charge_type="one_time",
        currency="USD",
    )

    second = BillingOffer(
        product_id=product.id,
        code="duplicate",
        name="Second",
        status="draft",
        charge_type="one_time",
        currency="USD",
    )

    db_session.add(first)
    db_session.commit()

    db_session.add(second)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_offer_rejects_inverted_price_range(
    db_session,
):
    product = get_product(db_session)

    offer = BillingOffer(
        product_id=product.id,
        code="invalid-range",
        name="Invalid Range",
        status="draft",
        charge_type="custom_quote",
        currency="USD",
        minimum_amount_cents=200000,
        maximum_amount_cents=50000,
    )

    db_session.add(offer)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_offer_references_product():
    foreign_keys = {
        foreign_key.target_fullname
        for foreign_key in (
            BillingOffer.__table__
            .columns["product_id"]
            .foreign_keys
        )
    }

    assert foreign_keys == {
        "products.id",
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


def renewaldesk_offer_payload(
    product_id,
):
    return {
        "product_id": product_id,
        "code": "pilot-30-day",
        "name": "30-day pilot",
        "description": (
            "30-day pilot access, standard "
            "onboarding, and pilot review."
        ),
        "status": "active",
        "charge_type": "one_time",
        "currency": "usd",
        "minimum_amount_cents": 9900,
        "maximum_amount_cents": 9900,
        "billing_interval": None,
        "service_period_days": 30,
    }


def test_platform_admin_can_create_offer(
    client,
    db_session,
):
    operator = make_platform_admin(
        db_session
    )
    product = get_product(db_session)

    response = client.post(
        "/api/v1/admin/billing/offers",
        json=renewaldesk_offer_payload(
            product.id
        ),
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["product_id"] == product.id
    assert payload["code"] == "pilot-30-day"
    assert payload["status"] == "active"
    assert payload["charge_type"] == "one_time"
    assert payload["currency"] == "USD"
    assert payload["minimum_amount_cents"] == 9900
    assert payload["maximum_amount_cents"] == 9900
    assert payload["service_period_days"] == 30

    offer = db_session.scalar(
        select(BillingOffer).where(
            BillingOffer.code
            == "pilot-30-day"
        )
    )

    assert offer is not None

    audit = db_session.scalar(
        select(AdminAuditLog).where(
            AdminAuditLog.action
            == "billing_offer.created"
        )
    )

    assert audit is not None
    assert audit.operator_user_id == operator.id
    assert audit.target_type == "billing_offer"
    assert audit.target_id == offer.id
    assert audit.tenant_id is None
    assert audit.before_data is None
    assert audit.after_data["code"] == (
        "pilot-30-day"
    )


def test_platform_admin_can_view_offer_directory(
    client,
    db_session,
):
    make_platform_admin(db_session)
    product = get_product(db_session)

    created = client.post(
        "/api/v1/admin/billing/offers",
        json=renewaldesk_offer_payload(
            product.id
        ),
    )

    assert created.status_code == 201

    response = client.get(
        "/api/v1/admin/billing/offers"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["counts"] == {
        "offers": 1,
        "draft": 0,
        "active": 1,
        "archived": 0,
    }

    row = payload["offers"][0]

    assert row["code"] == "pilot-30-day"
    assert row["product"]["id"] == product.id
    assert row["product"]["slug"] == "jobflow"


def test_duplicate_offer_code_returns_conflict(
    client,
    db_session,
):
    make_platform_admin(db_session)
    product = get_product(db_session)

    offer = renewaldesk_offer_payload(
        product.id
    )

    first = client.post(
        "/api/v1/admin/billing/offers",
        json=offer,
    )

    second = client.post(
        "/api/v1/admin/billing/offers",
        json=offer,
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"] == (
        "Offer code already exists "
        "for this product"
    )


def test_offer_creation_rejects_missing_product(
    client,
    db_session,
):
    make_platform_admin(db_session)

    response = client.post(
        "/api/v1/admin/billing/offers",
        json=renewaldesk_offer_payload(
            999999
        ),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Product not found"
    )


def test_non_platform_admin_cannot_manage_offers(
    client,
    db_session,
):
    product = get_product(db_session)

    create_response = client.post(
        "/api/v1/admin/billing/offers",
        json=renewaldesk_offer_payload(
            product.id
        ),
    )

    directory_response = client.get(
        "/api/v1/admin/billing/offers"
    )

    assert create_response.status_code == 403
    assert directory_response.status_code == 403


def test_unauthenticated_user_cannot_manage_offers(
    raw_client,
):
    create_response = raw_client.post(
        "/api/v1/admin/billing/offers",
        json=renewaldesk_offer_payload(1),
    )

    directory_response = raw_client.get(
        "/api/v1/admin/billing/offers"
    )

    assert create_response.status_code == 401
    assert directory_response.status_code == 401


def test_platform_admin_can_update_offer(
    client,
    db_session,
):
    make_platform_admin(db_session)
    product = get_product(db_session)

    created = client.post(
        "/api/v1/admin/billing/offers",
        json=renewaldesk_offer_payload(
            product.id
        ),
    )

    assert created.status_code == 201

    offer_id = created.json()["id"]

    updated_payload = (
        renewaldesk_offer_payload(
            product.id
        )
    )
    updated_payload["status"] = "archived"
    updated_payload["name"] = (
        "30-day pilot — archived"
    )

    response = client.put(
        (
            "/api/v1/admin/billing/offers/"
            f"{offer_id}"
        ),
        json=updated_payload,
    )

    assert response.status_code == 200
    assert response.json()["status"] == (
        "archived"
    )

    audit = db_session.scalar(
        select(AdminAuditLog).where(
            AdminAuditLog.action
            == "billing_offer.updated"
        )
    )

    assert audit is not None
    assert audit.target_id == offer_id
    assert audit.before_data["status"] == (
        "active"
    )
    assert audit.after_data["status"] == (
        "archived"
    )


def test_unchanged_offer_update_is_not_audited(
    client,
    db_session,
):
    make_platform_admin(db_session)
    product = get_product(db_session)

    payload = renewaldesk_offer_payload(
        product.id
    )

    created = client.post(
        "/api/v1/admin/billing/offers",
        json=payload,
    )

    assert created.status_code == 201

    response = client.put(
        (
            "/api/v1/admin/billing/offers/"
            f"{created.json()['id']}"
        ),
        json=payload,
    )

    assert response.status_code == 200

    updated_events = db_session.scalars(
        select(AdminAuditLog).where(
            AdminAuditLog.action
            == "billing_offer.updated"
        )
    ).all()

    assert updated_events == []


def test_offer_cannot_move_between_products(
    client,
    db_session,
):
    make_platform_admin(db_session)
    product = get_product(db_session)

    second_product = Product(
        name="Second Product",
        slug="second-product",
        status="active",
        workspace_key="second-product",
    )

    db_session.add(second_product)
    db_session.commit()
    db_session.refresh(second_product)

    created = client.post(
        "/api/v1/admin/billing/offers",
        json=renewaldesk_offer_payload(
            product.id
        ),
    )

    assert created.status_code == 201

    moved_payload = (
        renewaldesk_offer_payload(
            second_product.id
        )
    )

    response = client.put(
        (
            "/api/v1/admin/billing/offers/"
            f"{created.json()['id']}"
        ),
        json=moved_payload,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Billing offers cannot be moved "
        "between products"
    )


def test_offer_update_returns_404_when_missing(
    client,
    db_session,
):
    make_platform_admin(db_session)
    product = get_product(db_session)

    response = client.put(
        "/api/v1/admin/billing/offers/999999",
        json=renewaldesk_offer_payload(
            product.id
        ),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Billing offer not found"
    )


@pytest.mark.parametrize(
    "changes",
    [
        {
            "charge_type": "subscription",
            "billing_interval": None,
        },
        {
            "charge_type": "one_time",
            "billing_interval": "month",
        },
        {
            "minimum_amount_cents": 20000,
            "maximum_amount_cents": 10000,
        },
        {
            "currency": "dollars",
        },
        {
            "code": "Invalid Code",
        },
        {
            "service_period_days": 0,
        },
    ],
)
def test_offer_api_rejects_invalid_pricing(
    client,
    db_session,
    changes,
):
    make_platform_admin(db_session)
    product = get_product(db_session)

    payload = renewaldesk_offer_payload(
        product.id
    )
    payload.update(changes)

    response = client.post(
        "/api/v1/admin/billing/offers",
        json=payload,
    )

    assert response.status_code == 422


def test_non_platform_admin_cannot_update_offer(
    client,
    db_session,
):
    product = get_product(db_session)

    offer = BillingOffer(
        product_id=product.id,
        code="protected-offer",
        name="Protected Offer",
        status="draft",
        charge_type="one_time",
        currency="USD",
        minimum_amount_cents=1000,
        maximum_amount_cents=1000,
    )

    db_session.add(offer)
    db_session.commit()
    db_session.refresh(offer)

    payload = renewaldesk_offer_payload(
        product.id
    )

    response = client.put(
        (
            "/api/v1/admin/billing/offers/"
            f"{offer.id}"
        ),
        json=payload,
    )

    assert response.status_code == 403
