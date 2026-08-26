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
    DueFollowUpRead,
    FollowUpRecord,
    ManualCandidateCreate,
    OutreachSentRecord,
    ReplyRecord,
    SuppressionRecord,
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


@router.get(
    "/follow-ups/due",
    response_model=list[DueFollowUpRead],
)
def list_due_follow_ups(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_operator),
):
    statement = (
        select(
            ProspectCandidate,
            Lead,
        )
        .join(
            Lead,
            Lead.id
            == ProspectCandidate.lead_id,
        )
        .where(
            ProspectCandidate.review_status
            == "approved",
            ProspectCandidate.outreach_sent_at
            .is_not(None),
            ProspectCandidate.follow_up_due_at
            .is_not(None),
            ProspectCandidate.follow_up_completed_at
            .is_(None),
            ProspectCandidate.reply_received_at
            .is_(None),
            ProspectCandidate.suppressed_at
            .is_(None),
            Lead.status != "closed",
        )
        .order_by(
            ProspectCandidate.follow_up_due_at.asc(),
            ProspectCandidate.id.asc(),
        )
    )

    return [
        DueFollowUpRead(
            candidate_id=candidate.id,
            lead_id=lead.id,
            business_name=candidate.business_name,
            contact_name=candidate.contact_name,
            email=candidate.email,
            outreach_sent_at=(
                candidate.outreach_sent_at
            ),
            follow_up_due_at=(
                candidate.follow_up_due_at
            ),
        )
        for candidate, lead in db.execute(
            statement
        ).all()
    ]



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


def _activity_time(
    value: datetime,
) -> datetime:
    if value.tzinfo is None:
        return value

    return value.astimezone(
        timezone.utc
    ).replace(
        tzinfo=None
    )


def _activity_snapshot(
    candidate: ProspectCandidate,
) -> dict:
    def iso(
        value: datetime | None,
    ) -> str | None:
        if value is None:
            return None

        return value.isoformat()

    return {
        "outreach_channel":
            candidate.outreach_channel,
        "outreach_sent_at":
            iso(candidate.outreach_sent_at),
        "follow_up_due_at":
            iso(candidate.follow_up_due_at),
        "follow_up_completed_at":
            iso(
                candidate.follow_up_completed_at
            ),
        "reply_received_at":
            iso(candidate.reply_received_at),
        "reply_outcome":
            candidate.reply_outcome,
        "operator_notes":
            candidate.operator_notes,
        "suppressed_at":
            iso(candidate.suppressed_at),
        "suppression_reason":
            candidate.suppression_reason,
        "lead_id":
            candidate.lead_id,
    }


def _candidate_or_404(
    candidate_id: int,
    db: Session,
) -> ProspectCandidate:
    candidate = db.get(
        ProspectCandidate,
        candidate_id,
    )

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Prospect candidate not found",
        )

    return candidate


def _add_activity_audit(
    *,
    db: Session,
    operator: User,
    candidate: ProspectCandidate,
    action: str,
    before_data: dict,
) -> None:
    db.add(
        AdminAuditLog(
            operator_user_id=operator.id,
            action=(
                "workflow_automation."
                f"{action}"
            ),
            target_type="prospect_candidate",
            target_id=candidate.id,
            tenant_id=None,
            before_data=before_data,
            after_data=_activity_snapshot(
                candidate
            ),
        )
    )


@router.post(
    "/candidates/{candidate_id}/"
    "outreach/sent",
    response_model=CandidateRead,
)
def record_outreach_sent(
    candidate_id: int,
    payload: OutreachSentRecord,
    db: Session = Depends(get_db),
    operator: User = Depends(
        get_current_operator
    ),
):
    candidate = _candidate_or_404(
        candidate_id,
        db,
    )

    if candidate.review_status != "approved":
        raise HTTPException(
            status_code=409,
            detail=(
                "Only an approved candidate can "
                "be marked sent"
            ),
        )

    if candidate.suppressed_at is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Suppressed candidate cannot be "
                "contacted"
            ),
        )

    if candidate.outreach_sent_at is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Outreach has already been "
                "recorded as sent"
            ),
        )

    sent_at = _activity_time(
        payload.sent_at
    )
    follow_up_due_at = (
        _activity_time(
            payload.follow_up_due_at
        )
        if payload.follow_up_due_at
        is not None
        else None
    )

    if (
        follow_up_due_at is not None
        and follow_up_due_at < sent_at
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "Follow-up due time cannot be "
                "before the sent time"
            ),
        )

    lead = (
        db.get(
            Lead,
            candidate.lead_id,
        )
        if candidate.lead_id is not None
        else None
    )

    if (
        lead is not None
        and lead.status in {
            "closed",
            "converted",
        }
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Associated lead is not eligible "
                "for outreach"
            ),
        )

    before_data = _activity_snapshot(
        candidate
    )

    candidate.outreach_channel = (
        payload.channel
    )
    candidate.outreach_sent_at = sent_at
    candidate.follow_up_due_at = (
        follow_up_due_at
    )

    if payload.notes is not None:
        candidate.operator_notes = (
            payload.notes
        )

    if (
        lead is not None
        and lead.status == "new"
    ):
        lead.status = "contacted"

    _add_activity_audit(
        db=db,
        operator=operator,
        candidate=candidate,
        action="outreach_sent",
        before_data=before_data,
    )

    db.commit()
    db.refresh(candidate)

    return candidate


