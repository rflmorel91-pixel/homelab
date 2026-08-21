from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RenewalReminderDelivery(Base):
    __tablename__ = (
        "renewaldesk_reminder_deliveries"
    )

    __table_args__ = (
        UniqueConstraint(
            "renewal_item_id",
            "channel",
            "scheduled_for",
            name=(
                "uq_renewaldesk_reminder_"
                "delivery_occurrence"
            ),
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    renewal_item_id: Mapped[int] = mapped_column(
        ForeignKey(
            "renewaldesk_renewal_items.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    channel: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="email",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
    )

    scheduled_for: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
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
