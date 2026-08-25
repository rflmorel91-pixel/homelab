from datetime import datetime, timezone
import re
from zoneinfo import (
    ZoneInfo,
    ZoneInfoNotFoundError,
)

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    BillingAccount,
    BillingOffer,
    Lead,
    Product,
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
    products = db.execute(
        select(Product).order_by(Product.id)
    ).scalars().all()

    all_users = db.execute(
        select(User).order_by(User.id)
    ).scalars().all()

    commercial_user_ids = set(
        db.scalars(
            select(TenantMembership.user_id)
            .join(
                Tenant,
                Tenant.id
                == TenantMembership.tenant_id,
            )
            .where(
                Tenant.client_number.is_not(None)
            )
        ).all()
    )

    validation_user_ids = set(
        db.scalars(
            select(TenantMembership.user_id)
            .join(
                Tenant,
                Tenant.id
                == TenantMembership.tenant_id,
            )
            .where(
                Tenant.client_number.is_(None)
            )
        ).all()
    )

    users = [
        user
        for user in all_users
        if (
            user.is_platform_admin
            or user.id not in commercial_user_ids
            or user.id in validation_user_ids
        )
    ]

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
            "products": db.scalar(
                select(func.count()).select_from(Product)
            ),
            "users": len(users),
            "tenants": db.scalar(
                select(func.count()).select_from(Tenant)
            ),
            "clients": db.scalar(
                select(func.count())
                .select_from(Tenant)
                .where(Tenant.client_number.is_not(None))
            ),
            "validation_workspaces": db.scalar(
                select(func.count())
                .select_from(Tenant)
                .where(Tenant.client_number.is_(None))
            ),
            "memberships": db.scalar(
                select(func.count()).select_from(TenantMembership)
            ),
            "active_users": sum(
                user.is_active
                for user in users
            ),
            "platform_admins": db.scalar(
                select(func.count())
                .select_from(User)
                .where(User.is_platform_admin.is_(True))
            ),
        },
        "products": [
            {
                "id": product.id,
                "name": product.name,
                "slug": product.slug,
                "status": product.status,
                "workspace_key": product.workspace_key,
                "tenant_count": db.scalar(
                    select(func.count())
                    .select_from(Tenant)
                    .where(Tenant.product_id == product.id)
                ),
                "client_count": db.scalar(
                    select(func.count())
                    .select_from(Tenant)
                    .where(
                        Tenant.product_id == product.id,
                        Tenant.client_number.is_not(None),
                    )
                ),
                "validation_workspace_count": db.scalar(
                    select(func.count())
                    .select_from(Tenant)
                    .where(
                        Tenant.product_id == product.id,
                        Tenant.client_number.is_(None),
                    )
                ),
                "active_lead_count": db.scalar(
                    select(func.count())
                    .select_from(Lead)
                    .where(
                        Lead.product_id == product.id,
                        Lead.status.in_(
                            (
                                "new",
                                "contacted",
                                "qualified",
                            )
                        ),
                    )
                ),
                "converted_lead_count": db.scalar(
                    select(func.count())
                    .select_from(Lead)
                    .where(
                        Lead.product_id == product.id,
                        Lead.status == "converted",
                    )
                ),
                "created_at": product.created_at,
            }
            for product in products
        ],
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
                "client_number": tenant.client_number,
                "product_id": tenant.product_id,
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


