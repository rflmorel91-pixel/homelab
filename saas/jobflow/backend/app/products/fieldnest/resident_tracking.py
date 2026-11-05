"""One-request bearer links and private, normalized photos."""
import base64
import binascii
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from io import BytesIO
import secrets
from threading import BoundedSemaphore

from fastapi import APIRouter, Depends, HTTPException, Response
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant, Product
from app.products.fieldnest.models import FieldNestWorkOrder, FieldNestPhoto
from app.tenant_context import get_current_tenant, require_current_tenant_owner

public_tracking_router = APIRouter(prefix="/public/resident", tags=["FieldNest Resident Tracking"])
tracking_router = APIRouter(tags=["FieldNest Request Tracking"])
owner_tracking_router = APIRouter(tags=["FieldNest Tracking Links"], dependencies=[Depends(require_current_tenant_owner)])
MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_STORED_BYTES = 512 * 1024
MAX_TENANT_BYTES = 100 * 1024 * 1024
PHOTO_SLOTS = BoundedSemaphore(2)


class TrackingToken(BaseModel):
    token: str = Field(pattern=r"^[A-Za-z0-9_-]{43}$")
    model_config = ConfigDict(extra="forbid")


class PhotoInput(BaseModel):
    data: str = Field(min_length=1, max_length=2_800_000)
    model_config = ConfigDict(extra="forbid")


def normalize_photo(data):
    try:
        raw = base64.b64decode(data, validate=True)
    except (ValueError, binascii.Error):
        raise HTTPException(422, "A photo is not valid base64.")
    if not raw or len(raw) > MAX_INPUT_BYTES:
        raise HTTPException(413, "Each photo must be no larger than 2 MB.")
    try:
        with Image.open(BytesIO(raw), formats=["JPEG", "PNG"]) as image:
            if image.width * image.height > 12_000_000 or getattr(image, "n_frames", 1) != 1:
                raise HTTPException(413, "Use a still photo no larger than 12 megapixels.")
            image.load()
            oriented = ImageOps.exif_transpose(image)
            oriented.thumbnail((1600, 1600))
            # A fresh pixel-only image removes EXIF/GPS, comments, ICC and other metadata.
            clean = Image.new("RGB", oriented.size, "white")
            if "A" in oriented.getbands():
                clean.paste(oriented.convert("RGB"), mask=oriented.getchannel("A"))
            else:
                clean.paste(oriented.convert("RGB"))
            for _ in range(5):
                output = BytesIO()
                clean.save(output, format="JPEG", quality=80)
                if len(output.getvalue()) <= MAX_STORED_BYTES:
                    return output.getvalue()
                clean.thumbnail((max(1, int(clean.width * 0.75)), max(1, int(clean.height * 0.75))))
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError, OverflowError, Image.DecompressionBombError):
        raise HTTPException(415, "Use a valid JPEG or PNG photo.")
    raise HTTPException(413, "This photo is too complex. Please use a smaller image.")


def prepare_photos(db, tenant_id, photos):
    if not photos:
        return []
    if not PHOTO_SLOTS.acquire(blocking=False):
        raise HTTPException(503, "Photo processing is busy. Please try again shortly.")
    try:
        normalized = [normalize_photo(photo.data) for photo in photos]
    finally:
        PHOTO_SLOTS.release()
    # Serialize quota decisions per company across workers.
    db.scalar(select(Tenant.id).where(Tenant.id == tenant_id).with_for_update())
    used = db.scalar(select(func.coalesce(func.sum(FieldNestPhoto.byte_size), 0)).where(
        FieldNestPhoto.tenant_id == tenant_id
    ))
    if used + sum(map(len, normalized)) > MAX_TENANT_BYTES:
        raise HTTPException(413, "Photo storage is full. Remove the photos to submit, or contact your property manager.")
    return normalized


def tracking_result(row, supplied_secret=None):
    result = {"reference": f"FN-{row.id}", "status": "received"}
    if supplied_secret and row.tracking_token_hash == sha256(supplied_secret.encode()).hexdigest():
        result["tracking_path"] = f"/fieldnest/resident#{supplied_secret}"
    return result


