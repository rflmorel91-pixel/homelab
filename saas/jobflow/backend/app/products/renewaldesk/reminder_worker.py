from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Product, Tenant
from app.products.renewaldesk.reminders_api import (
    get_reminder_candidates,
    process_pending_deliveries,
    queue_reminder_deliveries_for_tenant,
)


@dataclass
class ReminderCycleSummary:
    dry_run: bool
    tenant_count: int = 0
    candidate_count: int = 0
    tracked_delivery_count: int = 0
    processed_count: int = 0
    sent_count: int = 0
    retry_scheduled_count: int = 0
    failed_count: int = 0


def active_renewaldesk_tenants(
    db: Session,
) -> list[Tenant]:
    return db.scalars(
        select(Tenant)
        .join(
            Product,
            Product.id == Tenant.product_id,
        )
        .where(
            Product.slug == "renewaldesk",
            Product.status == "active",
            Tenant.status == "active",
        )
        .order_by(
            Tenant.client_number,
            Tenant.id,
        )
    ).all()


def run_reminder_cycle(
    db: Session,
    *,
    dry_run: bool = False,
) -> ReminderCycleSummary:
    summary = ReminderCycleSummary(
        dry_run=dry_run,
    )

    tenants = active_renewaldesk_tenants(db)
    summary.tenant_count = len(tenants)

    for tenant in tenants:
        candidates = get_reminder_candidates(
            db,
            tenant.id,
        )

        summary.candidate_count += len(
            candidates
        )

        if dry_run:
            continue

        tracked = (
            queue_reminder_deliveries_for_tenant(
                db,
                tenant.id,
            )
        )

        summary.tracked_delivery_count += len(
            tracked
        )

        processed = process_pending_deliveries(
            db,
            tenant.id,
        )

        summary.processed_count += len(
            processed
        )

        for delivery in processed:
            if delivery.status == "sent":
                summary.sent_count += 1
            elif (
                delivery.status
                == "retry_scheduled"
            ):
                summary.retry_scheduled_count += 1
            elif delivery.status == "failed":
                summary.failed_count += 1

    return summary
