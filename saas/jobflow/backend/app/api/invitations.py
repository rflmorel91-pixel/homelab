from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.admin import add_admin_audit
from app.database import get_db
from app.tenant_context import (
    get_current_tenant,
    require_current_tenant_owner,
)
from app.models import (
    Lead,
    Product,
    Tenant,
    TenantMembership,
    User,
    UserInvitation,
)
from app.operator_context import get_current_operator
from app.platform import get_product
from app.security import (
    create_invitation_token,
    hash_invitation_token,
    hash_password,
)


INVITATION_LIFETIME_HOURS = 72


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class InvitationCreate(BaseModel):
    lead_id: int = Field(
        gt=0,
    )


class ClientInvitationCreate(BaseModel):
    display_name: str = Field(
        min_length=1,
        max_length=200,
    )
    email: str = Field(
        min_length=3,
        max_length=320,
    )
    role: Literal["owner", "member"] = "member"

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Display name is required"
            )

        return normalized

    @field_validator("email")
    @classmethod
    def normalize_email(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip().lower()

        if (
            "@" not in normalized
            or normalized.startswith("@")
            or normalized.endswith("@")
        ):
            raise ValueError(
                "A valid email is required"
            )

        return normalized


class InvitationAccept(BaseModel):
    token: str = Field(
        min_length=32,
        max_length=256,
    )
    password: str = Field(
        min_length=12,
        max_length=128,
    )


admin_router = APIRouter(
    prefix="/admin/user-invitations",
    tags=["Administration"],
)


client_admin_router = APIRouter(
    prefix="/admin/tenants",
    tags=["Administration"],
)


client_owner_router = APIRouter(
    prefix="/client",
    tags=["Client Team"],
)


public_router = APIRouter(
    prefix="/auth/invitations",
    tags=["auth"],
)


@admin_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
def create_user_invitation(
    payload: InvitationCreate,
    response: Response,
    db: Session = Depends(get_db),
    operator: User = Depends(get_current_operator),
):
    response.headers["Cache-Control"] = "no-store"

    lead = db.get(
        Lead,
        payload.lead_id,
    )

    if lead is None:
        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    if (
        lead.status != "qualified"
        or lead.converted_tenant_id is not None
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Invitation requires a qualified, "
                "unprovisioned lead"
            ),
        )

    product = db.get(
        Product,
        lead.product_id,
    )

    if product is None:
        raise HTTPException(
            status_code=500,
            detail="Lead product is unavailable",
        )

    email = lead.email.strip().lower()
    display_name = lead.contact_name.strip()

    existing_user = db.scalar(
        select(User).where(
            func.lower(User.email) == email,
        )
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=409,
            detail="A user with this email already exists",
        )

    now = utc_now_naive()

    active_invitation = db.scalar(
        select(UserInvitation).where(
            UserInvitation.lead_id == lead.id,
            UserInvitation.accepted_at.is_(None),
            UserInvitation.revoked_at.is_(None),
            UserInvitation.expires_at > now,
        )
    )

    if active_invitation is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "An active invitation already exists "
                "for this lead"
            ),
        )

    token, token_hash = create_invitation_token()

    invitation = UserInvitation(
        lead_id=lead.id,
        email=email,
        display_name=display_name,
        token_hash=token_hash,
        created_by_user_id=operator.id,
        expires_at=(
            now + timedelta(
                hours=INVITATION_LIFETIME_HOURS,
            )
        ),
    )
    db.add(invitation)
    db.flush()

    add_admin_audit(
        db,
        operator_user_id=operator.id,
        action="user.invitation_created",
        target_type="user_invitation",
        target_id=invitation.id,
        after_data={
            "lead_id": lead.id,
            "product_id": product.id,
            "product_slug": product.slug,
            "email": invitation.email,
            "display_name": invitation.display_name,
            "expires_at": invitation.expires_at.isoformat(),
        },
    )

    db.commit()
    db.refresh(invitation)

    return {
        "id": invitation.id,
        "lead": {
            "id": lead.id,
            "business_name": lead.business_name,
        },
        "product": {
            "id": product.id,
            "name": product.name,
            "slug": product.slug,
        },
        "email": invitation.email,
        "display_name": invitation.display_name,
        "expires_at": invitation.expires_at,
        "activation_path": (
            f"/accept-invitation#token={token}"
        ),
    }


