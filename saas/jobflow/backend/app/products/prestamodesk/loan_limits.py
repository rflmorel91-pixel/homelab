"""PréstamoDesk owns the definition of an active loan."""

from sqlalchemy import func, select

from app.platform.resource_limits import require_resource_capacity
from app.products.prestamodesk.models import Loan


ACTIVE_LOAN_RESOURCE = "prestamodesk.active_loans"


def require_new_loan_capacity(db, tenant_id: int) -> None:
    require_resource_capacity(
        db,
        tenant_id,
        ACTIVE_LOAN_RESOURCE,
        select(func.count(Loan.id)).where(
            Loan.tenant_id == tenant_id,
            Loan.status == "active",
        ),
        detail=(
            "Se alcanzó el límite de préstamos activos del plan. "
            "Contacte al administrador para revisar su capacidad."
        ),
    )
