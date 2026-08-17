from fastapi import Header, HTTPException
import jwt

from app.security import decode_access_token


def get_current_user_id(
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
) -> int:
    if authorization is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not token:
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
