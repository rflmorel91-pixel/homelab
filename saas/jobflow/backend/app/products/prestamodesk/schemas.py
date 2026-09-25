from datetime import date, datetime
from typing import Literal
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


DocumentType = Literal["cedula", "passport", "other"]
BorrowerStatus = Literal["active", "inactive"]


class BorrowerBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    document_type: DocumentType = "cedula"
    document_number: str | None = Field(
        default=None,
        max_length=50,
    )
    phone: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=320)
    address: str | None = None
    municipality: str | None = Field(
        default=None,
        max_length=120,
    )
    province: str | None = Field(
        default=None,
        max_length=120,
    )
    status: BorrowerStatus = "active"
    notes: str | None = None


class BorrowerCreate(BorrowerBase):
    model_config = ConfigDict(extra="forbid")


class BorrowerUpdate(BorrowerBase):
    model_config = ConfigDict(extra="forbid")


class BorrowerRead(BorrowerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


PaymentFrequency = Literal[
    "daily",
    "weekly",
    "biweekly",
    "monthly",
]

LoanStatus = Literal[
    "active",
    "paid",
    "cancelled",
]

InstallmentStatus = Literal[
    "pending",
    "partial",
    "paid",
    "overdue",
]


class LoanCreate(BaseModel):
    borrower_id: int = Field(gt=0)
    principal_amount: Decimal = Field(
        gt=0,
        max_digits=14,
        decimal_places=2,
    )
    flat_interest_rate_percent: Decimal = Field(
        ge=0,
        le=1000,
        max_digits=7,
        decimal_places=4,
    )
    installment_count: int = Field(ge=1, le=3660)
    payment_frequency: PaymentFrequency
    start_date: date
    first_payment_date: date
    notes: str | None = None

    model_config = ConfigDict(extra="forbid")


class LoanRead(BaseModel):
    id: int
    borrower_id: int
    principal_amount: Decimal
    flat_interest_rate_percent: Decimal
    total_interest: Decimal
    total_due: Decimal
    installment_count: int
    payment_frequency: PaymentFrequency
    start_date: date
    first_payment_date: date
    currency: Literal["DOP"]
    status: LoanStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InstallmentRead(BaseModel):
    id: int
    loan_id: int
    sequence_number: int
    due_date: date
    principal_due: Decimal
    interest_due: Decimal
    total_due: Decimal
    paid_amount: Decimal
    status: InstallmentStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoanDetail(LoanRead):
    installments: list[InstallmentRead]
