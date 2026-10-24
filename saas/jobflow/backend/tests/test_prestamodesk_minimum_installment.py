from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.products.prestamodesk.amortization import build_fixed_schedule
from app.products.prestamodesk.schemas import LoanCreate


@pytest.mark.parametrize(
    "count, rate, accepted",
    [
        (120, "0", False),
        (100, "0", True),
        (101, "0.49", False),
        (101, "0.50", True),
    ],
)
def test_minimum_installment_schema_and_calculator(count, rate, accepted):
    values = dict(
        principal_amount=Decimal("1.00"),
        flat_interest_rate_percent=Decimal(rate),
        installment_count=count,
        payment_frequency="daily",
        first_payment_date=date(2026, 1, 1),
    )
    payload = dict(
        **values,
        borrower_id=1,
        start_date=date(2026, 1, 1),
    )

    if not accepted:
        with pytest.raises(ValidationError, match="at least"):
            LoanCreate(**payload)
        with pytest.raises(ValueError, match="at least"):
            build_fixed_schedule(**values)
        return

    LoanCreate(**payload)
    result = build_fixed_schedule(**values)
    assert all(
        installment.total_due >= Decimal("0.01")
        for installment in result.installments
    )
    assert sum(
        installment.total_due for installment in result.installments
    ) == result.total_due
