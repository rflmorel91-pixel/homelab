from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant, TenantMembership
from app.products.prestamodesk.models import Borrower
from app.products.prestamodesk.schemas import (
    BorrowerCreate,
    BorrowerRead,
    BorrowerUpdate,
)
from app.tenant_context import (
    get_current_tenant,
    require_current_tenant_owner,
)


router = APIRouter(
    prefix="/borrowers",
    tags=["PréstamoDesk Borrowers"],
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
