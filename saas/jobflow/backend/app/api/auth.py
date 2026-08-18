from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
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
