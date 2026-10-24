"""Capacity checks shared by products; callers own their usage queries."""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Tenant, TenantResourceLimit


def lock_tenant_capacity(db: Session, tenant_id: int) -> Tenant:
    tenant = db.scalar(
        select(Tenant)
        .where(Tenant.id == tenant_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if tenant.status != "active":
        raise HTTPException(status_code=403, detail="Tenant is suspended")
    return tenant


def require_resource_capacity(
    db: Session,
    tenant_id: int,
    resource_key: str,
    usage_statement,
    *,
    detail: str,
) -> None:
    # Hold the tenant lock through the caller's creation and commit.
    lock_tenant_capacity(db, tenant_id)
    maximum = db.scalar(
        select(TenantResourceLimit.maximum_count).where(
            TenantResourceLimit.tenant_id == tenant_id,
            TenantResourceLimit.resource_key == resource_key,
        )
    )
    if maximum is None:
        return
    used = db.scalar(usage_statement)
    if used >= maximum:
        raise HTTPException(status_code=409, detail=detail)
