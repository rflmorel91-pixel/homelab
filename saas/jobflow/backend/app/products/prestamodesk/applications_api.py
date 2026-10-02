from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant
from app.products.prestamodesk.authorization import (
    require_prestamodesk_operations_member,
)
from app.products.prestamodesk.amortization import (
    build_fixed_schedule,
)
from app.products.prestamodesk.application_schemas import (
    ApplicationConversionRead,
    ApplicationRead,
    ApplicationUpdate,
)
from app.products.prestamodesk.models import (
    Borrower,
    Installment,
    Loan,
    LoanApplication,
)
from app.tenant_context import (
    get_current_tenant,
    require_current_tenant_owner,
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
    application.status = payload.status

    if payload.status == "reviewing":
        application.reviewed_at = now
    elif payload.status == "approved":
        application.approved_at = now

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

        application.converted_borrower_id = borrower.id
        application.converted_loan_id = loan.id
        application.status = "converted"
        application.converted_at = datetime.now(timezone.utc)

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
