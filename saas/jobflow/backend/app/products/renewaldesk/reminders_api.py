from datetime import (
    date,
    datetime,
    time,
    timedelta,
    timezone,
)

from fastapi import APIRouter, Depends
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant
from app.products.renewaldesk.models import (
    RenewalItem,
    RenewalReminderDelivery,
)
from app.products.renewaldesk.schemas import (
    RenewalItemRead,
    RenewalReminderDeliveryRead,
)
from app.products.renewaldesk.smtp_delivery import (
    send_reminder_email,
)
from app.tenant_context import get_current_tenant


router = APIRouter(
    prefix="/reminders",
    tags=["RenewalDesk Reminders"],
)


MAX_DELIVERY_ATTEMPTS = 4
DELIVERY_BATCH_SIZE = 100
STALE_PROCESSING_MINUTES = 15
RETRY_DELAYS = (
    timedelta(minutes=5),
    timedelta(minutes=30),
    timedelta(hours=2),
)


def utc_now_naive() -> datetime:
    return datetime.now(
        timezone.utc
    ).replace(
        tzinfo=None
    )


def get_reminder_candidates(
    db: Session,
    tenant_id: int,
) -> list[RenewalItem]:
    today = date.today()

    result = db.execute(
        select(RenewalItem)
        .where(
            RenewalItem.tenant_id == tenant_id,
            RenewalItem.status.in_(
                {
                    "active",
                    "renewal_in_progress",
                }
            ),
        )
        .order_by(
            RenewalItem.renewal_date,
            RenewalItem.id,
        )
    )

    candidates = []

    for item in result.scalars().all():
        days_until_renewal = (
            item.renewal_date - today
        ).days

        if days_until_renewal <= item.reminder_days:
            candidates.append(item)

    return candidates


def reminder_scheduled_for(
    item: RenewalItem,
) -> datetime:
    reminder_date = (
        item.renewal_date
        - timedelta(days=item.reminder_days)
    )

    return datetime.combine(
        reminder_date,
        time(hour=9),
    )


def deliver_reminder(
    delivery: RenewalReminderDelivery,
    item: RenewalItem,
) -> None:
    send_reminder_email(
        delivery,
        item,
    )


def claim_due_deliveries(
    db: Session,
    tenant_id: int,
    *,
    batch_size: int = DELIVERY_BATCH_SIZE,
) -> list[RenewalReminderDelivery]:
    now = utc_now_naive()

    deliveries = db.scalars(
        select(RenewalReminderDelivery)
        .where(
            RenewalReminderDelivery.tenant_id
            == tenant_id,
            or_(
                and_(
                    RenewalReminderDelivery.status
                    == "pending",
                    RenewalReminderDelivery.scheduled_for
                    <= now,
                ),
                and_(
                    RenewalReminderDelivery.status
                    == "retry_scheduled",
                    RenewalReminderDelivery.next_attempt_at
                    .is_not(None),
                    RenewalReminderDelivery.next_attempt_at
                    <= now,
                ),
            ),
        )
        .order_by(
            RenewalReminderDelivery.scheduled_for,
            RenewalReminderDelivery.id,
        )
        .with_for_update(
            skip_locked=True
        )
        .limit(batch_size)
    ).all()

    for delivery in deliveries:
        delivery.status = "processing"
        delivery.processing_started_at = now
        delivery.last_attempt_at = now
        delivery.attempt_count += 1

    db.commit()

    for delivery in deliveries:
        db.refresh(delivery)

    return deliveries


def delivery_retry_delay(
    attempt_count: int,
) -> timedelta:
    index = min(
        max(attempt_count - 1, 0),
        len(RETRY_DELAYS) - 1,
    )

    return RETRY_DELAYS[index]


def safe_delivery_error(
    error: Exception,
) -> str:
    return (
        f"{type(error).__name__}: {error}"
    )[:1000]


