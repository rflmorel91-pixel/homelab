"""Tenant-scoped team management; platform administrators are a separate concern."""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from datetime import datetime, timezone
import re
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select, and_, or_
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
from app.products.prestamodesk.models import LoanCollectorAssignment, MemberProfile, Loan, Borrower
from app.api.password_reset import PasswordResetRequest, request_password_reset
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
                                 "client_team.status_changed", "client_team.profile_changed", "client_team.password_reset_requested", "client_user.invitation_created",
                                 "client_user.invitation_revoked", "client_user.invitation_accepted",
                                 "collections.assignment_created", "collections.assignment_released", "payments.voided", "customer_data.exported", "portfolio.imported"]),
    ).order_by(AdminAuditLog.id.desc()).limit(limit)).all()
    return [{"id": row.id, "actor_user_id": row.operator_user_id, "action": row.action,
             "target_id": row.target_id, "created_at": row.created_at,
             "before": row.before_data, "after": row.after_data} for row in rows]


PROFILE_FIELDS = ("contact_name", "phone", "correspondence_email", "preferred_contact", "notes")


class MemberProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    contact_name: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=40)
    correspondence_email: str | None = Field(default=None, max_length=320)
    preferred_contact: Literal["email", "phone", "whatsapp"] = "email"
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("contact_name", "phone", "correspondence_email", "notes")
    @classmethod
    def normalize_contact(cls, value):
        if value is None:
            return None
        return value.strip() or None

    @field_validator("correspondence_email")
    @classmethod
    def validate_contact_email(cls, value):
        if value is None:
            return None
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("A valid correspondence email is required")
        return value.lower()


def member_profile(db, tenant_id, membership_id):
    return db.scalar(select(MemberProfile).where(
        MemberProfile.tenant_id == tenant_id, MemberProfile.membership_id == membership_id))


def profile_values(profile):
    return {name: getattr(profile, name) if profile is not None else ("email" if name == "preferred_contact" else None)
            for name in PROFILE_FIELDS}


def member_history(db, tenant_id, membership):
    statement = select(AdminAuditLog).where(
        AdminAuditLog.tenant_id == tenant_id,
        or_(
            and_(AdminAuditLog.target_type == "membership", AdminAuditLog.target_id == membership.id,
                 AdminAuditLog.action.in_(["client_team.role_changed", "client_team.status_changed",
                    "client_team.member_removed", "client_team.profile_changed", "client_team.password_reset_requested"])),
            and_(AdminAuditLog.action.in_(["collections.assignment_created", "collections.assignment_released"]),
                 or_(AdminAuditLog.after_data["collector_user_id"].as_integer() == membership.user_id,
                     AdminAuditLog.before_data["collector_user_id"].as_integer() == membership.user_id)),
            and_(AdminAuditLog.action == "client_user.invitation_accepted", AdminAuditLog.operator_user_id == membership.user_id),
        )).order_by(AdminAuditLog.id.desc()).limit(51)
    rows = db.scalars(statement).all()
    return [{"id": row.id, "action": row.action, "actor_user_id": row.operator_user_id,
             "created_at": row.created_at, "before": row.before_data, "after": row.after_data}
            for row in rows[:50]], len(rows) > 50


@router.get("/memberships/{membership_id}")
def member_detail(membership_id: int, response: Response, db: Session = Depends(get_db),
                  tenant: Tenant = Depends(get_current_tenant),
                  actor: TenantMembership = Depends(require_prestamodesk_administrator)):
    response.headers["Cache-Control"] = "no-store"
    target = target_membership(db, tenant, membership_id)
    user = db.get(User, target.user_id)
    profile = member_profile(db, tenant.id, target.id)
    rows = db.execute(select(LoanCollectorAssignment, Loan, Borrower).join(
        Loan, and_(Loan.id == LoanCollectorAssignment.loan_id, Loan.tenant_id == tenant.id)).join(
        Borrower, and_(Borrower.id == Loan.borrower_id, Borrower.tenant_id == tenant.id)).where(
        LoanCollectorAssignment.tenant_id == tenant.id,
        LoanCollectorAssignment.collector_user_id == target.user_id,
        LoanCollectorAssignment.released_at.is_(None),
    ).order_by(LoanCollectorAssignment.id.desc()).limit(101)).all()
    history, more_history = member_history(db, tenant.id, target)
    editable = actor.role == "owner" or target.role not in PRIVILEGED_ROLES
    return {"membership_id": target.id, "user_id": user.id, "display_name": user.display_name,
        "login_email": user.email, "role": target.role, "membership_active": target.is_active,
        "account_active": user.is_active, "editable": editable,
        "can_change_status": editable and target.user_id != actor.user_id,
        "assignable_roles": [role for role in ROLE_PERMISSIONS if actor.role == "owner" or role not in PRIVILEGED_ROLES],
        "permissions": ROLE_PERMISSIONS.get(target.role, []), "profile": profile_values(profile),
        "assignments": [{"assignment_id": assignment.id, "loan_id": loan.id,
            "borrower_name": borrower.full_name, "loan_type": loan.loan_type,
            "principal_amount": loan.principal_amount, "loan_status": loan.status,
            "assigned_at": assignment.assigned_at, "assigned_by_user_id": assignment.assigned_by_user_id}
            for assignment, loan, borrower in rows[:100]],
        "more_assignments": len(rows) > 100, "history": history, "more_history": more_history}


@router.put("/memberships/{membership_id}/profile")
def update_member_profile(membership_id: int, payload: MemberProfileUpdate, response: Response,
                          db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant),
                          actor: TenantMembership = Depends(require_prestamodesk_administrator)):
    response.headers["Cache-Control"] = "no-store"
    lock_team(db, tenant, actor)
    target = target_membership(db, tenant, membership_id)
    guard_privileged(actor, target.role)
    profile = member_profile(db, tenant.id, target.id)
    before = profile_values(profile)
    after = payload.model_dump()
    if before != after:
        if profile is None:
            profile = MemberProfile(tenant_id=tenant.id, membership_id=target.id)
            db.add(profile)
        for name, value in after.items():
            setattr(profile, name, value)
        profile.updated_at = datetime.now(timezone.utc)
        add_admin_audit(db, operator_user_id=actor.user_id, action="client_team.profile_changed",
            target_type="membership", target_id=target.id, tenant_id=tenant.id,
            before_data={**before, "user_id": target.user_id}, after_data={**after, "user_id": target.user_id})
        db.commit()
    return {"membership_id": target.id, "profile": after}


@router.post("/memberships/{membership_id}/password-reset")
def reset_member_password(membership_id: int, response: Response, db: Session = Depends(get_db),
                          tenant: Tenant = Depends(get_current_tenant),
                          actor: TenantMembership = Depends(require_prestamodesk_administrator)):
    response.headers["Cache-Control"] = "no-store"
    lock_team(db, tenant, actor)
    target = target_membership(db, tenant, membership_id)
    guard_privileged(actor, target.role)
    user = db.get(User, target.user_id)
    if not target.is_active or not user.is_active:
        raise HTTPException(status_code=409, detail="Reactivate access before requesting password recovery")
    result = request_password_reset(PasswordResetRequest(email=user.email, product_slug="prestamodesk"), db=db)
    add_admin_audit(db, operator_user_id=actor.user_id, action="client_team.password_reset_requested",
        target_type="membership", target_id=target.id, tenant_id=tenant.id,
        after_data={"user_id": target.user_id})
    db.commit()
    return result
