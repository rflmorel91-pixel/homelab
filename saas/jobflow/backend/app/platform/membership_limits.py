"""Active named memberships consume slots; pending invitations do not."""

from sqlalchemy import func, select

from app.models import TenantMembership
from app.platform.resource_limits import require_resource_capacity


ACTIVE_MEMBERSHIP_RESOURCE = "platform.active_memberships"


def require_membership_capacity(db, tenant_id: int) -> None:
    require_resource_capacity(
        db,
        tenant_id,
        ACTIVE_MEMBERSHIP_RESOURCE,
        select(func.count(TenantMembership.id)).where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.is_active.is_(True),
        ),
        detail=(
            "Se alcanzó el límite de usuarios activos del plan. "
            "Suspenda una membresía o solicite ampliar su capacidad."
        ),
        # Existing routes retain responsibility for tenant-status policy.
        require_active=False,
    )