def order_for_tracking(db, token):
    order = db.scalar(select(FieldNestWorkOrder).join(
        Tenant, Tenant.id == FieldNestWorkOrder.tenant_id
    ).join(Product, Product.id == Tenant.product_id).where(
        FieldNestWorkOrder.tracking_token_hash == sha256(token.encode()).hexdigest(),
        FieldNestWorkOrder.tracking_token_expires_at > datetime.now(timezone.utc),
        Tenant.status == "active", Product.slug == "fieldnest", Product.status == "active",
    ).with_for_update(read=True, of=FieldNestWorkOrder))
    if order is None:
        raise HTTPException(404, "This private request link is unavailable. Contact your property manager.")
    return order


def scoped_order(db, tenant_id, order_id):
    row = db.scalar(select(FieldNestWorkOrder).where(
        FieldNestWorkOrder.id == order_id, FieldNestWorkOrder.tenant_id == tenant_id
    ))
    if row is None:
        raise HTTPException(404, "Work order not found")
    return row


def photo_list(db, row):
    # Never load or list images from a different company or work order.
    return [{"id": photo_id} for photo_id in db.scalars(select(FieldNestPhoto.id).where(
        FieldNestPhoto.work_order_id == row.id, FieldNestPhoto.tenant_id == row.tenant_id
    ).order_by(FieldNestPhoto.created_at, FieldNestPhoto.id)).all()]


def private_photo(db, row, photo_id):
    photo = db.scalar(select(FieldNestPhoto).where(
        FieldNestPhoto.id == photo_id, FieldNestPhoto.work_order_id == row.id,
        FieldNestPhoto.tenant_id == row.tenant_id,
    ))
    if photo is None:
        raise HTTPException(404, "Photo not found")
    return Response(content=photo.content, media_type="image/jpeg", headers={
        "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
        "Content-Disposition": 'inline; filename="maintenance-photo.jpg"',
    })


@public_tracking_router.post("/context")
def tracking_context(payload: TrackingToken, response: Response, db: Session = Depends(get_db)):
    row = order_for_tracking(db, payload.token)
    response.headers["Cache-Control"] = "no-store"
    return {"reference": f"FN-{row.id}", "title": row.title, "unit": row.unit,
            "status": row.status, "received_at": row.created_at, "updated_at": row.updated_at,
            "photos": photo_list(db, row)}


@public_tracking_router.post("/photos/{photo_id}")
def resident_photo(photo_id: str, payload: TrackingToken, db: Session = Depends(get_db)):
    return private_photo(db, order_for_tracking(db, payload.token), photo_id)


@tracking_router.get("/work-orders/{order_id}/photos")
def manager_photos(order_id: int, response: Response, db: Session = Depends(get_db),
                   tenant: Tenant = Depends(get_current_tenant)):
    response.headers["Cache-Control"] = "no-store"
    return photo_list(db, scoped_order(db, tenant.id, order_id))


@tracking_router.get("/work-orders/{order_id}/photos/{photo_id}")
def manager_photo(order_id: int, photo_id: str, db: Session = Depends(get_db),
                  tenant: Tenant = Depends(get_current_tenant)):
    return private_photo(db, scoped_order(db, tenant.id, order_id), photo_id)


@owner_tracking_router.post("/work-orders/{order_id}/tracking-link")
def create_tracking_link(order_id: int, response: Response, db: Session = Depends(get_db),
                         tenant: Tenant = Depends(get_current_tenant)):
    row = scoped_order(db, tenant.id, order_id)
    token = secrets.token_urlsafe(32)
    row.tracking_token_hash = sha256(token.encode()).hexdigest()
    row.tracking_token_expires_at = datetime.now(timezone.utc) + timedelta(days=90)
    db.commit()
    response.headers["Cache-Control"] = "no-store"
    return {"path": f"/fieldnest/resident#{token}", "expires_at": row.tracking_token_expires_at}


@owner_tracking_router.delete("/work-orders/{order_id}/tracking-link", status_code=204)
def revoke_tracking_link(order_id: int, db: Session = Depends(get_db),
                         tenant: Tenant = Depends(get_current_tenant)):
    row = scoped_order(db, tenant.id, order_id)
    row.tracking_token_hash = None
    row.tracking_token_expires_at = None
    db.commit()
