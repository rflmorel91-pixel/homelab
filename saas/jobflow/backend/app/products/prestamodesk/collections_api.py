import csv
from datetime import date, datetime, timezone
from decimal import Decimal
import io

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.products.prestamodesk.authorization import COLLECTIONS_MANAGEMENT_ROLES
from app.api.admin import add_admin_audit
from app.database import get_db
from app.models import (
    Tenant,
    TenantMembership,
    User,
)
from app.products.prestamodesk.amortization import money
from app.products.prestamodesk.collections_schemas import (
    CollectionActivityCreate,
    CollectionActivityRead,
    CollectionPortfolioItem,
    CollectionsAgingBucketRead,
    CollectionsSupervisionRead,
    CollectorPerformanceRead,
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
    Payment,
    PaymentPromise,
    PromisePaymentAllocation,
)
from app.tenant_context import (
    get_current_tenant,
    get_current_tenant_membership,
)

from sqlalchemy.exc import IntegrityError

from app.products.prestamodesk.collections_schemas import (
    CollectorAssignmentCreate,
    CollectorAssignmentRead,
    CollectorAssignmentRelease,
    CollectorOptionRead,
)
from app.products.prestamodesk.models import (
    LoanCollectorAssignment,
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
        "administrator",
        "supervisor",
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
    assignment_status: str = Query(default="all"),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    membership: TenantMembership = Depends(
        get_current_tenant_membership
    ),
):
    require_collections_access(membership)

    if assignment_status not in {
        "all",
        "assigned",
        "unassigned",
    }:
        raise HTTPException(
            status_code=422,
            detail="Invalid assignment status",
        )

    statement = (
        select(
            Loan,
            Borrower,
            Installment,
            LoanCollectorAssignment,
            User,
        )
        .join(
            Borrower,
            Borrower.id == Loan.borrower_id,
        )
        .join(
            Installment,
            Installment.loan_id == Loan.id,
        )
        .outerjoin(
            LoanCollectorAssignment,
            (
                LoanCollectorAssignment.tenant_id
                == tenant.id
            )
            & (
                LoanCollectorAssignment.loan_id
                == Loan.id
            )
            & (
                LoanCollectorAssignment.released_at.is_(
                    None
                )
            ),
        )
        .outerjoin(
            User,
            User.id
            == LoanCollectorAssignment.collector_user_id,
        )
        .where(
            Loan.tenant_id == tenant.id,
            Borrower.tenant_id == tenant.id,
            Installment.tenant_id == tenant.id,
            Loan.status == "active",
            Installment.due_date < as_of,
        )
    )

    if membership.role == "collector":
        statement = statement.where(
            LoanCollectorAssignment.collector_user_id
            == membership.user_id
        )
    elif assignment_status == "assigned":
        statement = statement.where(
            LoanCollectorAssignment.id.is_not(None)
        )
    elif assignment_status == "unassigned":
        statement = statement.where(
            LoanCollectorAssignment.id.is_(None)
        )

    rows = db.execute(
        statement.order_by(
            Installment.due_date,
            Loan.id,
            Installment.sequence_number,
        )
    ).all()

    portfolio: dict[
        int,
        CollectionPortfolioItem,
    ] = {}

    for (
        loan,
        borrower,
        installment,
        assignment,
        collector,
    ) in rows:
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
                assigned_collector_user_id=(
                    assignment.collector_user_id
                    if assignment is not None
                    else None
                ),
                assigned_collector_display_name=(
                    collector.display_name
                    if collector is not None
                    else None
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

    require_collector_assignment_access(
        db=db,
        tenant_id=tenant.id,
        loan_id=loan_id,
        membership=membership,
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

    require_collector_assignment_access(
        db=db,
        tenant_id=tenant.id,
        loan_id=loan_id,
        membership=membership,
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

    require_collector_assignment_access(
        db=db,
        tenant_id=tenant.id,
        loan_id=loan_id,
        membership=membership,
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

    require_collector_assignment_access(
        db=db,
        tenant_id=tenant.id,
        loan_id=loan_id,
        membership=membership,
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

    if membership.role == "collector":
        statement = (
            statement
            .join(
                LoanCollectorAssignment,
                (
                    LoanCollectorAssignment.loan_id
                    == PaymentPromise.loan_id
                )
                & (
                    LoanCollectorAssignment.tenant_id
                    == tenant.id
                )
                & (
                    LoanCollectorAssignment.released_at.is_(
                        None
                    )
                ),
            )
            .where(
                LoanCollectorAssignment.collector_user_id
                == membership.user_id
            )
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

    require_collector_assignment_access(
        db=db,
        tenant_id=tenant.id,
        loan_id=promise.loan_id,
        membership=membership,
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

    require_collector_assignment_access(
        db=db,
        tenant_id=tenant.id,
        loan_id=promise.loan_id,
        membership=membership,
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



def fulfillment_percent(
    *,
    fulfilled: Decimal | int,
    total: Decimal | int,
) -> Decimal:
    total_decimal = Decimal(total)

    if total_decimal <= Decimal("0"):
        return Decimal("0.00")

    return money(
        Decimal(fulfilled)
        / total_decimal
        * Decimal("100")
    )


def performance_for_collector(
    *,
    user: User,
    activities: list[CollectionActivity],
    promises: list[PaymentPromise],
    as_of: date,
    active_overdue_loan_count: int,
    active_overdue_balance: Decimal,
) -> CollectorPerformanceRead:
    user_activities = [
        activity
        for activity in activities
        if activity.recorded_by_user_id == user.id
    ]
    user_promises = [
        promise
        for promise in promises
        if promise.created_by_user_id == user.id
    ]

    promised_amount = money(
        sum(
            (
                promise.promised_amount
                for promise in user_promises
            ),
            Decimal("0.00"),
        )
    )
    fulfilled_amount = money(
        sum(
            (
                promise.fulfilled_amount
                for promise in user_promises
            ),
            Decimal("0.00"),
        )
    )
    fulfilled_count = sum(
        promise.status == "fulfilled"
        for promise in user_promises
    )

    return CollectorPerformanceRead(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        active_overdue_loan_count=(
            active_overdue_loan_count
        ),
        active_overdue_balance=money(
            active_overdue_balance
        ),
        activity_count=len(user_activities),
        promise_count=len(user_promises),
        pending_promise_count=sum(
            promise.status == "pending"
            for promise in user_promises
        ),
        partial_promise_count=sum(
            promise.status == "partial"
            for promise in user_promises
        ),
        fulfilled_promise_count=fulfilled_count,
        cancelled_promise_count=sum(
            promise.status == "cancelled"
            for promise in user_promises
        ),
        overdue_promise_count=sum(
            promise.status in {"pending", "partial"}
            and promise.due_date < as_of
            for promise in user_promises
        ),
        promised_amount=promised_amount,
        fulfilled_amount=fulfilled_amount,
        promise_count_fulfillment_percent=(
            fulfillment_percent(
                fulfilled=fulfilled_count,
                total=len(user_promises),
            )
        ),
        promise_amount_fulfillment_percent=(
            fulfillment_percent(
                fulfilled=fulfilled_amount,
                total=promised_amount,
            )
        ),
    )


def spreadsheet_safe_value(
    value: object | None,
) -> str:
    text = "" if value is None else str(value)

    if text.startswith(
        ("=", "+", "-", "@", "\t", "\r")
    ):
        return "'" + text

    return text


@router.get("/supervision/export.csv")
def export_collections_supervision_csv(
    as_of: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    membership: TenantMembership = Depends(
        get_current_tenant_membership
    ),
):
    require_collections_owner(membership)

    portfolio = list_overdue_portfolio(
        as_of=as_of,
        assignment_status="all",
        db=db,
        tenant=tenant,
        membership=membership,
    )

    output = io.StringIO(newline="")
    writer = csv.writer(
        output,
        lineterminator="\r\n",
    )
    writer.writerow(
        (
            "Préstamo",
            "Cliente",
            "Documento",
            "Teléfono",
            "Correo electrónico",
            "Cobrador asignado",
            "Fecha vencida más antigua",
            "Días de atraso",
            "Cuotas vencidas",
            "Capital e interés vencido",
            "Mora vencida",
            "Saldo vencido total",
            "Moneda",
            "Fecha de corte",
        )
    )

    for item in portfolio:
        writer.writerow(
            (
                item.loan_id,
                spreadsheet_safe_value(
                    item.borrower_full_name
                ),
                spreadsheet_safe_value(
                    item.borrower_document_number
                ),
                spreadsheet_safe_value(
                    item.borrower_phone
                ),
                spreadsheet_safe_value(
                    item.borrower_email
                ),
                spreadsheet_safe_value(
                    item.assigned_collector_display_name
                    or "Sin asignar"
                ),
                item.oldest_due_date.isoformat(),
                item.days_overdue,
                item.overdue_installment_count,
                str(item.ordinary_balance_due),
                str(item.late_fee_balance_due),
                str(item.total_balance_due),
                item.currency,
                as_of.isoformat(),
            )
        )

    filename = (
        "prestamodesk-cartera-vencida-"
        f"{as_of.isoformat()}.csv"
    )
    content = "\ufeff" + output.getvalue()

    return Response(
        content=content.encode("utf-8"),
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            ),
            "Cache-Control": "no-store",
        },
    )


@router.get(
    "/supervision",
    response_model=CollectionsSupervisionRead,
)
def read_collections_supervision(
    as_of: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    membership: TenantMembership = Depends(
        get_current_tenant_membership
    ),
):
    if not membership.is_active or membership.role not in COLLECTIONS_MANAGEMENT_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Owner role required",
        )

    overdue_installments = db.scalars(
        select(Installment)
        .join(
            Loan,
            Loan.id == Installment.loan_id,
        )
        .where(
            Installment.tenant_id == tenant.id,
            Loan.tenant_id == tenant.id,
            Loan.status == "active",
            Installment.due_date < as_of,
        )
    ).all()

    overdue_loans: dict[int, dict[str, object]] = {}

    for installment in overdue_installments:
        balance = money(
            installment_ordinary_balance(installment)
            + installment_late_fee_balance(installment)
        )

        if balance <= Decimal("0.00"):
            continue

        loan_summary = overdue_loans.setdefault(
            installment.loan_id,
            {
                "oldest_due_date": installment.due_date,
                "balance": Decimal("0.00"),
            },
        )
        loan_summary["oldest_due_date"] = min(
            loan_summary["oldest_due_date"],
            installment.due_date,
        )
        loan_summary["balance"] = money(
            loan_summary["balance"] + balance
        )

    overdue_loan_ids = set(overdue_loans)
    overdue_balance = money(
        sum(
            (
                summary["balance"]
                for summary in overdue_loans.values()
            ),
            Decimal("0.00"),
        )
    )

    active_assignments = list(
        db.scalars(
            select(LoanCollectorAssignment).where(
                LoanCollectorAssignment.tenant_id
                == tenant.id,
                LoanCollectorAssignment.released_at.is_(
                    None
                ),
            )
        ).all()
    )
    assignment_by_loan = {
        assignment.loan_id: assignment
        for assignment in active_assignments
        if assignment.loan_id in overdue_loan_ids
    }

    assigned_loan_ids = (
        overdue_loan_ids & set(assignment_by_loan)
    )
    unassigned_loan_ids = (
        overdue_loan_ids - assigned_loan_ids
    )

    assigned_overdue_balance = money(
        sum(
            (
                overdue_loans[loan_id]["balance"]
                for loan_id in assigned_loan_ids
            ),
            Decimal("0.00"),
        )
    )
    unassigned_overdue_balance = money(
        overdue_balance - assigned_overdue_balance
    )

    aging_definitions = (
        ("days_1_30", "1–30 días", 1, 30),
        ("days_31_60", "31–60 días", 31, 60),
        ("days_61_90", "61–90 días", 61, 90),
        ("days_91_plus", "91 días o más", 91, None),
    )
    aging_buckets = []

    for key, label, minimum, maximum in aging_definitions:
        matching = [
            summary
            for summary in overdue_loans.values()
            if (
                (as_of - summary["oldest_due_date"]).days
                >= minimum
                and (
                    maximum is None
                    or (
                        as_of
                        - summary["oldest_due_date"]
                    ).days
                    <= maximum
                )
            )
        ]
        aging_buckets.append(
            CollectionsAgingBucketRead(
                key=key,
                label=label,
                minimum_days=minimum,
                maximum_days=maximum,
                loan_count=len(matching),
                balance=money(
                    sum(
                        (
                            summary["balance"]
                            for summary in matching
                        ),
                        Decimal("0.00"),
                    )
                ),
            )
        )

    activities = list(
        db.scalars(
            select(CollectionActivity).where(
                CollectionActivity.tenant_id
                == tenant.id
            )
        ).all()
    )
    promises = list(
        db.scalars(
            select(PaymentPromise).where(
                PaymentPromise.tenant_id
                == tenant.id
            )
        ).all()
    )
    collectors = list(
        db.scalars(
            select(User)
            .join(
                TenantMembership,
                TenantMembership.user_id == User.id,
            )
            .where(
                TenantMembership.tenant_id == tenant.id,
                TenantMembership.role == "collector",
            TenantMembership.is_active.is_(True),
                User.is_active.is_(True),
            )
            .order_by(
                User.display_name,
                User.email,
                User.id,
            )
        ).all()
    )

    total_recovered = money(
        db.scalar(
            select(
                func.coalesce(
                    func.sum(Payment.amount),
                    Decimal("0.00"),
                )
            ).where(
                Payment.tenant_id == tenant.id
            )
        )
        or Decimal("0.00")
    )
    promised_amount = money(
        sum(
            (
                promise.promised_amount
                for promise in promises
            ),
            Decimal("0.00"),
        )
    )
    fulfilled_amount = money(
        sum(
            (
                promise.fulfilled_amount
                for promise in promises
            ),
            Decimal("0.00"),
        )
    )
    fulfilled_count = sum(
        promise.status == "fulfilled"
        for promise in promises
    )

    active_promise_statuses = {"pending", "partial"}
    promises_due_today_count = sum(
        promise.status in active_promise_statuses
        and promise.due_date == as_of
        for promise in promises
    )
    follow_ups_due_today_count = sum(
        activity.next_follow_up_at is not None
        and activity.next_follow_up_at.date() == as_of
        for activity in activities
    )
    overdue_follow_up_count = sum(
        activity.next_follow_up_at is not None
        and activity.next_follow_up_at.date() < as_of
        for activity in activities
    )

    collector_portfolios: dict[
        int,
        dict[str, Decimal | int],
    ] = {}

    for loan_id, assignment in assignment_by_loan.items():
        summary = collector_portfolios.setdefault(
            assignment.collector_user_id,
            {
                "loan_count": 0,
                "balance": Decimal("0.00"),
            },
        )
        summary["loan_count"] += 1
        summary["balance"] = money(
            summary["balance"]
            + overdue_loans[loan_id]["balance"]
        )

    return CollectionsSupervisionRead(
        as_of=as_of,
        overdue_loan_count=len(overdue_loan_ids),
        overdue_balance=overdue_balance,
        assigned_overdue_loan_count=len(
            assigned_loan_ids
        ),
        assigned_overdue_balance=(
            assigned_overdue_balance
        ),
        unassigned_overdue_loan_count=len(
            unassigned_loan_ids
        ),
        unassigned_overdue_balance=(
            unassigned_overdue_balance
        ),
        promises_due_today_count=(
            promises_due_today_count
        ),
        follow_ups_due_today_count=(
            follow_ups_due_today_count
        ),
        overdue_follow_up_count=(
            overdue_follow_up_count
        ),
        aging_buckets=aging_buckets,
        total_recovered=total_recovered,
        activity_count=len(activities),
        promise_count=len(promises),
        pending_promise_count=sum(
            promise.status == "pending"
            for promise in promises
        ),
        partial_promise_count=sum(
            promise.status == "partial"
            for promise in promises
        ),
        fulfilled_promise_count=fulfilled_count,
        cancelled_promise_count=sum(
            promise.status == "cancelled"
            for promise in promises
        ),
        overdue_promise_count=sum(
            promise.status in {"pending", "partial"}
            and promise.due_date < as_of
            for promise in promises
        ),
        promised_amount=promised_amount,
        fulfilled_amount=fulfilled_amount,
        promise_count_fulfillment_percent=(
            fulfillment_percent(
                fulfilled=fulfilled_count,
                total=len(promises),
            )
        ),
        promise_amount_fulfillment_percent=(
            fulfillment_percent(
                fulfilled=fulfilled_amount,
                total=promised_amount,
            )
        ),
        collectors=[
            performance_for_collector(
                user=user,
                activities=activities,
                promises=promises,
                as_of=as_of,
                active_overdue_loan_count=int(
                    collector_portfolios.get(
                        user.id,
                        {},
                    ).get("loan_count", 0)
                ),
                active_overdue_balance=Decimal(
                    collector_portfolios.get(
                        user.id,
                        {},
                    ).get(
                        "balance",
                        Decimal("0.00"),
                    )
                ),
            )
            for user in collectors
        ],
    )


def require_collections_owner(
    membership: TenantMembership,
) -> None:
    if not membership.is_active or membership.role not in COLLECTIONS_MANAGEMENT_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Owner role required",
        )


def active_collector_assignment(
    *,
    db: Session,
    tenant_id: int,
    loan_id: int,
    lock: bool = False,
) -> LoanCollectorAssignment | None:
    statement = select(
        LoanCollectorAssignment
    ).where(
        LoanCollectorAssignment.tenant_id
        == tenant_id,
        LoanCollectorAssignment.loan_id
        == loan_id,
        LoanCollectorAssignment.released_at.is_(
            None
        ),
    )

    if lock:
        statement = statement.with_for_update()

    return db.scalar(statement)


def collector_assignment_read(
    *,
    db: Session,
    assignment: LoanCollectorAssignment,
) -> CollectorAssignmentRead:
    collector = db.get(
        User,
        assignment.collector_user_id,
    )

    if collector is None:
        raise RuntimeError(
            "Collector assignment references "
            "a missing user"
        )

    return CollectorAssignmentRead(
        id=assignment.id,
        tenant_id=assignment.tenant_id,
        loan_id=assignment.loan_id,
        collector_user_id=(
            assignment.collector_user_id
        ),
        collector_email=collector.email,
        collector_display_name=(
            collector.display_name
        ),
        assigned_by_user_id=(
            assignment.assigned_by_user_id
        ),
        assigned_at=assignment.assigned_at,
        released_at=assignment.released_at,
        released_by_user_id=(
            assignment.released_by_user_id
        ),
        release_reason=assignment.release_reason,
        is_active=assignment.released_at is None,
    )


def get_active_tenant_collector(
    *,
    db: Session,
    tenant_id: int,
    user_id: int,
) -> User:
    collector = db.scalar(
        select(User)
        .join(
            TenantMembership,
            TenantMembership.user_id == User.id,
        )
        .where(
            User.id == user_id,
            User.is_active.is_(True),
            TenantMembership.tenant_id
            == tenant_id,
            TenantMembership.role == "collector",
            TenantMembership.is_active.is_(True),
        )
    )

    if collector is None:
        raise HTTPException(
            status_code=404,
            detail="Active collector not found",
        )

    return collector


@router.get(
    "/collectors",
    response_model=list[CollectorOptionRead],
)
def list_collections_collectors(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    membership: TenantMembership = Depends(
        get_current_tenant_membership
    ),
):
    require_collections_owner(membership)

    collectors = db.scalars(
        select(User)
        .join(
            TenantMembership,
            TenantMembership.user_id == User.id,
        )
        .where(
            TenantMembership.tenant_id == tenant.id,
            TenantMembership.role == "collector",
            TenantMembership.is_active.is_(True),
            User.is_active.is_(True),
        )
        .order_by(
            User.display_name,
            User.email,
            User.id,
        )
    ).all()

    return [
        CollectorOptionRead(
            user_id=collector.id,
            email=collector.email,
            display_name=collector.display_name,
        )
        for collector in collectors
    ]


@router.post(
    "/loans/{loan_id}/assignment",
    response_model=CollectorAssignmentRead,
)
def assign_loan_collector(
    loan_id: int,
    payload: CollectorAssignmentCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    membership: TenantMembership = Depends(
        get_current_tenant_membership
    ),
):
    db.scalar(select(Tenant).where(Tenant.id == tenant.id).with_for_update())
    db.refresh(membership)
    require_collections_owner(membership)

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

    get_active_tenant_collector(
        db=db,
        tenant_id=tenant.id,
        user_id=payload.collector_user_id,
    )

    current = active_collector_assignment(
        db=db,
        tenant_id=tenant.id,
        loan_id=loan_id,
        lock=True,
    )

    if (
        current is not None
        and current.collector_user_id
        == payload.collector_user_id
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Loan is already assigned "
                "to this collector"
            ),
        )

    now = datetime.now(timezone.utc)

    if current is not None:
        current.released_at = now
        current.released_by_user_id = (
            membership.user_id
        )
        current.release_reason = "Reassigned"

    assignment = LoanCollectorAssignment(
        tenant_id=tenant.id,
        loan_id=loan_id,
        collector_user_id=(
            payload.collector_user_id
        ),
        assigned_by_user_id=membership.user_id,
        assigned_at=now,
    )

    try:
        db.add(assignment)
        db.flush()
        add_admin_audit(db, operator_user_id=membership.user_id,
                        action="collections.assignment_created", target_type="collector_assignment",
                        target_id=assignment.id, tenant_id=tenant.id,
                        before_data={"collector_user_id": current.collector_user_id} if current else None,
                        after_data={"loan_id": loan_id, "collector_user_id": assignment.collector_user_id})
        db.commit()
        db.refresh(assignment)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "Loan already has an active "
                "collector assignment"
            ),
        ) from exc
    except Exception:
        db.rollback()
        raise

    return collector_assignment_read(
        db=db,
        assignment=assignment,
    )


@router.post(
    "/loans/{loan_id}/assignment/release",
    response_model=CollectorAssignmentRead,
)
def release_loan_collector(
    loan_id: int,
    payload: CollectorAssignmentRelease,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    membership: TenantMembership = Depends(
        get_current_tenant_membership
    ),
):
    db.scalar(select(Tenant).where(Tenant.id == tenant.id).with_for_update())
    db.refresh(membership)
    require_collections_owner(membership)

    get_tenant_loan(
        db=db,
        tenant_id=tenant.id,
        loan_id=loan_id,
        lock=True,
    )

    assignment = active_collector_assignment(
        db=db,
        tenant_id=tenant.id,
        loan_id=loan_id,
        lock=True,
    )

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Active collector assignment "
                "not found"
            ),
        )

    assignment.released_at = datetime.now(
        timezone.utc
    )
    assignment.released_by_user_id = (
        membership.user_id
    )
    assignment.release_reason = payload.reason

    add_admin_audit(db, operator_user_id=membership.user_id,
                    action="collections.assignment_released", target_type="collector_assignment",
                    target_id=assignment.id, tenant_id=tenant.id,
                    after_data={"loan_id": loan_id, "collector_user_id": assignment.collector_user_id,
                                "reason": payload.reason})

    try:
        db.commit()
        db.refresh(assignment)
    except Exception:
        db.rollback()
        raise

    return collector_assignment_read(
        db=db,
        assignment=assignment,
    )


