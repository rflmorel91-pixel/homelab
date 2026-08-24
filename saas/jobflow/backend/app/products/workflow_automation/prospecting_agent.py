from collections.abc import Iterable
from datetime import datetime, timezone
import json
import os
from typing import Protocol
from urllib.parse import urlparse

import httpx
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (
    AdminAuditLog,
    Lead,
    Product,
)
from app.products.workflow_automation.models import (
    ProspectCandidate,
    ProspectingCampaign,
)
from app.products.workflow_automation.prospecting_schemas import (
    DiscoveredCandidate,
)


ALLOWED_SEGMENTS = {
    "small_it_provider",
}


class ProspectingConfigurationError(
    RuntimeError
):
    pass


class ProspectingProviderError(RuntimeError):
    pass


class ProspectingProvider(Protocol):
    def discover(
        self,
        campaign: ProspectingCampaign,
    ) -> list[DiscoveredCandidate]:
        ...


def normalize_domain(url: str) -> str:
    parsed = urlparse(url.strip())

    if parsed.scheme not in {
        "http",
        "https",
    }:
        raise ValueError(
            "Prospect website must use HTTP or HTTPS"
        )

    domain = (
        parsed.hostname or ""
    ).strip().lower()

    if domain.startswith("www."):
        domain = domain[4:]

    if not domain or "." not in domain:
        raise ValueError(
            "Prospect website domain is invalid"
        )

    return domain


def valid_business_email(
    email: str,
    domain: str,
) -> bool:
    normalized = email.strip().lower()

    if normalized.count("@") != 1:
        return False

    local, email_domain = normalized.split(
        "@",
        1,
    )

    if not local or not email_domain:
        return False

    return (
        email_domain == domain
        or email_domain.endswith(
            f".{domain}"
        )
    )


def _candidate_schema() -> dict:
    nullable_string = {
        "anyOf": [
            {
                "type": "string",
                "minLength": 1,
            },
            {
                "type": "null",
            },
        ]
    }

    evidence = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "url": {
                "type": "string",
                "minLength": 1,
            },
            "fact": {
                "type": "string",
                "minLength": 1,
            },
        },
        "required": [
            "url",
            "fact",
        ],
    }

    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "candidates": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "business_name": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "website_url": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "segment": {
                            "type": "string",
                            "enum": sorted(
                                ALLOWED_SEGMENTS
                            ),
                        },
                        "location": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "contact_name":
                            nullable_string,
                        "email": {
                            "type": "string",
                            "minLength": 3,
                        },
                        "phone":
                            nullable_string,
                        "evidence": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": 8,
                            "items": evidence,
                        },
                        "fit_score": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 100,
                        },
                        "score_reasons": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": 8,
                            "items": {
                                "type": "string",
                                "minLength": 1,
                            },
                        },
                        "disqualifiers": {
                            "type": "array",
                            "maxItems": 8,
                            "items": {
                                "type": "string",
                                "minLength": 1,
                            },
                        },
                        "outreach_subject": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "outreach_body": {
                            "type": "string",
                            "minLength": 1,
                        },
                    },
                    "required": [
                        "business_name",
                        "website_url",
                        "segment",
                        "location",
                        "contact_name",
                        "email",
                        "phone",
                        "evidence",
                        "fit_score",
                        "score_reasons",
                        "disqualifiers",
                        "outreach_subject",
                        "outreach_body",
                    ],
                },
            },
        },
        "required": [
            "candidates",
        ],
    }


def _extract_output_text(
    payload: dict,
) -> str:
    direct = payload.get("output_text")

    if isinstance(direct, str) and direct:
        return direct

    for item in payload.get("output", []):
        if item.get("type") != "message":
            continue

        for content in item.get(
            "content",
            [],
        ):
            if (
                content.get("type")
                == "output_text"
                and content.get("text")
            ):
                return content["text"]

    raise ProspectingProviderError(
        "OpenAI response contained no "
        "structured output text"
    )


def _extract_source_urls(
    payload: dict,
) -> set[str]:
    urls: set[str] = set()

    for item in payload.get("output", []):
        action = item.get("action") or {}

        for source in action.get(
            "sources",
            [],
        ):
            url = source.get("url")

            if isinstance(url, str) and url:
                urls.add(url)

    return urls


