from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, Tenant
from app.products.prestamodesk.models import Prospect
from app.products.prestamodesk.schemas import (
    PublicProspectCreate,
    PublicProspectRead,
)


CONSENT_NOTICE_VERSION = "2026-09-29"

router = APIRouter(
    prefix="/public/tenants",
    tags=["PréstamoDesk Public Prospects"],
)


@router.post(
    "/{tenant_slug}/prospects",
    response_model=PublicProspectRead,
    status_code=201,
)
def create_public_prospect(
    tenant_slug: str,
    payload: PublicProspectCreate,
    db: Session = Depends(get_db),
):
    tenant = db.scalar(
        select(Tenant)
        .join(
            Product,
            Product.id == Tenant.product_id,
        )
        .where(
            Tenant.slug == tenant_slug,
            Tenant.status == "active",
            Tenant.client_number.is_not(None),
            Product.slug == "prestamodesk",
            Product.status == "active",
        )
    )

    if tenant is None:
        raise HTTPException(
            status_code=404,
            detail="Solicitud no disponible",
        )

    prospect = Prospect(
        tenant_id=tenant.id,
        full_name=payload.full_name.strip(),
        phone=payload.phone.strip(),
        email=(
            payload.email.strip().lower()
            if payload.email
            else None
        ),
        municipality=(
            payload.municipality.strip()
            if payload.municipality
            else None
        ),
        province=(
            payload.province.strip()
            if payload.province
            else None
        ),
        requested_amount=payload.requested_amount,
        preferred_contact=payload.preferred_contact,
        message=(
            payload.message.strip()
            if payload.message
            else None
        ),
        status="new",
        consented_at=datetime.now(timezone.utc),
        consent_notice_version=CONSENT_NOTICE_VERSION,
    )

    db.add(prospect)
    db.commit()
    db.refresh(prospect)

    return PublicProspectRead(
        prospect_id=prospect.id,
        status="received",
    )
