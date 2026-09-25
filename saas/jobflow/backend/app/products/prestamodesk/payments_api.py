from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant, TenantMembership
from app.products.prestamodesk.amortization import money
from app.products.prestamodesk.models import (
    Installment,
    Loan,
    Payment,
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


@router.post("", response_model=PaymentReceipt, status_code=201)
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

    remaining = money(
        installment.total_due
        - installment.paid_amount
    )
    amount = money(payload.amount)

    if amount > remaining:
        raise HTTPException(
            status_code=409,
            detail="Payment exceeds installment balance",
        )

    installment.paid_amount = money(
        installment.paid_amount + amount
    )
    installment.status = (
        "paid"
        if installment.paid_amount == installment.total_due
        else "partial"
    )

    payment = Payment(
        tenant_id=tenant.id,
        loan_id=loan.id,
        installment_id=installment.id,
        recorded_by_user_id=membership.user_id,
        amount=amount,
        payment_method=payload.payment_method,
        reference=payload.reference,
        notes=payload.notes,
        paid_at=(
            payload.paid_at
            or datetime.now(timezone.utc)
        ),
    )

    try:
        db.add(payment)
        db.flush()

        loan_balance = money(
            sum(
                (
                    item.total_due
                    - item.paid_amount
                )
                for item in installments
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

    return PaymentReceipt(
        **payment_data,
        receipt_number=f"PM-{payment.id:08d}",
        installment_total=installment.total_due,
        installment_paid=installment.paid_amount,
        installment_balance=money(
            installment.total_due
            - installment.paid_amount
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
