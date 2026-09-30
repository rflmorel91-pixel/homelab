from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.products.prestamodesk.amortization import (
    build_fixed_schedule,
)
from app.products.prestamodesk.application_schemas import (
    ApplicationQuoteCreate,
    ApplicationQuoteRead,
    PublicApplicationCreate,
    PublicApplicationRead,
    QuoteInstallmentRead,
)
from app.products.prestamodesk.models import LoanApplication
from app.products.prestamodesk.prospects_public_api import (
    get_public_tenant,
)


APPLICATION_CONSENT_NOTICE_VERSION = "2026-09-30"

router = APIRouter(
    prefix="/public/tenants",
    tags=["PréstamoDesk Public Applications"],
)


def calculate(payload: ApplicationQuoteCreate):
    return build_fixed_schedule(
        principal_amount=payload.principal_amount,
        flat_interest_rate_percent=(
            payload.flat_interest_rate_percent
        ),
        installment_count=payload.installment_count,
        payment_frequency=payload.payment_frequency,
        first_payment_date=payload.first_payment_date,
    )


@router.post(
    "/{tenant_slug}/quote",
    response_model=ApplicationQuoteRead,
)
def create_public_quote(
    tenant_slug: str,
    payload: ApplicationQuoteCreate,
    db: Session = Depends(get_db),
):
    get_public_tenant(db, tenant_slug)
    calculation = calculate(payload)

    return ApplicationQuoteRead(
        principal_amount=calculation.principal_amount,
        flat_interest_rate_percent=(
            calculation.flat_interest_rate_percent
        ),
        total_interest=calculation.total_interest,
        total_due=calculation.total_due,
        installment_count=payload.installment_count,
        payment_frequency=payload.payment_frequency,
        installments=[
            QuoteInstallmentRead(
                sequence_number=item.sequence_number,
                due_date=item.due_date,
                principal_due=item.principal_due,
                interest_due=item.interest_due,
                total_due=item.total_due,
            )
            for item in calculation.installments
        ],
    )


@router.post(
    "/{tenant_slug}/applications",
    response_model=PublicApplicationRead,
    status_code=201,
)
def create_public_application(
    tenant_slug: str,
    payload: PublicApplicationCreate,
    db: Session = Depends(get_db),
):
    tenant = get_public_tenant(db, tenant_slug)
    calculation = calculate(payload)

    application = LoanApplication(
        tenant_id=tenant.id,
        full_name=payload.full_name,
        document_type=payload.document_type,
        document_number=payload.document_number,
        phone=payload.phone,
        email=payload.email,
        address=payload.address,
        municipality=payload.municipality,
        province=payload.province,
        loan_type=payload.loan_type,
        vehicle_cash_price=payload.vehicle_cash_price,
        vehicle_down_payment=payload.vehicle_down_payment,
        vehicle_make=payload.vehicle_make,
        vehicle_model=payload.vehicle_model,
        vehicle_year=payload.vehicle_year,
        vehicle_color=payload.vehicle_color,
        vehicle_vin=payload.vehicle_vin,
        vehicle_license_plate=payload.vehicle_license_plate,
        vehicle_seller=payload.vehicle_seller,
        vehicle_notes=payload.vehicle_notes,
        principal_amount=calculation.principal_amount,
        flat_interest_rate_percent=(
            calculation.flat_interest_rate_percent
        ),
        total_interest=calculation.total_interest,
        total_due=calculation.total_due,
        installment_count=payload.installment_count,
        payment_frequency=payload.payment_frequency,
        start_date=payload.start_date,
        first_payment_date=payload.first_payment_date,
        currency="DOP",
        status="new",
        notes=payload.notes,
        consented_at=datetime.now(timezone.utc),
        consent_notice_version=(
            APPLICATION_CONSENT_NOTICE_VERSION
        ),
    )

    try:
        db.add(application)
        db.commit()
        db.refresh(application)
    except Exception:
        db.rollback()
        raise

    return PublicApplicationRead(
        application_id=application.id,
        status="received",
    )
