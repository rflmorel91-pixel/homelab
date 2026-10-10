from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant, TenantMembership
from app.products.prestamodesk.authorization import (
    require_prestamodesk_operations_member,
    require_prestamodesk_manager as require_current_tenant_owner,
)
from app.products.prestamodesk.models import Borrower
from app.products.prestamodesk.schemas import (
    BorrowerContactUpdate,
    BorrowerCreate,
    BorrowerRead,
    BorrowerUpdate,
)
from app.tenant_context import (
    get_current_tenant,
)


router = APIRouter(
    prefix="/borrowers",
    tags=["PréstamoDesk Borrowers"],
    dependencies=[
        Depends(
            require_prestamodesk_operations_member
        ),
        Depends(require_current_tenant_owner),
    ],
)


def get_borrower_or_404(
    borrower_id: int,
    tenant: Tenant,
    db: Session,
) -> Borrower:
    borrower = db.scalar(
        select(Borrower).where(
            Borrower.id == borrower_id,
            Borrower.tenant_id == tenant.id,
        )
    )

    if borrower is None:
        raise HTTPException(
            status_code=404,
            detail="Borrower not found",
        )

    return borrower


@router.post("", response_model=BorrowerRead, status_code=201)
def create_borrower(
    payload: BorrowerCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    borrower = Borrower(
        tenant_id=tenant.id,
        **payload.model_dump(),
    )

    db.add(borrower)
    db.commit()
    db.refresh(borrower)

    return borrower


@router.get("", response_model=list[BorrowerRead])
def list_borrowers(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    result = db.execute(
        select(Borrower)
        .where(Borrower.tenant_id == tenant.id)
        .order_by(Borrower.full_name, Borrower.id)
    )

    return result.scalars().all()


@router.get("/{borrower_id}", response_model=BorrowerRead)
def get_borrower(
    borrower_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    return get_borrower_or_404(borrower_id, tenant, db)


@router.put("/{borrower_id}", response_model=BorrowerRead)
def update_borrower(
    borrower_id: int,
    payload: BorrowerUpdate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    borrower = get_borrower_or_404(borrower_id, tenant, db)

    for field, value in payload.model_dump().items():
        setattr(borrower, field, value)

    borrower.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    db.refresh(borrower)

    return borrower


@router.delete("/{borrower_id}", status_code=204)
def delete_borrower(
    borrower_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    _: TenantMembership = Depends(
        require_current_tenant_owner
    ),
):
    borrower = get_borrower_or_404(borrower_id, tenant, db)

    db.delete(borrower)
    db.commit()


@router.patch("/{borrower_id}/contact", response_model=BorrowerRead)
def update_borrower_contact(
    borrower_id: int,
    payload: BorrowerContactUpdate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    get_borrower_or_404(borrower_id, tenant, db)
    expected = payload.expected_updated_at
    # Existing borrower timestamps are stored without a timezone, in UTC.
    if expected.tzinfo is not None:
        expected = expected.astimezone(timezone.utc).replace(tzinfo=None)
    values = payload.model_dump(exclude={"expected_updated_at"})
    values["updated_at"] = datetime.now(timezone.utc).replace(tzinfo=None)
    result = db.execute(
        update(Borrower)
        .where(Borrower.id == borrower_id, Borrower.tenant_id == tenant.id,
               Borrower.updated_at == expected)
        .values(**values)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(status_code=409, detail="Borrower contact changed; refresh before saving")
    db.commit()
    db.expire_all()
    return get_borrower_or_404(borrower_id, tenant, db)