@router.get(
    "/loans/{loan_id}/assignments",
    response_model=list[CollectorAssignmentRead],
)
def list_loan_collector_assignments(
    loan_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    membership: TenantMembership = Depends(
        get_current_tenant_membership
    ),
):
    require_collections_owner(membership)

    get_tenant_loan(
        db=db,
        tenant_id=tenant.id,
        loan_id=loan_id,
    )

    assignments = db.scalars(
        select(LoanCollectorAssignment)
        .where(
            LoanCollectorAssignment.tenant_id
            == tenant.id,
            LoanCollectorAssignment.loan_id
            == loan_id,
        )
        .order_by(
            LoanCollectorAssignment.assigned_at.desc(),
            LoanCollectorAssignment.id.desc(),
        )
    ).all()

    return [
        collector_assignment_read(
            db=db,
            assignment=assignment,
        )
        for assignment in assignments
    ]


def require_collector_assignment_access(
    *,
    db: Session,
    tenant_id: int,
    loan_id: int,
    membership: TenantMembership,
) -> None:
    if membership.role in COLLECTIONS_MANAGEMENT_ROLES:
        return

    assignment = active_collector_assignment(
        db=db,
        tenant_id=tenant_id,
        loan_id=loan_id,
    )

    if (
        assignment is None
        or assignment.collector_user_id
        != membership.user_id
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Loan is not assigned "
                "to this collector"
            ),
        )
