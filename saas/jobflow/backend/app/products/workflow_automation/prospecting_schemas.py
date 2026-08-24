from datetime import datetime
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
)


RequiredText = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
    ),
]


ProspectSegment = Literal[
    "small_it_provider",
    "home_service_business",
]


class CampaignCreate(BaseModel):
    name: RequiredText
    geography: RequiredText = "New York State"
    segments: list[ProspectSegment] = Field(
        default_factory=lambda: [
            "small_it_provider",
            "home_service_business",
        ],
        min_length=1,
        max_length=2,
    )
    max_candidates: int = Field(
        default=10,
        ge=1,
        le=25,
    )
    minimum_score: int = Field(
        default=70,
        ge=0,
        le=100,
    )

    model_config = ConfigDict(extra="forbid")


class CampaignRead(BaseModel):
    id: int
    name: str
    geography: str
    segments: list[str]
    status: str
    max_candidates: int
    minimum_score: int
    model: str
    created_by_user_id: int
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class CandidateRead(BaseModel):
    id: int
    campaign_id: int
    lead_id: int | None
    business_name: str
    website_url: str
    normalized_domain: str
    segment: str
    location: str
    contact_name: str | None
    email: str | None
    phone: str | None
    evidence: list
    fit_score: int
    score_reasons: list
    disqualifiers: list
    outreach_subject: str
    outreach_body: str
    review_status: str
    reviewed_by_user_id: int | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class CandidateReview(BaseModel):
    decision: Literal[
        "approved",
        "rejected",
    ]
    outreach_subject: RequiredText | None = None
    outreach_body: RequiredText | None = None

    model_config = ConfigDict(extra="forbid")


class EvidenceItem(BaseModel):
    url: RequiredText
    fact: RequiredText

    model_config = ConfigDict(extra="forbid")


class DiscoveredCandidate(BaseModel):
    business_name: RequiredText
    website_url: RequiredText
    segment: ProspectSegment
    location: RequiredText
    contact_name: RequiredText | None = None
    email: RequiredText
    phone: RequiredText | None = None
    evidence: list[EvidenceItem] = Field(
        min_length=1,
        max_length=8,
    )
    fit_score: int = Field(
        ge=0,
        le=100,
    )
    score_reasons: list[RequiredText] = Field(
        min_length=1,
        max_length=8,
    )
    disqualifiers: list[RequiredText] = Field(
        default_factory=list,
        max_length=8,
    )
    outreach_subject: RequiredText
    outreach_body: RequiredText

    model_config = ConfigDict(extra="forbid")


class CampaignRunRead(BaseModel):
    campaign_id: int
    status: str
    discovered_count: int
    saved_count: int
    skipped_count: int

