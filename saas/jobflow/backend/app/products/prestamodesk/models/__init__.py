from app.products.prestamodesk.models.application import LoanApplication
from app.products.prestamodesk.models.borrower import Borrower
from app.products.prestamodesk.models.loan import Installment, Loan
from app.products.prestamodesk.models.payment import Payment
from app.products.prestamodesk.models.prospect import Prospect

__all__ = [
    "Borrower",
    "Installment",
    "Loan",
    "LoanApplication",
    "Payment",
    "Prospect",
]
