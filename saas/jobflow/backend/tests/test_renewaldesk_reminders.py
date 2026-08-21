from datetime import date, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Product, Tenant
from app.products.renewaldesk.models import (
    RenewalItem,
    RenewalReminderDelivery,
)


def create_renewaldesk_tenant(
    db_session,
    *,
    name,
    slug,
):
    product = db_session.scalar(
        select(Product).where(
            Product.slug == "renewaldesk"
        )
    )

    if product is None:
        product = Product(
            name="RenewalDesk",
            slug="renewaldesk",
            status="active",
            workspace_key="renewaldesk",
        )

        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)

    tenant = Tenant(
        product_id=product.id,
        name=name,
        slug=slug,
    )

    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    return tenant


def create_renewal_item(
    db_session,
    tenant,
):
    item = RenewalItem(
        tenant_id=tenant.id,
        name="General Liability Insurance",
        renewal_date=date(2027, 2, 15),
        status="active",
        reminder_days=30,
    )

    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    return item


def test_reminder_delivery_persists(
    db_session,
):
    tenant = create_renewaldesk_tenant(
        db_session,
        name="Reminder Delivery Tenant",
        slug="reminder-delivery-tenant",
    )

    item = create_renewal_item(
        db_session,
        tenant,
    )

    scheduled_for = datetime(
        2027,
        1,
        16,
        9,
        0,
        0,
    )

    delivery = RenewalReminderDelivery(
        tenant_id=tenant.id,
        renewal_item_id=item.id,
        channel="email",
        status="pending",
        scheduled_for=scheduled_for,
    )

    db_session.add(delivery)
    db_session.commit()
    db_session.refresh(delivery)

    assert delivery.id is not None
    assert delivery.tenant_id == tenant.id
    assert delivery.renewal_item_id == item.id
    assert delivery.channel == "email"
    assert delivery.status == "pending"
    assert delivery.scheduled_for == scheduled_for
    assert delivery.sent_at is None
    assert delivery.created_at is not None
    assert delivery.updated_at is not None


def test_reminder_delivery_occurrence_is_unique(
    db_session,
):
    tenant = create_renewaldesk_tenant(
        db_session,
        name="Reminder Idempotency Tenant",
        slug="reminder-idempotency-tenant",
    )

    item = create_renewal_item(
        db_session,
        tenant,
    )

    scheduled_for = datetime(
        2027,
        1,
        16,
        9,
        0,
        0,
    )

    first = RenewalReminderDelivery(
        tenant_id=tenant.id,
        renewal_item_id=item.id,
        channel="email",
        status="pending",
        scheduled_for=scheduled_for,
    )

    db_session.add(first)
    db_session.commit()

    duplicate = RenewalReminderDelivery(
        tenant_id=tenant.id,
        renewal_item_id=item.id,
        channel="email",
        status="pending",
        scheduled_for=scheduled_for,
    )

    db_session.add(duplicate)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_different_reminder_occurrences_are_allowed(
    db_session,
):
    tenant = create_renewaldesk_tenant(
        db_session,
        name="Reminder Occurrences Tenant",
        slug="reminder-occurrences-tenant",
    )

    item = create_renewal_item(
        db_session,
        tenant,
    )

    deliveries = [
        RenewalReminderDelivery(
            tenant_id=tenant.id,
            renewal_item_id=item.id,
            channel="email",
            status="pending",
            scheduled_for=datetime(
                2027,
                1,
                16,
                9,
                0,
                0,
            ),
        ),
        RenewalReminderDelivery(
            tenant_id=tenant.id,
            renewal_item_id=item.id,
            channel="email",
            status="pending",
            scheduled_for=datetime(
                2027,
                1,
                17,
                9,
                0,
                0,
            ),
        ),
    ]

    db_session.add_all(deliveries)
    db_session.commit()

    stored = db_session.scalars(
        select(RenewalReminderDelivery)
        .where(
            RenewalReminderDelivery.renewal_item_id
            == item.id
        )
        .order_by(
            RenewalReminderDelivery.scheduled_for
        )
    ).all()

    assert len(stored) == 2
