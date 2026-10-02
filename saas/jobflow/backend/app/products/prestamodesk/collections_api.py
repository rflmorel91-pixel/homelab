from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant, TenantMembership
from app.products.prestamodesk.amortization import money
from app.products.prestamodesk.collections_schemas import (
    CollectionActivityCreate,
    CollectionActivityRead,
    CollectionPortfolioItem,
    PaymentPromiseCancel,
    PaymentPromiseCreate,
    PaymentPromiseRead,
    PromisePaymentAllocationRead,
)
from app.products.prestamodesk.models import (
    Borrower,
    CollectionActivity,
    Installment,
    Loan,
    PaymentPromise,
    PromisePaymentAllocation,
)
from app.tenant_context import (
    get_current_tenant,
    get_current_tenant_membership,
)


router = APIRouter(
    prefix="/collections",
    tags=["PréstamoDesk Collections"],
)


def require_collections_access(
    membership: TenantMembership,
) -> None:
    if membership.role not in {
        "owner",
        "collector",
    }:
        raise HTTPException(
            status_code=403,
            detail=(
                "Owner or collector role required"
            ),
        )


def get_tenant_loan(
    *,
    db: Session,
    tenant_id: int,
    loan_id: int,
    lock: bool = False,
) -> Loan:
    statement = select(Loan).where(
        Loan.id == loan_id,
        Loan.tenant_id == tenant_id,
    )

    if lock:
        statement = statement.with_for_update()

    loan = db.scalar(statement)

    if loan is None:
        raise HTTPException(
            status_code=404,
            detail="Loan not found",
        )

    return loan


def installment_ordinary_balance(
    installment: Installment,
) -> Decimal:
    return money(
        installment.principal_due
        - installment.principal_paid
        + installment.interest_due
        - installment.interest_paid
    )


def installment_late_fee_balance(
    installment: Installment,
) -> Decimal:
    return money(
        installment.late_fee_accrued
        - installment.late_fee_paid
    )


def loan_outstanding_balance(
    *,
    db: Session,
    tenant_id: int,
    loan_id: int,
) -> Decimal:
    installments = db.scalars(
        select(Installment).where(
            Installment.tenant_id == tenant_id,
            Installment.loan_id == loan_id,
        )
    ).all()

    return money(
        sum(
            (
                installment_ordinary_balance(item)
                + installment_late_fee_balance(item)
                for item in installments
            ),
            Decimal("0.00"),
        )
    )


def promise_read(
    promise: PaymentPromise,
    *,
    as_of: date | None = None,
) -> PaymentPromiseRead:
    if as_of is None:
        as_of = date.today()

    remaining = money(
        promise.promised_amount
        - promise.fulfilled_amount
    )

    return PaymentPromiseRead(
        id=promise.id,
        tenant_id=promise.tenant_id,
        loan_id=promise.loan_id,
        created_by_user_id=(
            promise.created_by_user_id
        ),
        promised_amount=promise.promised_amount,
        fulfilled_amount=promise.fulfilled_amount,
        remaining_amount=remaining,
        due_date=promise.due_date,
        status=promise.status,
        is_overdue=(
            promise.status in {"pending", "partial"}
            and promise.due_date < as_of
        ),
        notes=promise.notes,
        fulfilled_at=promise.fulfilled_at,
        cancelled_at=promise.cancelled_at,
        created_at=promise.created_at,
        updated_at=promise.updated_at,
    )


