from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer, Job, Tenant
from app.schemas.public_request import (
    PublicRequestCreate,
    PublicRequestRead,
)


router = APIRouter(
    prefix="/public/tenants",
    tags=["Public Requests"],
)


@router.post(
    "/{tenant_slug}/requests",
    response_model=PublicRequestRead,
    status_code=201,
)
def create_public_request(
    tenant_slug: str,
    request: PublicRequestCreate,
    db: Session = Depends(get_db),
):
    tenant = db.scalar(
        select(Tenant).where(
            Tenant.slug == tenant_slug
        )
    )

    if tenant is None:
        raise HTTPException(
            status_code=404,
            detail="Request page not found",
        )

    customer = Customer(
        tenant_id=tenant.id,
        name=request.name,
        phone=request.phone,
        email=request.email,
        address=request.address,
    )

    db.add(customer)
    db.flush()

    job = Job(
        customer_id=customer.id,
        title=request.project_title,
        description=request.project_description,
        status="customer_requested",
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return PublicRequestRead(
        request_id=job.id,
        status="received",
    )
