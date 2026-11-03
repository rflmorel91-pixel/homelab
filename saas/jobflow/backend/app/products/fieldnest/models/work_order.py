from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FieldNestWorkOrder(Base):
    __tablename__ = "fieldnest_work_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("fieldnest_properties.id"), nullable=False, index=True)
    resident_id: Mapped[int | None] = mapped_column(ForeignKey("fieldnest_residents.id"), nullable=True, index=True)
    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("fieldnest_vendors.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    unit: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="open")
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
