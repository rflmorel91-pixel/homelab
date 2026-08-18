from fastapi import Cookie, Header, HTTPException
import jwt

from app.security import decode_access_token


def get_current_user_id(
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

    if authorization is not None:
        scheme, _, bearer_token = authorization.partition(" ")

        if scheme.lower() == "bearer" and bearer_token:
            token = bearer_token

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    try:
        return decode_access_token(token)
    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )
