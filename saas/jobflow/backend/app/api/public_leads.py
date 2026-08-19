from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Lead
from app.schemas.lead import (
    PublicLeadCreate,
    PublicLeadRead,
)


router = APIRouter(
    prefix="/public/leads",
    tags=["Public Leads"],
)


@router.post(
    "",
    response_model=PublicLeadRead,
    status_code=201,
)
def create_public_lead(
    lead: PublicLeadCreate,
    db: Session = Depends(get_db),
):
    db_lead = Lead(
        business_name=lead.business_name,
        contact_name=lead.contact_name,
        email=lead.email,
        phone=lead.phone,
        service_type=lead.service_type,
        message=lead.message,
        status="new",
    )

    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)

    return PublicLeadRead(
        lead_id=db_lead.id,
        status="received",
    )
