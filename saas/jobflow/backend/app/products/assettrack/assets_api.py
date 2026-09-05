from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
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


def commit_asset(
    db: Session,
    item: Asset,
) -> None:
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "Asset external_id already exists "
                "for this tenant"
            ),
        ) from error

    db.refresh(item)


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
        external_id=payload.external_id,
        name=payload.name,
        asset_type=payload.asset_type,
        manufacturer=payload.manufacturer,
        model=payload.model,
        serial_number=payload.serial_number,
        status=payload.status,
        attributes=payload.attributes,
    )

    db.add(item)
    commit_asset(db, item)

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

    item.external_id = payload.external_id
    item.name = payload.name
    item.asset_type = payload.asset_type
    item.manufacturer = payload.manufacturer
    item.model = payload.model
    item.serial_number = payload.serial_number
    item.status = payload.status
    item.attributes = payload.attributes

    commit_asset(db, item)

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
