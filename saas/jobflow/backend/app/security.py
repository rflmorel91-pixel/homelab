from hashlib import sha256
from secrets import token_urlsafe

from pwdlib import PasswordHash


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def hash_invitation_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def create_invitation_token() -> tuple[str, str]:
    token = token_urlsafe(32)

    return token, hash_invitation_token(token)


from datetime import datetime, timezone
import os

import jwt


JWT_SECRET = os.getenv(
    "JWT_SECRET"
)

if not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET environment variable is required"
    )
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ABSOLUTE_SESSION_LIFETIME_SECONDS = 8 * 60 * 60


def create_access_token(
    user_id: int,
    session_version: int = 0,
    *,
    authenticated_at: int | None = None,
) -> str:
    now = int(datetime.now(timezone.utc).timestamp())
    if authenticated_at is None:
        authenticated_at = now
    if (
        type(authenticated_at) is not int
        or authenticated_at < 0
        or authenticated_at > now
        or now >= authenticated_at + ABSOLUTE_SESSION_LIFETIME_SECONDS
    ):
        raise jwt.InvalidTokenError("Invalid authentication time")

    payload = {
        "sub": str(user_id),
        "session_version": session_version,
        "auth_time": authenticated_at,
        "iat": now,
        "exp": min(
            now + ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            authenticated_at + ABSOLUTE_SESSION_LIFETIME_SECONDS,
        ),
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token_session(token: str) -> tuple[int, int, int]:
    payload = jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
        options={"require": ["sub", "iat", "exp"]},
    )

    version = payload.get("session_version", 0)
    if type(version) is not int or version < 0:
        raise jwt.InvalidTokenError("Invalid session version")
    # Existing tokens use their signed issuance time once, then renewal retains it.
    authenticated_at = payload.get("auth_time", payload["iat"])
    now = int(datetime.now(timezone.utc).timestamp())
    if (
        type(payload["iat"]) is not int
        or type(authenticated_at) is not int
        or authenticated_at < 0
        or authenticated_at > payload["iat"]
        or now >= authenticated_at + ABSOLUTE_SESSION_LIFETIME_SECONDS
    ):
        raise jwt.InvalidTokenError("Session requires fresh authentication")
    return int(payload["sub"]), version, authenticated_at


def decode_access_token_claims(token: str) -> tuple[int, int]:
    user_id, version, _ = decode_access_token_session(token)
    return user_id, version


def session_cookie_max_age(authenticated_at: int) -> int:
    now = int(datetime.now(timezone.utc).timestamp())
    return max(0, min(
        ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        authenticated_at + ABSOLUTE_SESSION_LIFETIME_SECONDS - now,
    ))


def decode_access_token(token: str) -> int:
    user_id, _ = decode_access_token_claims(token)
    return user_id
