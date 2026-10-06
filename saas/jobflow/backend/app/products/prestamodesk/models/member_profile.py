from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class MemberProfile(Base):
    __tablename__ = "prestamodesk_member_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    membership_id: Mapped[int] = mapped_column(ForeignKey("tenant_memberships.id", ondelete="CASCADE"), nullable=False, unique=True)
    contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    correspondence_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    preferred_contact: Mapped[str] = mapped_column(String(30), nullable=False, default="email")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
