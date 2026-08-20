from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer, Estimate, Job, Tenant
from app.products.jobflow.schemas import EstimateCreate, EstimateRead, EstimateUpdate
from app.tenant_context import get_current_tenant


ESTIMATE_STATUS_TRANSITIONS = {
    "draft": {"sent"},
    "sent": {"approved", "declined"},
    "approved": set(),
    "declined": set(),
}


router = APIRouter(
    prefix="/estimates",
    tags=["Estimates"],
)


@router.post("/", response_model=EstimateRead, status_code=201)
def create_estimate(
    estimate: EstimateCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    job = db.scalar(
        select(Job)
        .join(Customer, Customer.id == Job.customer_id)
        .where(
            Job.id == estimate.job_id,
            Customer.tenant_id == tenant.id,
        )
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    db_estimate = Estimate(**estimate.model_dump())

    db.add(db_estimate)
    db.commit()
    db.refresh(db_estimate)

    return db_estimate


@router.get("/", response_model=list[EstimateRead])
def list_estimates(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    result = db.execute(
        select(Estimate)
        .join(Job, Job.id == Estimate.job_id)
        .join(Customer, Customer.id == Job.customer_id)
        .where(Customer.tenant_id == tenant.id)
        .order_by(Estimate.id)
    )

    return result.scalars().all()


@router.get("/{estimate_id}", response_model=EstimateRead)
def get_estimate(
    estimate_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    estimate = db.scalar(
        select(Estimate)
        .join(Job, Job.id == Estimate.job_id)
        .join(Customer, Customer.id == Job.customer_id)
        .where(
            Estimate.id == estimate_id,
            Customer.tenant_id == tenant.id,
        )
    )

    if estimate is None:
        raise HTTPException(
            status_code=404,
            detail="Estimate not found",
        )

    return estimate


@router.put("/{estimate_id}", response_model=EstimateRead)
def update_estimate(
    estimate_id: int,
    estimate: EstimateUpdate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    db_estimate = db.scalar(
        select(Estimate)
        .join(Job, Job.id == Estimate.job_id)
        .join(Customer, Customer.id == Job.customer_id)
        .where(
            Estimate.id == estimate_id,
            Customer.tenant_id == tenant.id,
        )
    )

    if db_estimate is None:
        raise HTTPException(
            status_code=404,
            detail="Estimate not found",
        )

    if estimate.job_id != db_estimate.job_id:
        raise HTTPException(
            status_code=409,
            detail="Estimate cannot be moved to a different job",
        )

    previous_status = db_estimate.status

    if estimate.status != previous_status:
        allowed_statuses = ESTIMATE_STATUS_TRANSITIONS.get(
            previous_status,
            set(),
        )

        if estimate.status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid estimate status transition: "
                    f"{previous_status} -> {estimate.status}"
                ),
            )

    for field, value in estimate.model_dump().items():
        setattr(db_estimate, field, value)

    if (
        previous_status == "sent"
        and estimate.status == "approved"
    ):
        job = db.scalar(
            select(Job)
            .join(Customer, Customer.id == Job.customer_id)
            .where(
                Job.id == db_estimate.job_id,
                Customer.tenant_id == tenant.id,
            )
        )

        if job is not None and job.status == "quoted":
            job.status = "approved"

    db.commit()
    db.refresh(db_estimate)

    return db_estimate


@router.delete("/{estimate_id}", status_code=204)
def delete_estimate(
    estimate_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    db_estimate = db.scalar(
        select(Estimate)
        .join(Job, Job.id == Estimate.job_id)
        .join(Customer, Customer.id == Job.customer_id)
        .where(
            Estimate.id == estimate_id,
            Customer.tenant_id == tenant.id,
        )
    )

    if db_estimate is None:
        raise HTTPException(
            status_code=404,
            detail="Estimate not found",
        )

    if db_estimate.status in {"approved", "declined"}:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete terminal estimate",
        )

    db.delete(db_estimate)
    db.commit()
