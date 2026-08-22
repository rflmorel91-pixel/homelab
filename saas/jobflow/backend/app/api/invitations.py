from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.admin import add_admin_audit
from app.database import get_db
from app.models import (
    Lead,
    Product,
    User,
    UserInvitation,
)
from app.operator_context import get_current_operator
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

    user = User(
        email=invitation.email,
        display_name=invitation.display_name,
        password_hash=hash_password(payload.password),
        is_active=True,
        is_platform_admin=False,
    )
    db.add(user)
    db.flush()

    invitation.accepted_user_id = user.id
    invitation.accepted_at = now

    db.commit()
    db.refresh(user)

    return {
        "status": "activated",
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
        },
    }
