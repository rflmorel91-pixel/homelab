from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProspectingCampaign(Base):
    __tablename__ = (
        "workflow_automation_prospecting_campaigns"
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    geography: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="New York State",
    )

    segments: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        index=True,
    )

    max_candidates: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10,
    )

    minimum_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=70,
    )

    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    started_at: Mapped[datetime | None] = (
        mapped_column(
            DateTime,
            nullable=True,
        )
    )

    completed_at: Mapped[datetime | None] = (
        mapped_column(
            DateTime,
            nullable=True,
        )
    )

    error_message: Mapped[str | None] = (
        mapped_column(
            Text,
            nullable=True,
        )
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
        index=True,
    )


class ProspectCandidate(Base):
    __tablename__ = (
        "workflow_automation_prospect_candidates"
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    campaign_id: Mapped[int] = mapped_column(
        ForeignKey(
            "workflow_automation_"
            "prospecting_campaigns.id"
        ),
        nullable=False,
        index=True,
    )

    lead_id: Mapped[int | None] = mapped_column(
        ForeignKey("leads.id"),
        nullable=True,
        unique=True,
        index=True,
    )

    business_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    website_url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    normalized_domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    segment: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    location: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )

    contact_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    evidence: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    fit_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    score_reasons: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    disqualifiers: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    outreach_subject: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )

    outreach_body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    review_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )

    reviewed_by_user_id: Mapped[int | None] = (
        mapped_column(
            ForeignKey("users.id"),
            nullable=True,
            index=True,
        )
    )

    reviewed_at: Mapped[datetime | None] = (
        mapped_column(
            DateTime,
            nullable=True,
        )
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
