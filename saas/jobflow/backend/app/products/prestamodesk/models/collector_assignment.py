from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LoanCollectorAssignment(Base):
    __tablename__ = "prestamodesk_loan_collector_assignments"
    __table_args__ = (
        CheckConstraint(
            "("
            "released_at IS NULL "
            "AND released_by_user_id IS NULL"
            ") OR ("
            "released_at IS NOT NULL "
            "AND released_by_user_id IS NOT NULL"
            ")",
            name=(
                "ck_prestamodesk_collector_assignment_release"
            ),
        ),
        Index(
            "uq_prestamodesk_active_collector_assignment",
            "tenant_id",
            "loan_id",
            unique=True,
            postgresql_where=text("released_at IS NULL"),
            sqlite_where=text("released_at IS NULL"),
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

    loan_id: Mapped[int] = mapped_column(
        ForeignKey(
            "prestamodesk_loans.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    collector_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    assigned_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    released_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )

    released_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    release_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
