from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    AdminAuditLog,
    Tenant,
    TenantMembership,
    User,
)
from app.operator_context import get_current_operator


def add_admin_audit(
    db: Session,
    *,
    operator_user_id: int,
    action: str,
    target_type: str,
    target_id: int,
    tenant_id: int | None = None,
    before_data: dict | None = None,
    after_data: dict | None = None,
) -> None:
    db.add(
        AdminAuditLog(
            operator_user_id=operator_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            tenant_id=tenant_id,
            before_data=before_data,
            after_data=after_data,
        )
    )


router = APIRouter(
    prefix="/admin",
    tags=["Administration"],
)


@router.get("/audit-log")
def admin_audit_log(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_operator),
):
    events = db.execute(
        select(
            AdminAuditLog,
            User.email,
            User.display_name,
        )
        .join(
            User,
            User.id
            == AdminAuditLog.operator_user_id,
        )
        .order_by(
            AdminAuditLog.created_at.desc(),
            AdminAuditLog.id.desc(),
        )
        .limit(100)
    ).all()

    return {
        "count": db.scalar(
            select(func.count())
            .select_from(AdminAuditLog)
        ),
        "events": [
            {
                "id": event.id,
                "operator_user_id":
                    event.operator_user_id,
                "operator_email": email,
                "operator_display_name":
                    display_name,
                "action": event.action,
                "target_type": event.target_type,
                "target_id": event.target_id,
                "tenant_id": event.tenant_id,
                "before_data": event.before_data,
                "after_data": event.after_data,
                "created_at": event.created_at,
            }
            for event, email, display_name
            in events
        ],
    }


@router.get("/overview")
def admin_overview(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_operator),
):
    users = db.execute(
        select(User).order_by(User.id)
    ).scalars().all()

    tenants = db.execute(
        select(Tenant).order_by(Tenant.id)
    ).scalars().all()

    memberships = db.execute(
        select(
            TenantMembership,
            User.email,
            Tenant.name,
        )
        .join(User, User.id == TenantMembership.user_id)
        .join(Tenant, Tenant.id == TenantMembership.tenant_id)
        .order_by(TenantMembership.id)
    ).all()

    return {
        "counts": {
            "users": db.scalar(
                select(func.count()).select_from(User)
            ),
            "tenants": db.scalar(
                select(func.count()).select_from(Tenant)
            ),
            "memberships": db.scalar(
                select(func.count()).select_from(TenantMembership)
            ),
            "active_users": db.scalar(
                select(func.count())
                .select_from(User)
                .where(User.is_active.is_(True))
            ),
            "platform_admins": db.scalar(
                select(func.count())
                .select_from(User)
                .where(User.is_platform_admin.is_(True))
            ),
        },
        "users": [
            {
                "id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "is_active": user.is_active,
                "is_platform_admin": user.is_platform_admin,
                "created_at": user.created_at,
            }
            for user in users
        ],
        "tenants": [
            {
                "id": tenant.id,
                "name": tenant.name,
                "slug": tenant.slug,
                "created_at": tenant.created_at,
            }
            for tenant in tenants
        ],
        "memberships": [
            {
                "id": membership.id,
                "tenant_id": membership.tenant_id,
                "tenant_name": tenant_name,
                "user_id": membership.user_id,
                "user_email": user_email,
                "role": membership.role,
                "created_at": membership.created_at,
            }
            for membership, user_email, tenant_name
            in memberships
        ],
    }


