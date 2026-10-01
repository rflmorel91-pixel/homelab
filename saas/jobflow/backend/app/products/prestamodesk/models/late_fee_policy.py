from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LateFeePolicy(Base):
    __tablename__ = "prestamodesk_late_fee_policies"

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"),
        unique=True,
        nullable=False,
        index=True,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    daily_rate_percent: Mapped[Decimal] = mapped_column(
        Numeric(7, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )

    grace_days: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False,
    )

    cap_percent: Mapped[Decimal] = mapped_column(
        Numeric(7, 4),
        default=Decimal("25.0000"),
        nullable=False,
    )

    effective_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
