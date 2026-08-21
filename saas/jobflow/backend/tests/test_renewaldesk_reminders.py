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
        owner_name="Renewal Owner",
        owner_email="owner@example.test",
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


REMINDER_QUEUE_URL = (
    "/api/v1/products/renewaldesk/reminders/queue"
)


def test_reminder_queue_creates_pending_delivery(
    authenticated_client,
    db_session,
    monkeypatch,
):
    from app.products.renewaldesk import reminders_api

    class FixedDate(date):
        @classmethod
        def today(cls):
            return cls(2027, 1, 20)

    monkeypatch.setattr(
        reminders_api,
        "date",
        FixedDate,
    )

    client = authenticated_client

    tenant = create_renewaldesk_tenant(
        db_session,
        name="Reminder Queue Tenant",
        slug="reminder-queue-tenant",
    )

    item = RenewalItem(
        tenant_id=tenant.id,
        name="Queue Insurance",
        renewal_date=date(2027, 2, 15),
        status="active",
        reminder_days=30,
    )

    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    response = client.post(
        REMINDER_QUEUE_URL,
        headers=client.auth_headers(tenant),
    )

    assert response.status_code == 200

    payload = response.json()

    assert len(payload) == 1
    assert payload[0]["renewal_item_id"] == item.id
    assert payload[0]["channel"] == "email"
    assert payload[0]["status"] == "pending"
    assert payload[0]["scheduled_for"].startswith(
        "2027-01-16T09:00:00"
    )

    stored = db_session.scalars(
        select(RenewalReminderDelivery)
        .where(
            RenewalReminderDelivery.tenant_id
            == tenant.id
        )
    ).all()

    assert len(stored) == 1


