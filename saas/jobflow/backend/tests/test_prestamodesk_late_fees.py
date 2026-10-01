from datetime import date
from decimal import Decimal

import pytest

from app.products.prestamodesk.late_fees import (
    calculate_late_fee,
)


def calculate(**overrides):
    values = {
        "due_date": date(2026, 10, 1),
        "ordinary_balance": Decimal("10000.00"),
        "installment_total": Decimal("10000.00"),
        "daily_rate_percent": Decimal("0.1000"),
        "grace_days": 5,
        "cap_percent": Decimal("25.0000"),
        "effective_date": date(2026, 10, 1),
        "assessment_through": date(2026, 10, 7),
    }
    values.update(overrides)
    return calculate_late_fee(**values)


def test_late_fee_starts_after_five_full_grace_days():
    during_grace = calculate(
        assessment_through=date(2026, 10, 6)
    )
    first_late_day = calculate(
        assessment_through=date(2026, 10, 7)
    )

    assert during_grace.days_assessed == 0
    assert during_grace.fee_added == Decimal("0.00")

    assert first_late_day.assessment_start == date(
        2026,
        10,
        7,
    )
    assert first_late_day.days_assessed == 1
    assert first_late_day.fee_added == Decimal("10.00")


def test_effective_date_prevents_retroactive_charge():
    result = calculate(
        due_date=date(2026, 9, 1),
        effective_date=date(2026, 10, 1),
        assessment_through=date(2026, 10, 3),
    )

    assert result.assessment_start == date(2026, 10, 1)
    assert result.days_assessed == 3
    assert result.fee_added == Decimal("30.00")


def test_incremental_assessment_does_not_duplicate_days():
    result = calculate(
        assessment_through=date(2026, 10, 10),
        previously_assessed_through=date(2026, 10, 8),
        previously_accrued=Decimal("20.00"),
    )

    assert result.assessment_start == date(2026, 10, 9)
    assert result.days_assessed == 2
    assert result.fee_added == Decimal("20.00")
    assert result.fee_accrued == Decimal("40.00")


def test_late_fee_uses_current_ordinary_balance():
    result = calculate(
        ordinary_balance=Decimal("4000.00"),
        assessment_through=date(2026, 10, 8),
    )

    assert result.days_assessed == 2
    assert result.fee_added == Decimal("8.00")


def test_late_fee_stops_at_installment_cap():
    result = calculate(
        assessment_through=date(2027, 12, 31),
        previously_accrued=Decimal("2490.00"),
    )

    assert result.fee_cap == Decimal("2500.00")
    assert result.fee_added == Decimal("10.00")
    assert result.fee_accrued == Decimal("2500.00")


def test_paid_installment_does_not_generate_late_fee():
    result = calculate(
        ordinary_balance=Decimal("0.00"),
        assessment_through=date(2026, 12, 1),
    )

    assert result.days_assessed == 0
    assert result.fee_added == Decimal("0.00")


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        (
            "ordinary_balance",
            Decimal("-0.01"),
            "Ordinary balance",
        ),
        (
            "daily_rate_percent",
            Decimal("-0.0001"),
            "rate",
        ),
        (
            "grace_days",
            -1,
            "Grace days",
        ),
        (
            "cap_percent",
            Decimal("-0.0001"),
            "cap",
        ),
    ],
)
def test_invalid_late_fee_terms_are_rejected(
    field,
    value,
    message,
):
    with pytest.raises(ValueError, match=message):
        calculate(**{field: value})
