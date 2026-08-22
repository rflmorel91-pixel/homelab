from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth_context import get_current_user_id
from app.database import get_db
from app.models import Tenant, TenantMembership, User


def get_current_tenant(
    x_tenant_id: int | None = Header(
        default=None,
        alias="X-Tenant-ID",
    ),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Tenant:
    if x_tenant_id is None:
        raise HTTPException(
            status_code=401,
            detail="Tenant context required",
        )

    user = db.get(User, user_id)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    membership = db.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == x_tenant_id,
            TenantMembership.user_id == user_id,
        )
    )

    if membership is None:
        raise HTTPException(
            status_code=403,
            detail="User is not a member of this tenant",
        )

    tenant = db.get(Tenant, x_tenant_id)

    if tenant is None:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    if tenant.status != "active":
        raise HTTPException(
            status_code=403,
            detail="Tenant is suspended",
        )

    return tenant


def get_current_tenant_membership(
    tenant: Tenant = Depends(get_current_tenant),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> TenantMembership:
    membership = db.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant.id,
            TenantMembership.user_id == user_id,
        )
    )

    if membership is None:
        raise HTTPException(
            status_code=403,
            detail="User is not a member of this tenant",
        )

    return membership


def require_current_tenant_owner(
    membership: TenantMembership = Depends(
        get_current_tenant_membership
    ),
) -> TenantMembership:
    if membership.role != "owner":
        raise HTTPException(
            status_code=403,
            detail="Tenant owner access required",
        )

    return membership
