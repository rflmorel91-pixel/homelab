"""Tenant-scoped team management; platform administrators are a separate concern."""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.admin import add_admin_audit
from app.api.invitations import (
    ClientInvitationCreate, ClientMembershipUpdate,
    create_client_user_invitation, get_current_client_team,
    list_client_user_invitations, revoke_client_user_invitation,
    update_current_client_membership,
)
from app.database import get_db
from app.models import AdminAuditLog, Tenant, TenantMembership, User, UserInvitation
from app.products.prestamodesk.authorization import (
    ROLE_PERMISSIONS, require_prestamodesk_administrator,
)
from app.products.prestamodesk.models import LoanCollectorAssignment
from app.tenant_context import get_current_tenant

router = APIRouter(prefix="/administration", tags=["PréstamoDesk Administration"],
                   dependencies=[Depends(require_prestamodesk_administrator)])
PRIVILEGED_ROLES = {"owner", "administrator"}
ROLE_LABELS = {"owner": "Propietario", "administrator": "Administrador",
               "supervisor": "Supervisor", "collector": "Cobrador",
               "cashier": "Cajero", "member": "Miembro (caja existente)"}


class MembershipStatusUpdate(BaseModel):
    is_active: bool


def require_released_portfolio(db: Session, tenant_id: int, user_id: int):
    assignment = db.scalar(select(LoanCollectorAssignment.id).where(
        LoanCollectorAssignment.tenant_id == tenant_id,
        LoanCollectorAssignment.collector_user_id == user_id,
        LoanCollectorAssignment.released_at.is_(None),
    ).limit(1))
    if assignment is not None:
        raise HTTPException(status_code=409, detail="Release collector assignments before changing or suspending this membership")


def guard_privileged(actor, current_role=None, new_role=None):
    if actor.role != "owner" and ({current_role, new_role} & PRIVILEGED_ROLES):
        raise HTTPException(status_code=403, detail="Only the owner may manage owners and administrators")


def lock_team(db, tenant, actor):
    db.scalar(select(Tenant).where(Tenant.id == tenant.id).with_for_update())
    db.refresh(actor)
    if not actor.is_active or actor.role not in {"owner", "administrator"}:
        raise HTTPException(status_code=403, detail="Administration access required")


def target_membership(db, tenant, membership_id):
    result = db.scalar(select(TenantMembership).where(
        TenantMembership.id == membership_id,
        TenantMembership.tenant_id == tenant.id,
    ).with_for_update())
    if result is None:
        raise HTTPException(status_code=404, detail="Membership not found")
    return result


@router.get("/team")
def team(response: Response, db: Session = Depends(get_db),
         tenant: Tenant = Depends(get_current_tenant),
         actor: TenantMembership = Depends(require_prestamodesk_administrator)):
    result = get_current_client_team(response=response, db=db, tenant=tenant, operator_membership=actor)
    result["roles"] = [{"role": role, "label": ROLE_LABELS[role], "permissions": permissions}
                       for role, permissions in ROLE_PERMISSIONS.items()]
    result["assignable_roles"] = [role for role in ROLE_PERMISSIONS
                                  if actor.role == "owner" or role not in PRIVILEGED_ROLES]
    return result


@router.put("/memberships/{membership_id}/role")
def change_role(membership_id: int, payload: ClientMembershipUpdate,
                db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant),
                actor: TenantMembership = Depends(require_prestamodesk_administrator)):
    lock_team(db, tenant, actor)
    target = target_membership(db, tenant, membership_id)
    guard_privileged(actor, target.role, payload.role)
    return update_current_client_membership(membership_id=membership_id, payload=payload,
                                            db=db, tenant=tenant, operator_membership=actor)


