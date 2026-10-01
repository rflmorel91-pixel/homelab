from datetime import date
from decimal import Decimal

import pytest

from app.products.prestamodesk.amortization import (
    build_fixed_schedule,
)


def test_fixed_weekly_schedule():
    calculation = build_fixed_schedule(
        principal_amount=Decimal("10000"),
        flat_interest_rate_percent=Decimal("10"),
        installment_count=5,
        payment_frequency="weekly",
        first_payment_date=date(2026, 10, 2),
    )

    assert calculation.total_interest == Decimal("1000.00")
    assert calculation.total_due == Decimal("11000.00")
    assert len(calculation.installments) == 5

    assert [
        item.total_due
        for item in calculation.installments
    ] == [Decimal("2200.00")] * 5

    assert calculation.installments[0].due_date == date(
        2026,
        10,
        2,
    )
    assert calculation.installments[-1].due_date == date(
        2026,
        10,
        30,
    )


def test_schedule_preserves_totals_after_rounding():
    calculation = build_fixed_schedule(
        principal_amount=Decimal("10000"),
        flat_interest_rate_percent=Decimal("7"),
        installment_count=3,
        payment_frequency="biweekly",
        first_payment_date=date(2026, 10, 1),
    )

    assert sum(
        item.principal_due
        for item in calculation.installments
    ) == Decimal("10000.00")

    assert sum(
        item.interest_due
        for item in calculation.installments
    ) == Decimal("700.00")

    assert sum(
        item.total_due
        for item in calculation.installments
    ) == Decimal("10700.00")


def test_monthly_schedule_preserves_month_end():
    calculation = build_fixed_schedule(
        principal_amount=Decimal("12000"),
        flat_interest_rate_percent=Decimal("0"),
        installment_count=4,
        payment_frequency="monthly",
        first_payment_date=date(2027, 1, 31),
    )

    assert [
        item.due_date
        for item in calculation.installments
    ] == [
        date(2027, 1, 31),
        date(2027, 2, 28),
        date(2027, 3, 31),
        date(2027, 4, 30),
    ]


@pytest.mark.parametrize(
    ("principal", "rate", "count", "message"),
    [
        ("0", "10", 5, "Principal amount"),
        ("1000", "-1", 5, "Interest rate"),
        ("1000", "10", 0, "Installment count"),
    ],
)
def test_schedule_rejects_invalid_terms(
    principal,
    rate,
    count,
    message,
):
    with pytest.raises(ValueError, match=message):
        build_fixed_schedule(
            principal_amount=Decimal(principal),
            flat_interest_rate_percent=Decimal(rate),
            installment_count=count,
            payment_frequency="weekly",
            first_payment_date=date(2026, 10, 1),
        )


def test_vehicle_schedule_distributes_cents_evenly():
    calculation = build_fixed_schedule(
        principal_amount=Decimal("800000.00"),
        flat_interest_rate_percent=Decimal("10.0000"),
        installment_count=12,
        payment_frequency="monthly",
        first_payment_date=date(2026, 10, 29),
    )

    totals = [
        item.total_due
        for item in calculation.installments
    ]

    assert totals == (
        [Decimal("73333.34")] * 4
        + [Decimal("73333.33")] * 8
    )

    assert max(totals) - min(totals) == Decimal("0.01")

    assert sum(
        item.principal_due
        for item in calculation.installments
    ) == Decimal("800000.00")

    assert sum(
        item.interest_due
        for item in calculation.installments
    ) == Decimal("80000.00")

    assert sum(totals) == Decimal("880000.00")

    assert all(
        item.total_due
        == item.principal_due + item.interest_due
        for item in calculation.installments
    )
