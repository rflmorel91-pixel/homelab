from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant
from app.products.renewaldesk.models import RenewalItem
from app.products.renewaldesk.schemas import (
    RenewalDashboard,
    RenewalItemRead,
)
from app.tenant_context import get_current_tenant


router = APIRouter(
    prefix="/dashboard",
    tags=["RenewalDesk Dashboard"],
)


@router.get(
    "",
    response_model=RenewalDashboard,
)
def get_renewaldesk_dashboard(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    result = db.execute(
        select(RenewalItem).where(
            RenewalItem.tenant_id == tenant.id
        )
    )

    items = [
        RenewalItemRead.model_validate(item)
        for item in result.scalars().all()
    ]

    priority = {
        "expired": 0,
        "due_soon": 1,
        "upcoming": 2,
        "inactive": 3,
    }

    items.sort(
        key=lambda item: (
            priority[item.renewal_state],
            item.renewal_date,
            item.id,
        )
    )

    counts = {
        "expired": 0,
        "due_soon": 0,
        "upcoming": 0,
        "inactive": 0,
    }

    for item in items:
        counts[item.renewal_state] += 1

    return RenewalDashboard(
        total=len(items),
        expired=counts["expired"],
        due_soon=counts["due_soon"],
        upcoming=counts["upcoming"],
        inactive=counts["inactive"],
        items=items,
    )
