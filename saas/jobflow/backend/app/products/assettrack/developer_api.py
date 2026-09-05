from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant
from app.products.assettrack.api_key_security import (
    get_developer_tenant,
)
from app.products.assettrack.assets_api import commit_asset
from app.products.assettrack.developer_schemas import (
    DeveloperStatusRead,
)
from app.products.assettrack.models import (
    Asset,
    AssetServiceEvent,
)
from app.products.assettrack.schemas import (
    AssetCreate,
    AssetRead,
    AssetServiceEventCreate,
    AssetServiceEventRead,
    AssetUpdate,
)


router = APIRouter(
    prefix="/developer/v1",
    tags=["AssetTrack Developer API"],
)


def find_asset(
    asset_id: int,
    tenant_id: int,
    db: Session,
) -> Asset:
    asset = db.scalar(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.tenant_id == tenant_id,
        )
    )

    if asset is None:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    return asset


@router.get(
    "/status",
    response_model=DeveloperStatusRead,
)
def developer_status(
    _: Tenant = Depends(get_developer_tenant),
):
    return {
        "product": "assettrack",
        "api_version": "v1",
        "status": "available",
    }


@router.post(
    "/assets",
    response_model=AssetRead,
    status_code=201,
)
def create_asset(
    payload: AssetCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_developer_tenant),
):
    asset = Asset(
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

    db.add(asset)
    commit_asset(db, asset)

    return asset


@router.get(
    "/assets",
    response_model=list[AssetRead],
)
def list_assets(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    asset_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_developer_tenant),
):
    statement = select(Asset).where(
        Asset.tenant_id == tenant.id
    )

    if asset_type is not None:
        statement = statement.where(
            Asset.asset_type == asset_type
        )

    if status is not None:
        statement = statement.where(
            Asset.status == status
        )

    return db.scalars(
        statement
        .order_by(Asset.id)
        .offset(offset)
        .limit(limit)
    ).all()


@router.get(
    "/assets/{asset_id}",
    response_model=AssetRead,
)
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_developer_tenant),
):
    return find_asset(
        asset_id,
        tenant.id,
        db,
    )


@router.put(
    "/assets/{asset_id}",
    response_model=AssetRead,
)
def update_asset(
    asset_id: int,
    payload: AssetUpdate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_developer_tenant),
):
    asset = find_asset(
        asset_id,
        tenant.id,
        db,
    )

    asset.external_id = payload.external_id
    asset.name = payload.name
    asset.asset_type = payload.asset_type
    asset.manufacturer = payload.manufacturer
    asset.model = payload.model
    asset.serial_number = payload.serial_number
    asset.status = payload.status
    asset.attributes = payload.attributes

    commit_asset(db, asset)

    return asset


@router.delete(
    "/assets/{asset_id}",
    status_code=204,
)
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_developer_tenant),
):
    asset = find_asset(
        asset_id,
        tenant.id,
        db,
    )

    db.delete(asset)
    db.commit()


@router.post(
    "/assets/{asset_id}/service-events",
    response_model=AssetServiceEventRead,
    status_code=201,
)
def create_service_event(
    asset_id: int,
    payload: AssetServiceEventCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_developer_tenant),
):
    find_asset(
        asset_id,
        tenant.id,
        db,
    )

    event = AssetServiceEvent(
        tenant_id=tenant.id,
        asset_id=asset_id,
        event_type=payload.event_type,
        occurred_at=payload.occurred_at,
        summary=payload.summary,
        details=payload.details,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event


@router.get(
    "/assets/{asset_id}/service-events",
    response_model=list[AssetServiceEventRead],
)
def list_service_events(
    asset_id: int,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_developer_tenant),
):
    find_asset(
        asset_id,
        tenant.id,
        db,
    )

    return db.scalars(
        select(AssetServiceEvent)
        .where(
            AssetServiceEvent.asset_id == asset_id,
            AssetServiceEvent.tenant_id == tenant.id,
        )
        .order_by(
            AssetServiceEvent.occurred_at,
            AssetServiceEvent.id,
        )
        .offset(offset)
        .limit(limit)
    ).all()
