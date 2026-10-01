from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from app.products.prestamodesk.amortization import money


PERCENT = Decimal("100")


@dataclass(frozen=True)
class LateFeeCalculation:
    assessment_start: date | None
    assessment_through: date | None
    days_assessed: int
    fee_added: Decimal
    fee_accrued: Decimal
    fee_cap: Decimal


def calculate_late_fee(
    *,
    due_date: date,
    ordinary_balance: Decimal,
    installment_total: Decimal,
    daily_rate_percent: Decimal,
    grace_days: int,
    cap_percent: Decimal,
    effective_date: date,
    assessment_through: date,
    previously_assessed_through: date | None = None,
    previously_accrued: Decimal = Decimal("0.00"),
) -> LateFeeCalculation:
    balance = money(ordinary_balance)
    total = money(installment_total)
    accrued = money(previously_accrued)

    if balance < 0:
        raise ValueError(
            "Ordinary balance cannot be negative"
        )

    if total <= 0:
        raise ValueError(
            "Installment total must be greater than zero"
        )

    if daily_rate_percent < 0:
        raise ValueError(
            "Daily late-fee rate cannot be negative"
        )

    if grace_days < 0:
        raise ValueError(
            "Grace days cannot be negative"
        )

    if cap_percent < 0:
        raise ValueError(
            "Late-fee cap cannot be negative"
        )

    fee_cap = money(
        total * cap_percent / PERCENT
    )

    first_late_date = due_date + timedelta(
        days=grace_days + 1
    )
    assessment_start = max(
        first_late_date,
        effective_date,
    )

    if previously_assessed_through is not None:
        assessment_start = max(
            assessment_start,
            previously_assessed_through
            + timedelta(days=1),
        )

    if (
        balance == Decimal("0.00")
        or daily_rate_percent == 0
        or accrued >= fee_cap
        or assessment_through < assessment_start
    ):
        return LateFeeCalculation(
            assessment_start=None,
            assessment_through=(
                previously_assessed_through
            ),
            days_assessed=0,
            fee_added=Decimal("0.00"),
            fee_accrued=min(accrued, fee_cap),
            fee_cap=fee_cap,
        )

    days_assessed = (
        assessment_through - assessment_start
    ).days + 1

    calculated_fee = money(
        balance
        * daily_rate_percent
        / PERCENT
        * days_assessed
    )
    available_cap = money(fee_cap - accrued)
    fee_added = min(
        calculated_fee,
        available_cap,
    )

    return LateFeeCalculation(
        assessment_start=assessment_start,
        assessment_through=assessment_through,
        days_assessed=days_assessed,
        fee_added=fee_added,
        fee_accrued=money(accrued + fee_added),
        fee_cap=fee_cap,
    )