@client_admin_router.post(
    "/{tenant_id}/user-invitations",
    status_code=status.HTTP_201_CREATED,
)
def create_client_user_invitation(
    tenant_id: int,
    payload: ClientInvitationCreate,
    response: Response,
    db: Session = Depends(get_db),
    operator: User = Depends(get_current_operator),
):
    response.headers["Cache-Control"] = "no-store"

    tenant = db.get(
        Tenant,
        tenant_id,
    )

    if tenant is None:
        raise HTTPException(
            status_code=404,
            detail="Client not found",
        )

    if tenant.client_number is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Client invitations require a "
                "commercial client workspace"
            ),
        )

    if tenant.status != "active":
        raise HTTPException(
            status_code=409,
            detail="Client must be active",
        )

    product = db.get(
        Product,
        tenant.product_id,
    )

    definition = (
        get_product(product.slug)
        if product is not None
        else None
    )

    if product is None or definition is None:
        raise HTTPException(
            status_code=500,
            detail="Client product is unavailable",
        )

    existing_user = db.scalar(
        select(User).where(
            func.lower(User.email)
            == payload.email,
        )
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "A platform user with this email "
                "already exists"
            ),
        )

    now = utc_now_naive()

    active_invitation = db.scalar(
        select(UserInvitation).where(
            UserInvitation.tenant_id == tenant.id,
            func.lower(UserInvitation.email)
            == payload.email,
            UserInvitation.accepted_at.is_(None),
            UserInvitation.revoked_at.is_(None),
            UserInvitation.expires_at > now,
        )
    )

    if active_invitation is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "An active invitation already exists "
                "for this client and email"
            ),
        )

    token, token_hash = create_invitation_token()

    invitation = UserInvitation(
        lead_id=None,
        tenant_id=tenant.id,
        role=payload.role,
        email=payload.email,
        display_name=payload.display_name,
        token_hash=token_hash,
        created_by_user_id=operator.id,
        expires_at=(
            now + timedelta(
                hours=INVITATION_LIFETIME_HOURS,
            )
        ),
    )
    db.add(invitation)
    db.flush()

    add_admin_audit(
        db,
        operator_user_id=operator.id,
        action="client_user.invitation_created",
        target_type="user_invitation",
        target_id=invitation.id,
        tenant_id=tenant.id,
        after_data={
            "product_id": product.id,
            "product_slug": product.slug,
            "client_number": tenant.client_number,
            "email": invitation.email,
            "display_name": invitation.display_name,
            "role": invitation.role,
            "expires_at":
                invitation.expires_at.isoformat(),
        },
    )

    db.commit()
    db.refresh(invitation)

    return {
        "id": invitation.id,
        "product": {
            "id": product.id,
            "name": product.name,
            "slug": product.slug,
        },
        "client": {
            "id": tenant.id,
            "client_number": tenant.client_number,
            "name": tenant.name,
            "slug": tenant.slug,
        },
        "email": invitation.email,
        "display_name": invitation.display_name,
        "role": invitation.role,
        "expires_at": invitation.expires_at,
        "activation_path": (
            f"/accept-invitation#token={token}"
        ),
    }


def client_invitation_status(
    invitation: UserInvitation,
    now: datetime,
) -> str:
    if invitation.accepted_at is not None:
        return "accepted"

    if invitation.revoked_at is not None:
        return "revoked"

    if invitation.expires_at <= now:
        return "expired"

    return "pending"


