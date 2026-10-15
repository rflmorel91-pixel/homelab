from fastapi import Cookie, Header, HTTPException, Response
import jwt

from app.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    decode_access_token,
)


def get_current_user_id(
    response: Response,
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
    jobflow_access_token: str | None = Cookie(
        default=None,
        alias="jobflow_access_token",
    ),
) -> int:
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
        user_id = decode_access_token(token)
    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    if cookie_authenticated:
        response.set_cookie(
            key="jobflow_access_token",
            value=create_access_token(user_id),
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            path="/",
        )

    return user_id
