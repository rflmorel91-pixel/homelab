"""Explicit, tenant-scoped recurring maintenance; no background scheduler."""
from calendar import monthrange
from datetime import date, datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth_context import get_current_user_id
from app.database import get_db
from app.models import Tenant
from app.tenant_context import get_current_tenant
from app.products.fieldnest.models import FieldNestProperty, FieldNestVendor, FieldNestWorkOrder
from app.products.fieldnest.models.maintenance import FieldNestMaintenancePlan as Plan, FieldNestMaintenanceOccurrence as Occurrence
from app.products.fieldnest.schemas import WorkOrderRead

router = APIRouter(tags=["FieldNest Maintenance"])


class PlanCreate(BaseModel):
    property_id: int = Field(gt=0)
    vendor_id: int | None = Field(default=None, gt=0)
    title: str = Field(min_length=1, max_length=180)
    interval_months: Literal[1, 3, 6, 12] = 1
    next_due: date
    model_config = ConfigDict(extra="forbid")

    @field_validator("title")
    @classmethod
    def strip_title(cls, value):
        if not value.strip():
            raise ValueError("Task title is required")
        return value.strip()


class PlanRead(PlanCreate):
    id: int
    paused: bool
    model_config = ConfigDict(from_attributes=True)


class PauseUpdate(BaseModel):
    paused: bool
    model_config = ConfigDict(extra="forbid")


class GenerateRequest(BaseModel):
    scheduled_date: date
    model_config = ConfigDict(extra="forbid")


class OccurrenceRead(BaseModel):
    id: int
    plan_id: int
    work_order_id: int
    scheduled_date: date
    completed_at: datetime | None
    model_config = ConfigDict(from_attributes=True)


def next_due_date(current: date, interval: int, anchor: int) -> date:
    month = current.year * 12 + current.month - 1 + interval
    year, index = divmod(month, 12)
    if year > 9999:
        raise HTTPException(422, "Next due date is outside the supported range")
    return date(year, index + 1, min(anchor, monthrange(year, index + 1)[1]))


def get_plan(db, tenant_id, plan_id):
    row = db.scalar(select(Plan).where(Plan.id == plan_id, Plan.tenant_id == tenant_id).with_for_update())
    if row is None:
        raise HTTPException(404, "Maintenance plan not found")
    return row


@router.get("/maintenance-plans", response_model=list[PlanRead])
def list_plans(db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant)):
    return db.scalars(select(Plan).where(Plan.tenant_id == tenant.id).order_by(Plan.next_due, Plan.id)).all()


@router.post("/maintenance-plans", response_model=PlanRead, status_code=201)
def create_plan(payload: PlanCreate, db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant)):
    if db.scalar(select(FieldNestProperty.id).where(FieldNestProperty.id == payload.property_id, FieldNestProperty.tenant_id == tenant.id)) is None:
        raise HTTPException(404, "Property not found")
    if payload.vendor_id is not None and db.scalar(select(FieldNestVendor.id).where(FieldNestVendor.id == payload.vendor_id, FieldNestVendor.tenant_id == tenant.id)) is None:
        raise HTTPException(404, "Vendor not found")
    next_due_date(payload.next_due, payload.interval_months, payload.next_due.day)
    row = Plan(tenant_id=tenant.id, anchor_day=payload.next_due.day, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/maintenance-plans/{plan_id}", response_model=PlanRead)
def pause_plan(plan_id: int, payload: PauseUpdate, db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant)):
    row = get_plan(db, tenant.id, plan_id)
    row.paused = payload.paused
    db.commit()
    db.refresh(row)
    return row


@router.get("/maintenance-occurrences", response_model=list[OccurrenceRead])
def list_occurrences(db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant)):
    return db.scalars(select(Occurrence).where(Occurrence.tenant_id == tenant.id).order_by(Occurrence.id.desc())).all()


@router.post("/maintenance-plans/{plan_id}/generate", response_model=WorkOrderRead)
def generate_order(plan_id: int, payload: GenerateRequest, db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant), user_id: int = Depends(get_current_user_id)):
    plan = get_plan(db, tenant.id, plan_id)
    # Lock the plan before checking uniqueness, so retries/workers reuse one order.
    existing = db.scalar(select(Occurrence).where(Occurrence.plan_id == plan.id, Occurrence.scheduled_date == payload.scheduled_date, Occurrence.tenant_id == tenant.id))
    if existing:
        return db.get(FieldNestWorkOrder, existing.work_order_id)
    if plan.paused:
        raise HTTPException(409, "Maintenance plan is paused")
    if payload.scheduled_date != plan.next_due:
        raise HTTPException(409, "Schedule changed; refresh the plan")
    if plan.next_due > datetime.now(timezone.utc).date():
        raise HTTPException(409, "Maintenance occurrence is not due yet")
    row = FieldNestWorkOrder(tenant_id=tenant.id, property_id=plan.property_id, vendor_id=plan.vendor_id, title=plan.title, target_date=plan.next_due, created_by_user_id=user_id)
    db.add(row)
    db.flush()
    db.add(Occurrence(tenant_id=tenant.id, plan_id=plan.id, work_order_id=row.id, scheduled_date=plan.next_due))
    db.commit()
    db.refresh(row)
    return row


def record_completion(db, tenant_id, order_id, status):
    occurrence = db.scalar(select(Occurrence).where(Occurrence.work_order_id == order_id, Occurrence.tenant_id == tenant_id))
    if occurrence is None:
        return
    plan = get_plan(db, tenant_id, occurrence.plan_id)
    db.refresh(occurrence)
    if status == "cancelled":
        raise HTTPException(409, "Pause the maintenance plan or complete its occurrence; recurring orders cannot be cancelled")
    if occurrence.completed_at is not None:
        if status != "completed":
            raise HTTPException(409, "Completed maintenance occurrences cannot be reopened")
        return
    if status == "completed":
        plan.next_due = next_due_date(occurrence.scheduled_date, plan.interval_months, plan.anchor_day)
        occurrence.completed_at = datetime.now(timezone.utc)


def protect_occurrence(db, tenant_id, order_id):
    if db.scalar(select(Occurrence.id).where(Occurrence.work_order_id == order_id, Occurrence.tenant_id == tenant_id)) is not None:
        raise HTTPException(409, "Recurring maintenance work orders retain their history and cannot be deleted")
