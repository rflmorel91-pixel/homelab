from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer, Job, Schedule, Tenant
from app.products.jobflow.schemas import ScheduleCreate, ScheduleRead, ScheduleUpdate
from app.tenant_context import get_current_tenant


router = APIRouter(
    prefix="/schedules",
    tags=["Schedules"],
)


@router.post("/", response_model=ScheduleRead, status_code=201)
def create_schedule(
    schedule: ScheduleCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    job = db.scalar(
        select(Job)
        .join(Customer, Customer.id == Job.customer_id)
        .where(
            Job.id == schedule.job_id,
            Customer.tenant_id == tenant.id,
        )
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    db_schedule = Schedule(**schedule.model_dump())

    db.add(db_schedule)

    if job.status == "approved":
        job.status = "scheduled"

    db.commit()
    db.refresh(db_schedule)

    return db_schedule


@router.get("/", response_model=list[ScheduleRead])
def list_schedules(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    result = db.execute(
        select(Schedule)
        .join(Job, Job.id == Schedule.job_id)
        .join(Customer, Customer.id == Job.customer_id)
        .where(Customer.tenant_id == tenant.id)
        .order_by(Schedule.id)
    )

    return result.scalars().all()


@router.get("/{schedule_id}", response_model=ScheduleRead)
def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    schedule = db.scalar(
        select(Schedule)
        .join(Job, Job.id == Schedule.job_id)
        .join(Customer, Customer.id == Job.customer_id)
        .where(
            Schedule.id == schedule_id,
            Customer.tenant_id == tenant.id,
        )
    )

    if schedule is None:
        raise HTTPException(
            status_code=404,
            detail="Schedule not found",
        )

    return schedule


@router.put("/{schedule_id}", response_model=ScheduleRead)
def update_schedule(
    schedule_id: int,
    schedule: ScheduleUpdate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    db_schedule = db.scalar(
        select(Schedule)
        .join(Job, Job.id == Schedule.job_id)
        .join(Customer, Customer.id == Job.customer_id)
        .where(
            Schedule.id == schedule_id,
            Customer.tenant_id == tenant.id,
        )
    )

    if db_schedule is None:
        raise HTTPException(
            status_code=404,
            detail="Schedule not found",
        )

    if schedule.job_id != db_schedule.job_id:
        raise HTTPException(
            status_code=409,
            detail="Schedule cannot be moved to a different job",
        )

    for field, value in schedule.model_dump().items():
        setattr(db_schedule, field, value)

    db.commit()
    db.refresh(db_schedule)

    return db_schedule


@router.delete("/{schedule_id}", status_code=204)
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    db_schedule = db.scalar(
        select(Schedule)
        .join(Job, Job.id == Schedule.job_id)
        .join(Customer, Customer.id == Job.customer_id)
        .where(
            Schedule.id == schedule_id,
            Customer.tenant_id == tenant.id,
        )
    )

    if db_schedule is None:
        raise HTTPException(
            status_code=404,
            detail="Schedule not found",
        )

    job = db.scalar(
        select(Job)
        .join(Customer, Customer.id == Job.customer_id)
        .where(
            Job.id == db_schedule.job_id,
            Customer.tenant_id == tenant.id,
        )
    )

    db.delete(db_schedule)
    db.flush()

    remaining_schedule = db.execute(
        select(Schedule.id)
        .where(Schedule.job_id == db_schedule.job_id)
        .limit(1)
    ).scalar_one_or_none()

    if (
        remaining_schedule is None
        and job is not None
        and job.status == "scheduled"
    ):
        job.status = "approved"

    db.commit()