@router.put("/memberships/{membership_id}/status")
def change_status(membership_id: int, payload: MembershipStatusUpdate,
                  db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant),
                  actor: TenantMembership = Depends(require_prestamodesk_administrator)):
    lock_team(db, tenant, actor)
    target = target_membership(db, tenant, membership_id)
    guard_privileged(actor, target.role)
    if target.user_id == actor.user_id and not payload.is_active:
        raise HTTPException(status_code=409, detail="You cannot suspend your own membership")
    if target.is_active and not payload.is_active:
        if target.role == "owner":
            another = db.scalar(select(TenantMembership.id).join(User, User.id == TenantMembership.user_id).where(
                TenantMembership.tenant_id == tenant.id, TenantMembership.role == "owner",
                TenantMembership.is_active.is_(True), User.is_active.is_(True),
                TenantMembership.id != target.id,
            ).limit(1))
            if another is None:
                raise HTTPException(status_code=409, detail="Client must retain at least one active owner")
        require_released_portfolio(db, tenant.id, target.user_id)
    before = target.is_active
    target.is_active = payload.is_active
    if before != target.is_active:
        add_admin_audit(db, operator_user_id=actor.user_id, action="client_team.status_changed",
                        target_type="membership", target_id=target.id, tenant_id=tenant.id,
                        before_data={"is_active": before, "user_id": target.user_id},
                        after_data={"is_active": target.is_active, "user_id": target.user_id})
    db.commit()
    return {"membership_id": target.id, "is_active": target.is_active}


@router.get("/invitations")
def invitations(response: Response, db: Session = Depends(get_db),
                tenant: Tenant = Depends(get_current_tenant),
                actor: TenantMembership = Depends(require_prestamodesk_administrator)):
    response.headers["Cache-Control"] = "no-store"
    return list_client_user_invitations(tenant_id=tenant.id, response=response, db=db, _=db.get(User, actor.user_id))


@router.post("/invitations", status_code=201)
def invite(payload: ClientInvitationCreate, response: Response, db: Session = Depends(get_db),
           tenant: Tenant = Depends(get_current_tenant),
           actor: TenantMembership = Depends(require_prestamodesk_administrator)):
    lock_team(db, tenant, actor)
    guard_privileged(actor, new_role=payload.role)
    return create_client_user_invitation(tenant_id=tenant.id, payload=payload, response=response,
                                        db=db, operator=db.get(User, actor.user_id))


@router.post("/invitations/{invitation_id}/revoke")
def revoke(invitation_id: int, response: Response, db: Session = Depends(get_db),
           tenant: Tenant = Depends(get_current_tenant),
           actor: TenantMembership = Depends(require_prestamodesk_administrator)):
    lock_team(db, tenant, actor)
    invitation = db.scalar(select(UserInvitation).where(UserInvitation.id == invitation_id,
                                                       UserInvitation.tenant_id == tenant.id))
    if invitation is None:
        raise HTTPException(status_code=404, detail="Invitation not found")
    guard_privileged(actor, current_role=invitation.role)
    return revoke_client_user_invitation(tenant_id=tenant.id, invitation_id=invitation_id,
                                        response=response, db=db, operator=db.get(User, actor.user_id))


@router.get("/audit")
def audit(response: Response, limit: int = Query(default=50, ge=1, le=200),
          db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant)):
    response.headers["Cache-Control"] = "no-store"
    rows = db.scalars(select(AdminAuditLog).where(
        AdminAuditLog.tenant_id == tenant.id,
        AdminAuditLog.action.in_(["client_team.role_changed", "client_team.member_removed",
                                 "client_team.status_changed", "client_user.invitation_created",
                                 "client_user.invitation_revoked", "client_user.invitation_accepted",
                                 "collections.assignment_created", "collections.assignment_released", "payments.voided"]),
    ).order_by(AdminAuditLog.id.desc()).limit(limit)).all()
    return [{"id": row.id, "actor_user_id": row.operator_user_id, "action": row.action,
             "target_id": row.target_id, "created_at": row.created_at,
             "before": row.before_data, "after": row.after_data} for row in rows]
