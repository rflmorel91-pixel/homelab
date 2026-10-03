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
    assigned_collector_user_id: int | None = None
    assigned_collector_display_name: str | None = None


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



class CollectionsAgingBucketRead(BaseModel):
    key: Literal[
        "days_1_30",
        "days_31_60",
        "days_61_90",
        "days_91_plus",
    ]
    label: str
    minimum_days: int
    maximum_days: int | None
    loan_count: int
    balance: Decimal


class CollectorPerformanceRead(BaseModel):
    user_id: int
    email: str
    display_name: str
    active_overdue_loan_count: int
    active_overdue_balance: Decimal
    activity_count: int
    promise_count: int
    pending_promise_count: int
    partial_promise_count: int
    fulfilled_promise_count: int
    cancelled_promise_count: int
    overdue_promise_count: int
    promised_amount: Decimal
    fulfilled_amount: Decimal
    promise_count_fulfillment_percent: Decimal
    promise_amount_fulfillment_percent: Decimal


class CollectionsSupervisionRead(BaseModel):
    as_of: date
    overdue_loan_count: int
    overdue_balance: Decimal
    assigned_overdue_loan_count: int
    assigned_overdue_balance: Decimal
    unassigned_overdue_loan_count: int
    unassigned_overdue_balance: Decimal
    promises_due_today_count: int
    follow_ups_due_today_count: int
    overdue_follow_up_count: int
    aging_buckets: list[CollectionsAgingBucketRead]
    total_recovered: Decimal
    activity_count: int
    promise_count: int
    pending_promise_count: int
    partial_promise_count: int
    fulfilled_promise_count: int
    cancelled_promise_count: int
    overdue_promise_count: int
    promised_amount: Decimal
    fulfilled_amount: Decimal
    promise_count_fulfillment_percent: Decimal
    promise_amount_fulfillment_percent: Decimal
    collectors: list[CollectorPerformanceRead]

class CollectorAssignmentCreate(BaseModel):
    collector_user_id: int = Field(gt=0)

    model_config = ConfigDict(extra="forbid")


class CollectorAssignmentRelease(BaseModel):
    reason: str | None = Field(
        default=None,
        max_length=2000,
    )

    model_config = ConfigDict(extra="forbid")


class CollectorAssignmentRead(BaseModel):
    id: int
    tenant_id: int
    loan_id: int
    collector_user_id: int
    collector_email: str
    collector_display_name: str
    assigned_by_user_id: int
    assigned_at: datetime
    released_at: datetime | None
    released_by_user_id: int | None
    release_reason: str | None
    is_active: bool


class CollectorOptionRead(BaseModel):
    user_id: int
    email: str
    display_name: str