@router.get("/products/{product_id}")
def admin_product_detail(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_operator),
):
    product = db.get(
        Product,
        product_id,
    )

    if product is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    clients = db.scalars(
        select(Tenant)
        .where(
            Tenant.product_id == product.id,
            Tenant.client_number.is_not(None),
        )
        .order_by(
            Tenant.client_number,
            Tenant.id,
        )
    ).all()

    validation_workspaces = db.scalars(
        select(Tenant)
        .where(
            Tenant.product_id == product.id,
            Tenant.client_number.is_(None),
        )
        .order_by(Tenant.id)
    ).all()

    membership_rows = db.execute(
        select(
            TenantMembership,
            User,
            Tenant,
        )
        .join(
            Tenant,
            Tenant.id == TenantMembership.tenant_id,
        )
        .join(
            User,
            User.id == TenantMembership.user_id,
        )
        .where(
            Tenant.product_id == product.id,
            Tenant.client_number.is_not(None),
        )
        .order_by(
            Tenant.client_number,
            User.display_name,
            User.id,
        )
    ).all()

    active_leads = db.scalars(
        select(Lead)
        .where(
            Lead.product_id == product.id,
            Lead.status.in_(
                (
                    "new",
                    "contacted",
                    "qualified",
                )
            ),
        )
        .order_by(
            Lead.created_at.desc(),
            Lead.id.desc(),
        )
    ).all()

    converted_leads = db.scalars(
        select(Lead)
        .where(
            Lead.product_id == product.id,
            Lead.status == "converted",
        )
        .order_by(
            Lead.converted_at.desc(),
            Lead.id.desc(),
        )
    ).all()

    product_user_ids = {
        user.id
        for _, user, _ in membership_rows
    }

    return {
        "product": {
            "id": product.id,
            "name": product.name,
            "slug": product.slug,
            "status": product.status,
            "workspace_key": product.workspace_key,
            "created_at": product.created_at,
        },
        "counts": {
            "clients": len(clients),
            "users": len(product_user_ids),
            "active_leads": len(active_leads),
            "converted_records": len(converted_leads),
            "validation_workspaces":
                len(validation_workspaces),
        },
        "clients": [
            {
                "id": tenant.id,
                "client_number": tenant.client_number,
                "name": tenant.name,
                "slug": tenant.slug,
                "status": tenant.status,
                "suspended_at": tenant.suspended_at,
                "created_at": tenant.created_at,
            }
            for tenant in clients
        ],
        "users": [
            {
                "user_id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "is_active": user.is_active,
                "client_id": tenant.id,
                "client_number": tenant.client_number,
                "client_name": tenant.name,
                "role": membership.role,
                "membership_id": membership.id,
            }
            for membership, user, tenant
            in membership_rows
        ],
        "active_leads": [
            {
                "id": lead.id,
                "business_name": lead.business_name,
                "contact_name": lead.contact_name,
                "email": lead.email,
                "service_type": lead.service_type,
                "status": lead.status,
                "created_at": lead.created_at,
            }
            for lead in active_leads
        ],
        "converted_history": [
            {
                "id": lead.id,
                "business_name": lead.business_name,
                "contact_name": lead.contact_name,
                "email": lead.email,
                "service_type": lead.service_type,
                "status": lead.status,
                "converted_tenant_id":
                    lead.converted_tenant_id,
                "converted_at": lead.converted_at,
                "created_at": lead.created_at,
            }
            for lead in converted_leads
        ],
        "validation_workspaces": [
            {
                "id": tenant.id,
                "name": tenant.name,
                "slug": tenant.slug,
                "status": tenant.status,
                "suspended_at": tenant.suspended_at,
                "created_at": tenant.created_at,
            }
            for tenant in validation_workspaces
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

    billing_account = db.scalar(
        select(BillingAccount).where(
            BillingAccount.tenant_id
            == tenant.id
        )
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

    return {
        "tenant": {
            "id": tenant.id,
            "client_number": tenant.client_number,
            "product_id": tenant.product_id,
            "name": tenant.name,
            "slug": tenant.slug,
            "status": tenant.status,
            "timezone_name": tenant.timezone_name,
            "suspended_at": tenant.suspended_at,
            "created_at": tenant.created_at,
        },
        "billing_account":
            billing_account_data(
                billing_account
            ),
        "counts": {
            "memberships": len(memberships),
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


@router.post("/tenants/{tenant_id}/suspend")
def admin_suspend_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    operator: User = Depends(get_current_operator),
):
    tenant = db.get(Tenant, tenant_id)

    if tenant is None:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    if tenant.status == "suspended":
        raise HTTPException(
            status_code=409,
            detail="Tenant is already suspended",
        )

    suspended_at = datetime.now(timezone.utc)

    before_data = {
        "status": tenant.status,
        "suspended_at": (
            tenant.suspended_at.isoformat()
            if tenant.suspended_at
            else None
        ),
    }

    tenant.status = "suspended"
    tenant.suspended_at = suspended_at

    add_admin_audit(
        db,
        operator_user_id=operator.id,
        action="tenant.suspended",
        target_type="tenant",
        target_id=tenant.id,
        tenant_id=tenant.id,
        before_data=before_data,
        after_data={
            "status": tenant.status,
            "suspended_at":
                tenant.suspended_at.isoformat(),
        },
    )

    db.commit()
    db.refresh(tenant)

    return {
        "id": tenant.id,
        "client_number": tenant.client_number,
        "name": tenant.name,
        "slug": tenant.slug,
        "status": tenant.status,
        "suspended_at": tenant.suspended_at,
    }


@router.post("/tenants/{tenant_id}/reactivate")
def admin_reactivate_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    operator: User = Depends(get_current_operator),
):
    tenant = db.get(Tenant, tenant_id)

    if tenant is None:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    if tenant.status == "active":
        raise HTTPException(
            status_code=409,
            detail="Tenant is already active",
        )

    before_data = {
        "status": tenant.status,
        "suspended_at": (
            tenant.suspended_at.isoformat()
            if tenant.suspended_at
            else None
        ),
    }

    tenant.status = "active"
    tenant.suspended_at = None

    add_admin_audit(
        db,
        operator_user_id=operator.id,
        action="tenant.reactivated",
        target_type="tenant",
        target_id=tenant.id,
        tenant_id=tenant.id,
        before_data=before_data,
        after_data={
            "status": tenant.status,
            "suspended_at": None,
        },
    )

    db.commit()
    db.refresh(tenant)

    return {
        "id": tenant.id,
        "client_number": tenant.client_number,
        "name": tenant.name,
        "slug": tenant.slug,
        "status": tenant.status,
        "suspended_at": tenant.suspended_at,
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
from pydantic import (
    BaseModel,
    field_validator,
    model_validator,
)


class TenantTimezoneUpdate(BaseModel):
    timezone_name: str

    @field_validator("timezone_name")
    @classmethod
    def validate_timezone_name(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()

        try:
            ZoneInfo(normalized)
        except (
            ValueError,
            ZoneInfoNotFoundError,
        ) as error:
            raise ValueError(
                "Unknown IANA timezone"
            ) from error

        return normalized


class UserAdminUpdate(BaseModel):
    is_active: bool | None = None
    is_platform_admin: bool | None = None


class MembershipCreate(BaseModel):
    user_id: int
    role: Literal["owner", "member"] = "member"


class MembershipUpdate(BaseModel):
    role: Literal["owner", "member"]


class BillingOfferWrite(BaseModel):
    product_id: int
    code: str
    name: str
    description: str | None = None
    status: Literal[
        "draft",
        "active",
        "archived",
    ] = "draft"
    charge_type: Literal[
        "one_time",
        "subscription",
        "custom_quote",
    ]
    currency: str = "USD"
    minimum_amount_cents: int
    maximum_amount_cents: int
    billing_interval: Literal[
        "month",
        "year",
    ] | None = None
    service_period_days: int | None = None

    @field_validator("code")
    @classmethod
    def validate_code(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip().lower()

        if not re.fullmatch(
            r"[a-z0-9]+(?:-[a-z0-9]+)*",
            normalized,
        ):
            raise ValueError(
                "Offer code must use lowercase "
                "letters, numbers, and hyphens"
            )

        return normalized

    @field_validator("name")
    @classmethod
    def validate_name(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Offer name is required"
            )

        return normalized

    @field_validator("description")
    @classmethod
    def normalize_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        return normalized or None

    @field_validator("currency")
    @classmethod
    def validate_offer_currency(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip().upper()

        if (
            len(normalized) != 3
            or not normalized.isalpha()
        ):
            raise ValueError(
                "Currency must be a "
                "three-letter code"
            )

        return normalized

    @field_validator(
        "minimum_amount_cents",
        "maximum_amount_cents",
    )
    @classmethod
    def validate_amount(
        cls,
        value: int,
    ) -> int:
        if value < 0:
            raise ValueError(
                "Offer amounts cannot be negative"
            )

        return value

    @field_validator("service_period_days")
    @classmethod
    def validate_service_period(
        cls,
        value: int | None,
    ) -> int | None:
        if (
            value is not None
            and value <= 0
        ):
            raise ValueError(
                "Service period must be positive"
            )

        return value

    @model_validator(mode="after")
    def validate_price_structure(
        self,
    ):
        if (
            self.minimum_amount_cents
            > self.maximum_amount_cents
        ):
            raise ValueError(
                "Minimum amount cannot exceed "
                "maximum amount"
            )

        if (
            self.charge_type == "subscription"
            and self.billing_interval is None
        ):
            raise ValueError(
                "Subscription offers require "
                "a billing interval"
            )

        if (
            self.charge_type != "subscription"
            and self.billing_interval is not None
        ):
            raise ValueError(
                "Only subscription offers can "
                "have a billing interval"
            )

        return self


class BillingAccountUpdate(BaseModel):
    billing_mode: Literal[
        "subscription",
        "fixed_scope",
        "manual",
    ]
    provider: Literal["manual"] = "manual"
    status: Literal[
        "pending",
        "active",
        "past_due",
        "canceled",
    ]
    currency: str = "USD"
    provider_customer_id: str | None = None
    provider_subscription_id: str | None = None

    @field_validator("currency")
    @classmethod
    def validate_currency(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip().upper()

        if (
            len(normalized) != 3
            or not normalized.isalpha()
        ):
            raise ValueError(
                "Currency must be a "
                "three-letter code"
            )

        return normalized

    @field_validator(
        "provider_customer_id",
        "provider_subscription_id",
    )
    @classmethod
    def normalize_provider_identifier(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        return normalized or None


def billing_offer_data(
    offer: BillingOffer,
) -> dict:
    return {
        "id": offer.id,
        "product_id": offer.product_id,
        "code": offer.code,
        "name": offer.name,
        "description": offer.description,
        "status": offer.status,
        "charge_type": offer.charge_type,
        "currency": offer.currency,
        "minimum_amount_cents":
            offer.minimum_amount_cents,
        "maximum_amount_cents":
            offer.maximum_amount_cents,
        "billing_interval":
            offer.billing_interval,
        "service_period_days":
            offer.service_period_days,
        "created_at": (
            offer.created_at.isoformat()
            if offer.created_at
            else None
        ),
        "updated_at": (
            offer.updated_at.isoformat()
            if offer.updated_at
            else None
        ),
    }


def billing_account_data(
    account: BillingAccount | None,
) -> dict | None:
    if account is None:
        return None

    return {
        "id": account.id,
        "tenant_id": account.tenant_id,
        "billing_mode": account.billing_mode,
        "provider": account.provider,
        "status": account.status,
        "currency": account.currency,
        "provider_customer_id":
            account.provider_customer_id,
        "provider_subscription_id":
            account.provider_subscription_id,
        "created_at": (
            account.created_at.isoformat()
            if account.created_at
            else None
        ),
        "updated_at": (
            account.updated_at.isoformat()
            if account.updated_at
            else None
        ),
    }


@router.get("/billing/offers")
def admin_billing_offer_directory(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_operator),
):
    rows = db.execute(
        select(
            BillingOffer,
            Product,
        )
        .join(
            Product,
            Product.id
            == BillingOffer.product_id,
        )
        .order_by(
            Product.name,
            BillingOffer.status,
            BillingOffer.name,
            BillingOffer.id,
        )
    ).all()

    offers = [
        offer
        for offer, _ in rows
    ]

    return {
        "counts": {
            "offers": len(offers),
            "draft": sum(
                offer.status == "draft"
                for offer in offers
            ),
            "active": sum(
                offer.status == "active"
                for offer in offers
            ),
            "archived": sum(
                offer.status == "archived"
                for offer in offers
            ),
        },
        "offers": [
            {
                **billing_offer_data(offer),
                "product": {
                    "id": product.id,
                    "name": product.name,
                    "slug": product.slug,
                },
            }
            for offer, product in rows
        ],
    }


@router.post(
    "/billing/offers",
    status_code=status.HTTP_201_CREATED,
)
def admin_create_billing_offer(
    payload: BillingOfferWrite,
    db: Session = Depends(get_db),
    operator: User = Depends(
        get_current_operator
    ),
):
    product = db.get(
        Product,
        payload.product_id,
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    existing = db.scalar(
        select(BillingOffer).where(
            BillingOffer.product_id
            == product.id,
            BillingOffer.code
            == payload.code,
        )
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Offer code already exists "
                "for this product"
            ),
        )

    offer = BillingOffer(
        product_id=product.id,
        code=payload.code,
        name=payload.name,
        description=payload.description,
        status=payload.status,
        charge_type=payload.charge_type,
        currency=payload.currency,
        minimum_amount_cents=(
            payload.minimum_amount_cents
        ),
        maximum_amount_cents=(
            payload.maximum_amount_cents
        ),
        billing_interval=(
            payload.billing_interval
        ),
        service_period_days=(
            payload.service_period_days
        ),
    )

    db.add(offer)
    db.flush()

    after_data = billing_offer_data(
        offer
    )

    add_admin_audit(
        db,
        operator_user_id=operator.id,
        action="billing_offer.created",
        target_type="billing_offer",
        target_id=offer.id,
        before_data=None,
        after_data=after_data,
    )

    db.commit()
    db.refresh(offer)

    return billing_offer_data(offer)


@router.put(
    "/billing/offers/{offer_id}"
)
def admin_update_billing_offer(
    offer_id: int,
    payload: BillingOfferWrite,
    db: Session = Depends(get_db),
    operator: User = Depends(
        get_current_operator
    ),
):
    offer = db.get(
        BillingOffer,
        offer_id,
    )

    if offer is None:
        raise HTTPException(
            status_code=404,
            detail="Billing offer not found",
        )

    if payload.product_id != offer.product_id:
        raise HTTPException(
            status_code=409,
            detail=(
                "Billing offers cannot be moved "
                "between products"
            ),
        )

    duplicate = db.scalar(
        select(BillingOffer).where(
            BillingOffer.product_id
            == offer.product_id,
            BillingOffer.code
            == payload.code,
            BillingOffer.id
            != offer.id,
        )
    )

    if duplicate is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Offer code already exists "
                "for this product"
            ),
        )

    requested_data = {
        "code": payload.code,
        "name": payload.name,
        "description": payload.description,
        "status": payload.status,
        "charge_type": payload.charge_type,
        "currency": payload.currency,
        "minimum_amount_cents":
            payload.minimum_amount_cents,
        "maximum_amount_cents":
            payload.maximum_amount_cents,
        "billing_interval":
            payload.billing_interval,
        "service_period_days":
            payload.service_period_days,
    }

    if all(
        getattr(offer, field) == value
        for field, value
        in requested_data.items()
    ):
        return billing_offer_data(offer)

    before_data = billing_offer_data(
        offer
    )

    for field, value in requested_data.items():
        setattr(
            offer,
            field,
            value,
        )

    db.flush()

    after_data = billing_offer_data(
        offer
    )

    add_admin_audit(
        db,
        operator_user_id=operator.id,
        action="billing_offer.updated",
        target_type="billing_offer",
        target_id=offer.id,
        before_data=before_data,
        after_data=after_data,
    )

    db.commit()
    db.refresh(offer)

    return billing_offer_data(offer)


@router.get("/billing")
def admin_billing_directory(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_operator),
):
    rows = db.execute(
        select(
            Tenant,
            Product,
            BillingAccount,
        )
        .join(
            Product,
            Product.id == Tenant.product_id,
        )
        .outerjoin(
            BillingAccount,
            BillingAccount.tenant_id
            == Tenant.id,
        )
        .order_by(
            Product.name,
            Tenant.client_number,
            Tenant.id,
        )
    ).all()

    billable_accounts = [
        account
        for tenant, _, account in rows
        if (
            tenant.client_number is not None
            and account is not None
        )
    ]

    client_count = sum(
        tenant.client_number is not None
        for tenant, _, _ in rows
    )

    status_counts = {
        billing_status: sum(
            account.status == billing_status
            for account in billable_accounts
        )
        for billing_status in (
            "pending",
            "active",
            "past_due",
            "canceled",
        )
    }

    return {
        "counts": {
            "tenants": len(rows),
            "clients": client_count,
            "validation_workspaces": sum(
                tenant.client_number is None
                for tenant, _, _ in rows
            ),
            "configured":
                len(billable_accounts),
            "unconfigured": (
                client_count
                - len(billable_accounts)
            ),
            **status_counts,
        },
        "accounts": [
            {
                "tenant": {
                    "id": tenant.id,
                    "client_number":
                        tenant.client_number,
                    "name": tenant.name,
                    "slug": tenant.slug,
                    "status": tenant.status,
                },
                "product": {
                    "id": product.id,
                    "name": product.name,
                    "slug": product.slug,
                },
                "access_kind": (
                    "client"
                    if tenant.client_number
                    is not None
                    else "validation_workspace"
                ),
                "billing_account":
                    billing_account_data(
                        account
                    ),
            }
            for tenant, product, account
            in rows
        ],
    }


@router.put(
    "/tenants/{tenant_id}/billing"
)
def admin_update_tenant_billing(
    tenant_id: int,
    payload: BillingAccountUpdate,
    db: Session = Depends(get_db),
    operator: User = Depends(get_current_operator),
):
    tenant = db.get(Tenant, tenant_id)

    if tenant is None:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    if tenant.client_number is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Validation workspaces "
                "cannot have billing accounts"
            ),
        )

    account = db.scalar(
        select(BillingAccount).where(
            BillingAccount.tenant_id
            == tenant.id
        )
    )

    requested_data = {
        "billing_mode":
            payload.billing_mode,
        "provider":
            payload.provider,
        "status":
            payload.status,
        "currency":
            payload.currency,
        "provider_customer_id":
            payload.provider_customer_id,
        "provider_subscription_id":
            payload.provider_subscription_id,
    }

    if (
        account is not None
        and all(
            getattr(account, field) == value
            for field, value
            in requested_data.items()
        )
    ):
        return billing_account_data(account)

    before_data = billing_account_data(
        account
    )

    if account is None:
        account = BillingAccount(
            tenant_id=tenant.id,
            billing_mode=payload.billing_mode,
            provider=payload.provider,
            status=payload.status,
            currency=payload.currency,
            provider_customer_id=(
                payload.provider_customer_id
            ),
            provider_subscription_id=(
                payload.provider_subscription_id
            ),
        )

        db.add(account)
        db.flush()
        audit_action = (
            "billing_account.created"
        )
    else:
        account.billing_mode = (
            payload.billing_mode
        )
        account.provider = payload.provider
        account.status = payload.status
        account.currency = payload.currency
        account.provider_customer_id = (
            payload.provider_customer_id
        )
        account.provider_subscription_id = (
            payload.provider_subscription_id
        )
        db.flush()
        audit_action = (
            "billing_account.updated"
        )

    after_data = billing_account_data(
        account
    )

    add_admin_audit(
        db,
        operator_user_id=operator.id,
        action=audit_action,
        target_type="billing_account",
        target_id=account.id,
        tenant_id=tenant.id,
        before_data=before_data,
        after_data=after_data,
    )

    db.commit()
    db.refresh(account)

    return billing_account_data(account)


@router.put(
    "/tenants/{tenant_id}/timezone"
)
def admin_update_tenant_timezone(
    tenant_id: int,
    payload: TenantTimezoneUpdate,
    db: Session = Depends(get_db),
    operator: User = Depends(get_current_operator),
):
    tenant = db.get(Tenant, tenant_id)

    if tenant is None:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    before_timezone = tenant.timezone_name
    tenant.timezone_name = payload.timezone_name

    if before_timezone != tenant.timezone_name:
        add_admin_audit(
            db,
            operator_user_id=operator.id,
            action="tenant.timezone_updated",
            target_type="tenant",
            target_id=tenant.id,
            tenant_id=tenant.id,
            before_data={
                "timezone_name": before_timezone,
            },
            after_data={
                "timezone_name":
                    tenant.timezone_name,
            },
        )

    db.commit()
    db.refresh(tenant)

    return {
        "id": tenant.id,
        "timezone_name": tenant.timezone_name,
    }


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
