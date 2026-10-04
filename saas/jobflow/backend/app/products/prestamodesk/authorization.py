from fastapi import Depends, HTTPException

from app.models import TenantMembership
from app.tenant_context import get_current_tenant_membership

OPERATIONS_ROLES = frozenset({"owner", "member", "administrator"})
PAYMENT_ROLES = OPERATIONS_ROLES | {"cashier"}
COLLECTIONS_MANAGEMENT_ROLES = frozenset({"owner", "administrator", "supervisor"})
ADMINISTRATION_ROLES = frozenset({"owner", "administrator"})

# This is also the source for the administration screen's permission matrix.
ROLE_PERMISSIONS = {
    "owner": ["operations", "payments", "collections", "assignments", "supervision", "team", "privileged_roles"],
    "administrator": ["operations", "payments", "collections", "assignments", "supervision", "team"],
    "supervisor": ["collections", "assignments", "supervision"],
    "collector": ["assigned_collections"],
    "cashier": ["payments", "own_cash_closing"],
    "member": ["loan_read", "payments", "own_cash_closing"],
}


def require_roles(membership: TenantMembership, roles) -> TenantMembership:
    if not membership.is_active or membership.role not in roles:
        raise HTTPException(status_code=403, detail="Role does not permit this operation")
    return membership


def require_prestamodesk_operations_member(
    membership: TenantMembership = Depends(get_current_tenant_membership),
) -> TenantMembership:
    return require_roles(membership, OPERATIONS_ROLES)


def require_prestamodesk_payment_member(
    membership: TenantMembership = Depends(get_current_tenant_membership),
) -> TenantMembership:
    return require_roles(membership, PAYMENT_ROLES)


def require_prestamodesk_administrator(
    membership: TenantMembership = Depends(get_current_tenant_membership),
) -> TenantMembership:
    return require_roles(membership, ADMINISTRATION_ROLES)


def require_prestamodesk_manager(
    membership: TenantMembership = Depends(get_current_tenant_membership),
) -> TenantMembership:
    if not membership.is_active or membership.role not in ADMINISTRATION_ROLES:
        raise HTTPException(status_code=403, detail="Tenant owner access required")
    return membership
