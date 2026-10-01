from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from app.products.prestamodesk.schemas import (
    DocumentType,
    InstallmentRead,
    LoanStatus,
    LoanType,
)


class CashierLoanSummary(BaseModel):
    id: int
    borrower_full_name: str
    borrower_document_type: DocumentType
    borrower_document_number: str | None
    loan_type: LoanType
    vehicle_make: str | None
    vehicle_model: str | None
    vehicle_year: int | None
    currency: Literal["DOP"]
    status: LoanStatus
    total_due: Decimal
    paid_amount: Decimal
    balance_due: Decimal
    next_due_date: date | None


class CashierLoanDetail(CashierLoanSummary):
    installments: list[InstallmentRead]
