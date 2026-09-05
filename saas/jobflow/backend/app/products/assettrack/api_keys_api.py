from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth_context import get_current_user_id
from app.database import get_db
from app.models import Tenant, TenantMembership
from app.products.assettrack.api_key_security import (
    create_api_key,
)
from app.products.assettrack.developer_schemas import (
    DeveloperApiKeyCreate,
    DeveloperApiKeyCreated,
    DeveloperApiKeyRead,
)
from app.products.assettrack.models import AssetTrackApiKey
from app.tenant_context import (
    get_current_tenant,
    require_current_tenant_owner,
)


router = APIRouter(
    prefix="/developer-api-keys",
    tags=["AssetTrack Developer API Keys"],
)


@router.post(
    "",
    response_model=DeveloperApiKeyCreated,
    status_code=201,
)
def create_developer_api_key(
    payload: DeveloperApiKeyCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    _: TenantMembership = Depends(
        require_current_tenant_owner
    ),
    user_id: int = Depends(get_current_user_id),
):
    token, key_prefix, token_hash = create_api_key()

    record = AssetTrackApiKey(
        tenant_id=tenant.id,
        created_by_user_id=user_id,
        name=payload.name,
        key_prefix=key_prefix,
        token_hash=token_hash,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return DeveloperApiKeyCreated(
        id=record.id,
        name=record.name,
        key_prefix=record.key_prefix,
        api_key=token,
        last_used_at=record.last_used_at,
        revoked_at=record.revoked_at,
        created_at=record.created_at,
    )


@router.get(
    "",
    response_model=list[DeveloperApiKeyRead],
)
def list_developer_api_keys(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    _: TenantMembership = Depends(
        require_current_tenant_owner
    ),
):
    return db.scalars(
        select(AssetTrackApiKey)
        .where(
            AssetTrackApiKey.tenant_id == tenant.id
        )
        .order_by(AssetTrackApiKey.id)
    ).all()


@router.delete(
    "/{key_id}",
    status_code=204,
)
def revoke_developer_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    _: TenantMembership = Depends(
        require_current_tenant_owner
    ),
):
    record = db.scalar(
        select(AssetTrackApiKey).where(
            AssetTrackApiKey.id == key_id,
            AssetTrackApiKey.tenant_id == tenant.id,
        )
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Developer API key not found",
        )

    if record.revoked_at is None:
        record.revoked_at = datetime.now(timezone.utc)
        db.commit()