def test_reminder_queue_is_idempotent(
    authenticated_client,
    db_session,
    monkeypatch,
):
    from app.products.renewaldesk import reminders_api

    class FixedDate(date):
        @classmethod
        def today(cls):
            return cls(2027, 1, 20)

    monkeypatch.setattr(
        reminders_api,
        "date",
        FixedDate,
    )

    client = authenticated_client

    tenant = create_renewaldesk_tenant(
        db_session,
        name="Idempotent Queue Tenant",
        slug="idempotent-queue-tenant",
    )

    item = RenewalItem(
        tenant_id=tenant.id,
        name="Idempotent Insurance",
        renewal_date=date(2027, 2, 15),
        status="active",
        reminder_days=30,
    )

    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    headers = client.auth_headers(tenant)

    first = client.post(
        REMINDER_QUEUE_URL,
        headers=headers,
    )

    second = client.post(
        REMINDER_QUEUE_URL,
        headers=headers,
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert first.json()[0]["id"] == (
        second.json()[0]["id"]
    )

    stored = db_session.scalars(
        select(RenewalReminderDelivery)
        .where(
            RenewalReminderDelivery.renewal_item_id
            == item.id
        )
    ).all()

    assert len(stored) == 1


def test_reminder_queue_ignores_ineligible_items(
    authenticated_client,
    db_session,
    monkeypatch,
):
    from app.products.renewaldesk import reminders_api

    class FixedDate(date):
        @classmethod
        def today(cls):
            return cls(2027, 1, 15)

    monkeypatch.setattr(
        reminders_api,
        "date",
        FixedDate,
    )

    client = authenticated_client

    tenant = create_renewaldesk_tenant(
        db_session,
        name="Queue Eligibility Tenant",
        slug="queue-eligibility-tenant",
    )

    items = [
        RenewalItem(
            tenant_id=tenant.id,
            name="Too Far Away",
            renewal_date=date(2027, 4, 1),
            status="active",
            reminder_days=30,
        ),
        RenewalItem(
            tenant_id=tenant.id,
            name="Already Renewed",
            renewal_date=date(2027, 1, 20),
            status="renewed",
            reminder_days=30,
        ),
        RenewalItem(
            tenant_id=tenant.id,
            name="Inactive",
            renewal_date=date(2027, 1, 20),
            status="inactive",
            reminder_days=30,
        ),
    ]

    db_session.add_all(items)
    db_session.commit()

    response = client.post(
        REMINDER_QUEUE_URL,
        headers=client.auth_headers(tenant),
    )

    assert response.status_code == 200
    assert response.json() == []

    stored = db_session.scalars(
        select(RenewalReminderDelivery)
        .where(
            RenewalReminderDelivery.tenant_id
            == tenant.id
        )
    ).all()

    assert stored == []


REMINDER_PROCESS_URL = (
    "/api/v1/products/renewaldesk/reminders/process"
)


def create_pending_delivery(
    db_session,
    tenant,
    item,
):
    delivery = RenewalReminderDelivery(
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
    )

    db_session.add(delivery)
    db_session.commit()
    db_session.refresh(delivery)

    return delivery


def test_reminder_process_marks_delivery_sent(
    authenticated_client,
    db_session,
    monkeypatch,
):
    from app.products.renewaldesk import reminders_api

    monkeypatch.setattr(
        reminders_api,
        "deliver_reminder",
        lambda delivery, item: None,
    )

    client = authenticated_client

    tenant = create_renewaldesk_tenant(
        db_session,
        name="Reminder Process Tenant",
        slug="reminder-process-tenant",
    )

    item = create_renewal_item(
        db_session,
        tenant,
    )

    delivery = create_pending_delivery(
        db_session,
        tenant,
        item,
    )

    response = client.post(
        REMINDER_PROCESS_URL,
        headers=client.auth_headers(tenant),
    )

    assert response.status_code == 200

    payload = response.json()

    assert len(payload) == 1
    assert payload[0]["id"] == delivery.id
    assert payload[0]["status"] == "sent"
    assert payload[0]["sent_at"] is not None

    db_session.refresh(delivery)

    assert delivery.status == "sent"
    assert delivery.sent_at is not None


def test_reminder_process_marks_failure(
    authenticated_client,
    db_session,
    monkeypatch,
):
    from app.products.renewaldesk import reminders_api

    def fail_delivery(delivery, item):
        raise RuntimeError("Delivery failed")

    monkeypatch.setattr(
        reminders_api,
        "deliver_reminder",
        fail_delivery,
    )

    client = authenticated_client

    tenant = create_renewaldesk_tenant(
        db_session,
        name="Reminder Failure Tenant",
        slug="reminder-failure-tenant",
    )

    item = create_renewal_item(
        db_session,
        tenant,
    )

    delivery = create_pending_delivery(
        db_session,
        tenant,
        item,
    )

    response = client.post(
        REMINDER_PROCESS_URL,
        headers=client.auth_headers(tenant),
    )

    assert response.status_code == 200
    assert response.json()[0]["status"] == "failed"

    db_session.refresh(delivery)

    assert delivery.status == "failed"
    assert delivery.sent_at is None


def test_reminder_process_skips_sent_delivery(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    tenant = create_renewaldesk_tenant(
        db_session,
        name="Reminder Sent Tenant",
        slug="reminder-sent-tenant",
    )

    item = create_renewal_item(
        db_session,
        tenant,
    )

    delivery = create_pending_delivery(
        db_session,
        tenant,
        item,
    )

    delivery.status = "sent"
    delivery.sent_at = datetime(
        2027,
        1,
        16,
        9,
        5,
        0,
    )

    db_session.commit()

    response = client.post(
        REMINDER_PROCESS_URL,
        headers=client.auth_headers(tenant),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_reminder_process_is_tenant_scoped(
    authenticated_client,
    db_session,
    monkeypatch,
):
    from app.products.renewaldesk import reminders_api

    monkeypatch.setattr(
        reminders_api,
        "deliver_reminder",
        lambda delivery, item: None,
    )

    client = authenticated_client

    tenant_one = create_renewaldesk_tenant(
        db_session,
        name="Process Tenant One",
        slug="process-tenant-one",
    )

    tenant_two = create_renewaldesk_tenant(
        db_session,
        name="Process Tenant Two",
        slug="process-tenant-two",
    )

    item_one = create_renewal_item(
        db_session,
        tenant_one,
    )

    item_two = create_renewal_item(
        db_session,
        tenant_two,
    )

    delivery_one = create_pending_delivery(
        db_session,
        tenant_one,
        item_one,
    )

    delivery_two = create_pending_delivery(
        db_session,
        tenant_two,
        item_two,
    )

    response = client.post(
        REMINDER_PROCESS_URL,
        headers=client.auth_headers(
            tenant_one
        ),
    )

    assert response.status_code == 200

    payload = response.json()

    assert [
        delivery["id"]
        for delivery in payload
    ] == [delivery_one.id]

    db_session.refresh(delivery_one)
    db_session.refresh(delivery_two)

    assert delivery_one.status == "sent"
    assert delivery_two.status == "pending"


def test_smtp_delivery_uses_owner_email(
    monkeypatch,
):
    from app.products.renewaldesk import smtp_delivery

    monkeypatch.setenv(
        "RENEWALDESK_SMTP_HOST",
        "smtp.example.test",
    )
    monkeypatch.setenv(
        "RENEWALDESK_SMTP_PORT",
        "587",
    )
    monkeypatch.setenv(
        "RENEWALDESK_SMTP_FROM_EMAIL",
        "reminders@example.test",
    )
    monkeypatch.setenv(
        "RENEWALDESK_SMTP_USE_TLS",
        "true",
    )

    sent_messages = []

    class FakeSMTP:
        def __init__(
            self,
            host,
            port,
            timeout,
        ):
            assert host == "smtp.example.test"
            assert port == 587
            assert timeout == 15

        def __enter__(self):
            return self

        def __exit__(
            self,
            exc_type,
            exc,
            tb,
        ):
            return False

        def starttls(self):
            return None

        def send_message(
            self,
            message,
        ):
            sent_messages.append(message)

    monkeypatch.setattr(
        smtp_delivery.smtplib,
        "SMTP",
        FakeSMTP,
    )

    item = RenewalItem(
        tenant_id=1,
        name="Business Insurance",
        renewal_date=date(2027, 3, 1),
        owner_name="Office Manager",
        owner_email="owner@example.test",
        reminder_days=30,
    )

    delivery = RenewalReminderDelivery(
        tenant_id=1,
        renewal_item_id=1,
        channel="email",
        status="pending",
        scheduled_for=datetime(
            2027,
            1,
            30,
            9,
            0,
        ),
    )

    smtp_delivery.send_reminder_email(
        delivery,
        item,
    )

    assert len(sent_messages) == 1

    message = sent_messages[0]

    assert message["To"] == (
        "owner@example.test"
    )
    assert message["From"] == (
        "reminders@example.test"
    )
    assert "Business Insurance" in (
        message["Subject"]
    )


def test_smtp_delivery_requires_owner_email(
    monkeypatch,
):
    from app.products.renewaldesk import smtp_delivery

    monkeypatch.setenv(
        "RENEWALDESK_SMTP_HOST",
        "smtp.example.test",
    )
    monkeypatch.setenv(
        "RENEWALDESK_SMTP_FROM_EMAIL",
        "reminders@example.test",
    )

    item = RenewalItem(
        tenant_id=1,
        name="Business Insurance",
        renewal_date=date(2027, 3, 1),
        owner_email=None,
        reminder_days=30,
    )

    delivery = RenewalReminderDelivery(
        tenant_id=1,
        renewal_item_id=1,
        channel="email",
        status="pending",
        scheduled_for=datetime(
            2027,
            1,
            30,
            9,
            0,
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="no owner email",
    ):
        smtp_delivery.send_reminder_email(
            delivery,
            item,
        )
