from decimal import Decimal

import pytest

from app.products.prestamodesk.payment_allocation import (
    allocate_payment,
)


def allocate(amount):
    return allocate_payment(
        amount=Decimal(amount),
        late_fee_balance=Decimal("100.00"),
        interest_balance=Decimal("500.00"),
        principal_balance=Decimal("5000.00"),
    )


def test_payment_is_applied_to_late_fee_first():
    result = allocate("75.00")

    assert result.late_fee_amount == Decimal("75.00")
    assert result.interest_amount == Decimal("0.00")
    assert result.principal_amount == Decimal("0.00")


def test_payment_moves_from_late_fee_to_interest():
    result = allocate("300.00")

    assert result.late_fee_amount == Decimal("100.00")
    assert result.interest_amount == Decimal("200.00")
    assert result.principal_amount == Decimal("0.00")


def test_payment_moves_to_principal_last():
    result = allocate("1000.00")

    assert result.late_fee_amount == Decimal("100.00")
    assert result.interest_amount == Decimal("500.00")
    assert result.principal_amount == Decimal("400.00")


def test_full_payment_closes_every_component():
    result = allocate("5600.00")

    assert result.late_fee_amount == Decimal("100.00")
    assert result.interest_amount == Decimal("500.00")
    assert result.principal_amount == Decimal("5000.00")
    assert result.unapplied_amount == Decimal("0.00")


def test_payment_without_late_fee_starts_with_interest():
    result = allocate_payment(
        amount=Decimal("600.00"),
        late_fee_balance=Decimal("0.00"),
        interest_balance=Decimal("500.00"),
        principal_balance=Decimal("5000.00"),
    )

    assert result.late_fee_amount == Decimal("0.00")
    assert result.interest_amount == Decimal("500.00")
    assert result.principal_amount == Decimal("100.00")


def test_overpayment_is_rejected():
    with pytest.raises(
        ValueError,
        match="Payment exceeds installment balance",
    ):
        allocate("5600.01")


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("amount", "0.00", "greater than zero"),
        ("late_fee_balance", "-0.01", "Late-fee"),
        ("interest_balance", "-0.01", "Interest"),
        ("principal_balance", "-0.01", "Principal"),
    ],
)
def test_invalid_allocation_values_are_rejected(
    field,
    value,
    message,
):
    values = {
        "amount": Decimal("1.00"),
        "late_fee_balance": Decimal("0.00"),
        "interest_balance": Decimal("0.00"),
        "principal_balance": Decimal("1.00"),
    }
    values[field] = Decimal(value)

    with pytest.raises(ValueError, match=message):
        allocate_payment(**values)
