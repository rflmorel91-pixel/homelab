from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant
from app.products.prestamodesk.amortization import money
from app.products.prestamodesk.cashier_schemas import (
    CashierLoanDetail,
    CashierLoanSummary,
)
from app.products.prestamodesk.models import (
    Borrower,
    Installment,
    Loan,
)
from app.products.prestamodesk.schemas import InstallmentRead
from app.tenant_context import get_current_tenant


router = APIRouter(
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


def build_summary(
    loan: Loan,
    borrower: Borrower,
    installments: list[Installment],
) -> CashierLoanSummary:
    paid_amount = money(
        sum(
            (
                installment.paid_amount
                for installment in installments
            ),
            Decimal("0.00"),
        )
    )
    balance_due = money(
        loan.total_due - paid_amount
    )
    next_installment = next(
        (
            installment
            for installment in installments
            if installment.status != "paid"
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
        total_due=loan.total_due,
        paid_amount=paid_amount,
        balance_due=balance_due,
        next_due_date=(
            next_installment.due_date
            if next_installment is not None
            else None
        ),
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


@router.get(
    "/loans",
    response_model=list[CashierLoanSummary],
)
def search_cashier_loans(
    query: str | None = Query(
        default=None,
        max_length=200,
    ),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
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
        )
        for loan, borrower in rows
    ]


@router.get(
    "/loans/{loan_id}",
    response_model=CashierLoanDetail,
)
def get_cashier_loan_detail(
    loan_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
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
    summary = build_summary(
        loan,
        borrower,
        installments,
    )

    return CashierLoanDetail(
        **summary.model_dump(),
        installments=[
            InstallmentRead.model_validate(
                installment
            )
            for installment in installments
        ],
    )
