from dataclasses import dataclass
from decimal import Decimal

from app.products.prestamodesk.amortization import money


@dataclass(frozen=True)
class PaymentAllocation:
    amount: Decimal
    late_fee_amount: Decimal
    interest_amount: Decimal
    principal_amount: Decimal
    unapplied_amount: Decimal


def allocate_payment(
    *,
    amount: Decimal,
    late_fee_balance: Decimal,
    interest_balance: Decimal,
    principal_balance: Decimal,
) -> PaymentAllocation:
    payment = money(amount)
    late_balance = money(late_fee_balance)
    interest = money(interest_balance)
    principal = money(principal_balance)

    if payment <= 0:
        raise ValueError(
            "Payment amount must be greater than zero"
        )

    for name, balance in (
        ("Late-fee", late_balance),
        ("Interest", interest),
        ("Principal", principal),
    ):
        if balance < 0:
            raise ValueError(
                f"{name} balance cannot be negative"
            )

    total_balance = money(
        late_balance + interest + principal
    )

    if payment > total_balance:
        raise ValueError(
            "Payment exceeds installment balance"
        )

    remaining = payment

    late_fee_amount = min(
        remaining,
        late_balance,
    )
    remaining = money(
        remaining - late_fee_amount
    )

    interest_amount = min(
        remaining,
        interest,
    )
    remaining = money(
        remaining - interest_amount
    )

    principal_amount = min(
        remaining,
        principal,
    )
    remaining = money(
        remaining - principal_amount
    )

    return PaymentAllocation(
        amount=payment,
        late_fee_amount=late_fee_amount,
        interest_amount=interest_amount,
        principal_amount=principal_amount,
        unapplied_amount=remaining,
    )