def _normalize_url_for_match(
    url: str,
) -> str:
    parsed = urlparse(url.strip())

    if parsed.scheme not in {
        "http",
        "https",
    }:
        return url.strip().rstrip("/")

    hostname = (
        parsed.hostname or ""
    ).lower()

    if hostname.startswith("www."):
        hostname = hostname[4:]

    path = parsed.path.rstrip("/")

    return f"{hostname}{path}"


def evidence_matches_source(
    evidence_url: str,
    source_url: str,
) -> bool:
    if (
        _normalize_url_for_match(evidence_url)
        == _normalize_url_for_match(source_url)
    ):
        return True

    try:
        return (
            normalize_domain(evidence_url)
            == normalize_domain(source_url)
        )
    except ValueError:
        return False


class OpenAIWebSearchProvider:
    def __init__(
        self,
        *,
        api_key: str,
        timeout_seconds: float = 120.0,
    ):
        if not api_key.strip():
            raise ProspectingConfigurationError(
                "OPENAI_API_KEY is required"
            )

        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_environment(
        cls,
    ) -> "OpenAIWebSearchProvider":
        return cls(
            api_key=os.getenv(
                "OPENAI_API_KEY",
                "",
            )
        )

    def discover(
        self,
        campaign: ProspectingCampaign,
    ) -> list[DiscoveredCandidate]:
        segment_labels = {
            "small_it_provider":
                "small IT providers",
        }

        requested_segments = [
            segment_labels[segment]
            for segment in campaign.segments
        ]

        prompt = (
            "Actively perform multiple web searches "
            "before answering. Find up to "
            f"{campaign.max_candidates} "
            "small IT service providers in "
            f"{campaign.geography}. Search Albany, "
            "Buffalo, Rochester, Syracuse, New York "
            "City, Long Island, Westchester, and other "
            "New York markets. Target managed service "
            "providers, local IT consultants, computer "
            "support firms, Microsoft 365 or Google "
            "Workspace consultants, web technology "
            "agencies, and similar client-service "
            "businesses. The commercial goal is to find "
            "firms that may subcontract fixed-scope "
            "development and automation work to Rafael "
            "or use FieldLookers as a white-label "
            "implementation partner. Relevant overflow "
            "work includes API integrations, form-to-"
            "database workflows, spreadsheet "
            "replacements, internal dashboards, "
            "scheduled notifications, Microsoft 365 or "
            "Google Workspace automation, and custom "
            "client workflow implementation. Favor "
            "small local firms serving small businesses, "
            "firms offering a broad service catalog, "
            "firms discussing custom solutions or "
            "projects, and firms that may lack a large "
            "internal development team. A candidate must "
            "have a real public business website, clear "
            "New York location or service-area evidence, "
            "and a verifiable public business email. "
            "The email may be domain-based or a public "
            "business address from a reputable provider. "
            "Exclude large enterprises, staffing and "
            "recruiting agencies, job boards, hardware-"
            "only retailers, businesses outside New "
            "York, and companies that do not provide IT "
            "services to clients. Score from 0 to 100 "
            "for likelihood of needing a freelance, "
            "overflow, subcontract, or white-label "
            "implementation partner. Workflow or "
            "capacity fit may be a clearly labeled "
            "inference, but factual claims about the "
            "business, services, location, and contact "
            "details must be supported by public source "
            "URLs. The disqualifiers array must be empty "
            "unless a hard exclusion clearly applies. "
            "Do not use disqualifiers merely because no "
            "job posting or subcontractor request is "
            "public. Draft a short, truthful partnership "
            "outreach message for Rafael to review. "
            "Position Rafael as providing fixed-scope "
            "overflow implementation support that the "
            "IT provider can subcontract or offer to its "
            "clients without hiring a full-time "
            "developer. Draft only the personalized "
            "message body without a signature, postal "
            "address, website footer, advertisement "
            "notice, or opt-out text; the platform adds "
            "its verified compliance footer. Do not "
            "claim prior contact, do not invent a person, "
            "do not promise a delivery timeline, and do "
            "not imply the message was sent."
        )

        request_payload = {
            "model": campaign.model,
            "store": False,
            "tools": [
                {
                    "type": "web_search",
                }
            ],
            "include": [
                (
                    "web_search_call."
                    "action.sources"
                )
            ],
            "input": prompt,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": (
                        "workflow_automation_"
                        "prospects"
                    ),
                    "strict": True,
                    "schema":
                        _candidate_schema(),
                }
            },
        }

        try:
            response = httpx.post(
                os.getenv(
                    "OPENAI_RESPONSES_URL",
                    (
                        "https://api.openai.com/"
                        "v1/responses"
                    ),
                ),
                headers={
                    "Authorization":
                        f"Bearer {self.api_key}",
                    "Content-Type":
                        "application/json",
                },
                json=request_payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()

        except httpx.HTTPStatusError as exc:
            request_id = exc.response.headers.get(
                "x-request-id",
                "unavailable",
            )

            raise ProspectingProviderError(
                "OpenAI prospect search failed "
                f"with HTTP "
                f"{exc.response.status_code}; "
                f"request_id={request_id}"
            ) from exc

        except httpx.HTTPError as exc:
            raise ProspectingProviderError(
                "OpenAI prospect search failed"
            ) from exc

        payload = response.json()
        source_urls = _extract_source_urls(
            payload
        )

        try:
            result = json.loads(
                _extract_output_text(payload)
            )
        except (
            json.JSONDecodeError,
            TypeError,
        ) as exc:
            raise ProspectingProviderError(
                "OpenAI prospect output was not "
                "valid JSON"
            ) from exc

        candidates: list[
            DiscoveredCandidate
        ] = []

        for item in result.get(
            "candidates",
            [],
        ):
            try:
                candidate = (
                    DiscoveredCandidate
                    .model_validate(item)
                )
            except ValidationError:
                continue

            verified_evidence = [
                evidence
                for evidence
                in candidate.evidence
                if any(
                    evidence_matches_source(
                        evidence.url,
                        source_url,
                    )
                    for source_url in source_urls
                )
            ]

            if not verified_evidence:
                continue

            candidate.evidence = (
                verified_evidence
            )
            candidates.append(candidate)

        return candidates


def outreach_body_with_footer(
    body: str,
) -> str:
    offer_url = os.getenv(
        "FIELDLOOKERS_WORKFLOW_AUTOMATION_URL",
        (
            "https://jobflow.fieldlookers.com/"
            "workflow-automation"
        ),
    ).strip()

    postal_address = os.getenv(
        "FIELDLOOKERS_OUTREACH_POSTAL_ADDRESS",
        (
            "3 E Evergreen Road, Suite 101 PMB 1172, "
            "New City, NY 10956"
        ),
    ).strip()

    footer = (
        "Rafael Morel\n"
        "FieldLookers LLC\n"
        "Workflow Automation Package: "
        f"{offer_url}\n"
        f"{postal_address}\n\n"
        "This is a business outreach message. "
        "If you prefer not to receive future "
        "messages from me, reply "
        "\"unsubscribe.\""
    )

    return (
        body.strip()
        + "\n\n"
        + footer
    )


def _service_type(segment: str) -> str:
    return {
        "small_it_provider":
            "Small IT provider partnership",
    }[segment]


def run_campaign(
    *,
    db: Session,
    campaign: ProspectingCampaign,
    provider: ProspectingProvider,
) -> dict:
    if campaign.status not in {
        "draft",
        "queued",
    }:
        raise ValueError(
            "Only draft or queued campaigns "
            "can be run"
        )

    campaign.status = "running"
    campaign.started_at = datetime.now(
        timezone.utc
    )
    campaign.completed_at = None
    campaign.error_message = None
    db.commit()

    try:
        discovered = provider.discover(
            campaign
        )

        product = db.scalar(
            select(Product).where(
                Product.slug
                == "workflow-automation",
                Product.status == "active",
            )
        )

        if product is None:
            raise ProspectingConfigurationError(
                "Workflow Automation product "
                "is unavailable"
            )

        saved_count = 0
        skipped_count = 0
        skip_reasons = {
            "invalid_website": 0,
            "wrong_segment": 0,
            "below_minimum_score": 0,
            "has_disqualifiers": 0,
            "missing_evidence": 0,
            "invalid_business_email": 0,
            "duplicate": 0,
        }

        for item in discovered[
            : campaign.max_candidates
        ]:
            try:
                domain = normalize_domain(
                    item.website_url
                )
            except ValueError:
                skipped_count += 1
                skip_reasons[
                    "invalid_website"
                ] += 1
                continue

            rejection_reason = None

            if item.segment not in campaign.segments:
                rejection_reason = "wrong_segment"
            elif (
                item.fit_score
                < campaign.minimum_score
            ):
                rejection_reason = (
                    "below_minimum_score"
                )
            elif item.disqualifiers:
                rejection_reason = (
                    "has_disqualifiers"
                )
            elif not item.evidence:
                rejection_reason = (
                    "missing_evidence"
                )
            elif not valid_business_email(
                item.email,
                domain,
            ):
                rejection_reason = (
                    "invalid_business_email"
                )

            if rejection_reason is not None:
                skipped_count += 1
                skip_reasons[
                    rejection_reason
                ] += 1
                continue

            existing_candidate = db.scalar(
                select(ProspectCandidate).where(
                    ProspectCandidate
                    .normalized_domain
                    == domain
                )
            )

            existing_lead = db.scalar(
                select(Lead).where(
                    Lead.product_id
                    == product.id,
                    Lead.email
                    == item.email.strip().lower(),
                )
            )

            if (
                existing_candidate is not None
                or existing_lead is not None
            ):
                skipped_count += 1
                skip_reasons["duplicate"] += 1
                continue

            lead = Lead(
                product_id=product.id,
                business_name=(
                    item.business_name
                ),
                contact_name=(
                    item.contact_name
                    or "Business contact"
                ),
                email=(
                    item.email
                    .strip()
                    .lower()
                ),
                phone=item.phone,
                service_type=_service_type(
                    item.segment
                ),
                message=(
                    "Agent-qualified Product #6 "
                    "prospect. Review evidence and "
                    "the outreach draft in the "
                    "prospecting queue before "
                    "contacting this business."
                ),
                status="new",
            )

            db.add(lead)
            db.flush()

            candidate = ProspectCandidate(
                campaign_id=campaign.id,
                lead_id=lead.id,
                business_name=(
                    item.business_name
                ),
                website_url=(
                    item.website_url
                ),
                normalized_domain=domain,
                segment=item.segment,
                location=item.location,
                contact_name=(
                    item.contact_name
                ),
                email=(
                    item.email
                    .strip()
                    .lower()
                ),
                phone=item.phone,
                evidence=[
                    evidence.model_dump()
                    for evidence
                    in item.evidence
                ],
                fit_score=item.fit_score,
                score_reasons=(
                    item.score_reasons
                ),
                disqualifiers=(
                    item.disqualifiers
                ),
                outreach_subject=(
                    item.outreach_subject
                ),
                outreach_body=(
                    outreach_body_with_footer(
                        item.outreach_body
                    )
                ),
                review_status="pending",
            )

            db.add(candidate)
            saved_count += 1

        campaign.status = "completed"
        campaign.completed_at = datetime.now(
            timezone.utc
        )

        db.add(
            AdminAuditLog(
                operator_user_id=(
                    campaign.created_by_user_id
                ),
                action=(
                    "workflow_automation."
                    "campaign_completed"
                ),
                target_type=(
                    "prospecting_campaign"
                ),
                target_id=campaign.id,
                tenant_id=None,
                before_data={
                    "status": "running",
                },
                after_data={
                    "status": "completed",
                    "discovered_count":
                        len(discovered),
                    "saved_count":
                        saved_count,
                    "skipped_count":
                        skipped_count,
                    "skip_reasons":
                        skip_reasons,
                },
            )
        )

        db.commit()

        return {
            "campaign_id": campaign.id,
            "status": campaign.status,
            "discovered_count":
                len(discovered),
            "saved_count": saved_count,
            "skipped_count": skipped_count,
        }

    except Exception as exc:
        db.rollback()

        failed_campaign = db.get(
            ProspectingCampaign,
            campaign.id,
        )

        if failed_campaign is not None:
            failed_campaign.status = "failed"
            failed_campaign.completed_at = (
                datetime.now(timezone.utc)
            )
            failed_campaign.error_message = (
                str(exc)[:2000]
            )
            db.commit()

        raise


def run_campaign_in_background(
    campaign_id: int,
) -> None:
    """Run one queued campaign with its own DB session."""
    with SessionLocal() as db:
        campaign = db.get(
            ProspectingCampaign,
            campaign_id,
        )

        if (
            campaign is None
            or campaign.status != "queued"
        ):
            return

        try:
            provider = (
                OpenAIWebSearchProvider
                .from_environment()
            )

            run_campaign(
                db=db,
                campaign=campaign,
                provider=provider,
            )

        except Exception as exc:
            db.rollback()

            failed = db.get(
                ProspectingCampaign,
                campaign_id,
            )

            if (
                failed is not None
                and failed.status
                not in {
                    "completed",
                    "failed",
                }
            ):
                failed.status = "failed"
                failed.completed_at = datetime.now(
                    timezone.utc
                )
                failed.error_message = (
                    str(exc)[:2000]
                )
                db.commit()
