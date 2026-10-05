from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant
from app.products.prestamodesk.authorization import (
    require_prestamodesk_operations_member,
    require_prestamodesk_manager as require_current_tenant_owner,
)
from app.products.prestamodesk.models import (
    Borrower,
    Prospect,
    LoanApplication,
)
from app.products.prestamodesk.schemas import (
    ProspectConversionRead,
    ProspectRead,
    PublicProspectPageRead,
    ProspectUpdate,
)
from app.products.prestamodesk.application_schemas import InternalApplicationTerms, ApplicationRead
from app.products.prestamodesk.applications_api import quote_terms
from sqlalchemy.exc import IntegrityError
from app.tenant_context import (
    get_current_tenant,
)


router = APIRouter(
    prefix="/prospects",
    tags=["PréstamoDesk Prospects"],
    dependencies=[
        Depends(
            require_prestamodesk_operations_member
        ),
        Depends(require_current_tenant_owner),
    ],
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


def linked_application(db: Session, tenant_id: int, prospect_id: int):
    return db.scalar(select(LoanApplication).where(
        LoanApplication.source_prospect_id == prospect_id,
        LoanApplication.tenant_id == tenant_id,
    ))


@router.post("/{prospect_id}/application", response_model=ApplicationRead, status_code=201)
def create_prospect_application(
    prospect_id: int, payload: InternalApplicationTerms,
    db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant),
):
    prospect = get_tenant_prospect(db, tenant.id, prospect_id, lock=True)
    if prospect.status != "qualified" or prospect.converted_borrower_id is not None:
        raise HTTPException(status_code=409, detail="Prospect must be qualified and unconverted")
    if linked_application(db, tenant.id, prospect.id) is not None:
        raise HTTPException(status_code=409, detail="Prospect already has a loan application")
    quote = quote_terms(payload)
    application = LoanApplication(
        **payload.model_dump(), tenant_id=tenant.id, source_prospect_id=prospect.id,
        full_name=prospect.full_name, document_type="cedula", phone=prospect.phone,
        email=prospect.email, municipality=prospect.municipality, province=prospect.province,
        total_interest=quote.total_interest, total_due=quote.total_due,
        currency="DOP", status="new", consented_at=prospect.consented_at,
        consent_notice_version=prospect.consent_notice_version,
    )
    try:
        db.add(application)
        db.commit()
        db.refresh(application)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Prospect already has a loan application")
    return application


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
    "/public-page",
    response_model=PublicProspectPageRead,
)
def get_prospect_public_page(
    tenant: Tenant = Depends(get_current_tenant),
):
    if tenant.client_number is None:
        raise HTTPException(
            status_code=404,
            detail="Public prospect page not available",
        )

    return PublicProspectPageRead(
        tenant_slug=tenant.slug,
        business_name=tenant.name,
        client_number=tenant.client_number,
    )


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

    if linked_application(db, tenant.id, prospect.id) is not None:
        raise HTTPException(status_code=409, detail="Manage this prospect through its loan application")

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

    if linked_application(db, tenant.id, prospect.id) is not None:
        raise HTTPException(status_code=409, detail="Convert the approved loan application instead")

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
