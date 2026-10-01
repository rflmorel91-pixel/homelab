from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant, TenantMembership
from app.products.prestamodesk.amortization import money
from app.products.prestamodesk.late_fees import (
    calculate_late_fee,
)
from app.products.prestamodesk.models import (
    Installment,
    LateFeePolicy,
    Loan,
    Payment,
)
from app.products.prestamodesk.payment_allocation import (
    allocate_payment,
)
from app.products.prestamodesk.schemas import (
    PaymentCreate,
    PaymentRead,
    PaymentReceipt,
)
from app.tenant_context import (
    get_current_tenant,
    get_current_tenant_membership,
)


router = APIRouter(
    prefix="/payments",
    tags=["PréstamoDesk Payments"],
)


def ordinary_balance(
    installment: Installment,
) -> Decimal:
    return money(
        installment.principal_due
        - installment.principal_paid
        + installment.interest_due
        - installment.interest_paid
    )


def late_fee_balance(
    installment: Installment,
) -> Decimal:
    return money(
        installment.late_fee_accrued
        - installment.late_fee_paid
    )


def total_installment_balance(
    installment: Installment,
) -> Decimal:
    return money(
        ordinary_balance(installment)
        + late_fee_balance(installment)
    )


def assess_late_fee(
    *,
    installment: Installment,
    policy: LateFeePolicy | None,
    payment_date,
) -> None:
    if policy is None or not policy.enabled:
        return

    if (
        installment.late_fee_assessed_through
        is not None
        and payment_date
        < installment.late_fee_assessed_through
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Payment date precedes an existing "
                "late-fee assessment"
            ),
        )

    calculation = calculate_late_fee(
        due_date=installment.due_date,
        ordinary_balance=ordinary_balance(
            installment
        ),
        installment_total=installment.total_due,
        daily_rate_percent=(
            policy.daily_rate_percent
        ),
        grace_days=policy.grace_days,
        cap_percent=policy.cap_percent,
        effective_date=policy.effective_date,
        assessment_through=payment_date,
        previously_assessed_through=(
            installment.late_fee_assessed_through
        ),
        previously_accrued=(
            installment.late_fee_accrued
        ),
    )

    installment.late_fee_accrued = (
        calculation.fee_accrued
    )

    if calculation.assessment_through is not None:
        installment.late_fee_assessed_through = (
            calculation.assessment_through
        )


@router.post(
    "",
    response_model=PaymentReceipt,
    status_code=201,
)
def record_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    membership: TenantMembership = Depends(
        get_current_tenant_membership
    ),
):
    installment = db.scalar(
        select(Installment)
        .where(
            Installment.id == payload.installment_id,
            Installment.tenant_id == tenant.id,
        )
        .with_for_update()
    )

    if installment is None:
        raise HTTPException(
            status_code=404,
            detail="Installment not found",
        )

    loan = db.scalar(
        select(Loan)
        .where(
            Loan.id == installment.loan_id,
            Loan.tenant_id == tenant.id,
        )
        .with_for_update()
    )

    if loan is None:
        raise HTTPException(
            status_code=404,
            detail="Loan not found",
        )

    if loan.status != "active":
        raise HTTPException(
            status_code=409,
            detail="Loan is not active",
        )

    installments = db.scalars(
        select(Installment)
        .where(
            Installment.loan_id == loan.id,
            Installment.tenant_id == tenant.id,
        )
        .order_by(Installment.sequence_number)
        .with_for_update()
    ).all()

    policy = db.scalar(
        select(LateFeePolicy)
        .where(
            LateFeePolicy.tenant_id == tenant.id
        )
        .with_for_update()
    )

    paid_at = (
        payload.paid_at
        or datetime.now(timezone.utc)
    )
    payment_date = paid_at.date()

    if payment_date > datetime.now(
        timezone.utc
    ).date():
        raise HTTPException(
            status_code=422,
            detail="Payment date cannot be in the future",
        )

    assess_late_fee(
        installment=installment,
        policy=policy,
        payment_date=payment_date,
    )

    try:
        allocation = allocate_payment(
            amount=payload.amount,
            late_fee_balance=late_fee_balance(
                installment
            ),
            interest_balance=money(
                installment.interest_due
                - installment.interest_paid
            ),
            principal_balance=money(
                installment.principal_due
                - installment.principal_paid
            ),
        )
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from None

    installment.late_fee_paid = money(
        installment.late_fee_paid
        + allocation.late_fee_amount
    )
    installment.interest_paid = money(
        installment.interest_paid
        + allocation.interest_amount
    )
    installment.principal_paid = money(
        installment.principal_paid
        + allocation.principal_amount
    )
    installment.paid_amount = money(
        installment.interest_paid
        + installment.principal_paid
    )

    installment.status = (
        "paid"
        if total_installment_balance(
            installment
        ) == Decimal("0.00")
        else "partial"
    )

    payment = Payment(
        tenant_id=tenant.id,
        loan_id=loan.id,
        installment_id=installment.id,
        recorded_by_user_id=membership.user_id,
        amount=allocation.amount,
        principal_amount=(
            allocation.principal_amount
        ),
        interest_amount=(
            allocation.interest_amount
        ),
        late_fee_amount=(
            allocation.late_fee_amount
        ),
        payment_method=payload.payment_method,
        reference=payload.reference,
        notes=payload.notes,
        paid_at=paid_at,
    )

    try:
        db.add(payment)
        db.flush()

        loan_balance = money(
            sum(
                (
                    total_installment_balance(
                        item
                    )
                    for item in installments
                ),
                Decimal("0.00"),
            )
        )

        if loan_balance == Decimal("0.00"):
            loan.status = "paid"

        db.commit()
        db.refresh(payment)
        db.refresh(installment)
        db.refresh(loan)
    except Exception:
        db.rollback()
        raise

    payment_data = PaymentRead.model_validate(
        payment
    ).model_dump()

    ordinary_remaining = ordinary_balance(
        installment
    )
    late_remaining = late_fee_balance(
        installment
    )

    return PaymentReceipt(
        **payment_data,
        receipt_number=f"PM-{payment.id:08d}",
        installment_total=installment.total_due,
        installment_paid=installment.paid_amount,
        installment_balance=money(
            ordinary_remaining + late_remaining
        ),
        installment_ordinary_balance=(
            ordinary_remaining
        ),
        installment_late_fee_accrued=(
            installment.late_fee_accrued
        ),
        installment_late_fee_paid=(
            installment.late_fee_paid
        ),
        installment_late_fee_balance=(
            late_remaining
        ),
        installment_status=installment.status,
        loan_balance=loan_balance,
        loan_status=loan.status,
        currency="DOP",
    )


@router.get(
    "/loan/{loan_id}",
    response_model=list[PaymentRead],
)
def list_loan_payments(
    loan_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    membership: TenantMembership = Depends(
        get_current_tenant_membership
    ),
):
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

    result = db.execute(
        select(Payment)
        .where(
            Payment.loan_id == loan.id,
            Payment.tenant_id == tenant.id,
        )
        .order_by(Payment.paid_at, Payment.id)
    )

    return result.scalars().all()
