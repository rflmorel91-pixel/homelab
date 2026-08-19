from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)

    business_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    contact_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(50),
    )

    service_type: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    message: Mapped[str | None] = mapped_column(
        Text,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="new",
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
