from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CollectionActivity(Base):
    __tablename__ = "prestamodesk_collection_activities"
    __table_args__ = (
        CheckConstraint(
            "channel IN ("
            "'phone', 'whatsapp', 'sms', "
            "'email', 'visit', 'other'"
            ")",
            name=(
                "ck_prestamodesk_collection_activity_channel"
            ),
        ),
    )

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

    recorded_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    channel: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    outcome: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    contacted_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    next_follow_up_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class PaymentPromise(Base):
    __tablename__ = "prestamodesk_payment_promises"
    __table_args__ = (
        CheckConstraint(
            "status IN ("
            "'pending', 'partial', "
            "'fulfilled', 'cancelled'"
            ")",
            name="ck_prestamodesk_payment_promise_status",
        ),
        CheckConstraint(
            "promised_amount > 0",
            name=(
                "ck_prestamodesk_payment_promise_amount"
            ),
        ),
        CheckConstraint(
            "fulfilled_amount >= 0 "
            "AND fulfilled_amount <= promised_amount",
            name=(
                "ck_prestamodesk_payment_promise_fulfilled"
            ),
        ),
    )

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

    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    promised_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    fulfilled_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    due_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    fulfilled_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime,
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


class PromisePaymentAllocation(Base):
    __tablename__ = (
        "prestamodesk_promise_payment_allocations"
    )
    __table_args__ = (
        UniqueConstraint(
            "promise_id",
            "payment_id",
            name=(
                "uq_prestamodesk_promise_payment_allocation"
            ),
        ),
        CheckConstraint(
            "amount > 0",
            name=(
                "ck_prestamodesk_promise_payment_allocation_amount"
            ),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    promise_id: Mapped[int] = mapped_column(
        ForeignKey(
            "prestamodesk_payment_promises.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    payment_id: Mapped[int] = mapped_column(
        ForeignKey(
            "prestamodesk_payments.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
