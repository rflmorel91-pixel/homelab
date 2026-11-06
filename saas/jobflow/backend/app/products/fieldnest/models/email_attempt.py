"""Short-lived send-budget history, independent of deletable maintenance rows."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FieldNestEmailAttempt(Base):
    __tablename__ = "fieldnest_email_attempts"
    __table_args__ = (
        Index("ix_fieldnest_email_attempts_tenant_time", "tenant_id", "attempted_at"),
        Index("ix_fieldnest_email_attempts_recipient_time", "recipient_hash", "attempted_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Deliberately no cascading foreign keys: deleting a report cannot reset
    # recipient, business or platform budgets.
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    notification_id: Mapped[int] = mapped_column(Integer, nullable=False)
    recipient_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        nullable=False, index=True,
    )