@client_admin_router.get(
    "/{tenant_id}/user-invitations",
)
def list_client_user_invitations(
    tenant_id: int,
    response: Response,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_operator),
):
    response.headers["Cache-Control"] = "no-store"

    tenant = db.get(
        Tenant,
        tenant_id,
    )

    if tenant is None:
        raise HTTPException(
            status_code=404,
            detail="Client not found",
        )

    if tenant.client_number is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Client invitations require a "
                "commercial client workspace"
            ),
        )

    invitations = db.scalars(
        select(UserInvitation)
        .where(
            UserInvitation.tenant_id == tenant.id,
        )
        .order_by(
            UserInvitation.created_at.desc(),
            UserInvitation.id.desc(),
        )
    ).all()

    now = utc_now_naive()

    return {
        "client": {
            "id": tenant.id,
            "client_number": tenant.client_number,
            "name": tenant.name,
            "slug": tenant.slug,
        },
        "invitations": [
            {
                "id": invitation.id,
                "email": invitation.email,
                "display_name":
                    invitation.display_name,
                "role": invitation.role,
                "status":
                    client_invitation_status(
                        invitation,
                        now,
                    ),
                "created_at": invitation.created_at,
                "expires_at": invitation.expires_at,
                "accepted_at": invitation.accepted_at,
                "revoked_at": invitation.revoked_at,
            }
            for invitation in invitations
        ],
    }


@client_admin_router.post(
    "/{tenant_id}/user-invitations/"
    "{invitation_id}/revoke",
)
def revoke_client_user_invitation(
    tenant_id: int,
    invitation_id: int,
    response: Response,
    db: Session = Depends(get_db),
    operator: User = Depends(get_current_operator),
):
    response.headers["Cache-Control"] = "no-store"

    tenant = db.get(
        Tenant,
        tenant_id,
    )

    if (
        tenant is None
        or tenant.client_number is None
    ):
        raise HTTPException(
            status_code=404,
            detail="Client not found",
        )

    invitation = db.scalar(
        select(UserInvitation)
        .where(
            UserInvitation.id == invitation_id,
            UserInvitation.tenant_id == tenant.id,
        )
        .with_for_update()
    )

    if invitation is None:
        raise HTTPException(
            status_code=404,
            detail="Client invitation not found",
        )

    now = utc_now_naive()
    current_status = client_invitation_status(
        invitation,
        now,
    )

    if current_status != "pending":
        raise HTTPException(
            status_code=409,
            detail=(
                "Only pending client invitations "
                "can be revoked"
            ),
        )

    invitation.revoked_at = now

    add_admin_audit(
        db,
        operator_user_id=operator.id,
        action="client_user.invitation_revoked",
        target_type="user_invitation",
        target_id=invitation.id,
        tenant_id=tenant.id,
        before_data={
            "status": "pending",
        },
        after_data={
            "status": "revoked",
            "email": invitation.email,
            "role": invitation.role,
            "client_number": tenant.client_number,
            "revoked_at":
                invitation.revoked_at.isoformat(),
        },
    )

    db.commit()
    db.refresh(invitation)

    return {
        "id": invitation.id,
        "status": "revoked",
        "revoked_at": invitation.revoked_at,
    }


@client_owner_router.get("/team")
def get_current_client_team(
    response: Response,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    _: TenantMembership = Depends(
        require_current_tenant_owner
    ),
):
    response.headers["Cache-Control"] = "no-store"

    rows = db.execute(
        select(
            TenantMembership,
            User,
        )
        .join(
            User,
            User.id == TenantMembership.user_id,
        )
        .where(
            TenantMembership.tenant_id == tenant.id,
        )
        .order_by(
            TenantMembership.role.desc(),
            User.display_name,
            User.id,
        )
    ).all()

    return {
        "client": {
            "id": tenant.id,
            "client_number": tenant.client_number,
            "name": tenant.name,
            "slug": tenant.slug,
        },
        "members": [
            {
                "membership_id": membership.id,
                "user_id": user.id,
                "display_name": user.display_name,
                "email": user.email,
                "role": membership.role,
                "is_active": user.is_active,
            }
            for membership, user in rows
        ],
    }


@client_owner_router.post(
    "/user-invitations",
    status_code=status.HTTP_201_CREATED,
)
def create_current_client_user_invitation(
    payload: ClientInvitationCreate,
    response: Response,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    membership: TenantMembership = Depends(
        require_current_tenant_owner
    ),
):
    operator = db.get(
        User,
        membership.user_id,
    )

    if operator is None or not operator.is_active:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    return create_client_user_invitation(
        tenant_id=tenant.id,
        payload=payload,
        response=response,
        db=db,
        operator=operator,
    )


