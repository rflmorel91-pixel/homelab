from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant
from app.products.renewaldesk.models import RenewalItem
from app.products.renewaldesk.schemas import (
    RenewalItemCreate,
    RenewalItemRead,
    RenewalItemUpdate,
)
from app.tenant_context import get_current_tenant


router = APIRouter(
    prefix="/items",
    tags=["RenewalDesk Items"],
)


@router.post(
    "",
    response_model=RenewalItemRead,
    status_code=201,
)
def create_renewal_item(
    item: RenewalItemCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    db_item = RenewalItem(
        tenant_id=tenant.id,
        name=item.name,
        category=item.category,
        renewal_date=item.renewal_date,
        status=item.status,
        owner_name=item.owner_name,
        reminder_days=item.reminder_days,
        notes=item.notes,
    )

    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return db_item


@router.get(
    "",
    response_model=list[RenewalItemRead],
)
def list_renewal_items(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    result = db.execute(
        select(RenewalItem)
        .where(
            RenewalItem.tenant_id == tenant.id
        )
        .order_by(RenewalItem.id)
    )

    return result.scalars().all()


@router.get(
    "/{item_id}",
    response_model=RenewalItemRead,
)
def get_renewal_item(
    item_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    item = db.scalar(
        select(RenewalItem).where(
            RenewalItem.id == item_id,
            RenewalItem.tenant_id == tenant.id,
        )
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Renewal item not found",
        )

    return item


@router.put(
    "/{item_id}",
    response_model=RenewalItemRead,
)
def update_renewal_item(
    item_id: int,
    update: RenewalItemUpdate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    item = db.scalar(
        select(RenewalItem).where(
            RenewalItem.id == item_id,
            RenewalItem.tenant_id == tenant.id,
        )
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Renewal item not found",
        )

    item.name = update.name
    item.category = update.category
    item.renewal_date = update.renewal_date
    item.status = update.status
    item.owner_name = update.owner_name
    item.reminder_days = update.reminder_days
    item.notes = update.notes

    db.commit()
    db.refresh(item)

    return item


@router.delete(
    "/{item_id}",
    status_code=204,
)
def delete_renewal_item(
    item_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    item = db.scalar(
        select(RenewalItem).where(
            RenewalItem.id == item_id,
            RenewalItem.tenant_id == tenant.id,
        )
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Renewal item not found",
        )

    db.delete(item)
    db.commit()
