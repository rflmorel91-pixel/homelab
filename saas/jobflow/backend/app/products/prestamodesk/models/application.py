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
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LoanApplication(Base):
    __tablename__ = "prestamodesk_applications"

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    converted_borrower_id: Mapped[int | None] = mapped_column(
        ForeignKey("prestamodesk_borrowers.id"),
        nullable=True,
        unique=True,
    )

    converted_loan_id: Mapped[int | None] = mapped_column(
        ForeignKey("prestamodesk_loans.id"),
        nullable=True,
        unique=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    document_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="cedula",
    )

    document_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True,
    )

    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    municipality: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    province: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    loan_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="vehicle",
    )

    vehicle_cash_price: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    vehicle_down_payment: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    vehicle_make: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    vehicle_model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    vehicle_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
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
        default="monthly",
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
        default="new",
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    consented_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    consent_notice_version: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    converted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