@client_owner_router.get(
    "/user-invitations",
)
def list_current_client_user_invitations(
    response: Response,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    _: TenantMembership = Depends(
        require_current_tenant_owner
    ),
):
    operator = db.get(
        User,
        _.user_id,
    )

    if operator is None or not operator.is_active:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    return list_client_user_invitations(
        tenant_id=tenant.id,
        response=response,
        db=db,
        _=operator,
    )


@client_owner_router.post(
    "/user-invitations/{invitation_id}/revoke",
)
def revoke_current_client_user_invitation(
    invitation_id: int,
    response: Response,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    membership: TenantMembership = Depends(
        require_current_tenant_owner
    ),
):
    operator = db.get(
        User,
        membership.user_id,
    )

    if operator is None or not operator.is_active:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    return revoke_client_user_invitation(
        tenant_id=tenant.id,
        invitation_id=invitation_id,
        response=response,
        db=db,
        operator=operator,
    )


@public_router.post("/accept")
def accept_user_invitation(
    payload: InvitationAccept,
    response: Response,
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store"

    invitation = db.scalar(
        select(UserInvitation)
        .where(
            UserInvitation.token_hash
            == hash_invitation_token(payload.token)
        )
        .with_for_update()
    )

    now = utc_now_naive()

    if (
        invitation is None
        or invitation.accepted_at is not None
        or invitation.revoked_at is not None
        or invitation.expires_at <= now
    ):
        raise HTTPException(
            status_code=400,
            detail="Invitation is invalid or expired",
        )

    existing_user = db.scalar(
        select(User).where(
            func.lower(User.email) == invitation.email,
        )
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=409,
            detail="A user with this email already exists",
        )

    lead = None
    tenant = None

    if invitation.lead_id is not None:
        lead = db.get(
            Lead,
            invitation.lead_id,
        )

        if lead is None:
            raise HTTPException(
                status_code=400,
                detail="Invitation lead is unavailable",
            )

        product = db.get(
            Product,
            lead.product_id,
        )

    elif (
        invitation.tenant_id is not None
        and invitation.role in {"owner", "member"}
    ):
        tenant = db.get(
            Tenant,
            invitation.tenant_id,
        )

        if (
            tenant is None
            or tenant.client_number is None
        ):
            raise HTTPException(
                status_code=400,
                detail="Invitation client is unavailable",
            )

        if tenant.status != "active":
            raise HTTPException(
                status_code=409,
                detail="Invitation client is not active",
            )

        product = db.get(
            Product,
            tenant.product_id,
        )

    else:
        raise HTTPException(
            status_code=400,
            detail="Invitation target is unavailable",
        )

    definition = (
        get_product(product.slug)
        if product is not None
        else None
    )

    if product is None or definition is None:
        raise HTTPException(
            status_code=400,
            detail="Invitation product is unavailable",
        )

    user = User(
        email=invitation.email,
        display_name=invitation.display_name,
        password_hash=hash_password(payload.password),
        is_active=True,
        is_platform_admin=False,
    )
    db.add(user)
    db.flush()

    membership = None

    if tenant is not None:
        membership = TenantMembership(
            tenant_id=tenant.id,
            user_id=user.id,
            role=invitation.role,
        )
        db.add(membership)
        db.flush()

        add_admin_audit(
            db,
            operator_user_id=invitation.created_by_user_id,
            action="client_user.invitation_accepted",
            target_type="membership",
            target_id=membership.id,
            tenant_id=tenant.id,
            after_data={
                "invitation_id": invitation.id,
                "user_id": user.id,
                "role": membership.role,
                "product_id": product.id,
                "product_slug": product.slug,
                "client_number": tenant.client_number,
            },
        )

    invitation.accepted_user_id = user.id
    invitation.accepted_at = now

    db.commit()
    db.refresh(user)

    return {
        "status": "activated",
        "product": {
            "id": product.id,
            "name": product.name,
            "slug": product.slug,
            "landing_route": definition.landing_route,
            "workspace_route": definition.workspace_route,
        },
        "client": (
            {
                "id": tenant.id,
                "client_number": tenant.client_number,
                "name": tenant.name,
                "slug": tenant.slug,
                "role": membership.role,
            }
            if tenant is not None
            and membership is not None
            else None
        ),
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
        },
    }
