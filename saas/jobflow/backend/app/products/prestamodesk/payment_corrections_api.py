"""Traceable void of the latest, unclosed, snapshot-backed loan payment."""
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.admin import add_admin_audit
from app.database import get_db
from app.models import Tenant, TenantMembership
from app.products.prestamodesk.amortization import money
from app.products.prestamodesk.authorization import require_prestamodesk_administrator
from app.products.prestamodesk.models import Installment, Loan, Payment, PaymentPromise, PromisePaymentAllocation
from app.products.prestamodesk.payment_corrections import MONEY_FIELDS, installment_snapshot, lock_financial_actor
from app.products.prestamodesk.schemas import PaymentRead, PaymentVoidCreate
from app.tenant_context import get_current_tenant, get_current_tenant_membership

router = APIRouter(prefix="/payments", tags=["PréstamoDesk Payment Corrections"],
                   dependencies=[Depends(require_prestamodesk_administrator)])


def conflict(message):
    raise HTTPException(status_code=409, detail=message)


@router.post("/{payment_id}/void", response_model=PaymentRead)
def void_payment(payment_id: int, payload: PaymentVoidCreate,
                 db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant),
                 membership: TenantMembership = Depends(get_current_tenant_membership)):
    lock_financial_actor(db, tenant, membership, {"owner", "administrator"})
    payment = db.scalar(select(Payment).where(Payment.id == payment_id, Payment.tenant_id == tenant.id).with_for_update())
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.voided_at is not None:
        if payment.void_reason != payload.reason:
            conflict("Payment is already voided; the original reason cannot be changed")
        return PaymentRead.model_validate(payment)
    if payment.cash_closing_id is not None:
        conflict("Payment belongs to a cash closing; a reconciled adjustment is required")
    snapshot = payment.correction_snapshot
    if not snapshot or "before" not in snapshot or "after" not in snapshot:
        conflict("Payment predates correction snapshots; a reconciled adjustment is required")
    latest = db.scalar(select(Payment.id).where(Payment.tenant_id == tenant.id, Payment.loan_id == payment.loan_id,
                                               Payment.voided_at.is_(None)).order_by(Payment.id.desc()).limit(1))
    if latest != payment.id:
        conflict("Only the latest recorded payment on the loan may be voided")
    loan = db.scalar(select(Loan).where(Loan.id == payment.loan_id, Loan.tenant_id == tenant.id).with_for_update())
    installments = list(db.scalars(select(Installment).where(Installment.loan_id == payment.loan_id,
                                                            Installment.tenant_id == tenant.id)
                                   .order_by(Installment.id).with_for_update()).all())
    installment = next((item for item in installments if item.id == payment.installment_id), None)
    if loan is None or installment is None:
        conflict("Payment ledger is incomplete; reconciliation is required")
    if loan.status not in {"active", "paid"}:
        conflict("Loan status does not allow payment correction")
    if installment_snapshot(installment) != snapshot["after"]:
        conflict("Installment changed after payment; reconciliation is required")
    allocations = list(db.scalars(select(PromisePaymentAllocation).where(
        PromisePaymentAllocation.tenant_id == tenant.id, PromisePaymentAllocation.payment_id == payment.id,
        PromisePaymentAllocation.reversed_at.is_(None)).order_by(PromisePaymentAllocation.promise_id).with_for_update()).all())
    promises = {}
    for allocation in allocations:
        promise = db.scalar(select(PaymentPromise).where(PaymentPromise.id == allocation.promise_id,
                                                          PaymentPromise.tenant_id == tenant.id).with_for_update())
        if promise is None or promise.loan_id != payment.loan_id or promise.fulfilled_amount < allocation.amount:
            conflict("Promise allocation requires reconciliation")
        promises[allocation.promise_id] = promise
    before = {"installment": installment_snapshot(installment), "loan_status": loan.status,
              "amount": str(payment.amount), "receipt_number": f"PM-{payment.id:08d}"}
    now = datetime.now(timezone.utc)
    try:
        for name in MONEY_FIELDS:
            setattr(installment, name, Decimal(snapshot["before"][name]))
        installment.status = snapshot["before"]["status"]
        through = snapshot["before"]["late_fee_assessed_through"]
        installment.late_fee_assessed_through = date.fromisoformat(through) if through else None
        for allocation in allocations:
            promise = promises[allocation.promise_id]
            promise.fulfilled_amount = money(promise.fulfilled_amount - allocation.amount)
            if promise.status != "cancelled":
                promise.status = "partial" if promise.fulfilled_amount > 0 else "pending"
            promise.fulfilled_at = None
            promise.updated_at = now
            allocation.reversed_at = now
        balance = money(sum((item.principal_due - item.principal_paid + item.interest_due - item.interest_paid
                             + item.late_fee_accrued - item.late_fee_paid for item in installments), Decimal("0.00")))
        loan.status = "paid" if balance == 0 else "active"
        payment.voided_at = now
        payment.voided_by_user_id = membership.user_id
        payment.void_reason = payload.reason
        add_admin_audit(db, operator_user_id=membership.user_id, action="payments.voided", target_type="payment",
                        target_id=payment.id, tenant_id=tenant.id, before_data=before,
                        after_data={"installment": installment_snapshot(installment), "loan_status": loan.status,
                                    "loan_balance": str(balance), "reason": payload.reason,
                                    "reversed_promise_allocation_ids": [item.id for item in allocations]})
        db.commit()
        db.refresh(payment)
    except Exception:
        db.rollback()
        raise
    return PaymentRead.model_validate(payment)
