from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


CollectionChannel = Literal[
    "phone",
    "whatsapp",
    "sms",
    "email",
    "visit",
    "other",
]

PromiseStatus = Literal[
    "pending",
    "partial",
    "fulfilled",
    "cancelled",
]


class CollectionPortfolioItem(BaseModel):
    loan_id: int
    borrower_id: int
    borrower_full_name: str
    borrower_document_number: str | None
    borrower_phone: str | None
    borrower_email: str | None
    currency: Literal["DOP"]
    oldest_due_date: date
    days_overdue: int
    overdue_installment_count: int
    ordinary_balance_due: Decimal
    late_fee_balance_due: Decimal
    total_balance_due: Decimal


class CollectionActivityCreate(BaseModel):
    channel: CollectionChannel
    outcome: str = Field(
        min_length=1,
        max_length=100,
    )
    notes: str | None = Field(
        default=None,
        max_length=2000,
    )
    contacted_at: datetime
    next_follow_up_at: datetime | None = None

    model_config = ConfigDict(extra="forbid")


class CollectionActivityRead(BaseModel):
    id: int
    tenant_id: int
    loan_id: int
    recorded_by_user_id: int
    channel: CollectionChannel
    outcome: str
    notes: str | None
    contacted_at: datetime
    next_follow_up_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentPromiseCreate(BaseModel):
    promised_amount: Decimal = Field(
        gt=0,
        max_digits=14,
        decimal_places=2,
    )
    due_date: date
    notes: str | None = Field(
        default=None,
        max_length=2000,
    )

    model_config = ConfigDict(extra="forbid")


class PaymentPromiseCancel(BaseModel):
    notes: str | None = Field(
        default=None,
        max_length=2000,
    )

    model_config = ConfigDict(extra="forbid")


class PaymentPromiseRead(BaseModel):
    id: int
    tenant_id: int
    loan_id: int
    created_by_user_id: int
    promised_amount: Decimal
    fulfilled_amount: Decimal
    remaining_amount: Decimal
    due_date: date
    status: PromiseStatus
    is_overdue: bool
    notes: str | None
    fulfilled_at: datetime | None
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PromisePaymentAllocationRead(BaseModel):
    id: int
    promise_id: int
    payment_id: int
    amount: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
