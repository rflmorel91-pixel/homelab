from datetime import date, datetime
from typing import Literal
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


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

LoanType = Literal[
    "personal",
    "vehicle",
]


class LoanCreate(BaseModel):
    borrower_id: int = Field(gt=0)
    loan_type: LoanType = "personal"
    vehicle_cash_price: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=14,
        decimal_places=2,
    )
    vehicle_down_payment: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=14,
        decimal_places=2,
    )
    vehicle_make: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    vehicle_model: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    vehicle_year: int | None = Field(
        default=None,
        ge=1886,
        le=2100,
    )
    vehicle_color: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    vehicle_vin: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    vehicle_license_plate: str | None = Field(
        default=None,
        min_length=1,
        max_length=30,
    )
    vehicle_seller: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    vehicle_notes: str | None = None
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
    late_fee_enabled: bool = False
    notes: str | None = None

    @model_validator(mode="after")
    def validate_vehicle_financing(self):
        vehicle_values = (
            self.vehicle_cash_price,
            self.vehicle_down_payment,
            self.vehicle_make,
            self.vehicle_model,
            self.vehicle_year,
            self.vehicle_color,
            self.vehicle_vin,
            self.vehicle_license_plate,
            self.vehicle_seller,
            self.vehicle_notes,
        )

        if self.loan_type == "personal":
            if any(
                value is not None
                for value in vehicle_values
            ):
                raise ValueError(
                    "Vehicle fields require a vehicle loan"
                )

            return self

        required = (
            self.vehicle_cash_price,
            self.vehicle_down_payment,
            self.vehicle_make,
            self.vehicle_model,
            self.vehicle_year,
        )

        if any(value is None for value in required):
            raise ValueError(
                "Vehicle cash price, down payment, make, "
                "model and year are required"
            )

        if (
            self.vehicle_down_payment
            > self.vehicle_cash_price
        ):
            raise ValueError(
                "Vehicle down payment cannot exceed cash price"
            )

        financed_amount = (
            self.vehicle_cash_price
            - self.vehicle_down_payment
        ).quantize(Decimal("0.01"))

        if financed_amount != self.principal_amount.quantize(
            Decimal("0.01")
        ):
            raise ValueError(
                "Principal amount must equal vehicle cash "
                "price minus down payment"
            )

        return self

    model_config = ConfigDict(extra="forbid")


class LoanRead(BaseModel):
    id: int
    borrower_id: int
    loan_type: LoanType
    vehicle_cash_price: Decimal | None
    vehicle_down_payment: Decimal | None
    vehicle_make: str | None
    vehicle_model: str | None
    vehicle_year: int | None
    vehicle_color: str | None
    vehicle_vin: str | None
    vehicle_license_plate: str | None
    vehicle_seller: str | None
    vehicle_notes: str | None
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
    late_fee_enabled: bool
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
    principal_paid: Decimal
    interest_paid: Decimal
    late_fee_accrued: Decimal
    late_fee_paid: Decimal
    late_fee_assessed_through: date | None
    status: InstallmentStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoanDetail(LoanRead):
    installments: list[InstallmentRead]


class LoanLateFeeUpdate(BaseModel):
    late_fee_enabled: bool

    model_config = ConfigDict(extra="forbid")


PaymentMethod = Literal[
    "cash",
    "bank_transfer",
    "card",
    "other",
]


class PaymentCreate(BaseModel):
    installment_id: int = Field(gt=0)
    amount: Decimal = Field(
        gt=0,
        max_digits=14,
        decimal_places=2,
    )
    payment_method: PaymentMethod = "cash"
    reference: str | None = Field(
        default=None,
        max_length=200,
    )
    notes: str | None = None
    paid_at: datetime | None = None

    model_config = ConfigDict(extra="forbid")


class PaymentRead(BaseModel):
    id: int
    loan_id: int
    installment_id: int
    recorded_by_user_id: int
    cash_closing_id: int | None
    amount: Decimal
    principal_amount: Decimal
    interest_amount: Decimal
    late_fee_amount: Decimal
    payment_method: PaymentMethod
    reference: str | None
    notes: str | None
    paid_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentReceipt(PaymentRead):
    receipt_number: str
    installment_total: Decimal
    installment_paid: Decimal
    installment_balance: Decimal
    installment_ordinary_balance: Decimal
    installment_late_fee_accrued: Decimal
    installment_late_fee_paid: Decimal
    installment_late_fee_balance: Decimal
    installment_status: InstallmentStatus
    loan_balance: Decimal
    loan_status: LoanStatus
    currency: Literal["DOP"]


ProspectStatus = Literal[
    "new",
    "contacted",
    "qualified",
    "rejected",
    "converted",
]

PreferredContact = Literal[
    "phone",
    "whatsapp",
    "email",
]


class PublicProspectCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    phone: str = Field(min_length=1, max_length=40)
    email: str | None = Field(default=None, max_length=320)
    municipality: str | None = Field(
        default=None,
        max_length=120,
    )
    province: str | None = Field(
        default=None,
        max_length=120,
    )
    requested_amount: Decimal = Field(
        gt=0,
        max_digits=14,
        decimal_places=2,
    )
    preferred_contact: PreferredContact = "phone"
    message: str | None = Field(
        default=None,
        max_length=2000,
    )
    consent_to_contact: Literal[True]

    @field_validator(
        "full_name",
        "phone",
    )
    @classmethod
    def reject_blank_required_text(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Value cannot be blank"
            )

        return normalized

    model_config = ConfigDict(extra="forbid")


class PublicProspectRead(BaseModel):
    prospect_id: int
    status: Literal["received"]


class ProspectRead(BaseModel):
    id: int
    converted_borrower_id: int | None
    full_name: str
    phone: str
    email: str | None
    municipality: str | None
    province: str | None
    requested_amount: Decimal
    preferred_contact: PreferredContact
    message: str | None
    status: ProspectStatus
    consented_at: datetime
    consent_notice_version: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProspectUpdate(BaseModel):
    status: Literal[
        "new",
        "contacted",
        "qualified",
        "rejected",
    ]

    model_config = ConfigDict(extra="forbid")


class ProspectConversionRead(BaseModel):
    prospect_id: int
    borrower_id: int
    status: Literal["converted"]


class PublicProspectPageRead(BaseModel):
    tenant_slug: str
    business_name: str
    client_number: int
