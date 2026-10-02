from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CashClosingCreate(BaseModel):
    cash_counted: Decimal = Field(
        ge=0,
        max_digits=14,
        decimal_places=2,
    )
    notes: str | None = Field(
        default=None,
        max_length=1000,
    )

    model_config = ConfigDict(extra="forbid")


class CashClosingPreview(BaseModel):
    opened_at: datetime
    payment_count: int
    total_collected: Decimal
    cash_expected: Decimal
    bank_transfer_total: Decimal
    card_total: Decimal
    other_total: Decimal


class CashClosingRead(CashClosingPreview):
    id: int
    cashier_user_id: int
    closed_at: datetime
    cash_counted: Decimal
    cash_difference: Decimal
    notes: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