def recover_stale_deliveries(
    db: Session,
    tenant_id: int,
) -> list[RenewalReminderDelivery]:
    now = utc_now_naive()
    stale_before = (
        now
        - timedelta(
            minutes=STALE_PROCESSING_MINUTES
        )
    )

    deliveries = db.scalars(
        select(RenewalReminderDelivery)
        .where(
            RenewalReminderDelivery.tenant_id
            == tenant_id,
            RenewalReminderDelivery.status
            == "processing",
            or_(
                RenewalReminderDelivery
                .processing_started_at.is_(None),
                RenewalReminderDelivery
                .processing_started_at
                <= stale_before,
            ),
        )
        .order_by(
            RenewalReminderDelivery.id
        )
        .with_for_update(
            skip_locked=True
        )
        .limit(DELIVERY_BATCH_SIZE)
    ).all()

    for delivery in deliveries:
        delivery.processing_started_at = None
        delivery.sent_at = None
        delivery.last_error = (
            "Processing claim expired before "
            "an outcome was recorded"
        )

        if (
            delivery.attempt_count
            >= MAX_DELIVERY_ATTEMPTS
        ):
            delivery.status = "failed"
            delivery.failed_at = now
            delivery.next_attempt_at = None

        else:
            delivery.status = "retry_scheduled"
            delivery.failed_at = None
            delivery.next_attempt_at = (
                now
                + delivery_retry_delay(
                    delivery.attempt_count
                )
            )

    db.commit()

    for delivery in deliveries:
        db.refresh(delivery)

    return deliveries


def process_pending_deliveries(
    db: Session,
    tenant_id: int,
) -> list[RenewalReminderDelivery]:
    recover_stale_deliveries(
        db,
        tenant_id,
    )

    deliveries = claim_due_deliveries(
        db,
        tenant_id,
    )

    processed = []

    for delivery in deliveries:
        item = db.scalar(
            select(RenewalItem).where(
                RenewalItem.id
                == delivery.renewal_item_id,
                RenewalItem.tenant_id
                == tenant_id,
            )
        )

        try:
            if item is None:
                raise RuntimeError(
                    "Renewal item not found"
                )

            deliver_reminder(
                delivery,
                item,
            )

            delivery.status = "sent"
            delivery.sent_at = utc_now_naive()
            delivery.next_attempt_at = None
            delivery.last_error = None
            delivery.failed_at = None

        except Exception as error:
            delivery.sent_at = None
            delivery.last_error = safe_delivery_error(
                error
            )

            if (
                delivery.attempt_count
                >= MAX_DELIVERY_ATTEMPTS
            ):
                delivery.status = "failed"
                delivery.failed_at = utc_now_naive()
                delivery.next_attempt_at = None

            else:
                delivery.status = "retry_scheduled"
                delivery.failed_at = None
                delivery.next_attempt_at = (
                    utc_now_naive()
                    + delivery_retry_delay(
                        delivery.attempt_count
                    )
                )

        delivery.processing_started_at = None

        db.commit()
        db.refresh(delivery)
        processed.append(delivery)

    return processed


@router.get(
    "/candidates",
    response_model=list[RenewalItemRead],
)
def list_reminder_candidates(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    return get_reminder_candidates(
        db,
        tenant.id,
    )


def queue_reminder_deliveries_for_tenant(
    db: Session,
    tenant_id: int,
) -> list[RenewalReminderDelivery]:
    candidates = get_reminder_candidates(
        db,
        tenant_id,
    )

    deliveries = []

    for item in candidates:
        scheduled_for = reminder_scheduled_for(
            item
        )

        existing = db.scalar(
            select(RenewalReminderDelivery)
            .where(
                RenewalReminderDelivery.renewal_item_id
                == item.id,
                RenewalReminderDelivery.channel
                == "email",
                RenewalReminderDelivery.scheduled_for
                == scheduled_for,
            )
        )

        if existing is not None:
            deliveries.append(existing)
            continue

        delivery = RenewalReminderDelivery(
            tenant_id=tenant_id,
            renewal_item_id=item.id,
            channel="email",
            status="pending",
            scheduled_for=scheduled_for,
            recipient_email=item.owner_email,
            next_attempt_at=scheduled_for,
        )

        db.add(delivery)
        deliveries.append(delivery)

    db.commit()

    for delivery in deliveries:
        db.refresh(delivery)

    return deliveries


@router.post(
    "/queue",
    response_model=list[RenewalReminderDeliveryRead],
)
def queue_reminder_deliveries(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    return queue_reminder_deliveries_for_tenant(
        db,
        tenant.id,
    )


@router.post(
    "/process",
    response_model=list[RenewalReminderDeliveryRead],
)
def process_reminder_deliveries(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    return process_pending_deliveries(
        db,
        tenant.id,
    )
