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


from datetime import datetime, timedelta, timezone
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


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> int:
    payload = jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
    )

    return int(payload["sub"])
