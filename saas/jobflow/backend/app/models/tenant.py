from datetime import datetime, timezone
from zoneinfo import (
    ZoneInfo,
    ZoneInfoNotFoundError,
)

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    validates,
)

from app.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "client_number",
            name="uq_tenants_product_client_number",
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

    client_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
        index=True,
    )

    timezone_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="UTC",
        server_default="UTC",
    )

    @validates("timezone_name")
    def validate_timezone_name(
        self,
        key: str,
        value: str,
    ) -> str:
        normalized = value.strip()

        try:
            ZoneInfo(normalized)
        except (
            ValueError,
            ZoneInfoNotFoundError,
        ) as error:
            raise ValueError(
                "Unknown IANA timezone"
            ) from error

        return normalized

    suspended_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
