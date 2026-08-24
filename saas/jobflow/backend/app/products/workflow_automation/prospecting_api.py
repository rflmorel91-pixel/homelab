from datetime import datetime, timezone
import os

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AdminAuditLog, User
from app.operator_context import get_current_operator
from app.products.workflow_automation.models import (
    ProspectCandidate,
    ProspectingCampaign,
)
from app.products.workflow_automation.prospecting_agent import (
    OpenAIWebSearchProvider,
    ProspectingConfigurationError,
    ProspectingProviderError,
    run_campaign,
)
from app.products.workflow_automation.prospecting_schemas import (
    CampaignCreate,
    CampaignRead,
    CampaignRunRead,
    CandidateRead,
    CandidateReview,
)


router = APIRouter(
    prefix="/prospecting",
    tags=[
        "Workflow Automation Prospecting",
    ],
)


@router.post(
    "/campaigns",
    response_model=CampaignRead,
    status_code=201,
)
def create_campaign(
    payload: CampaignCreate,
    db: Session = Depends(get_db),
    operator: User = Depends(
        get_current_operator
    ),
):
    campaign = ProspectingCampaign(
        name=payload.name,
        geography=payload.geography,
        segments=list(payload.segments),
        status="draft",
        max_candidates=payload.max_candidates,
        minimum_score=payload.minimum_score,
        model=os.getenv(
            "OPENAI_MODEL",
            "gpt-5-mini",
        ),
        created_by_user_id=operator.id,
    )

    db.add(campaign)
    db.flush()

    db.add(
        AdminAuditLog(
            operator_user_id=operator.id,
            action=(
                "workflow_automation."
                "campaign_created"
            ),
            target_type=(
                "prospecting_campaign"
            ),
            target_id=campaign.id,
            tenant_id=None,
            before_data=None,
            after_data={
                "name": campaign.name,
                "geography": campaign.geography,
                "segments": campaign.segments,
                "max_candidates":
                    campaign.max_candidates,
                "minimum_score":
                    campaign.minimum_score,
                "model": campaign.model,
                "status": campaign.status,
            },
        )
    )

    db.commit()
    db.refresh(campaign)

    return campaign


@router.post(
    "/campaigns/{campaign_id}/run",
    response_model=CampaignRunRead,
)
def run_prospecting_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_operator),
):
    campaign = db.get(
        ProspectingCampaign,
        campaign_id,
    )

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail="Prospecting campaign not found",
        )

    try:
        provider = (
            OpenAIWebSearchProvider
            .from_environment()
        )

        return run_campaign(
            db=db,
            campaign=campaign,
            provider=provider,
        )

    except ProspectingConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except ProspectingProviderError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


@router.get(
    "/campaigns",
    response_model=list[CampaignRead],
)
def list_campaigns(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_operator),
):
    return list(
        db.scalars(
            select(ProspectingCampaign)
            .order_by(
                ProspectingCampaign.created_at.desc(),
                ProspectingCampaign.id.desc(),
            )
        )
    )


@router.get(
    "/candidates",
    response_model=list[CandidateRead],
)
def list_candidates(
    campaign_id: int | None = None,
    review_status: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_operator),
):
    statement = select(ProspectCandidate)

    if campaign_id is not None:
        statement = statement.where(
            ProspectCandidate.campaign_id
            == campaign_id
        )

    if review_status is not None:
        if review_status not in {
            "pending",
            "approved",
            "rejected",
        }:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Unsupported candidate "
                    "review status"
                ),
            )

        statement = statement.where(
            ProspectCandidate.review_status
            == review_status
        )

    statement = statement.order_by(
        ProspectCandidate.fit_score.desc(),
        ProspectCandidate.created_at.desc(),
        ProspectCandidate.id.desc(),
    )

    return list(db.scalars(statement))


@router.put(
    "/candidates/{candidate_id}/review",
    response_model=CandidateRead,
)
def review_candidate(
    candidate_id: int,
    payload: CandidateReview,
    db: Session = Depends(get_db),
    operator: User = Depends(
        get_current_operator
    ),
):
    candidate = db.get(
        ProspectCandidate,
        candidate_id,
    )

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Prospect candidate not found",
        )

    if candidate.review_status != "pending":
        raise HTTPException(
            status_code=409,
            detail=(
                "Prospect candidate has already "
                "been reviewed"
            ),
        )

    before_data = {
        "review_status":
            candidate.review_status,
        "outreach_subject":
            candidate.outreach_subject,
        "outreach_body":
            candidate.outreach_body,
    }

    if payload.outreach_subject is not None:
        candidate.outreach_subject = (
            payload.outreach_subject
        )

    if payload.outreach_body is not None:
        candidate.outreach_body = (
            payload.outreach_body
        )

    candidate.review_status = payload.decision
    candidate.reviewed_by_user_id = operator.id
    candidate.reviewed_at = datetime.now(
        timezone.utc
    )

    db.add(
        AdminAuditLog(
            operator_user_id=operator.id,
            action=(
                "workflow_automation."
                "candidate_reviewed"
            ),
            target_type=(
                "prospect_candidate"
            ),
            target_id=candidate.id,
            tenant_id=None,
            before_data=before_data,
            after_data={
                "review_status":
                    candidate.review_status,
                "outreach_subject":
                    candidate.outreach_subject,
                "outreach_body":
                    candidate.outreach_body,
                "lead_id":
                    candidate.lead_id,
            },
        )
    )

    db.commit()
    db.refresh(candidate)

    return candidate
