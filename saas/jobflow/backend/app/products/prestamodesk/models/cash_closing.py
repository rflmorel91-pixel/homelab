from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CashClosing(Base):
    __tablename__ = "prestamodesk_cash_closings"

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    cashier_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    opened_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    closed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    payment_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    total_collected: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    cash_expected: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    cash_counted: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    cash_difference: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    bank_transfer_total: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    card_total: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    other_total: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
