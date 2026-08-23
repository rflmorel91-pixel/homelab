from datetime import (
    date,
    datetime,
    timezone,
)

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Product, Tenant
from app.products.renewaldesk.reminders_api import (
    reminder_scheduled_for,
    tenant_local_today,
)
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


def test_tenant_local_today_uses_tenant_timezone():
    tenant = Tenant(
        product_id=1,
        name="Eastern Tenant",
        slug="eastern-tenant",
        timezone_name="America/New_York",
    )

    result = tenant_local_today(
        tenant,
        now=datetime(
            2027,
            1,
            1,
            2,
            0,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert result == date(2026, 12, 31)


def test_reminder_schedule_converts_winter_time_to_utc():
    item = RenewalItem(
        tenant_id=1,
        name="Winter Insurance",
        renewal_date=date(2027, 3, 1),
        reminder_days=30,
    )

    assert reminder_scheduled_for(
        item,
        "America/New_York",
    ) == datetime(
        2027,
        1,
        30,
        14,
        0,
        0,
    )


def test_reminder_schedule_converts_summer_time_to_utc():
    item = RenewalItem(
        tenant_id=1,
        name="Summer Insurance",
        renewal_date=date(2027, 7, 1),
        reminder_days=30,
    )

    assert reminder_scheduled_for(
        item,
        "America/New_York",
    ) == datetime(
        2027,
        6,
        1,
        13,
        0,
        0,
    )


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
        occurrence_renewal_date=item.renewal_date,
        reminder_days_snapshot=item.reminder_days,
        channel="email",
        status="pending",
        scheduled_for=scheduled_for,
        recipient_email="owner@example.test",
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
    assert delivery.occurrence_renewal_date == (
        item.renewal_date
    )
    assert delivery.reminder_days_snapshot == (
        item.reminder_days
    )
    assert delivery.recipient_email == (
        "owner@example.test"
    )
    assert delivery.attempt_count == 0
    assert delivery.last_attempt_at is None
    assert delivery.next_attempt_at is None
    assert delivery.processing_started_at is None
    assert delivery.last_error is None
    assert delivery.provider_message_id is None
    assert delivery.failed_at is None
    assert delivery.sent_at is None
    assert delivery.created_at is not None
    assert delivery.updated_at is not None


def test_reminder_delivery_rejects_invalid_status(
    db_session,
):
    tenant = create_renewaldesk_tenant(
        db_session,
        name="Invalid Delivery Status Tenant",
        slug="invalid-delivery-status-tenant",
    )

    item = create_renewal_item(
        db_session,
        tenant,
    )

    delivery = RenewalReminderDelivery(
        tenant_id=tenant.id,
        renewal_item_id=item.id,
        occurrence_renewal_date=item.renewal_date,
        reminder_days_snapshot=item.reminder_days,
        channel="email",
        status="unknown",
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

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


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
        occurrence_renewal_date=item.renewal_date,
        reminder_days_snapshot=item.reminder_days,
        channel="email",
        status="pending",
        scheduled_for=scheduled_for,
    )

    db_session.add(first)
    db_session.commit()

    duplicate = RenewalReminderDelivery(
        tenant_id=tenant.id,
        renewal_item_id=item.id,
        occurrence_renewal_date=item.renewal_date,
        reminder_days_snapshot=item.reminder_days,
        channel="email",
        status="pending",
        scheduled_for=(
            scheduled_for.replace(hour=14)
        ),
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
            occurrence_renewal_date=item.renewal_date,
            reminder_days_snapshot=item.reminder_days,
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
            occurrence_renewal_date=date(2028, 2, 15),
            reminder_days_snapshot=item.reminder_days,
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

    monkeypatch.setattr(
        reminders_api,
        "tenant_local_today",
        lambda tenant: date(2027, 1, 20),
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
        owner_email="queue-owner@example.test",
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
    assert payload[0]["recipient_email"] == (
        "queue-owner@example.test"
    )
    assert payload[0]["attempt_count"] == 0
    assert payload[0]["occurrence_renewal_date"] == (
        "2027-02-15"
    )
    assert payload[0]["reminder_days_snapshot"] == 30
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
    assert stored[0].recipient_email == (
        "queue-owner@example.test"
    )
    assert stored[0].attempt_count == 0
    assert stored[0].occurrence_renewal_date == (
        item.renewal_date
    )
    assert stored[0].reminder_days_snapshot == 30


def test_reminder_queue_is_idempotent(
    authenticated_client,
    db_session,
    monkeypatch,
):
    from app.products.renewaldesk import reminders_api

    monkeypatch.setattr(
        reminders_api,
        "tenant_local_today",
        lambda tenant: date(2027, 1, 20),
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


def test_queue_reuses_sent_occurrence_when_schedule_changes(
    authenticated_client,
    db_session,
    monkeypatch,
):
    from app.products.renewaldesk import reminders_api

    monkeypatch.setattr(
        reminders_api,
        "tenant_local_today",
        lambda tenant: date(2027, 1, 20),
    )

    client = authenticated_client

    tenant = create_renewaldesk_tenant(
        db_session,
        name="Timezone Safe Queue Tenant",
        slug="timezone-safe-queue-tenant",
    )

    item = RenewalItem(
        tenant_id=tenant.id,
        name="Timezone Safe Insurance",
        renewal_date=date(2027, 2, 15),
        status="active",
        owner_email="timezone-owner@example.test",
        reminder_days=30,
    )

    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    sent_delivery = RenewalReminderDelivery(
        tenant_id=tenant.id,
        renewal_item_id=item.id,
        channel="email",
        status="sent",
        scheduled_for=datetime(
            2027, 1, 16, 9, 0, 0
        ),
        occurrence_renewal_date=item.renewal_date,
        reminder_days_snapshot=item.reminder_days,
        recipient_email=item.owner_email,
        sent_at=datetime(
            2027, 1, 16, 9, 1, 0
        ),
    )

    db_session.add(sent_delivery)
    db_session.commit()
    db_session.refresh(sent_delivery)

    monkeypatch.setattr(
        reminders_api,
        "reminder_scheduled_for",
        lambda item, timezone_name: datetime(
            2027, 1, 16, 14, 0, 0
        ),
    )

    response = client.post(
        REMINDER_QUEUE_URL,
        headers=client.auth_headers(tenant),
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == sent_delivery.id
    assert response.json()[0]["status"] == "sent"
    assert response.json()[0]["scheduled_for"].startswith(
        "2027-01-16T09:00:00"
    )

    stored = db_session.scalars(
        select(RenewalReminderDelivery).where(
            RenewalReminderDelivery.renewal_item_id
            == item.id
        )
    ).all()

    assert len(stored) == 1
    assert stored[0].id == sent_delivery.id
    assert stored[0].sent_at is not None


def test_reminder_queue_ignores_ineligible_items(
    authenticated_client,
    db_session,
    monkeypatch,
):
    from app.products.renewaldesk import reminders_api

    monkeypatch.setattr(
        reminders_api,
        "tenant_local_today",
        lambda tenant: date(2027, 1, 15),
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
        occurrence_renewal_date=item.renewal_date,
        reminder_days_snapshot=item.reminder_days,
        channel="email",
        status="pending",
        scheduled_for=datetime(
            2020,
            1,
            1,
            9,
            0,
            0,
        ),
        recipient_email=item.owner_email,
        next_attempt_at=datetime(
            2020,
            1,
            1,
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
    assert delivery.attempt_count == 1
    assert delivery.last_attempt_at is not None
    assert delivery.processing_started_at is None
    assert delivery.next_attempt_at is None
    assert delivery.last_error is None
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
    assert (
        response.json()[0]["status"]
        == "retry_scheduled"
    )

    db_session.refresh(delivery)

    assert delivery.status == "retry_scheduled"
    assert delivery.attempt_count == 1
    assert delivery.last_attempt_at is not None
    assert delivery.next_attempt_at is not None
    assert delivery.processing_started_at is None
    assert delivery.last_error == (
        "RuntimeError: Delivery failed"
    )
    assert delivery.failed_at is None
    assert delivery.sent_at is None


def test_reminder_process_marks_terminal_failure(
    authenticated_client,
    db_session,
    monkeypatch,
):
    from app.products.renewaldesk import reminders_api

    def fail_delivery(delivery, item):
        raise RuntimeError("Permanent failure")

    monkeypatch.setattr(
        reminders_api,
        "deliver_reminder",
        fail_delivery,
    )

    client = authenticated_client

    tenant = create_renewaldesk_tenant(
        db_session,
        name="Terminal Failure Tenant",
        slug="terminal-failure-tenant",
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

    delivery.attempt_count = 3
    db_session.commit()

    response = client.post(
        REMINDER_PROCESS_URL,
        headers=client.auth_headers(tenant),
    )

    assert response.status_code == 200
    assert response.json()[0]["status"] == "failed"

    db_session.refresh(delivery)

    assert delivery.status == "failed"
    assert delivery.attempt_count == 4
    assert delivery.next_attempt_at is None
    assert delivery.processing_started_at is None
    assert delivery.last_error == (
        "RuntimeError: Permanent failure"
    )
    assert delivery.failed_at is not None
    assert delivery.sent_at is None


def test_reminder_process_skips_future_delivery(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    tenant = create_renewaldesk_tenant(
        db_session,
        name="Future Delivery Tenant",
        slug="future-delivery-tenant",
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

    delivery.scheduled_for = datetime(
        2099,
        1,
        1,
        9,
        0,
        0,
    )
    delivery.next_attempt_at = delivery.scheduled_for
    db_session.commit()

    response = client.post(
        REMINDER_PROCESS_URL,
        headers=client.auth_headers(tenant),
    )

    assert response.status_code == 200
    assert response.json() == []

    db_session.refresh(delivery)

    assert delivery.status == "pending"
    assert delivery.attempt_count == 0
    assert delivery.sent_at is None


def test_stale_processing_delivery_is_recovered(
    db_session,
):
    from app.products.renewaldesk import reminders_api

    tenant = create_renewaldesk_tenant(
        db_session,
        name="Stale Processing Tenant",
        slug="stale-processing-tenant",
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

    delivery.status = "processing"
    delivery.attempt_count = 1
    delivery.last_attempt_at = datetime(
        2020,
        1,
        1,
        9,
        0,
        0,
    )
    delivery.processing_started_at = datetime(
        2020,
        1,
        1,
        9,
        0,
        0,
    )
    delivery.next_attempt_at = None
    db_session.commit()

    recovered = (
        reminders_api.recover_stale_deliveries(
            db_session,
            tenant.id,
        )
    )

    assert [row.id for row in recovered] == [
        delivery.id
    ]

    db_session.refresh(delivery)

    assert delivery.status == "retry_scheduled"
    assert delivery.attempt_count == 1
    assert delivery.processing_started_at is None
    assert delivery.next_attempt_at is not None
    assert delivery.failed_at is None
    assert delivery.sent_at is None
    assert delivery.last_error == (
        "Processing claim expired before "
        "an outcome was recorded"
    )


def test_recent_processing_delivery_is_not_recovered(
    db_session,
):
    from app.products.renewaldesk import reminders_api

    tenant = create_renewaldesk_tenant(
        db_session,
        name="Recent Processing Tenant",
        slug="recent-processing-tenant",
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

    delivery.status = "processing"
    delivery.attempt_count = 1
    delivery.processing_started_at = datetime(
        2099,
        1,
        1,
        9,
        0,
        0,
    )
    delivery.next_attempt_at = None
    db_session.commit()

    recovered = (
        reminders_api.recover_stale_deliveries(
            db_session,
            tenant.id,
        )
    )

    assert recovered == []

    db_session.refresh(delivery)

    assert delivery.status == "processing"
    assert delivery.attempt_count == 1
    assert delivery.processing_started_at is not None
    assert delivery.next_attempt_at is None


def test_terminal_stale_delivery_is_failed(
    db_session,
):
    from app.products.renewaldesk import reminders_api

    tenant = create_renewaldesk_tenant(
        db_session,
        name="Terminal Stale Tenant",
        slug="terminal-stale-tenant",
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

    delivery.status = "processing"
    delivery.attempt_count = 4
    delivery.processing_started_at = datetime(
        2020,
        1,
        1,
        9,
        0,
        0,
    )
    delivery.next_attempt_at = None
    db_session.commit()

    recovered = (
        reminders_api.recover_stale_deliveries(
            db_session,
            tenant.id,
        )
    )

    assert [row.id for row in recovered] == [
        delivery.id
    ]

    db_session.refresh(delivery)

    assert delivery.status == "failed"
    assert delivery.attempt_count == 4
    assert delivery.processing_started_at is None
    assert delivery.next_attempt_at is None
    assert delivery.failed_at is not None
    assert delivery.sent_at is None
    assert delivery.last_error == (
        "Processing claim expired before "
        "an outcome was recorded"
    )


def test_due_retry_is_claimed_and_sent(
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
        name="Due Retry Tenant",
        slug="due-retry-tenant",
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

    delivery.status = "retry_scheduled"
    delivery.attempt_count = 1
    delivery.last_error = (
        "RuntimeError: Initial failure"
    )
    delivery.next_attempt_at = datetime(
        2020,
        1,
        1,
        10,
        0,
        0,
    )
    db_session.commit()

    response = client.post(
        REMINDER_PROCESS_URL,
        headers=client.auth_headers(tenant),
    )

    assert response.status_code == 200
    assert response.json()[0]["status"] == "sent"

    db_session.refresh(delivery)

    assert delivery.status == "sent"
    assert delivery.attempt_count == 2
    assert delivery.last_attempt_at is not None
    assert delivery.next_attempt_at is None
    assert delivery.processing_started_at is None
    assert delivery.last_error is None
    assert delivery.failed_at is None
    assert delivery.sent_at is not None


def test_claim_due_deliveries_skips_locked_row(
    db_session,
):
    from app.database import SessionLocal
    from app.products.renewaldesk import reminders_api

    tenant = create_renewaldesk_tenant(
        db_session,
        name="Locked Delivery Tenant",
        slug="locked-delivery-tenant",
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

    lock_session = SessionLocal()
    worker_session = SessionLocal()

    try:
        locked_delivery = lock_session.scalar(
            select(RenewalReminderDelivery)
            .where(
                RenewalReminderDelivery.id
                == delivery.id
            )
            .with_for_update()
        )

        assert locked_delivery is not None

        claimed = (
            reminders_api.claim_due_deliveries(
                worker_session,
                tenant.id,
            )
        )

        assert claimed == []

    finally:
        worker_session.rollback()
        worker_session.close()
        lock_session.rollback()
        lock_session.close()

    db_session.expire_all()

    stored = db_session.get(
        RenewalReminderDelivery,
        delivery.id,
    )

    assert stored is not None
    assert stored.status == "pending"
    assert stored.attempt_count == 0
    assert stored.processing_started_at is None


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
    monkeypatch.delenv(
        "RENEWALDESK_SMTP_USERNAME",
        raising=False,
    )
    monkeypatch.delenv(
        "RENEWALDESK_SMTP_PASSWORD",
        raising=False,
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
