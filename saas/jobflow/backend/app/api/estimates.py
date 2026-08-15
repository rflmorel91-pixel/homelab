from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Estimate, Job
from app.schemas import EstimateCreate, EstimateRead, EstimateUpdate


router = APIRouter(
    prefix="/estimates",
    tags=["Estimates"],
)


@router.post("/", response_model=EstimateRead, status_code=201)
def create_estimate(
    estimate: EstimateCreate,
    db: Session = Depends(get_db),
):
    job = db.get(Job, estimate.job_id)

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
):
    result = db.execute(
        select(Estimate).order_by(Estimate.id)
    )

    return result.scalars().all()


@router.get("/{estimate_id}", response_model=EstimateRead)
def get_estimate(
    estimate_id: int,
    db: Session = Depends(get_db),
):
    estimate = db.get(Estimate, estimate_id)

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
):
    db_estimate = db.get(Estimate, estimate_id)

    if db_estimate is None:
        raise HTTPException(
            status_code=404,
            detail="Estimate not found",
        )

    if estimate.job_id != db_estimate.job_id:
        job = db.get(Job, estimate.job_id)

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Job not found",
            )

    for field, value in estimate.model_dump().items():
        setattr(db_estimate, field, value)

    db.commit()
    db.refresh(db_estimate)

    return db_estimate


@router.delete("/{estimate_id}", status_code=204)
def delete_estimate(
    estimate_id: int,
    db: Session = Depends(get_db),
):
    db_estimate = db.get(Estimate, estimate_id)

    if db_estimate is None:
        raise HTTPException(
            status_code=404,
            detail="Estimate not found",
        )

    db.delete(db_estimate)
    db.commit()