@router.get(
    "/portfolio",
    response_model=list[CollectionPortfolioItem],
)
def list_overdue_portfolio(
    as_of: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    membership: TenantMembership = Depends(
        get_current_tenant_membership
    ),
):
    require_collections_access(membership)

    rows = db.execute(
        select(
            Loan,
            Borrower,
            Installment,
        )
        .join(
            Borrower,
            Borrower.id == Loan.borrower_id,
        )
        .join(
            Installment,
            Installment.loan_id == Loan.id,
        )
        .where(
            Loan.tenant_id == tenant.id,
            Borrower.tenant_id == tenant.id,
            Installment.tenant_id == tenant.id,
            Loan.status == "active",
            Installment.due_date < as_of,
        )
        .order_by(
            Installment.due_date,
            Loan.id,
            Installment.sequence_number,
        )
    ).all()

    portfolio: dict[
        int,
        CollectionPortfolioItem,
    ] = {}

    for loan, borrower, installment in rows:
        ordinary = installment_ordinary_balance(
            installment
        )
        late_fee = installment_late_fee_balance(
            installment
        )
        total = money(ordinary + late_fee)

        if total <= Decimal("0.00"):
            continue

        item = portfolio.get(loan.id)

        if item is None:
            item = CollectionPortfolioItem(
                loan_id=loan.id,
                borrower_id=borrower.id,
                borrower_full_name=(
                    borrower.full_name
                ),
                borrower_document_number=(
                    borrower.document_number
                ),
                borrower_phone=borrower.phone,
                borrower_email=borrower.email,
                currency=loan.currency,
                oldest_due_date=(
                    installment.due_date
                ),
                days_overdue=(
                    as_of - installment.due_date
                ).days,
                overdue_installment_count=0,
                ordinary_balance_due=Decimal(
                    "0.00"
                ),
                late_fee_balance_due=Decimal(
                    "0.00"
                ),
                total_balance_due=Decimal(
                    "0.00"
                ),
            )
            portfolio[loan.id] = item

        item.overdue_installment_count += 1
        item.ordinary_balance_due = money(
            item.ordinary_balance_due + ordinary
        )
        item.late_fee_balance_due = money(
            item.late_fee_balance_due + late_fee
        )
        item.total_balance_due = money(
            item.total_balance_due + total
        )

    return sorted(
        portfolio.values(),
        key=lambda item: (
            -item.days_overdue,
            item.borrower_full_name.lower(),
            item.loan_id,
        ),
    )


@router.post(
    "/loans/{loan_id}/activities",
    response_model=CollectionActivityRead,
    status_code=201,
)
def create_collection_activity(
    loan_id: int,
    payload: CollectionActivityCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    membership: TenantMembership = Depends(
        get_current_tenant_membership
    ),
):
    require_collections_access(membership)

    get_tenant_loan(
        db=db,
        tenant_id=tenant.id,
        loan_id=loan_id,
    )

    if (
        payload.next_follow_up_at is not None
        and payload.next_follow_up_at
        <= payload.contacted_at
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "Next follow-up must be after "
                "the contact time"
            ),
        )

    activity = CollectionActivity(
        tenant_id=tenant.id,
        loan_id=loan_id,
        recorded_by_user_id=membership.user_id,
        channel=payload.channel,
        outcome=payload.outcome,
        notes=payload.notes,
        contacted_at=payload.contacted_at,
        next_follow_up_at=(
            payload.next_follow_up_at
        ),
    )

    try:
        db.add(activity)
        db.commit()
        db.refresh(activity)
    except Exception:
        db.rollback()
        raise

    return activity


@router.get(
    "/loans/{loan_id}/activities",
    response_model=list[CollectionActivityRead],
)
def list_collection_activities(
    loan_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    membership: TenantMembership = Depends(
        get_current_tenant_membership
    ),
):
    require_collections_access(membership)

    get_tenant_loan(
        db=db,
        tenant_id=tenant.id,
        loan_id=loan_id,
    )

    return list(
        db.scalars(
            select(CollectionActivity)
            .where(
                CollectionActivity.tenant_id
                == tenant.id,
                CollectionActivity.loan_id
                == loan_id,
            )
            .order_by(
                CollectionActivity.contacted_at.desc(),
                CollectionActivity.id.desc(),
            )
        ).all()
    )


@router.post(
    "/loans/{loan_id}/promises",
    response_model=PaymentPromiseRead,
    status_code=201,
)
def create_payment_promise(
    loan_id: int,
    payload: PaymentPromiseCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    membership: TenantMembership = Depends(
        get_current_tenant_membership
    ),
):
    require_collections_access(membership)

    loan = get_tenant_loan(
        db=db,
        tenant_id=tenant.id,
        loan_id=loan_id,
        lock=True,
    )

    if loan.status != "active":
        raise HTTPException(
            status_code=409,
            detail="Loan is not active",
        )

    outstanding = loan_outstanding_balance(
        db=db,
        tenant_id=tenant.id,
        loan_id=loan_id,
    )
    promised_amount = money(
        payload.promised_amount
    )

    if promised_amount > outstanding:
        raise HTTPException(
            status_code=409,
            detail=(
                "Promise amount exceeds "
                "the loan balance"
            ),
        )

    promise = PaymentPromise(
        tenant_id=tenant.id,
        loan_id=loan_id,
        created_by_user_id=membership.user_id,
        promised_amount=promised_amount,
        fulfilled_amount=Decimal("0.00"),
        due_date=payload.due_date,
        status="pending",
        notes=payload.notes,
    )

    try:
        db.add(promise)
        db.commit()
        db.refresh(promise)
    except Exception:
        db.rollback()
        raise

    return promise_read(promise)


