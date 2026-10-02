from fastapi import Depends, HTTPException

from app.models import TenantMembership
from app.tenant_context import (
    get_current_tenant_membership,
)


def require_prestamodesk_operations_member(
    membership: TenantMembership = Depends(
        get_current_tenant_membership
    ),
) -> TenantMembership:
    if membership.role == "collector":
        raise HTTPException(
            status_code=403,
            detail=(
                "Collectors may access only the "
                "collections workspace"
            ),
        )

    return membership