@router.post(
    "/candidates/{candidate_id}/"
    "outreach/follow-up",
    response_model=CandidateRead,
)
def record_follow_up(
    candidate_id: int,
    payload: FollowUpRecord,
    db: Session = Depends(get_db),
    operator: User = Depends(
        get_current_operator
    ),
):
    candidate = _candidate_or_404(
        candidate_id,
        db,
    )

    if candidate.outreach_sent_at is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Outreach must be recorded as "
                "sent before a follow-up"
            ),
        )

    if candidate.suppressed_at is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Suppressed candidate cannot "
                "receive a follow-up"
            ),
        )

    if (
        candidate.follow_up_completed_at
        is not None
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Follow-up has already been "
                "recorded"
            ),
        )

    completed_at = _activity_time(
        payload.completed_at
    )

    if (
        completed_at
        < candidate.outreach_sent_at
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "Follow-up completion cannot be "
                "before the sent time"
            ),
        )

    before_data = _activity_snapshot(
        candidate
    )

    candidate.follow_up_completed_at = (
        completed_at
    )

    if payload.notes is not None:
        candidate.operator_notes = (
            payload.notes
        )

    _add_activity_audit(
        db=db,
        operator=operator,
        candidate=candidate,
        action="follow_up_recorded",
        before_data=before_data,
    )

    db.commit()
    db.refresh(candidate)

    return candidate


@router.post(
    "/candidates/{candidate_id}/"
    "outreach/reply",
    response_model=CandidateRead,
)
def record_reply(
    candidate_id: int,
    payload: ReplyRecord,
    db: Session = Depends(get_db),
    operator: User = Depends(
        get_current_operator
    ),
):
    candidate = _candidate_or_404(
        candidate_id,
        db,
    )

    if candidate.outreach_sent_at is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Outreach must be recorded as "
                "sent before a reply"
            ),
        )

    if candidate.reply_received_at is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Reply has already been "
                "recorded"
            ),
        )

    received_at = _activity_time(
        payload.received_at
    )

    if (
        received_at
        < candidate.outreach_sent_at
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "Reply time cannot be before "
                "the sent time"
            ),
        )

    before_data = _activity_snapshot(
        candidate
    )

    candidate.reply_received_at = (
        received_at
    )
    candidate.reply_outcome = (
        payload.outcome
    )

    if payload.notes is not None:
        candidate.operator_notes = (
            payload.notes
        )

    if payload.outcome == "unsubscribe":
        candidate.suppressed_at = (
            received_at
        )
        candidate.suppression_reason = (
            "Unsubscribe request"
        )

        if candidate.lead_id is not None:
            lead = db.get(
                Lead,
                candidate.lead_id,
            )

            if (
                lead is not None
                and lead.status in {
                    "new",
                    "contacted",
                }
            ):
                lead.status = "closed"

    _add_activity_audit(
        db=db,
        operator=operator,
        candidate=candidate,
        action="reply_recorded",
        before_data=before_data,
    )

    db.commit()
    db.refresh(candidate)

    return candidate


@router.post(
    "/candidates/{candidate_id}/"
    "outreach/suppression",
    response_model=CandidateRead,
)
def record_suppression(
    candidate_id: int,
    payload: SuppressionRecord,
    db: Session = Depends(get_db),
    operator: User = Depends(
        get_current_operator
    ),
):
    candidate = _candidate_or_404(
        candidate_id,
        db,
    )

    if candidate.suppressed_at is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Candidate is already "
                "suppressed"
            ),
        )

    before_data = _activity_snapshot(
        candidate
    )

    candidate.suppressed_at = (
        _activity_time(
            payload.suppressed_at
        )
    )
    candidate.suppression_reason = (
        payload.reason
    )

    if payload.notes is not None:
        candidate.operator_notes = (
            payload.notes
        )

    if candidate.lead_id is not None:
        lead = db.get(
            Lead,
            candidate.lead_id,
        )

        if (
            lead is not None
            and lead.status in {
                "new",
                "contacted",
            }
        ):
            lead.status = "closed"

    _add_activity_audit(
        db=db,
        operator=operator,
        candidate=candidate,
        action="candidate_suppressed",
        before_data=before_data,
    )

    db.commit()
    db.refresh(candidate)

    return candidate