@router.get(
    "/loans/{loan_id}/promises",
    response_model=list[PaymentPromiseRead],
)
def list_payment_promises(
    loan_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    membership: TenantMembership = Depends(
        get_current_tenant_membership
    ),
):
    require_collections_access(membership)

    get_tenant_loan(
        db=db,
        tenant_id=tenant.id,
        loan_id=loan_id,
    )

    promises = db.scalars(
        select(PaymentPromise)
        .where(
            PaymentPromise.tenant_id == tenant.id,
            PaymentPromise.loan_id == loan_id,
        )
        .order_by(
            PaymentPromise.due_date.desc(),
            PaymentPromise.id.desc(),
        )
    ).all()

    return [
        promise_read(promise)
        for promise in promises
    ]


@router.get(
    "/promises",
    response_model=list[PaymentPromiseRead],
)
def list_tenant_promises(
    status: str | None = None,
    overdue_only: bool = False,
    as_of: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    membership: TenantMembership = Depends(
        get_current_tenant_membership
    ),
):
    require_collections_access(membership)

    statement = select(PaymentPromise).where(
        PaymentPromise.tenant_id == tenant.id
    )

    if status is not None:
        if status not in {
            "pending",
            "partial",
            "fulfilled",
            "cancelled",
        }:
            raise HTTPException(
                status_code=422,
                detail="Invalid promise status",
            )

        statement = statement.where(
            PaymentPromise.status == status
        )

    if overdue_only:
        statement = statement.where(
            PaymentPromise.status.in_(
                {"pending", "partial"}
            ),
            PaymentPromise.due_date < as_of,
        )

    promises = db.scalars(
        statement.order_by(
            PaymentPromise.due_date,
            PaymentPromise.id,
        )
    ).all()

    return [
        promise_read(promise, as_of=as_of)
        for promise in promises
    ]


@router.post(
    "/promises/{promise_id}/cancel",
    response_model=PaymentPromiseRead,
)
def cancel_payment_promise(
    promise_id: int,
    payload: PaymentPromiseCancel,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    membership: TenantMembership = Depends(
        get_current_tenant_membership
    ),
):
    require_collections_access(membership)

    promise = db.scalar(
        select(PaymentPromise)
        .where(
            PaymentPromise.id == promise_id,
            PaymentPromise.tenant_id == tenant.id,
        )
        .with_for_update()
    )

    if promise is None:
        raise HTTPException(
            status_code=404,
            detail="Payment promise not found",
        )

    if promise.status not in {
        "pending",
        "partial",
    }:
        raise HTTPException(
            status_code=409,
            detail=(
                "Payment promise cannot be cancelled"
            ),
        )

    now = datetime.now(timezone.utc)
    promise.status = "cancelled"
    promise.cancelled_at = now
    promise.updated_at = now

    if payload.notes is not None:
        promise.notes = payload.notes

    try:
        db.commit()
        db.refresh(promise)
    except Exception:
        db.rollback()
        raise

    return promise_read(promise)


@router.get(
    "/promises/{promise_id}/allocations",
    response_model=list[
        PromisePaymentAllocationRead
    ],
)
def list_promise_allocations(
    promise_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    membership: TenantMembership = Depends(
        get_current_tenant_membership
    ),
):
    require_collections_access(membership)

    promise = db.scalar(
        select(PaymentPromise).where(
            PaymentPromise.id == promise_id,
            PaymentPromise.tenant_id == tenant.id,
        )
    )

    if promise is None:
        raise HTTPException(
            status_code=404,
            detail="Payment promise not found",
        )

    return list(
        db.scalars(
            select(PromisePaymentAllocation)
            .where(
                PromisePaymentAllocation.tenant_id
                == tenant.id,
                PromisePaymentAllocation.promise_id
                == promise_id,
            )
            .order_by(
                PromisePaymentAllocation.created_at,
                PromisePaymentAllocation.id,
            )
        ).all()
    )
