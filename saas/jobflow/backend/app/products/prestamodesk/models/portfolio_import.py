"""Immutable opening-balance source and tenant-unique external loan references."""
from datetime import date, datetime, timezone
from sqlalchemy import Date, DateTime, ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class PortfolioImport(Base):
    __tablename__ = "prestamodesk_portfolio_imports"
    __table_args__ = (UniqueConstraint("tenant_id", "fingerprint", name="uq_prestamodesk_import_fingerprint"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    actor_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    cutoff_date: Mapped[date] = mapped_column(Date, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class ImportedLoan(Base):
    __tablename__ = "prestamodesk_imported_loans"
    __table_args__ = (UniqueConstraint("tenant_id", "external_reference", name="uq_prestamodesk_import_reference"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    import_id: Mapped[int] = mapped_column(ForeignKey("prestamodesk_portfolio_imports.id"), nullable=False)
    loan_id: Mapped[int] = mapped_column(ForeignKey("prestamodesk_loans.id"), nullable=False)
    external_reference: Mapped[str] = mapped_column(String(100), nullable=False)
