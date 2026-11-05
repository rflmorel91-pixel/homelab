from fastapi import Cookie, Depends, Header, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
import jwt

from app.security import (
    create_access_token,
    decode_access_token_session,
    session_cookie_max_age,
)


def authenticate_user(
    *,
    authorization: str | None,
    jobflow_access_token: str | None,
    db: Session,
) -> tuple[User, int, bool]:
    token = jobflow_access_token
    cookie_authenticated = token is not None

    if authorization is not None:
        scheme, _, bearer_token = authorization.partition(" ")

        if scheme.lower() == "bearer" and bearer_token:
            token = bearer_token
            cookie_authenticated = False

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    try:
        user_id, session_version, authenticated_at = decode_access_token_session(token)
    except (jwt.InvalidTokenError, ValueError, KeyError, TypeError, OverflowError):
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    user = db.get(User, user_id)
    if (
        user is None
        or not user.is_active
        or user.session_version != session_version
    ):
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    return user, authenticated_at, cookie_authenticated


def get_current_user_id(
    response: Response,
    authorization: str | None = Header(default=None, alias="Authorization"),
    jobflow_access_token: str | None = Cookie(default=None, alias="jobflow_access_token"),
    db: Session = Depends(get_db),
) -> int:
    user, authenticated_at, cookie_authenticated = authenticate_user(
        authorization=authorization,
        jobflow_access_token=jobflow_access_token,
        db=db,
    )

    if cookie_authenticated:
        try:
            renewed_token = create_access_token(
                user.id, user.session_version, authenticated_at=authenticated_at,
            )
        except jwt.InvalidTokenError:
            # The absolute deadline may pass between validation and renewal.
            raise HTTPException(status_code=401, detail="Authentication required")
        response.set_cookie(
            key="jobflow_access_token",
            value=renewed_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=session_cookie_max_age(authenticated_at),
            path="/",
        )

    return user.id
