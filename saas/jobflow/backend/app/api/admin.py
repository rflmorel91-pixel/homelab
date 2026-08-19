from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant, TenantMembership, User
from app.operator_context import get_current_operator


router = APIRouter(
    prefix="/admin",
    tags=["Administration"],
)


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
    _: User = Depends(get_current_operator),
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
