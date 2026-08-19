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
