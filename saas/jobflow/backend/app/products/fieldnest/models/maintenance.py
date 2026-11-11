from datetime import date, datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class FieldNestMaintenancePlan(Base):
    __tablename__ = "fieldnest_maintenance_plans"
    __table_args__ = (CheckConstraint("interval_months IN (1, 3, 6, 12)", name="ck_fieldnest_plan_interval"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("fieldnest_properties.id"))
    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("fieldnest_vendors.id"))
    title: Mapped[str] = mapped_column(String(180))
    interval_months: Mapped[int]
    anchor_day: Mapped[int]
    next_due: Mapped[date] = mapped_column(Date)
    paused: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class FieldNestMaintenanceOccurrence(Base):
    __tablename__ = "fieldnest_maintenance_occurrences"
    __table_args__ = (UniqueConstraint("plan_id", "scheduled_date", name="uq_fieldnest_plan_date"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("fieldnest_maintenance_plans.id"))
    work_order_id: Mapped[int] = mapped_column(ForeignKey("fieldnest_work_orders.id"), unique=True)
    scheduled_date: Mapped[date] = mapped_column(Date)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