@router.get("/tenants/{tenant_id}")
def admin_tenant_detail(
    tenant_id: int,
    db: Session = Depends(get_db),
    operator: User = Depends(get_current_operator),
):
    tenant = db.get(Tenant, tenant_id)

    if tenant is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    memberships = db.execute(
        select(
            TenantMembership,
            User.email,
            User.display_name,
        )
        .join(User, User.id == TenantMembership.user_id)
        .where(TenantMembership.tenant_id == tenant_id)
        .order_by(TenantMembership.id)
    ).all()

    from app.models import (
        Customer,
        Estimate,
        Invoice,
        Job,
        Payment,
        Schedule,
    )

    customer_ids = select(Customer.id).where(
        Customer.tenant_id == tenant_id
    )

    job_ids = select(Job.id).where(
        Job.customer_id.in_(customer_ids)
    )

    invoice_ids = select(Invoice.id).where(
        Invoice.job_id.in_(job_ids)
    )

    return {
        "tenant": {
            "id": tenant.id,
            "name": tenant.name,
            "slug": tenant.slug,
            "created_at": tenant.created_at,
        },
        "counts": {
            "memberships": len(memberships),
            "customers": db.scalar(
                select(func.count())
                .select_from(Customer)
                .where(Customer.tenant_id == tenant_id)
            ),
            "jobs": db.scalar(
                select(func.count())
                .select_from(Job)
                .where(Job.customer_id.in_(customer_ids))
            ),
            "estimates": db.scalar(
                select(func.count())
                .select_from(Estimate)
                .where(Estimate.job_id.in_(job_ids))
            ),
            "schedules": db.scalar(
                select(func.count())
                .select_from(Schedule)
                .where(Schedule.job_id.in_(job_ids))
            ),
            "invoices": db.scalar(
                select(func.count())
                .select_from(Invoice)
                .where(Invoice.job_id.in_(job_ids))
            ),
            "payments": db.scalar(
                select(func.count())
                .select_from(Payment)
                .where(Payment.invoice_id.in_(invoice_ids))
            ),
        },
        "memberships": [
            {
                "id": membership.id,
                "user_id": membership.user_id,
                "user_email": email,
                "display_name": display_name,
                "role": membership.role,
            }
            for membership, email, display_name
            in memberships
        ],
    }


@router.get("/users/{user_id}")
def admin_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_operator),
):
    user = db.get(User, user_id)

    if user is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    memberships = db.execute(
        select(
            TenantMembership,
            Tenant.name,
            Tenant.slug,
        )
        .join(Tenant, Tenant.id == TenantMembership.tenant_id)
        .where(TenantMembership.user_id == user_id)
        .order_by(TenantMembership.id)
    ).all()

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "is_active": user.is_active,
            "is_platform_admin": user.is_platform_admin,
            "created_at": user.created_at,
        },
        "memberships": [
            {
                "id": membership.id,
                "tenant_id": membership.tenant_id,
                "tenant_name": tenant_name,
                "tenant_slug": tenant_slug,
                "role": membership.role,
            }
            for membership, tenant_name, tenant_slug
            in memberships
        ],
    }


from typing import Literal

from fastapi import HTTPException, Response, status
from pydantic import BaseModel


class UserAdminUpdate(BaseModel):
    is_active: bool | None = None
    is_platform_admin: bool | None = None


class MembershipCreate(BaseModel):
    user_id: int
    role: Literal["owner", "member"] = "member"


class MembershipUpdate(BaseModel):
    role: Literal["owner", "member"]


@router.put("/users/{user_id}")
def admin_update_user(
    user_id: int,
    payload: UserAdminUpdate,
    db: Session = Depends(get_db),
    operator: User = Depends(get_current_operator),
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    if (
        user.id == operator.id
        and payload.is_active is False
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Current operator cannot "
                "deactivate themselves"
            ),
        )

    if (
        user.id == operator.id
        and payload.is_platform_admin is False
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Current operator cannot revoke "
                "their own platform access"
            ),
        )

    if (
        user.is_platform_admin
        and payload.is_platform_admin is False
    ):
        admin_count = db.scalar(
            select(func.count())
            .select_from(User)
            .where(User.is_platform_admin.is_(True))
        )

        if admin_count <= 1:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Platform must retain at least "
                    "one administrator"
                ),
            )

    before_active = user.is_active
    before_platform_admin = user.is_platform_admin

    if payload.is_active is not None:
        user.is_active = payload.is_active

    if payload.is_platform_admin is not None:
        user.is_platform_admin = (
            payload.is_platform_admin
        )

    if before_active != user.is_active:
        add_admin_audit(
            db,
            operator_user_id=operator.id,
            action=(
                "user.activated"
                if user.is_active
                else "user.deactivated"
            ),
            target_type="user",
            target_id=user.id,
            before_data={
                "is_active": before_active,
            },
            after_data={
                "is_active": user.is_active,
            },
        )

    if (
        before_platform_admin
        != user.is_platform_admin
    ):
        add_admin_audit(
            db,
            operator_user_id=operator.id,
            action=(
                "user.platform_admin_granted"
                if user.is_platform_admin
                else "user.platform_admin_revoked"
            ),
            target_type="user",
            target_id=user.id,
            before_data={
                "is_platform_admin":
                    before_platform_admin,
            },
            after_data={
                "is_platform_admin":
                    user.is_platform_admin,
            },
        )

    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "is_active": user.is_active,
        "is_platform_admin": user.is_platform_admin,
    }


