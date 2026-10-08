from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.products.prestamodesk.payment_corrections import lock_financial_actor, installment_snapshot
from app.models import Tenant, TenantMembership
from app.products.prestamodesk.authorization import (
    require_prestamodesk_payment_member,
)
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
from app.products.prestamodesk.promise_reconciliation import (
    reconcile_payment_promises,
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
    dependencies=[
        Depends(
            require_prestamodesk_payment_member
        ),
    ],
    prefix="/payments",
    tags=["PréstamoDesk Payments"],
)


def payment_fingerprint(payload: PaymentCreate) -> str:
    data = payload.model_dump(mode="json", exclude={"idempotency_key"})
    data["amount"] = format(payload.amount.quantize(Decimal("0.01")), "f")
    if payload.paid_at is not None:
        # Naive dates are interpreted as UTC, matching existing API behavior.
        value = payload.paid_at
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        data["paid_at"] = value.astimezone(timezone.utc).isoformat()
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


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
    loan_late_fee_enabled: bool,
    payment_date,
) -> None:
    if (
        not loan_late_fee_enabled
        or policy is None
        or not policy.enabled
    ):
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
    if membership.role == "collector":
        raise HTTPException(
            status_code=403,
            detail=(
                "Collectors cannot record payments"
            ),
        )

    lock_financial_actor(db, tenant, membership, {"owner", "administrator", "member", "cashier"})

    request_key = str(payload.idempotency_key) if payload.idempotency_key else None
    fingerprint = payment_fingerprint(payload) if request_key else None
    if request_key:
        existing = db.scalar(select(Payment).where(
            Payment.tenant_id == tenant.id,
            Payment.idempotency_key == request_key,
        ))
        if existing is not None:
            if existing.recorded_by_user_id != membership.user_id:
                raise HTTPException(status_code=409, detail="Payment request belongs to another operator")
            if existing.request_fingerprint != fingerprint:
                raise HTTPException(status_code=409, detail="Payment request key was used with different details")
            if existing.voided_at is not None:
                raise HTTPException(status_code=409, detail="Original payment was voided; use a new request key")
            if existing.receipt_snapshot is None:
                raise HTTPException(status_code=409, detail="Original receipt unavailable; review payment history")
            return PaymentReceipt.model_validate(existing.receipt_snapshot)

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

    before_payment = installment_snapshot(installment)

    assess_late_fee(
        installment=installment,
        policy=policy,
        loan_late_fee_enabled=(
            loan.late_fee_enabled
        ),
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
        idempotency_key=request_key,
        request_fingerprint=fingerprint,
        correction_snapshot={"before": before_payment, "after": installment_snapshot(installment)},
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

        reconcile_payment_promises(
            db=db,
            payment=payment,
        )

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

        payment_data = PaymentRead.model_validate(
            payment
        ).model_dump()

        ordinary_remaining = ordinary_balance(
            installment
        )
        late_remaining = late_fee_balance(
            installment
        )

        receipt = PaymentReceipt(
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
        if request_key:
            payment.receipt_snapshot = receipt.model_dump(mode="json")
        db.commit()
    except Exception:
        db.rollback()
        raise

    return receipt


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
