from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth_context import get_current_user_id
from app.database import get_db
from app.models import Tenant, TenantMembership
from app.products.fieldnest.models import (
    FieldNestProperty,
    FieldNestResident,
    FieldNestVendor,
    FieldNestWorkOrder,
)
from app.products.fieldnest.schemas import (
    PropertyCreate,
    PropertyRead,
    ResidentCreate,
    ResidentRead,
    VendorCreate,
    VendorRead,
    WorkOrderCreate,
    WorkOrderRead,
    WorkOrderUpdate,
)
from app.tenant_context import get_current_tenant, get_current_tenant_membership


status_router = APIRouter(prefix="/status", tags=["FieldNest"])
router = APIRouter(tags=["FieldNest Workspace"])


@status_router.get("")
def fieldnest_status():
    return {"product": "fieldnest", "status": "available"}


@router.get("/properties", response_model=list[PropertyRead])
def list_properties(db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant)):
    return db.scalars(select(FieldNestProperty).where(FieldNestProperty.tenant_id == tenant.id).order_by(FieldNestProperty.name)).all()


@router.post("/properties", response_model=PropertyRead, status_code=201)
def create_property(payload: PropertyCreate, db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant)):
    row = FieldNestProperty(tenant_id=tenant.id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/residents", response_model=list[ResidentRead])
def list_residents(db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant)):
    return db.scalars(select(FieldNestResident).where(FieldNestResident.tenant_id == tenant.id).order_by(FieldNestResident.name)).all()


@router.post("/residents", response_model=ResidentRead, status_code=201)
def create_resident(payload: ResidentCreate, db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant)):
    prop = db.scalar(select(FieldNestProperty).where(FieldNestProperty.id == payload.property_id, FieldNestProperty.tenant_id == tenant.id))
    if prop is None:
        raise HTTPException(status_code=404, detail="Property not found")
    row = FieldNestResident(tenant_id=tenant.id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/vendors", response_model=list[VendorRead])
def list_vendors(db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant)):
    return db.scalars(select(FieldNestVendor).where(FieldNestVendor.tenant_id == tenant.id).order_by(FieldNestVendor.name)).all()


@router.post("/vendors", response_model=VendorRead, status_code=201)
def create_vendor(payload: VendorCreate, db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant)):
    row = FieldNestVendor(tenant_id=tenant.id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/work-orders", response_model=list[WorkOrderRead])
def list_work_orders(db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant)):
    return db.scalars(select(FieldNestWorkOrder).where(FieldNestWorkOrder.tenant_id == tenant.id).order_by(FieldNestWorkOrder.created_at.desc(), FieldNestWorkOrder.id.desc())).all()


def _validate_work_order_links(db: Session, tenant_id: int, payload: WorkOrderCreate | WorkOrderUpdate) -> None:
    prop = db.scalar(select(FieldNestProperty).where(FieldNestProperty.id == payload.property_id, FieldNestProperty.tenant_id == tenant_id)) if hasattr(payload, "property_id") else None
    if prop is None and hasattr(payload, "property_id"):
        raise HTTPException(status_code=404, detail="Property not found")
    if payload.resident_id is not None:
        resident = db.scalar(select(FieldNestResident).where(FieldNestResident.id == payload.resident_id, FieldNestResident.tenant_id == tenant_id))
        if resident is None:
            raise HTTPException(status_code=404, detail="Resident not found")
        if hasattr(payload, "property_id") and resident.property_id != payload.property_id:
            raise HTTPException(status_code=422, detail="Resident must belong to the selected property")
    if payload.vendor_id is not None:
        vendor = db.scalar(select(FieldNestVendor).where(FieldNestVendor.id == payload.vendor_id, FieldNestVendor.tenant_id == tenant_id))
        if vendor is None:
            raise HTTPException(status_code=404, detail="Vendor not found")


def _validate_update_links(db: Session, tenant_id: int, row: FieldNestWorkOrder, payload: WorkOrderUpdate) -> None:
    if payload.resident_id is not None:
        resident = db.scalar(select(FieldNestResident).where(FieldNestResident.id == payload.resident_id, FieldNestResident.tenant_id == tenant_id))
        if resident is None:
            raise HTTPException(status_code=404, detail="Resident not found")
        if resident.property_id != row.property_id:
            raise HTTPException(status_code=422, detail="Resident must belong to the work order property")
    if payload.vendor_id is not None:
        vendor = db.scalar(select(FieldNestVendor).where(FieldNestVendor.id == payload.vendor_id, FieldNestVendor.tenant_id == tenant_id))
        if vendor is None:
            raise HTTPException(status_code=404, detail="Vendor not found")


@router.post("/work-orders", response_model=WorkOrderRead, status_code=201)
def create_work_order(payload: WorkOrderCreate, db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant), user_id: int = Depends(get_current_user_id)):
    _validate_work_order_links(db, tenant.id, payload)
    row = FieldNestWorkOrder(tenant_id=tenant.id, created_by_user_id=user_id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/work-orders/{work_order_id}", response_model=WorkOrderRead)
def update_work_order(work_order_id: int, payload: WorkOrderUpdate, db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant)):
    row = db.scalar(select(FieldNestWorkOrder).where(FieldNestWorkOrder.id == work_order_id, FieldNestWorkOrder.tenant_id == tenant.id))
    if row is None:
        raise HTTPException(status_code=404, detail="Work order not found")
    _validate_update_links(db, tenant.id, row, payload)
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/work-orders/{work_order_id}", status_code=204)
def delete_work_order(work_order_id: int, db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant), membership: TenantMembership = Depends(get_current_tenant_membership)):
    if membership.role != "owner":
        raise HTTPException(status_code=403, detail="Tenant owner access required")
    row = db.scalar(select(FieldNestWorkOrder).where(FieldNestWorkOrder.id == work_order_id, FieldNestWorkOrder.tenant_id == tenant.id))
    if row is None:
        raise HTTPException(status_code=404, detail="Work order not found")
    db.delete(row)
    db.commit()
