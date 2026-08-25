from datetime import datetime, timezone
import os

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    AdminAuditLog,
    Lead,
    Product,
    User,
)
from app.operator_context import get_current_operator
from app.products.workflow_automation.models import (
    ProspectCandidate,
    ProspectingCampaign,
)
from app.products.workflow_automation.prospecting_agent import (
    OpenAIWebSearchProvider,
    ProspectingConfigurationError,
    normalize_domain,
    outreach_body_with_footer,
    run_campaign_in_background,
    valid_business_email,
)
from app.products.workflow_automation.prospecting_schemas import (
    CampaignCreate,
    CampaignRead,
    CampaignRunAccepted,
    CandidateRead,
    CandidateReview,
    ManualCandidateCreate,
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
    response_model=CampaignRunAccepted,
    status_code=202,
)
def run_prospecting_campaign(
    campaign_id: int,
    background_tasks: BackgroundTasks,
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

    if campaign.status != "draft":
        raise HTTPException(
            status_code=409,
            detail=(
                "Only draft campaigns can be run"
            ),
        )

    try:
        (
            OpenAIWebSearchProvider
            .from_environment()
        )
    except ProspectingConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    campaign.status = "queued"
    campaign.started_at = None
    campaign.completed_at = None
    campaign.error_message = None
    db.commit()

    background_tasks.add_task(
        run_campaign_in_background,
        campaign.id,
    )

    return {
        "campaign_id": campaign.id,
        "status": "queued",
    }


@router.post(
    "/candidates",
    response_model=CandidateRead,
    status_code=201,
)
def create_manual_candidate(
    payload: ManualCandidateCreate,
    db: Session = Depends(get_db),
    operator: User = Depends(
        get_current_operator
    ),
):
    campaign = db.get(
        ProspectingCampaign,
        payload.campaign_id,
    )

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail="Prospecting campaign not found",
        )

    if payload.segment not in campaign.segments:
        raise HTTPException(
            status_code=422,
            detail=(
                "Candidate segment is not enabled "
                "for this campaign"
            ),
        )

    if payload.fit_score < campaign.minimum_score:
        raise HTTPException(
            status_code=422,
            detail=(
                "Candidate is below the campaign "
                "minimum score"
            ),
        )

    if payload.disqualifiers:
        raise HTTPException(
            status_code=422,
            detail=(
                "Disqualified candidates cannot "
                "be added"
            ),
        )

    try:
        domain = normalize_domain(
            payload.website_url
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    email = payload.email.strip().lower()

    if not valid_business_email(
        email,
        domain,
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "Candidate email must use the "
                "business website domain"
            ),
        )

    product = db.scalar(
        select(Product).where(
            Product.slug
            == "workflow-automation",
            Product.status == "active",
        )
    )

    if product is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Workflow Automation product "
                "is unavailable"
            ),
        )

    existing_candidate = db.scalar(
        select(ProspectCandidate).where(
            ProspectCandidate.normalized_domain
            == domain
        )
    )

    existing_lead = db.scalar(
        select(Lead).where(
            Lead.product_id == product.id,
            Lead.email == email,
        )
    )

    if (
        existing_candidate is not None
        or existing_lead is not None
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Prospect candidate already "
                "exists"
            ),
        )

    lead = Lead(
        product_id=product.id,
        business_name=payload.business_name,
        contact_name=(
            payload.contact_name
            or "Business contact"
        ),
        email=email,
        phone=payload.phone,
        service_type=(
            "Small IT provider partnership"
        ),
        message=(
            "Operator-researched Workflow "
            "Automation prospect. Review "
            "evidence and approve the outreach "
            "draft before any manual contact."
        ),
        status="new",
    )

    db.add(lead)
    db.flush()

    candidate = ProspectCandidate(
        campaign_id=campaign.id,
        lead_id=lead.id,
        business_name=payload.business_name,
        website_url=payload.website_url,
        normalized_domain=domain,
        segment=payload.segment,
        location=payload.location,
        contact_name=payload.contact_name,
        email=email,
        phone=payload.phone,
        evidence=[
            item.model_dump()
            for item in payload.evidence
        ],
        fit_score=payload.fit_score,
        score_reasons=payload.score_reasons,
        disqualifiers=[],
        outreach_subject=(
            payload.outreach_subject
        ),
        outreach_body=(
            outreach_body_with_footer(
                payload.outreach_body
            )
        ),
        review_status="pending",
    )

    db.add(candidate)
    db.flush()

    db.add(
        AdminAuditLog(
            operator_user_id=operator.id,
            action=(
                "workflow_automation."
                "manual_candidate_created"
            ),
            target_type="prospect_candidate",
            target_id=candidate.id,
            tenant_id=None,
            before_data=None,
            after_data={
                "campaign_id": campaign.id,
                "lead_id": lead.id,
                "business_name":
                    candidate.business_name,
                "normalized_domain":
                    candidate.normalized_domain,
                "email": candidate.email,
                "fit_score":
                    candidate.fit_score,
                "review_status":
                    candidate.review_status,
            },
        )
    )

    db.commit()
    db.refresh(candidate)

    return candidate


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

    if (
        payload.decision == "rejected"
        and candidate.lead_id is not None
    ):
        lead = db.get(
            Lead,
            candidate.lead_id,
        )

        if (
            lead is not None
            and lead.status == "new"
        ):
            lead.status = "closed"

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
