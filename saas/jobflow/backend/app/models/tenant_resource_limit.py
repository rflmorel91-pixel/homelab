"""Explicit per-tenant limits; no row means no assigned limit."""

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TenantResourceLimit(Base):
    __tablename__ = "platform_tenant_resource_limits"
    __table_args__ = (
        CheckConstraint(
            "maximum_count >= 0",
            name="ck_platform_tenant_resource_limits_nonnegative",
        ),
    )

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"), primary_key=True,
    )
    resource_key: Mapped[str] = mapped_column(
        String(100), primary_key=True,
    )
    maximum_count: Mapped[int] = mapped_column(
        Integer, nullable=False,
    )