@router.post(
    "/tenants/{tenant_id}/memberships",
    status_code=status.HTTP_201_CREATED,
)
def admin_create_membership(
    tenant_id: int,
    payload: MembershipCreate,
    db: Session = Depends(get_db),
    operator: User = Depends(get_current_operator),
):
    tenant = db.get(Tenant, tenant_id)

    if tenant is None:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    user = db.get(User, payload.user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    existing = db.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.user_id == payload.user_id,
        )
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="User is already a tenant member",
        )

    membership = TenantMembership(
        tenant_id=tenant_id,
        user_id=payload.user_id,
        role=payload.role,
    )

    db.add(membership)
    db.flush()

    add_admin_audit(
        db,
        operator_user_id=operator.id,
        action="membership.created",
        target_type="membership",
        target_id=membership.id,
        tenant_id=membership.tenant_id,
        after_data={
            "user_id": membership.user_id,
            "role": membership.role,
        },
    )

    db.commit()
    db.refresh(membership)

    return {
        "id": membership.id,
        "tenant_id": membership.tenant_id,
        "user_id": membership.user_id,
        "role": membership.role,
    }


@router.put("/memberships/{membership_id}")
def admin_update_membership(
    membership_id: int,
    payload: MembershipUpdate,
    db: Session = Depends(get_db),
    operator: User = Depends(get_current_operator),
):
    membership = db.get(
        TenantMembership,
        membership_id,
    )

    if membership is None:
        raise HTTPException(
            status_code=404,
            detail="Membership not found",
        )

    if (
        membership.role == "owner"
        and payload.role != "owner"
    ):
        owner_count = db.scalar(
            select(func.count())
            .select_from(TenantMembership)
            .where(
                TenantMembership.tenant_id
                == membership.tenant_id,
                TenantMembership.role == "owner",
            )
        )

        if owner_count <= 1:
            raise HTTPException(
                status_code=409,
                detail="Tenant must retain at least one owner",
            )

    previous_role = membership.role
    membership.role = payload.role

    if previous_role != membership.role:
        add_admin_audit(
            db,
            operator_user_id=operator.id,
            action="membership.role_changed",
            target_type="membership",
            target_id=membership.id,
            tenant_id=membership.tenant_id,
            before_data={
                "role": previous_role,
            },
            after_data={
                "role": membership.role,
            },
        )

    db.commit()
    db.refresh(membership)

    return {
        "id": membership.id,
        "tenant_id": membership.tenant_id,
        "user_id": membership.user_id,
        "role": membership.role,
    }


@router.delete(
    "/memberships/{membership_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def admin_delete_membership(
    membership_id: int,
    db: Session = Depends(get_db),
    operator: User = Depends(get_current_operator),
):
    membership = db.get(
        TenantMembership,
        membership_id,
    )

    if membership is None:
        raise HTTPException(
            status_code=404,
            detail="Membership not found",
        )

    if membership.role == "owner":
        owner_count = db.scalar(
            select(func.count())
            .select_from(TenantMembership)
            .where(
                TenantMembership.tenant_id
                == membership.tenant_id,
                TenantMembership.role == "owner",
            )
        )

        if owner_count <= 1:
            raise HTTPException(
                status_code=409,
                detail="Tenant must retain at least one owner",
            )

    audit_target_id = membership.id
    audit_tenant_id = membership.tenant_id
    audit_user_id = membership.user_id
    audit_role = membership.role

    db.delete(membership)

    add_admin_audit(
        db,
        operator_user_id=operator.id,
        action="membership.removed",
        target_type="membership",
        target_id=audit_target_id,
        tenant_id=audit_tenant_id,
        before_data={
            "user_id": audit_user_id,
            "role": audit_role,
        },
    )

    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
