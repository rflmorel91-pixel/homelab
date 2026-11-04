"""Property-scoped, revocable resident intake; no public workspace access."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, Tenant
from app.products.fieldnest.models import FieldNestProperty, FieldNestWorkOrder
from app.products.fieldnest.notifications import queue_request_notifications
from app.tenant_context import get_current_tenant, require_current_tenant_owner

public_router = APIRouter(prefix="/public/maintenance", tags=["FieldNest Resident Requests"])
link_router = APIRouter(tags=["FieldNest Resident Links"], dependencies=[Depends(require_current_tenant_owner)])


class LinkToken(BaseModel):
    token: str = Field(pattern=r"^[A-Za-z0-9_-]{43}$")
    model_config = ConfigDict(extra="forbid")


class ResidentIssue(LinkToken):
    submission_id: UUID
    name: str = Field(min_length=1, max_length=120)
    contact: str = Field(min_length=3, max_length=200)
    unit: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=180)
    description: str = Field(min_length=10, max_length=3000)
    receipt_email: str | None = Field(
        default=None, max_length=254,
        pattern=r"^[A-Za-z0-9.!#$%&'*+/=?^_{|}~-]+@(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$",
    )
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


def property_for_token(db: Session, token: str) -> FieldNestProperty:
    prop = db.scalar(
        select(FieldNestProperty)
        .join(Tenant, Tenant.id == FieldNestProperty.tenant_id)
        .join(Product, Product.id == Tenant.product_id)
        .where(
            FieldNestProperty.request_token_hash == sha256(token.encode()).hexdigest(),
            FieldNestProperty.request_token_expires_at > datetime.now(timezone.utc),
            Tenant.status == "active", Product.slug == "fieldnest", Product.status == "active",
        )
        # Hold a shared row lock until commit so revocation cannot race intake.
        .with_for_update(read=True, of=FieldNestProperty)
    )
    if prop is None:
        raise HTTPException(404, "This request link is unavailable. Ask your property manager for a current link.")
    return prop


@link_router.post("/properties/{property_id}/request-link")
def create_link(property_id: int, response: Response, db: Session = Depends(get_db),
                tenant: Tenant = Depends(get_current_tenant)):
    prop = db.scalar(select(FieldNestProperty).where(
        FieldNestProperty.id == property_id, FieldNestProperty.tenant_id == tenant.id
    ).with_for_update())
    if prop is None:
        raise HTTPException(404, "Property not found")
    token = secrets.token_urlsafe(32)
    prop.request_token_hash = sha256(token.encode()).hexdigest()
    prop.request_token_expires_at = datetime.now(timezone.utc) + timedelta(days=90)
    db.commit()
    no_store(response)
    return {"path": f"/fieldnest/report#{token}", "expires_at": prop.request_token_expires_at}


@link_router.delete("/properties/{property_id}/request-link", status_code=204)
def revoke_link(property_id: int, db: Session = Depends(get_db),
                tenant: Tenant = Depends(get_current_tenant)):
    prop = db.scalar(select(FieldNestProperty).where(
        FieldNestProperty.id == property_id, FieldNestProperty.tenant_id == tenant.id
    ).with_for_update())
    if prop is None:
        raise HTTPException(404, "Property not found")
    prop.request_token_hash = None
    prop.request_token_expires_at = None
    db.commit()


@public_router.post("/context")
def request_context(payload: LinkToken, response: Response, db: Session = Depends(get_db)):
    prop = property_for_token(db, payload.token)
    no_store(response)
    # Deliberately omit address, IDs, residents, vendors and existing work orders.
    return {"property_name": prop.name}


@public_router.post("", status_code=201)
def report_issue(payload: ResidentIssue, response: Response, db: Session = Depends(get_db)):
    prop = property_for_token(db, payload.token)
    key = str(payload.submission_id)
    existing = db.scalar(select(FieldNestWorkOrder).where(FieldNestWorkOrder.intake_key == key))
    if existing:
        if existing.tenant_id != prop.tenant_id or existing.property_id != prop.id:
            raise HTTPException(409, "Please reload the form and try again.")
        no_store(response)
        return {"reference": f"FN-{existing.id}", "status": "received"}
    row = FieldNestWorkOrder(
        tenant_id=prop.tenant_id, property_id=prop.id, created_by_user_id=None,
        resident_id=None, vendor_id=None, title=payload.title, unit=payload.unit,
        priority="normal", status="open", intake_key=key,
        description=(
            "RESIDENT REPORT — contact details are self-reported.\n"
            f"Name: {payload.name}\nContact: {payload.contact}\n\n{payload.description}"
        ),
    )
    db.add(row)
    try:
        db.flush()
        queue_request_notifications(db, row, payload.receipt_email)
        db.commit()
    except IntegrityError:
        # Concurrent retries with the same submission ID create only one order.
        db.rollback()
        existing = db.scalar(select(FieldNestWorkOrder).where(
            FieldNestWorkOrder.intake_key == key,
            FieldNestWorkOrder.tenant_id == prop.tenant_id,
            FieldNestWorkOrder.property_id == prop.id,
        ))
        if existing is None:
            raise HTTPException(409, "Please reload the form and try again.")
        row = existing
    no_store(response)
    return {"reference": f"FN-{row.id}", "status": "received"}
