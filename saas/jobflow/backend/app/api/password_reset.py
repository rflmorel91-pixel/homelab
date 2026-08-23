from datetime import datetime, timedelta, timezone
import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    PasswordResetToken,
    Product,
    Tenant,
    TenantMembership,
    User,
)
from app.platform import get_product
from app.platform_email import send_password_reset_email
from app.security import (
    create_invitation_token,
    hash_invitation_token,
    hash_password,
)


logger = logging.getLogger(__name__)

RESET_LIFETIME_MINUTES = 30
RESET_REQUEST_COOLDOWN_SECONDS = 60
GENERIC_RESET_MESSAGE = (
    "If an eligible account exists, "
    "a password reset email has been sent."
)


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class PasswordResetRequest(BaseModel):
    email: str = Field(
        min_length=3,
        max_length=320,
    )
    product_slug: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9-]+$",
    )

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


class PasswordResetConfirm(BaseModel):
    token: str = Field(
        min_length=32,
        max_length=256,
    )
    password: str = Field(
        min_length=12,
        max_length=128,
    )


router = APIRouter(
    prefix="/auth/password-reset",
    tags=["auth"],
)


@router.post("/request")
def request_password_reset(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    generic_response = {
        "status": "accepted",
        "message": GENERIC_RESET_MESSAGE,
    }

    product = db.scalar(
        select(Product).where(
            Product.slug == payload.product_slug,
            Product.status == "active",
        )
    )
    definition = get_product(payload.product_slug)

    user = db.scalar(
        select(User).where(
            func.lower(User.email) == payload.email,
            User.is_active.is_(True),
        )
    )

    if (
        product is None
        or definition is None
        or user is None
    ):
        return generic_response

    membership_id = db.scalar(
        select(TenantMembership.id)
        .join(
            Tenant,
            Tenant.id == TenantMembership.tenant_id,
        )
        .where(
            TenantMembership.user_id == user.id,
            Tenant.product_id == product.id,
            Tenant.client_number.is_not(None),
            Tenant.status == "active",
        )
        .limit(1)
    )

    if membership_id is None:
        return generic_response

    now = utc_now_naive()

    latest_active_token = db.scalar(
        select(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.product_slug
            == product.slug,
            PasswordResetToken.used_at.is_(None),
        )
        .order_by(
            PasswordResetToken.created_at.desc(),
            PasswordResetToken.id.desc(),
        )
        .limit(1)
    )

    if (
        latest_active_token is not None
        and latest_active_token.created_at
        >= now
        - timedelta(
            seconds=RESET_REQUEST_COOLDOWN_SECONDS
        )
    ):
        return generic_response

    active_tokens = db.scalars(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.product_slug
            == product.slug,
            PasswordResetToken.used_at.is_(None),
        )
    ).all()

    for active_token in active_tokens:
        active_token.used_at = now

    token, token_hash = create_invitation_token()

    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        product_slug=product.slug,
        expires_at=(
            now
            + timedelta(
                minutes=RESET_LIFETIME_MINUTES
            )
        ),
    )
    db.add(reset_record)
    db.commit()

    public_base_url = os.getenv(
        "PLATFORM_PUBLIC_BASE_URL",
        "",
    ).rstrip("/")

    if not public_base_url:
        reset_record.used_at = now
        db.commit()

        logger.error(
            "Password reset email was not sent: "
            "PLATFORM_PUBLIC_BASE_URL is missing"
        )

        return generic_response

    reset_url = (
        f"{public_base_url}/reset-password"
        f"#token={token}&product={product.slug}"
    )

    try:
        send_password_reset_email(
            to_email=user.email,
            product_name=product.name,
            reset_url=reset_url,
        )
    except Exception:
        reset_record.used_at = now
        db.commit()

        logger.exception(
            "Password reset email delivery failed"
        )

    return generic_response


@router.post("/confirm")
def confirm_password_reset(
    payload: PasswordResetConfirm,
    response: Response,
    db: Session = Depends(get_db),
):
    now = utc_now_naive()

    reset_record = db.scalar(
        select(PasswordResetToken)
        .where(
            PasswordResetToken.token_hash
            == hash_invitation_token(payload.token)
        )
        .with_for_update()
    )

    if (
        reset_record is None
        or reset_record.used_at is not None
        or reset_record.expires_at <= now
    ):
        raise HTTPException(
            status_code=400,
            detail="Reset link is invalid or expired",
        )

    user = db.get(
        User,
        reset_record.user_id,
    )

    definition = get_product(
        reset_record.product_slug
    )

    if (
        user is None
        or not user.is_active
        or definition is None
    ):
        raise HTTPException(
            status_code=400,
            detail="Reset link is invalid or expired",
        )

    user.password_hash = hash_password(
        payload.password
    )

    unused_tokens = db.scalars(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        )
    ).all()

    for unused_token in unused_tokens:
        unused_token.used_at = now

    db.commit()

    response.delete_cookie(
        key="jobflow_access_token",
        path="/",
        secure=True,
        httponly=True,
        samesite="strict",
    )

    return {
        "status": "password_updated",
        "product": {
            "slug": reset_record.product_slug,
            "workspace_route": (
                definition.workspace_route
            ),
        },
    }
