from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    AdminAuditLog,
    Lead,
    Tenant,
    TenantMembership,
    User,
)
from app.operator_context import get_current_operator
from app.schemas.lead import (
    LeadProvisionRead,
    LeadProvisionRequest,
    LeadProvisioningOptionsRead,
    LeadRead,
    LeadUpdate,
)


LEAD_STATUS_TRANSITIONS = {
    "new": {"contacted"},
    "contacted": {"qualified", "closed"},
    "qualified": {"closed"},
    "converted": set(),
    "closed": set(),
}


router = APIRouter(
    prefix="/leads",
    tags=["Leads"],
)


@router.get(
    "/provisioning-options",
    response_model=LeadProvisioningOptionsRead,
)
def lead_provisioning_options(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_operator),
):
    users = db.scalars(
        select(User)
        .where(User.is_active.is_(True))
        .order_by(
            User.display_name,
            User.email,
            User.id,
        )
    ).all()

    return {
        "owners": [
            {
                "user_id": user.id,
                "email": user.email,
                "display_name": user.display_name,
            }
            for user in users
        ],
    }


@router.get(
    "/",
    response_model=list[LeadRead],
)
def list_leads(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_operator),
):
    result = db.execute(
        select(Lead)
        .order_by(
            Lead.created_at.desc(),
            Lead.id.desc(),
        )
    )

    return result.scalars().all()


@router.put(
    "/{lead_id}",
    response_model=LeadRead,
)
def update_lead(
    lead_id: int,
    lead: LeadUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_operator),
):
    db_lead = db.get(Lead, lead_id)

    if db_lead is None:
        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    if lead.status != db_lead.status:
        allowed_statuses = LEAD_STATUS_TRANSITIONS.get(
            db_lead.status,
            set(),
        )

        if lead.status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid lead status transition: "
                    f"{db_lead.status} -> {lead.status}"
                ),
            )

    db_lead.status = lead.status

    db.commit()
    db.refresh(db_lead)

    return db_lead


@router.post(
    "/{lead_id}/provision",
    response_model=LeadProvisionRead,
    status_code=status.HTTP_201_CREATED,
)
def provision_lead(
    lead_id: int,
    payload: LeadProvisionRequest,
    db: Session = Depends(get_db),
    operator: User = Depends(get_current_operator),
):
    lead = db.get(Lead, lead_id)

    if lead is None:
        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    if (
        lead.converted_tenant_id is not None
        or lead.status == "converted"
    ):
        raise HTTPException(
            status_code=409,
            detail="Lead has already been provisioned",
        )

    if lead.status != "qualified":
        raise HTTPException(
            status_code=409,
            detail="Lead must be qualified before provisioning",
        )

    owner = db.get(User, payload.owner_user_id)

    if owner is None:
        raise HTTPException(
            status_code=404,
            detail="Owner user not found",
        )

    if not owner.is_active:
        raise HTTPException(
            status_code=409,
            detail="Owner user must be active",
        )

    existing_tenant = db.scalar(
        select(Tenant).where(
            Tenant.slug == payload.tenant_slug
        )
    )

    if existing_tenant is not None:
        raise HTTPException(
            status_code=409,
            detail="Tenant slug already exists",
        )

    converted_at = datetime.now(timezone.utc)

    try:
        tenant = Tenant(
            name=lead.business_name,
            slug=payload.tenant_slug,
            status="active",
        )
        db.add(tenant)
        db.flush()

        membership = TenantMembership(
            tenant_id=tenant.id,
            user_id=owner.id,
            role="owner",
        )
        db.add(membership)

        lead.status = "converted"
        lead.converted_tenant_id = tenant.id
        lead.converted_at = converted_at

        db.add(
            AdminAuditLog(
                operator_user_id=operator.id,
                action="tenant.provisioned",
                target_type="tenant",
                target_id=tenant.id,
                tenant_id=tenant.id,
                before_data=None,
                after_data={
                    "lead_id": lead.id,
                    "owner_user_id": owner.id,
                    "tenant_name": tenant.name,
                    "tenant_slug": tenant.slug,
                    "status": tenant.status,
                },
            )
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    db.refresh(tenant)
    db.refresh(lead)

    return {
        "lead_id": lead.id,
        "status": lead.status,
        "converted_at": lead.converted_at,
        "tenant": {
            "id": tenant.id,
            "name": tenant.name,
            "slug": tenant.slug,
            "status": tenant.status,
        },
        "owner": {
            "user_id": owner.id,
            "email": owner.email,
            "display_name": owner.display_name,
            "role": "owner",
        },
    }


@router.post(
    "/{lead_id}/reopen-conversion",
    response_model=LeadRead,
)
def reopen_legacy_conversion(
    lead_id: int,
    db: Session = Depends(get_db),
    operator: User = Depends(get_current_operator),
):
    lead = db.get(Lead, lead_id)

    if lead is None:
        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    if lead.status != "converted":
        raise HTTPException(
            status_code=409,
            detail="Lead is not converted",
        )

    if (
        lead.converted_tenant_id is not None
        or lead.converted_at is not None
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Provisioned lead conversion "
                "cannot be reopened"
            ),
        )

    before_data = {
        "status": lead.status,
        "converted_tenant_id":
            lead.converted_tenant_id,
        "converted_at": lead.converted_at,
    }

    lead.status = "qualified"

    db.add(
        AdminAuditLog(
            operator_user_id=operator.id,
            action="lead.legacy_conversion_reopened",
            target_type="lead",
            target_id=lead.id,
            tenant_id=None,
            before_data=before_data,
            after_data={
                "status": "qualified",
            },
        )
    )

    db.commit()
    db.refresh(lead)

    return lead
