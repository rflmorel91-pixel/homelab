from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BillingAccount(Base):
    __tablename__ = "platform_billing_accounts"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            name=(
                "uq_platform_billing_accounts_"
                "tenant_id"
            ),
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
    )

    billing_offer_id: Mapped[int | None] = (
        mapped_column(
            ForeignKey(
                "platform_billing_offers.id"
            ),
            nullable=True,
            index=True,
        )
    )

    billing_mode: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="manual",
    )

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="manual",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )

    provider_customer_id: Mapped[str | None] = (
        mapped_column(
            String(255),
            nullable=True,
        )
    )

    provider_subscription_id: Mapped[str | None] = (
        mapped_column(
            String(255),
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
