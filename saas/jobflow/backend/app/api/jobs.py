from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer, Job
from app.schemas import JobCreate, JobRead, JobUpdate


router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


@router.post("/", response_model=JobRead, status_code=201)
def create_job(
    job: JobCreate,
    db: Session = Depends(get_db),
):
    customer = db.get(Customer, job.customer_id)

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
):
    result = db.execute(
        select(Job).order_by(Job.id)
    )

    return result.scalars().all()


@router.get("/{job_id}", response_model=JobRead)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = db.get(Job, job_id)

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
):
    db_job = db.get(Job, job_id)

    if db_job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    customer = db.get(Customer, job.customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
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
):
    db_job = db.get(Job, job_id)

    if db_job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    db.delete(db_job)
    db.commit()
