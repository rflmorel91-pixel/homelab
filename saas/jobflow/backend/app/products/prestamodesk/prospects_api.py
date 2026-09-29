from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant
from app.products.prestamodesk.models import (
    Borrower,
    Prospect,
)
from app.products.prestamodesk.schemas import (
    ProspectConversionRead,
    ProspectRead,
    ProspectUpdate,
)
from app.tenant_context import get_current_tenant


router = APIRouter(
    prefix="/prospects",
    tags=["PréstamoDesk Prospects"],
)


def get_tenant_prospect(
    db: Session,
    tenant_id: int,
    prospect_id: int,
    *,
    lock: bool = False,
) -> Prospect:
    statement = select(Prospect).where(
        Prospect.id == prospect_id,
        Prospect.tenant_id == tenant_id,
    )

    if lock:
        statement = statement.with_for_update()

    prospect = db.scalar(statement)

    if prospect is None:
        raise HTTPException(
            status_code=404,
            detail="Prospect not found",
        )

    return prospect


@router.get(
    "",
    response_model=list[ProspectRead],
)
def list_prospects(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    return db.scalars(
        select(Prospect)
        .where(
            Prospect.tenant_id == tenant.id,
        )
        .order_by(
            Prospect.created_at.desc(),
            Prospect.id.desc(),
        )
    ).all()


@router.get(
    "/{prospect_id}",
    response_model=ProspectRead,
)
def get_prospect(
    prospect_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    return get_tenant_prospect(
        db,
        tenant.id,
        prospect_id,
    )


@router.put(
    "/{prospect_id}",
    response_model=ProspectRead,
)
def update_prospect(
    prospect_id: int,
    payload: ProspectUpdate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    prospect = get_tenant_prospect(
        db,
        tenant.id,
        prospect_id,
        lock=True,
    )

    if prospect.status == "converted":
        raise HTTPException(
            status_code=409,
            detail="Converted prospect cannot be changed",
        )

    prospect.status = payload.status
    db.commit()
    db.refresh(prospect)

    return prospect


@router.post(
    "/{prospect_id}/convert",
    response_model=ProspectConversionRead,
    status_code=201,
)
def convert_prospect(
    prospect_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    prospect = get_tenant_prospect(
        db,
        tenant.id,
        prospect_id,
        lock=True,
    )

    if (
        prospect.status == "converted"
        or prospect.converted_borrower_id is not None
    ):
        raise HTTPException(
            status_code=409,
            detail="Prospect has already been converted",
        )

    if prospect.status != "qualified":
        raise HTTPException(
            status_code=409,
            detail=(
                "Prospect must be qualified "
                "before conversion"
            ),
        )

    borrower = Borrower(
        tenant_id=tenant.id,
        full_name=prospect.full_name,
        document_type="cedula",
        phone=prospect.phone,
        email=prospect.email,
        municipality=prospect.municipality,
        province=prospect.province,
        status="active",
        notes=(
            "Creado desde prospecto "
            f"#{prospect.id}."
        ),
    )

    db.add(borrower)
    db.flush()

    prospect.converted_borrower_id = borrower.id
    prospect.status = "converted"

    db.commit()
    db.refresh(prospect)

    return ProspectConversionRead(
        prospect_id=prospect.id,
        borrower_id=borrower.id,
        status="converted",
    )
