from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant
from app.products.prestamodesk.authorization import (
    require_prestamodesk_payment_member,
)
from app.products.prestamodesk.amortization import money
from app.products.prestamodesk.cashier_schemas import (
    CashierInstallmentRead,
    CashierLoanDetail,
    CashierLoanSummary,
)
from app.products.prestamodesk.late_fees import (
    calculate_late_fee,
)
from app.products.prestamodesk.models import (
    Borrower,
    Installment,
    LateFeePolicy,
    Loan,
)
from app.products.prestamodesk.schemas import InstallmentRead
from app.tenant_context import get_current_tenant


router = APIRouter(
    dependencies=[
        Depends(
            require_prestamodesk_payment_member
        ),
    ],
    prefix="/cashier",
    tags=["PréstamoDesk Cashier"],
)


def get_installments(
    db: Session,
    tenant_id: int,
    loan_id: int,
) -> list[Installment]:
    return list(
        db.scalars(
            select(Installment)
            .where(
                Installment.tenant_id == tenant_id,
                Installment.loan_id == loan_id,
            )
            .order_by(Installment.sequence_number)
        ).all()
    )


def get_policy(
    db: Session,
    tenant_id: int,
) -> LateFeePolicy | None:
    return db.scalar(
        select(LateFeePolicy).where(
            LateFeePolicy.tenant_id == tenant_id
        )
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


def projected_late_fee(
    installment: Installment,
    policy: LateFeePolicy | None,
    loan_late_fee_enabled: bool,
    as_of: date,
) -> Decimal:
    if (
        not loan_late_fee_enabled
        or policy is None
        or not policy.enabled
    ):
        return money(
            installment.late_fee_accrued
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
        assessment_through=as_of,
        previously_assessed_through=(
            installment.late_fee_assessed_through
        ),
        previously_accrued=(
            installment.late_fee_accrued
        ),
    )

    return calculation.fee_accrued


def build_installment_read(
    installment: Installment,
    policy: LateFeePolicy | None,
    loan_late_fee_enabled: bool,
    as_of: date,
) -> CashierInstallmentRead:
    ordinary = ordinary_balance(installment)
    projected_accrued = projected_late_fee(
        installment,
        policy,
        loan_late_fee_enabled,
        as_of,
    )
    late_balance = money(
        projected_accrued
        - installment.late_fee_paid
    )

    data = InstallmentRead.model_validate(
        installment
    ).model_dump()

    return CashierInstallmentRead(
        **data,
        ordinary_balance=ordinary,
        projected_late_fee_accrued=(
            projected_accrued
        ),
        late_fee_balance=late_balance,
        total_balance=money(
            ordinary + late_balance
        ),
        projected_through=as_of,
    )


def build_summary(
    loan: Loan,
    borrower: Borrower,
    installments: list[Installment],
    policy: LateFeePolicy | None,
    as_of: date,
) -> CashierLoanSummary:
    projected = [
        build_installment_read(
            installment,
            policy,
            loan.late_fee_enabled,
            as_of,
        )
        for installment in installments
    ]

    paid_amount = money(
        sum(
            (
                installment.paid_amount
                for installment in installments
            ),
            Decimal("0.00"),
        )
    )
    ordinary_due = money(
        sum(
            (
                installment.ordinary_balance
                for installment in projected
            ),
            Decimal("0.00"),
        )
    )
    late_due = money(
        sum(
            (
                installment.late_fee_balance
                for installment in projected
            ),
            Decimal("0.00"),
        )
    )
    next_installment = next(
        (
            installment
            for installment in projected
            if installment.total_balance
            > Decimal("0.00")
        ),
        None,
    )

    return CashierLoanSummary(
        id=loan.id,
        borrower_full_name=borrower.full_name,
        borrower_document_type=borrower.document_type,
        borrower_document_number=borrower.document_number,
        loan_type=loan.loan_type,
        vehicle_make=loan.vehicle_make,
        vehicle_model=loan.vehicle_model,
        vehicle_year=loan.vehicle_year,
        currency=loan.currency,
        status=loan.status,
        late_fee_enabled=loan.late_fee_enabled,
        total_due=loan.total_due,
        paid_amount=paid_amount,
        ordinary_balance_due=ordinary_due,
        late_fee_balance_due=late_due,
        balance_due=money(
            ordinary_due + late_due
        ),
        next_due_date=(
            next_installment.due_date
            if next_installment is not None
            else None
        ),
        projected_through=as_of,
    )


def get_cashier_loan(
    loan_id: int,
    db: Session,
    tenant: Tenant,
) -> tuple[Loan, Borrower]:
    row = db.execute(
        select(Loan, Borrower)
        .join(
            Borrower,
            Borrower.id == Loan.borrower_id,
        )
        .where(
            Loan.id == loan_id,
            Loan.tenant_id == tenant.id,
            Borrower.tenant_id == tenant.id,
        )
    ).one_or_none()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Loan not found",
        )

    return row


def projection_date(
    as_of: date | None,
) -> date:
    selected = (
        as_of
        or datetime.now(timezone.utc).date()
    )

    if selected > datetime.now(
        timezone.utc
    ).date():
        raise HTTPException(
            status_code=422,
            detail=(
                "Projection date cannot be in the future"
            ),
        )

    return selected


@router.get(
    "/loans",
    response_model=list[CashierLoanSummary],
)
def search_cashier_loans(
    query: str | None = Query(
        default=None,
        max_length=200,
    ),
    as_of: date | None = Query(default=None),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    selected_date = projection_date(as_of)
    policy = get_policy(db, tenant.id)

    statement = (
        select(Loan, Borrower)
        .join(
            Borrower,
            Borrower.id == Loan.borrower_id,
        )
        .where(
            Loan.tenant_id == tenant.id,
            Borrower.tenant_id == tenant.id,
        )
        .order_by(Loan.id.desc())
    )

    normalized = (
        query.strip()
        if query is not None
        else ""
    )

    if normalized:
        conditions = [
            Borrower.full_name.ilike(
                f"%{normalized}%"
            ),
            Borrower.document_number.ilike(
                f"%{normalized}%"
            ),
        ]

        if normalized.isdigit():
            conditions.append(
                Loan.id == int(normalized)
            )

        statement = statement.where(
            or_(*conditions)
        )

    rows = db.execute(statement).all()

    return [
        build_summary(
            loan,
            borrower,
            get_installments(
                db,
                tenant.id,
                loan.id,
            ),
            policy,
            selected_date,
        )
        for loan, borrower in rows
    ]


@router.get(
    "/loans/{loan_id}",
    response_model=CashierLoanDetail,
)
def get_cashier_loan_detail(
    loan_id: int,
    as_of: date | None = Query(default=None),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    selected_date = projection_date(as_of)
    loan, borrower = get_cashier_loan(
        loan_id,
        db,
        tenant,
    )
    installments = get_installments(
        db,
        tenant.id,
        loan.id,
    )
    policy = get_policy(db, tenant.id)
    summary = build_summary(
        loan,
        borrower,
        installments,
        policy,
        selected_date,
    )

    return CashierLoanDetail(
        **summary.model_dump(),
        installments=[
            build_installment_read(
                installment,
                policy,
                loan.late_fee_enabled,
                selected_date,
            )
            for installment in installments
        ],
    )
