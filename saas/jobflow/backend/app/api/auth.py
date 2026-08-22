from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth_context import get_current_user_id
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


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


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
            User.email == credentials.email,
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

    token = create_access_token(user.id)

    response.set_cookie(
        key="jobflow_access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=30 * 60,
        path="/",
    )

    return LoginResponse(
        access_token=token,
    )



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
def logout(response: Response):
    response.delete_cookie(
        key="jobflow_access_token",
        path="/",
        secure=True,
        httponly=True,
        samesite="strict",
    )

    return {"status": "signed_out"}
