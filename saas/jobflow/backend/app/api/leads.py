from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Lead, User
from app.operator_context import get_current_operator
from app.schemas.lead import LeadRead, LeadUpdate


LEAD_STATUS_TRANSITIONS = {
    "new": {"contacted"},
    "contacted": {"qualified", "closed"},
    "qualified": {"converted", "closed"},
    "converted": set(),
    "closed": set(),
}


router = APIRouter(
    prefix="/leads",
    tags=["Leads"],
)


@router.get(
    "/",
    response_model=list[LeadRead],
)
def list_leads(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_operator),
):
    result = db.execute(
        select(Lead)
        .order_by(
            Lead.created_at.desc(),
            Lead.id.desc(),
        )
    )

    return result.scalars().all()


@router.put(
    "/{lead_id}",
    response_model=LeadRead,
)
def update_lead(
    lead_id: int,
    lead: LeadUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_operator),
):
    db_lead = db.get(Lead, lead_id)

    if db_lead is None:
        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    if lead.status != db_lead.status:
        allowed_statuses = LEAD_STATUS_TRANSITIONS.get(
            db_lead.status,
            set(),
        )

        if lead.status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid lead status transition: "
                    f"{db_lead.status} -> {lead.status}"
                ),
            )

    db_lead.status = lead.status

    db.commit()
    db.refresh(db_lead)

    return db_lead
