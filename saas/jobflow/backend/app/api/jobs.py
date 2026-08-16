from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer, Estimate, Invoice, Job, Schedule, Tenant
from app.schemas import JobCreate, JobRead, JobUpdate
from app.tenant_context import get_current_tenant


JOB_STATUS_TRANSITIONS = {
    "customer_requested": {"quoted"},
    "quoted": {"approved"},
    "approved": {"scheduled"},
    "scheduled": {"in_progress"},
    "in_progress": {"completed"},
    "completed": {"invoiced"},
    "invoiced": {"paid"},
    "paid": set(),
}


router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


@router.post("/", response_model=JobRead, status_code=201)
def create_job(
    job: JobCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    customer = db.scalar(
        select(Customer).where(
            Customer.id == job.customer_id,
            Customer.tenant_id == tenant.id,
        )
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    db_job = Job(**job.model_dump())

    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    return db_job


@router.get("/", response_model=list[JobRead])
def list_jobs(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    result = db.execute(
        select(Job)
        .join(Customer, Customer.id == Job.customer_id)
        .where(Customer.tenant_id == tenant.id)
        .order_by(Job.id)
    )

    return result.scalars().all()


@router.get("/{job_id}", response_model=JobRead)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    job = db.scalar(
        select(Job)
        .join(Customer, Customer.id == Job.customer_id)
        .where(
            Job.id == job_id,
            Customer.tenant_id == tenant.id,
        )
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return job


@router.put("/{job_id}", response_model=JobRead)
def update_job(
    job_id: int,
    job: JobUpdate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    db_job = db.scalar(
        select(Job)
        .join(Customer, Customer.id == Job.customer_id)
        .where(
            Job.id == job_id,
            Customer.tenant_id == tenant.id,
        )
    )

    if db_job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    if job.customer_id != db_job.customer_id:
        raise HTTPException(
            status_code=409,
            detail="Job cannot be moved to a different customer",
        )

    if job.status != db_job.status:
        allowed_statuses = JOB_STATUS_TRANSITIONS.get(
            db_job.status,
            set(),
        )

        if job.status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid job status transition: "
                    f"{db_job.status} -> {job.status}"
                ),
            )

    for field, value in job.model_dump().items():
        setattr(db_job, field, value)

    db.commit()
    db.refresh(db_job)

    return db_job


@router.delete("/{job_id}", status_code=204)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    db_job = db.scalar(
        select(Job)
        .join(Customer, Customer.id == Job.customer_id)
        .where(
            Job.id == job_id,
            Customer.tenant_id == tenant.id,
        )
    )

    if db_job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    related_records = (
        db.execute(
            select(Estimate.id).where(
                Estimate.job_id == job_id
            ).limit(1)
        ).first()
        or db.execute(
            select(Schedule.id).where(
                Schedule.job_id == job_id
            ).limit(1)
        ).first()
        or db.execute(
            select(Invoice.id).where(
                Invoice.job_id == job_id
            ).limit(1)
        ).first()
    )

    if related_records is not None:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete job with existing related records",
        )

    db.delete(db_job)
    db.commit()
