from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Job, Schedule
from app.schemas import ScheduleCreate, ScheduleRead, ScheduleUpdate


router = APIRouter(
    prefix="/schedules",
    tags=["Schedules"],
)


@router.post("/", response_model=ScheduleRead, status_code=201)
def create_schedule(
    schedule: ScheduleCreate,
    db: Session = Depends(get_db),
):
    job = db.get(Job, schedule.job_id)

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
):
    result = db.execute(
        select(Schedule).order_by(Schedule.id)
    )

    return result.scalars().all()


@router.get("/{schedule_id}", response_model=ScheduleRead)
def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
):
    schedule = db.get(Schedule, schedule_id)

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
):
    db_schedule = db.get(Schedule, schedule_id)

    if db_schedule is None:
        raise HTTPException(
            status_code=404,
            detail="Schedule not found",
        )

    if schedule.job_id != db_schedule.job_id:
        job = db.get(Job, schedule.job_id)

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Job not found",
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
):
    db_schedule = db.get(Schedule, schedule_id)

    if db_schedule is None:
        raise HTTPException(
            status_code=404,
            detail="Schedule not found",
        )

    db.delete(db_schedule)
    db.commit()
