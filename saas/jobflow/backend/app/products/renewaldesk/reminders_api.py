from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant
from app.products.renewaldesk.models import RenewalItem
from app.products.renewaldesk.schemas import RenewalItemRead
from app.tenant_context import get_current_tenant


router = APIRouter(
    prefix="/reminders",
    tags=["RenewalDesk Reminders"],
)


@router.get(
    "/candidates",
    response_model=list[RenewalItemRead],
)
def list_reminder_candidates(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    today = date.today()

    result = db.execute(
        select(RenewalItem)
        .where(
            RenewalItem.tenant_id == tenant.id,
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
