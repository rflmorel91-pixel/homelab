from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Lead, User
from app.operator_context import get_current_operator
from app.schemas.lead import LeadRead


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
