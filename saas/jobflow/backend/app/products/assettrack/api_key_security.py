from datetime import datetime, timezone
from hashlib import sha256
from secrets import token_urlsafe

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, Tenant
from app.products.assettrack.models import AssetTrackApiKey


API_KEY_PREFIX = "flk_at_"


def hash_api_key(token: str) -> str:
    return sha256(
        token.encode("utf-8")
    ).hexdigest()


def create_api_key() -> tuple[str, str, str]:
    token = API_KEY_PREFIX + token_urlsafe(32)

    return (
        token,
        token[:16],
        hash_api_key(token),
    )


def get_developer_tenant(
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
    db: Session = Depends(get_db),
) -> Tenant:
    if authorization is None:
        raise HTTPException(
            status_code=401,
            detail="Developer API key required",
        )

    scheme, _, token = authorization.partition(" ")

    if (
        scheme.lower() != "bearer"
        or not token.startswith(API_KEY_PREFIX)
    ):
        raise HTTPException(
            status_code=401,
            detail="Developer API key required",
        )

    record = db.scalar(
        select(AssetTrackApiKey).where(
            AssetTrackApiKey.token_hash
            == hash_api_key(token),
            AssetTrackApiKey.revoked_at.is_(None),
        )
    )

    if record is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid developer API key",
        )

    tenant = db.get(Tenant, record.tenant_id)

    product = (
        db.get(Product, tenant.product_id)
        if tenant is not None
        else None
    )

    if (
        tenant is None
        or tenant.status != "active"
        or product is None
        or product.slug != "assettrack"
    ):
        raise HTTPException(
            status_code=403,
            detail="Tenant is unavailable",
        )

    record.last_used_at = datetime.now(timezone.utc)
    db.commit()

    return tenant
