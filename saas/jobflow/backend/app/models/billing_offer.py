from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BillingOffer(Base):
    __tablename__ = "platform_billing_offers"

    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "code",
            name=(
                "uq_platform_billing_offers_"
                "product_code"
            ),
        ),
        CheckConstraint(
            (
                "minimum_amount_cents IS NULL "
                "OR minimum_amount_cents >= 0"
            ),
            name=(
                "ck_platform_billing_offers_"
                "minimum_amount"
            ),
        ),
        CheckConstraint(
            (
                "maximum_amount_cents IS NULL "
                "OR maximum_amount_cents >= 0"
            ),
            name=(
                "ck_platform_billing_offers_"
                "maximum_amount"
            ),
        ),
        CheckConstraint(
            (
                "minimum_amount_cents IS NULL "
                "OR maximum_amount_cents IS NULL "
                "OR minimum_amount_cents "
                "<= maximum_amount_cents"
            ),
            name=(
                "ck_platform_billing_offers_"
                "amount_range"
            ),
        ),
        CheckConstraint(
            (
                "service_period_days IS NULL "
                "OR service_period_days > 0"
            ),
            name=(
                "ck_platform_billing_offers_"
                "service_period"
            ),
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        index=True,
    )

    charge_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )

    minimum_amount_cents: Mapped[int | None] = (
        mapped_column(
            Integer,
            nullable=True,
        )
    )

    maximum_amount_cents: Mapped[int | None] = (
        mapped_column(
            Integer,
            nullable=True,
        )
    )

    billing_interval: Mapped[str | None] = (
        mapped_column(
            String(50),
            nullable=True,
        )
    )

    service_period_days: Mapped[int | None] = (
        mapped_column(
            Integer,
            nullable=True,
        )
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
