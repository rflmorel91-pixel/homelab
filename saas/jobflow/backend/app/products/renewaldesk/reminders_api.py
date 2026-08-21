from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
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
from app.tenant_context import get_current_tenant


router = APIRouter(
    prefix="/reminders",
    tags=["RenewalDesk Reminders"],
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


@router.post(
    "/queue",
    response_model=list[RenewalReminderDeliveryRead],
)
def queue_reminder_deliveries(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    candidates = get_reminder_candidates(
        db,
        tenant.id,
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
            tenant_id=tenant.id,
            renewal_item_id=item.id,
            channel="email",
            status="pending",
            scheduled_for=scheduled_for,
        )

        db.add(delivery)
        deliveries.append(delivery)

    db.commit()

    for delivery in deliveries:
        db.refresh(delivery)

    return deliveries
