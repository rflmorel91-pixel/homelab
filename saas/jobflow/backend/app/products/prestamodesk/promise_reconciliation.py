from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.products.prestamodesk.amortization import money
from app.products.prestamodesk.models import (
    Payment,
    PaymentPromise,
    PromisePaymentAllocation,
)


OPEN_PROMISE_STATUSES = (
    "pending",
    "partial",
)


def reconcile_payment_promises(
    *,
    db: Session,
    payment: Payment,
) -> list[PromisePaymentAllocation]:
    already_allocated = db.scalar(
        select(
            func.coalesce(
                func.sum(
                    PromisePaymentAllocation.amount
                ),
                Decimal("0.00"),
            )
        ).where(
            PromisePaymentAllocation.tenant_id
            == payment.tenant_id,
            PromisePaymentAllocation.payment_id
            == payment.id,
        )
    )

    remaining = money(
        payment.amount
        - Decimal(already_allocated or 0)
    )

    if remaining <= Decimal("0.00"):
        return []

    promises = list(
        db.scalars(
            select(PaymentPromise)
            .where(
                PaymentPromise.tenant_id
                == payment.tenant_id,
                PaymentPromise.loan_id
                == payment.loan_id,
                PaymentPromise.status.in_(
                    OPEN_PROMISE_STATUSES
                ),
            )
            .order_by(
                PaymentPromise.due_date,
                PaymentPromise.created_at,
                PaymentPromise.id,
            )
            .with_for_update()
        ).all()
    )

    reconciled_at = datetime.now(timezone.utc)
    allocations: list[
        PromisePaymentAllocation
    ] = []

    for promise in promises:
        promise_remaining = money(
            promise.promised_amount
            - promise.fulfilled_amount
        )

        if promise_remaining <= Decimal("0.00"):
            promise.status = "fulfilled"

            if promise.fulfilled_at is None:
                promise.fulfilled_at = reconciled_at

            continue

        allocation_amount = money(
            min(remaining, promise_remaining)
        )

        if allocation_amount <= Decimal("0.00"):
            break

        allocation = PromisePaymentAllocation(
            tenant_id=payment.tenant_id,
            promise_id=promise.id,
            payment_id=payment.id,
            amount=allocation_amount,
        )
        db.add(allocation)
        allocations.append(allocation)

        promise.fulfilled_amount = money(
            promise.fulfilled_amount
            + allocation_amount
        )
        promise.updated_at = reconciled_at

        if (
            promise.fulfilled_amount
            >= promise.promised_amount
        ):
            promise.fulfilled_amount = (
                promise.promised_amount
            )
            promise.status = "fulfilled"
            promise.fulfilled_at = reconciled_at
        else:
            promise.status = "partial"
            promise.fulfilled_at = None

        remaining = money(
            remaining - allocation_amount
        )

        if remaining <= Decimal("0.00"):
            break

    return allocations
