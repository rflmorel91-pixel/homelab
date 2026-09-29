from app.products.prestamodesk.models.borrower import Borrower
from app.products.prestamodesk.models.loan import Installment, Loan
from app.products.prestamodesk.models.payment import Payment

__all__ = [
    "Borrower",
    "Installment",
    "Loan",
    "Payment",
]

from app.products.prestamodesk.models.prospect import Prospect
