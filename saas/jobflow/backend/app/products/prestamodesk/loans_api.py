from decimal import Decimal
import hashlib
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.products.prestamodesk.payment_corrections import lock_financial_actor
from app.database import get_db
from app.models import Tenant, TenantMembership
from app.products.prestamodesk.authorization import (
    require_prestamodesk_operations_member,
    require_prestamodesk_manager as require_current_tenant_owner,
)
from app.products.prestamodesk.amortization import (
    build_fixed_schedule,
)
from app.products.prestamodesk.models import (
    Borrower,
    Installment,
    LateFeePolicy,
    Loan,
)
from app.products.prestamodesk.schemas import (
    InstallmentRead,
    LoanCreate,
    LoanDetail,
    LoanLateFeeUpdate,
    LoanRead,
)
from app.tenant_context import (
    get_current_tenant,
)


router = APIRouter(
    dependencies=[
        Depends(
            require_prestamodesk_operations_member
        ),
    ],
    prefix="/loans",
    tags=["PréstamoDesk Loans"],
)


def get_loan_or_404(
    loan_id: int,
    tenant: Tenant,
    db: Session,
) -> Loan:
    loan = db.scalar(
        select(Loan).where(
            Loan.id == loan_id,
            Loan.tenant_id == tenant.id,
        )
    )

    if loan is None:
        raise HTTPException(
            status_code=404,
            detail="Loan not found",
        )

    return loan


def require_enabled_late_fee_policy(
    db: Session,
    tenant_id: int,
) -> None:
    policy = db.scalar(
        select(LateFeePolicy).where(
            LateFeePolicy.tenant_id == tenant_id,
            LateFeePolicy.enabled.is_(True),
        )
    )

    if policy is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Configure and enable the tenant "
                "late-fee policy first"
            ),
        )


def build_loan_detail(
    loan: Loan,
    db: Session,
) -> LoanDetail:
    installments = db.scalars(
        select(Installment)
        .where(
            Installment.loan_id == loan.id,
            Installment.tenant_id == loan.tenant_id,
        )
        .order_by(Installment.sequence_number)
    ).all()

    loan_data = LoanRead.model_validate(loan).model_dump()

    return LoanDetail(
        **loan_data,
        installments=[
            InstallmentRead.model_validate(item)
            for item in installments
        ],
    )


def loan_fingerprint(payload: LoanCreate) -> str:
    data = payload.model_dump(mode="json", exclude={"idempotency_key"})
    for name, value in payload.model_dump().items():
        if isinstance(value, Decimal):
            data[name] = format(value.normalize(), "f")
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@router.post("", response_model=LoanDetail, status_code=201)
def create_loan(
    payload: LoanCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    membership: TenantMembership = Depends(
        require_current_tenant_owner
    ),
):
    lock_financial_actor(db, tenant, membership, {"owner", "administrator"})
    key = str(payload.idempotency_key) if payload.idempotency_key else None
    fingerprint = loan_fingerprint(payload) if key else None
    if key:
        existing = db.scalar(select(Loan).where(Loan.tenant_id == tenant.id, Loan.idempotency_key == key))
        if existing is not None:
            if existing.created_by_user_id != membership.user_id:
                raise HTTPException(status_code=409, detail="Loan request belongs to another operator")
            if existing.request_fingerprint != fingerprint:
                raise HTTPException(status_code=409, detail="Loan request key was used with different details")
            return LoanDetail.model_validate(existing.creation_snapshot)
    borrower = db.scalar(
        select(Borrower).where(
            Borrower.id == payload.borrower_id,
            Borrower.tenant_id == tenant.id,
        )
    )

    if borrower is None:
        raise HTTPException(
            status_code=404,
            detail="Borrower not found",
        )

    if borrower.status != "active":
        raise HTTPException(
            status_code=409,
            detail="Borrower is inactive",
        )

    if payload.first_payment_date < payload.start_date:
        raise HTTPException(
            status_code=422,
            detail=(
                "First payment date cannot be before "
                "the loan start date"
            ),
        )

    if payload.late_fee_enabled:
        require_enabled_late_fee_policy(
            db,
            tenant.id,
        )

    calculation = build_fixed_schedule(
        principal_amount=payload.principal_amount,
        flat_interest_rate_percent=(
            payload.flat_interest_rate_percent
        ),
        installment_count=payload.installment_count,
        payment_frequency=payload.payment_frequency,
        first_payment_date=payload.first_payment_date,
    )

    loan = Loan(
        idempotency_key=key,
        request_fingerprint=fingerprint,
        created_by_user_id=membership.user_id,
        tenant_id=tenant.id,
        borrower_id=borrower.id,
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
        status="active",
        late_fee_enabled=payload.late_fee_enabled,
        notes=payload.notes,
    )

    try:
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

        db.flush()
        detail = build_loan_detail(loan, db)
        if key:
            loan.creation_snapshot = detail.model_dump(mode="json")
        db.commit()
        db.refresh(loan)
    except Exception:
        db.rollback()
        raise

    return detail


@router.put(
    "/{loan_id}/late-fee",
    response_model=LoanRead,
)
def update_loan_late_fee(
    loan_id: int,
    payload: LoanLateFeeUpdate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    _: TenantMembership = Depends(
        require_current_tenant_owner
    ),
):
    loan = get_loan_or_404(
        loan_id,
        tenant,
        db,
    )

    if payload.late_fee_enabled:
        require_enabled_late_fee_policy(
            db,
            tenant.id,
        )

    loan.late_fee_enabled = payload.late_fee_enabled

    db.commit()
    db.refresh(loan)

    return loan


@router.get("", response_model=list[LoanRead])
def list_loans(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    result = db.execute(
        select(Loan)
        .where(Loan.tenant_id == tenant.id)
        .order_by(Loan.id)
    )

    return result.scalars().all()


@router.get("/{loan_id}", response_model=LoanDetail)
def get_loan(
    loan_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    loan = get_loan_or_404(loan_id, tenant, db)
    return build_loan_detail(loan, db)
