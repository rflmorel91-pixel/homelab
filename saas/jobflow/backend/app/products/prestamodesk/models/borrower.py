from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Borrower(Base):
    __tablename__ = "prestamodesk_borrowers"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "document_number",
            name="uq_prestamodesk_borrower_tenant_document",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
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
