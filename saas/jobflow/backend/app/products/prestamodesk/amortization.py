from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal


PaymentFrequency = Literal[
    "daily",
    "weekly",
    "biweekly",
    "monthly",
]

MONEY = Decimal("0.01")
PERCENT = Decimal("100")


@dataclass(frozen=True)
class InstallmentCalculation:
    sequence_number: int
    due_date: date
    principal_due: Decimal
    interest_due: Decimal
    total_due: Decimal


@dataclass(frozen=True)
class LoanCalculation:
    principal_amount: Decimal
    flat_interest_rate_percent: Decimal
    total_interest: Decimal
    total_due: Decimal
    installments: tuple[InstallmentCalculation, ...]


def money(value: Decimal) -> Decimal:
    return value.quantize(
        MONEY,
        rounding=ROUND_HALF_UP,
    )


def add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(
        value.day,
        monthrange(year, month)[1],
    )
    return date(year, month, day)


def installment_due_date(
    first_payment_date: date,
    frequency: PaymentFrequency,
    installment_index: int,
) -> date:
    if frequency == "daily":
        return first_payment_date + timedelta(
            days=installment_index
        )

    if frequency == "weekly":
        return first_payment_date + timedelta(
            days=7 * installment_index
        )

    if frequency == "biweekly":
        return first_payment_date + timedelta(
            days=14 * installment_index
        )

    if frequency == "monthly":
        return add_months(
            first_payment_date,
            installment_index,
        )

    raise ValueError(
        f"Unsupported payment frequency: {frequency}"
    )


def split_amount(
    total: Decimal,
    count: int,
) -> tuple[Decimal, ...]:
    if count <= 0:
        raise ValueError(
            "Installment count must be greater than zero"
        )

    regular = money(total / count)
    values = [regular] * (count - 1)
    final = money(
        total - sum(values, Decimal("0.00"))
    )
    values.append(final)

    return tuple(values)


def build_fixed_schedule(
    *,
    principal_amount: Decimal,
    flat_interest_rate_percent: Decimal,
    installment_count: int,
    payment_frequency: PaymentFrequency,
    first_payment_date: date,
) -> LoanCalculation:
    principal = money(principal_amount)
    rate = flat_interest_rate_percent

    if principal <= 0:
        raise ValueError(
            "Principal amount must be greater than zero"
        )

    if rate < 0:
        raise ValueError(
            "Interest rate cannot be negative"
        )

    if installment_count <= 0:
        raise ValueError(
            "Installment count must be greater than zero"
        )

    total_interest = money(
        principal * rate / PERCENT
    )
    total_due = money(
        principal + total_interest
    )

    principal_parts = split_amount(
        principal,
        installment_count,
    )
    interest_parts = split_amount(
        total_interest,
        installment_count,
    )

    installments = tuple(
        InstallmentCalculation(
            sequence_number=index + 1,
            due_date=installment_due_date(
                first_payment_date,
                payment_frequency,
                index,
            ),
            principal_due=principal_parts[index],
            interest_due=interest_parts[index],
            total_due=money(
                principal_parts[index]
                + interest_parts[index]
            ),
        )
        for index in range(installment_count)
    )

    return LoanCalculation(
        principal_amount=principal,
        flat_interest_rate_percent=rate,
        total_interest=total_interest,
        total_due=total_due,
        installments=installments,
    )
