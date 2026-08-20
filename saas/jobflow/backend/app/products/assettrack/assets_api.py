from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant
from app.products.assettrack.models import Asset
from app.products.assettrack.schemas import (
    AssetCreate,
    AssetRead,
    AssetUpdate,
)
from app.tenant_context import get_current_tenant


router = APIRouter(
    prefix="/assets",
    tags=["AssetTrack Assets"],
)


@router.post(
    "",
    response_model=AssetRead,
    status_code=201,
)
def create_asset(
    payload: AssetCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    item = Asset(
        tenant_id=tenant.id,
        name=payload.name,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


@router.get(
    "",
    response_model=list[AssetRead],
)
def list_assets(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    result = db.execute(
        select(Asset)
        .where(
            Asset.tenant_id
            == tenant.id
        )
        .order_by(Asset.id)
    )

    return result.scalars().all()


@router.get(
    "/{item_id}",
    response_model=AssetRead,
)
def get_asset(
    item_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    item = db.scalar(
        select(Asset).where(
            Asset.id == item_id,
            Asset.tenant_id
            == tenant.id,
        )
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    return item


@router.put(
    "/{item_id}",
    response_model=AssetRead,
)
def update_asset(
    item_id: int,
    payload: AssetUpdate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    item = db.scalar(
        select(Asset).where(
            Asset.id == item_id,
            Asset.tenant_id
            == tenant.id,
        )
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    item.name = payload.name

    db.commit()
    db.refresh(item)

    return item


@router.delete(
    "/{item_id}",
    status_code=204,
)
def delete_asset(
    item_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    item = db.scalar(
        select(Asset).where(
            Asset.id == item_id,
            Asset.tenant_id
            == tenant.id,
        )
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    db.delete(item)
    db.commit()
