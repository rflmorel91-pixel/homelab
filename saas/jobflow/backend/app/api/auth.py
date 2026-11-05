from typing import Literal

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response
from pydantic import BaseModel, field_validator
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.auth_context import authenticate_user, get_current_user_id
from app.database import get_db
from app.models import (
    Product,
    Tenant,
    TenantMembership,
    User,
)
from app.platform import get_product
from app.security import create_access_token, verify_password


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(
        cls,
        value: str,
    ) -> str:
        return value.strip().lower()


class LoginResponse(BaseModel):
    status: Literal["signed_in"] = "signed_in"


@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    credentials: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(
            func.lower(User.email)
            == credentials.email,
        )
    )

    if (
        user is None
        or not user.is_active
        or user.password_hash is None
        or not verify_password(
            credentials.password,
            user.password_hash,
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    token = create_access_token(user.id, user.session_version)

    response.set_cookie(
        key="jobflow_access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=30 * 60,
        path="/",
    )

    return LoginResponse()



@router.get("/products/{product_slug}/access")
def product_access(
    product_slug: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    product = db.scalar(
        select(Product).where(
            Product.slug == product_slug,
        )
    )

    definition = get_product(product_slug)

    if product is None or definition is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    user = db.get(
        User,
        user_id,
    )

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    rows = db.execute(
        select(
            TenantMembership,
            Tenant,
        )
        .join(
            Tenant,
            Tenant.id == TenantMembership.tenant_id,
        )
        .where(
            TenantMembership.user_id == user.id,
            TenantMembership.is_active.is_(True),
            Tenant.product_id == product.id,
            Tenant.client_number.is_not(None),
        )
        .order_by(
            Tenant.client_number,
            Tenant.id,
        )
    ).all()

    return {
        "product": {
            "id": product.id,
            "name": product.name,
            "slug": product.slug,
            "landing_route": definition.landing_route,
            "workspace_route": definition.workspace_route,
        },
        "clients": [
            {
                "tenant_id": tenant.id,
                "client_number": tenant.client_number,
                "name": tenant.name,
                "slug": tenant.slug,
                "status": tenant.status,
                "role": membership.role,
            }
            for membership, tenant in rows
        ],
    }


@router.post("/logout")
def logout(
    response: Response,
    authorization: str | None = Header(default=None, alias="Authorization"),
    jobflow_access_token: str | None = Cookie(default=None, alias="jobflow_access_token"),
    db: Session = Depends(get_db),
):
    try:
        user, _, _ = authenticate_user(
            authorization=authorization,
            jobflow_access_token=jobflow_access_token,
            db=db,
        )
    except HTTPException as error:
        if error.status_code != 401:
            raise
        # Missing, expired or already revoked sessions still clear the cookie.
    else:
        # Revoke every device atomically. A stale logout cannot revoke a newer
        # generation already created by password reset or another logout.
        db.execute(
            update(User).where(
                User.id == user.id,
                User.session_version == user.session_version,
            ).values(session_version=User.session_version + 1)
        )
        db.commit()

    response.delete_cookie(
        key="jobflow_access_token",
        path="/",
        secure=True,
        httponly=True,
        samesite="strict",
    )

    return {"status": "signed_out"}
