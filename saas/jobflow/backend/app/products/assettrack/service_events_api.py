from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant
from app.products.assettrack.models import (
    Asset,
    AssetServiceEvent,
)
from app.products.assettrack.schemas import (
    AssetServiceEventCreate,
    AssetServiceEventRead,
)
from app.tenant_context import get_current_tenant


router = APIRouter(
    prefix="/assets/{asset_id}/service-events",
    tags=["AssetTrack Service History"],
)


def require_asset(
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


@router.post(
    "",
    response_model=AssetServiceEventRead,
    status_code=201,
)
def create_service_event(
    asset_id: int,
    payload: AssetServiceEventCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    require_asset(
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
    "",
    response_model=list[AssetServiceEventRead],
)
def list_service_events(
    asset_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    require_asset(
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
    ).all()


@router.get(
    "/{event_id}",
    response_model=AssetServiceEventRead,
)
def get_service_event(
    asset_id: int,
    event_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    require_asset(
        asset_id,
        tenant.id,
        db,
    )

    event = db.scalar(
        select(AssetServiceEvent).where(
            AssetServiceEvent.id == event_id,
            AssetServiceEvent.asset_id == asset_id,
            AssetServiceEvent.tenant_id == tenant.id,
        )
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Service event not found",
        )

    return event
