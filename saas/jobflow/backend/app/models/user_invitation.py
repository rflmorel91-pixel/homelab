from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserInvitation(Base):
    __tablename__ = "user_invitations"

    __table_args__ = (
        CheckConstraint(
            """
            (
                lead_id IS NOT NULL
                AND tenant_id IS NULL
                AND role IS NULL
            )
            OR
            (
                lead_id IS NULL
                AND tenant_id IS NOT NULL
                AND role IN ('owner', 'member')
            )
            """,
            name="ck_user_invitations_single_target",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        index=True,
    )

    display_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    lead_id: Mapped[int | None] = mapped_column(
        ForeignKey("leads.id"),
        nullable=True,
        index=True,
    )

    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=True,
        index=True,
    )

    role: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    accepted_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=True,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
