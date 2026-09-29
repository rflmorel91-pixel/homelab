from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Loan(Base):
    __tablename__ = "prestamodesk_loans"

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    borrower_id: Mapped[int] = mapped_column(
        ForeignKey("prestamodesk_borrowers.id"),
        nullable=False,
        index=True,
    )

    loan_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="personal",
    )

    vehicle_cash_price: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    vehicle_down_payment: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    vehicle_make: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    vehicle_model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    vehicle_year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    vehicle_color: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    vehicle_vin: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    vehicle_license_plate: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    vehicle_seller: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    vehicle_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    principal_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    flat_interest_rate_percent: Mapped[Decimal] = mapped_column(
        Numeric(7, 4),
        nullable=False,
    )

    total_interest: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    total_due: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    installment_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    payment_frequency: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    first_payment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="DOP",
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="active",
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

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class Installment(Base):
    __table_args__ = (
        UniqueConstraint(
            "loan_id",
            "sequence_number",
            name="uq_prestamodesk_installment_sequence",
        ),
    )

    __tablename__ = "prestamodesk_installments"

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    loan_id: Mapped[int] = mapped_column(
        ForeignKey(
            "prestamodesk_loans.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    due_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    principal_due: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    interest_due: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    total_due: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
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
