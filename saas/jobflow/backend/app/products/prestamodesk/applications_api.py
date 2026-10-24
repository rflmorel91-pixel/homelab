from app.platform.resource_limits import lock_tenant_capacity
from app.products.prestamodesk.loan_limits import require_new_loan_capacity
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant
from app.products.prestamodesk.authorization import (
    require_prestamodesk_operations_member,
    require_prestamodesk_manager as require_current_tenant_owner,
)
from app.products.prestamodesk.amortization import (
    build_fixed_schedule,
)
from app.products.prestamodesk.application_schemas import (
    ApplicationQuoteRead,
    QuoteInstallmentRead,
    InternalApplicationTerms,
    ApplicationConversionRead,
    ApplicationRead,
    ApplicationUpdate,
    ApplicationReviewPacketRead,
    ApplicationReviewEventRead,
    PrivateReviewDocumentRead,
)
from app.products.prestamodesk.models import (
    Borrower,
    Installment,
    Loan,
    Prospect,
    LoanApplication,
    ApplicationReview,
    ApplicationReviewEvent,
    ApplicationReviewDocument,
)
from app.products.prestamodesk.private_documents import (
    MAX_PRIVATE_DOCUMENT_BYTES,
    detect_document,
    private_document_path,
    remove_private_document,
    store_private_document,
)
from app.tenant_context import (
    get_current_tenant,
)


router = APIRouter(
    prefix="/applications",
    tags=["PréstamoDesk Applications"],
    dependencies=[
        Depends(
            require_prestamodesk_operations_member
        ),
        Depends(require_current_tenant_owner),
    ],
)


def get_tenant_application(
    db: Session,
    tenant_id: int,
    application_id: int,
    *,
    lock: bool = False,
) -> LoanApplication:
    statement = select(LoanApplication).where(
        LoanApplication.id == application_id,
        LoanApplication.tenant_id == tenant_id,
    )

    if lock:
        statement = statement.with_for_update()

    application = db.scalar(statement)

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    return application


def approval_gaps(
    db: Session,
    tenant_id: int,
    application: LoanApplication,
    packet: ApplicationReviewPacketRead,
) -> list[str]:
    gaps = []
    if application.loan_type == "vehicle":
        if packet.inspection.status != "passed":
            gaps.append("vehicle inspection must pass")
        if not packet.inspection.inspector_name or not packet.inspection.inspected_at:
            gaps.append("vehicle inspection must identify inspector and date")
        if not packet.inspection.findings:
            gaps.append("vehicle inspection findings must be recorded")

    required_documents = {"identity", "income"}
    if application.loan_type == "vehicle":
        required_documents.add("vehicle_registration")
    documents = {item.document_type: item for item in packet.documents}
    stored = {
        item.storage_ref: item
        for item in db.scalars(
            select(ApplicationReviewDocument).where(
                ApplicationReviewDocument.tenant_id == tenant_id,
                ApplicationReviewDocument.application_id == application.id,
            )
        )
    }
    for document_type in sorted(required_documents):
        item = documents.get(document_type)
        record = stored.get(str(item.storage_ref)) if item and item.storage_ref else None
        if (
            item is None or item.status != "verified" or record is None
            or record.document_type != document_type
        ):
            gaps.append(f"{document_type} document must be verified")

    if not any(
        item.status == "contacted" and item.outcome_notes
        for item in packet.references
    ):
        gaps.append("at least one reference must be contacted and documented")

    if packet.assessment is None:
        gaps.append("credit assessment is required")
    elif packet.assessment.recommendation != "approve":
        gaps.append("credit assessment must recommend approval")

    return gaps


DocumentUploadType = Literal["identity", "income", "vehicle_registration", "contract"]


@router.put(
    "/{application_id}/documents/{document_type}",
    response_model=PrivateReviewDocumentRead,
    status_code=201,
)
async def upload_application_document(
    application_id: int,
    document_type: DocumentUploadType,
    request: Request,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    application = get_tenant_application(db, tenant.id, application_id, lock=True)
    if application.status in {"rejected", "converted"}:
        raise HTTPException(status_code=409, detail="This application can no longer be reviewed")
    if application.status == "approved" and document_type != "contract":
        raise HTTPException(status_code=409, detail="Approved review evidence is read-only")

    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_PRIVATE_DOCUMENT_BYTES:
        raise HTTPException(status_code=413, detail="Document exceeds the 8 MiB limit")
    data = bytearray()
    async for chunk in request.stream():
        data.extend(chunk)
        if len(data) > MAX_PRIVATE_DOCUMENT_BYTES:
            raise HTTPException(status_code=413, detail="Document exceeds the 8 MiB limit")
    extension, content_type = detect_document(request.headers.get("content-type", ""), bytes(data))
    storage_ref, file_key, digest = store_private_document(
        tenant.id, application.id, bytes(data), extension,
    )
    record = ApplicationReviewDocument(
        storage_ref=str(storage_ref),
        tenant_id=tenant.id,
        application_id=application.id,
        document_type=document_type,
        content_type=content_type,
        byte_size=len(data),
        sha256=digest,
        file_key=file_key,
    )
    db.add(record)
    write_review_event(db, application, tenant.id, "document_uploaded", {
        "document_type": document_type,
        "storage_ref": str(storage_ref),
        "byte_size": len(data),
        "sha256": digest,
    })
    try:
        db.commit()
    except Exception:
        db.rollback()
        remove_private_document(file_key)
        raise
    db.refresh(record)
    return record


@router.get(
    "/{application_id}/documents/{document_type}/{storage_ref}",
)
def download_application_document(
    application_id: int,
    document_type: DocumentUploadType,
    storage_ref: UUID,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    application = get_tenant_application(db, tenant.id, application_id)
    record = db.scalar(select(ApplicationReviewDocument).where(
        ApplicationReviewDocument.storage_ref == str(storage_ref),
        ApplicationReviewDocument.tenant_id == tenant.id,
        ApplicationReviewDocument.application_id == application.id,
        ApplicationReviewDocument.document_type == document_type,
    ))
    if record is None:
        raise HTTPException(status_code=404, detail="Document not found")
    try:
        path = private_document_path(record.file_key)
    except (FileNotFoundError, OSError):
        raise HTTPException(status_code=404, detail="Document not found") from None
    extension = {"application/pdf": "pdf", "image/jpeg": "jpg", "image/png": "png"}[record.content_type]
    return FileResponse(
        path,
        media_type=record.content_type,
        filename=f"{document_type}-{storage_ref}.{extension}",
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )


def write_review_event(db: Session, application: LoanApplication, tenant_id: int, event_type: str, details: dict):
    db.add(ApplicationReviewEvent(
        application_id=application.id,
        tenant_id=tenant_id,
        event_type=event_type,
        details=details,
    ))


def quote_terms(payload: InternalApplicationTerms) -> ApplicationQuoteRead:
    calculation = build_fixed_schedule(
        principal_amount=payload.principal_amount,
        flat_interest_rate_percent=payload.flat_interest_rate_percent,
        installment_count=payload.installment_count,
        payment_frequency=payload.payment_frequency,
        first_payment_date=payload.first_payment_date,
    )
    return ApplicationQuoteRead(
        principal_amount=calculation.principal_amount,
        flat_interest_rate_percent=calculation.flat_interest_rate_percent,
        total_interest=calculation.total_interest,
        total_due=calculation.total_due,
        installment_count=payload.installment_count,
        payment_frequency=payload.payment_frequency,
        installments=[QuoteInstallmentRead(
            sequence_number=item.sequence_number, due_date=item.due_date,
            principal_due=item.principal_due, interest_due=item.interest_due,
            total_due=item.total_due,
        ) for item in calculation.installments],
    )


@router.post("/quote", response_model=ApplicationQuoteRead)
def quote_internal_application(payload: InternalApplicationTerms):
    return quote_terms(payload)


@router.get(
    "",
    response_model=list[ApplicationRead],
)
def list_applications(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    return db.scalars(
        select(LoanApplication)
        .where(
            LoanApplication.tenant_id == tenant.id,
        )
        .order_by(
            LoanApplication.created_at.desc(),
            LoanApplication.id.desc(),
        )
    ).all()


@router.get(
    "/{application_id}",
    response_model=ApplicationRead,
)
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    return get_tenant_application(
        db,
        tenant.id,
        application_id,
    )


@router.put(
    "/{application_id}/review-packet",
    response_model=ApplicationReviewPacketRead,
)
def update_application_review_packet(
    application_id: int,
    payload: ApplicationReviewPacketRead,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    application = get_tenant_application(db, tenant.id, application_id, lock=True)
    if application.status in {"rejected", "converted"}:
        raise HTTPException(status_code=409, detail="This application can no longer be reviewed")

    packet_data = payload.model_dump(mode="json")
    if application.status == "approved" and application.review_packet is not None:
        current = ApplicationReviewPacketRead.model_validate(
            application.review_packet.packet if application.review_packet else {}
        ).model_dump(mode="json")
        current_evidence = {key: value for key, value in current.items() if key != "contract"}
        new_evidence = {key: value for key, value in packet_data.items() if key != "contract"}
        if current_evidence != new_evidence:
            raise HTTPException(status_code=409, detail="Approved review evidence is read-only")

    packet_was_missing = application.review_packet is None
    if packet_was_missing:
        application.review_packet = ApplicationReview(
            tenant_id=tenant.id,
            packet=packet_data,
        )
    else:
        application.review_packet.packet = packet_data

    if application.status == "new":
        application.status = "reviewing"
        application.reviewed_at = datetime.now(timezone.utc)
    write_review_event(db, application, tenant.id, "packet_backfilled" if packet_was_missing and application.status == "approved" else "packet_updated", {
        "status": application.status,
    })
    db.commit()
    db.refresh(application)
    return ApplicationReviewPacketRead.model_validate(packet_data)


@router.get(
    "/{application_id}/review-events",
    response_model=list[ApplicationReviewEventRead],
)
def list_application_review_events(
    application_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    application = get_tenant_application(db, tenant.id, application_id)
    return db.scalars(
        select(ApplicationReviewEvent)
        .where(
            ApplicationReviewEvent.application_id == application.id,
            ApplicationReviewEvent.tenant_id == tenant.id,
        )
        .order_by(ApplicationReviewEvent.created_at, ApplicationReviewEvent.id)
    ).all()


@router.put(
    "/{application_id}",
    response_model=ApplicationRead,
)
def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    application = get_tenant_application(
        db,
        tenant.id,
        application_id,
        lock=True,
    )

    if application.status == "converted":
        raise HTTPException(
            status_code=409,
            detail="Converted application cannot be changed",
        )

    if application.status == "rejected":
        raise HTTPException(
            status_code=409,
            detail="Rejected application cannot be changed",
        )

    allowed_transitions = {
        "new": {"reviewing"},
        "reviewing": {"approved", "rejected"},
        "approved": set(),
    }

    if payload.status not in allowed_transitions.get(
        application.status,
        set(),
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                f"Application cannot move from "
                f"{application.status} to {payload.status}"
            ),
        )

    now = datetime.now(timezone.utc)
    if payload.status in {"approved", "rejected"} and not payload.decision_reason:
        raise HTTPException(status_code=422, detail="A written decision reason is required")
    if payload.status == "approved":
        packet = ApplicationReviewPacketRead.model_validate(
            application.review_packet.packet if application.review_packet else {}
        )
        gaps = approval_gaps(db, tenant.id, application, packet)
        if gaps:
            raise HTTPException(
                status_code=409,
                detail={"message": "Review packet is incomplete", "gaps": gaps},
            )
    application.status = payload.status
    application.decision_reason = payload.decision_reason

    if payload.status == "reviewing":
        application.reviewed_at = now
    elif payload.status == "approved":
        application.approved_at = now

    write_review_event(db, application, tenant.id, payload.status, {
        "reason": payload.decision_reason,
    })

    db.commit()
    db.refresh(application)

    return application


@router.post(
    "/{application_id}/convert",
    response_model=ApplicationConversionRead,
    status_code=201,
)
def convert_application(
    application_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    lock_tenant_capacity(db, tenant.id)
    application = get_tenant_application(
        db,
        tenant.id,
        application_id,
        lock=True,
    )

    if (
        application.status == "converted"
        or application.converted_borrower_id is not None
        or application.converted_loan_id is not None
    ):
        raise HTTPException(
            status_code=409,
            detail="Application has already been converted",
        )
    if application.status != "approved":
        raise HTTPException(
            status_code=409,
            detail=(
                "Application must be approved "
                "before conversion"
            ),
        )

    packet = ApplicationReviewPacketRead.model_validate(
        application.review_packet.packet if application.review_packet else {}
    )
    if (
        packet.contract.status != "signed"
        or packet.contract.signed_copy_ref is None
        or packet.contract.signed_at is None
        or packet.contract.template_version is None
    ):
        raise HTTPException(
            status_code=409,
            detail="A signed contract and private copy reference are required before conversion",
        )
    contract_document = db.scalar(select(ApplicationReviewDocument.id).where(
        ApplicationReviewDocument.storage_ref == str(packet.contract.signed_copy_ref),
        ApplicationReviewDocument.tenant_id == tenant.id,
        ApplicationReviewDocument.application_id == application.id,
        ApplicationReviewDocument.document_type == "contract",
    ))
    if contract_document is None:
        raise HTTPException(
            status_code=409,
            detail="The signed contract copy must be uploaded to private storage before conversion",
        )

    prospect = None
    if application.source_prospect_id is not None:
        prospect = db.scalar(select(Prospect).where(
            Prospect.id == application.source_prospect_id,
            Prospect.tenant_id == tenant.id,
        ).with_for_update())
        if prospect is None or prospect.status != "qualified" or prospect.converted_borrower_id is not None:
            raise HTTPException(status_code=409, detail="Source prospect cannot be converted")

    require_new_loan_capacity(db, tenant.id)

    calculation = build_fixed_schedule(
        principal_amount=application.principal_amount,
        flat_interest_rate_percent=(
            application.flat_interest_rate_percent
        ),
        installment_count=application.installment_count,
        payment_frequency=application.payment_frequency,
        first_payment_date=application.first_payment_date,
    )

    borrower = Borrower(
        tenant_id=tenant.id,
        full_name=application.full_name,
        document_type=application.document_type,
        document_number=application.document_number,
        phone=application.phone,
        email=application.email,
        address=application.address,
        municipality=application.municipality,
        province=application.province,
        status="active",
        notes=(
            "Creado desde solicitud "
            f"#{application.id}."
        ),
    )

    loan = Loan(
        tenant_id=tenant.id,
        borrower_id=0,
        loan_type=application.loan_type,
        vehicle_cash_price=application.vehicle_cash_price,
        vehicle_down_payment=application.vehicle_down_payment,
        vehicle_make=application.vehicle_make,
        vehicle_model=application.vehicle_model,
        vehicle_year=application.vehicle_year,
        vehicle_color=application.vehicle_color,
        vehicle_vin=application.vehicle_vin,
        vehicle_license_plate=(
            application.vehicle_license_plate
        ),
        vehicle_seller=application.vehicle_seller,
        vehicle_notes=application.vehicle_notes,
        principal_amount=calculation.principal_amount,
        flat_interest_rate_percent=(
            calculation.flat_interest_rate_percent
        ),
        total_interest=calculation.total_interest,
        total_due=calculation.total_due,
        installment_count=application.installment_count,
        payment_frequency=application.payment_frequency,
        start_date=application.start_date,
        first_payment_date=application.first_payment_date,
        currency="DOP",
        status="active",
        late_fee_enabled=False,
        notes=application.notes,
    )

    try:
        db.add(borrower)
        db.flush()

        loan.borrower_id = borrower.id
        db.add(loan)
        db.flush()

        db.add_all(
            [
                Installment(
                    tenant_id=tenant.id,
                    loan_id=loan.id,
                    sequence_number=item.sequence_number,
                    due_date=item.due_date,
                    principal_due=item.principal_due,
                    interest_due=item.interest_due,
                    total_due=item.total_due,
                    paid_amount=0,
                    status="pending",
                )
                for item in calculation.installments
            ]
        )

        if prospect is not None:
            prospect.converted_borrower_id = borrower.id
            prospect.status = "converted"
        application.converted_borrower_id = borrower.id
        application.converted_loan_id = loan.id
        application.status = "converted"
        application.converted_at = datetime.now(timezone.utc)
        write_review_event(db, application, tenant.id, "converted", {
            "borrower_id": borrower.id,
            "loan_id": loan.id,
        })

        db.commit()
        db.refresh(application)
    except Exception:
        db.rollback()
        raise

    return ApplicationConversionRead(
        application_id=application.id,
        borrower_id=borrower.id,
        loan_id=loan.id,
        status="converted",
    )
