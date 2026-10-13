from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.products.prestamodesk.schemas import (
    DocumentType,
    PaymentFrequency,
)


ApplicationStatus = Literal[
    "new",
    "reviewing",
    "approved",
    "rejected",
    "converted",
]


class VehicleApplicationTerms(BaseModel):
    loan_type: Literal["vehicle"] = "vehicle"

    vehicle_cash_price: Decimal = Field(
        gt=0,
        max_digits=14,
        decimal_places=2,
    )
    vehicle_down_payment: Decimal = Field(
        ge=0,
        max_digits=14,
        decimal_places=2,
    )
    vehicle_make: str = Field(min_length=1, max_length=100)
    vehicle_model: str = Field(min_length=1, max_length=100)
    vehicle_year: int = Field(ge=1886, le=2100)
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
    payment_frequency: PaymentFrequency = "monthly"
    start_date: date
    first_payment_date: date
    notes: str | None = None

    @field_validator(
        "vehicle_make",
        "vehicle_model",
    )
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Value cannot be blank")
        return normalized

    @model_validator(mode="after")
    def validate_financing(self):
        if self.vehicle_down_payment > self.vehicle_cash_price:
            raise ValueError(
                "Vehicle down payment cannot exceed cash price"
            )

        financed = (
            self.vehicle_cash_price
            - self.vehicle_down_payment
        ).quantize(Decimal("0.01"))

        if financed != self.principal_amount.quantize(
            Decimal("0.01")
        ):
            raise ValueError(
                "Principal amount must equal vehicle cash "
                "price minus down payment"
            )

        if self.first_payment_date < self.start_date:
            raise ValueError(
                "First payment date cannot be before start date"
            )

        return self

    model_config = ConfigDict(extra="forbid")


class InternalApplicationTerms(VehicleApplicationTerms):
    """Authenticated terms for either route; identity comes from the prospect."""

    loan_type: Literal["personal", "vehicle"]
    vehicle_cash_price: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    vehicle_down_payment: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    vehicle_make: str | None = Field(default=None, min_length=1, max_length=100)
    vehicle_model: str | None = Field(default=None, min_length=1, max_length=100)
    vehicle_year: int | None = Field(default=None, ge=1886, le=2100)

    @field_validator("vehicle_make", "vehicle_model")
    @classmethod
    def strip_required_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return super().strip_required_text(value)

    @model_validator(mode="after")
    def validate_financing(self):
        if self.first_payment_date < self.start_date:
            raise ValueError("First payment date cannot be before start date")
        vehicle_values = [getattr(self, name) for name in type(self).model_fields if name.startswith("vehicle_")]
        if self.loan_type == "personal":
            if any(value is not None for value in vehicle_values):
                raise ValueError("Vehicle fields require a vehicle loan")
            return self
        if any(value is None for value in (self.vehicle_cash_price, self.vehicle_down_payment, self.vehicle_make, self.vehicle_model, self.vehicle_year)):
            raise ValueError("Vehicle price, down payment, make, model and year are required")
        return super().validate_financing()


class ApplicationQuoteCreate(VehicleApplicationTerms):
    pass


class PublicApplicationCreate(VehicleApplicationTerms):
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
    consent_to_contact: Literal[True]

    @field_validator("full_name")
    @classmethod
    def strip_full_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Value cannot be blank")
        return normalized

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        return normalized or None


class QuoteInstallmentRead(BaseModel):
    sequence_number: int
    due_date: date
    principal_due: Decimal
    interest_due: Decimal
    total_due: Decimal


class ApplicationQuoteRead(BaseModel):
    estimate_only: Literal[True] = True
    currency: Literal["DOP"] = "DOP"
    principal_amount: Decimal
    flat_interest_rate_percent: Decimal
    total_interest: Decimal
    total_due: Decimal
    installment_count: int
    payment_frequency: PaymentFrequency
    installments: list[QuoteInstallmentRead]


class PublicApplicationRead(BaseModel):
    application_id: int
    status: Literal["received"]


class ApplicationRead(BaseModel):
    id: int
    source_prospect_id: int | None
    converted_borrower_id: int | None
    converted_loan_id: int | None
    full_name: str
    document_type: DocumentType
    document_number: str | None
    phone: str | None
    email: str | None
    address: str | None
    municipality: str | None
    province: str | None
    loan_type: Literal["personal", "vehicle"]
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
    status: ApplicationStatus
    decision_reason: str | None
    review_packet: "ApplicationReviewPacketRead | None" = Field(
        default=None, validation_alias="review_packet_data"
    )
    notes: str | None
    consented_at: datetime
    consent_notice_version: str
    reviewed_at: datetime | None
    approved_at: datetime | None
    converted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationUpdate(BaseModel):
    status: Literal[
        "reviewing",
        "approved",
        "rejected",
    ]
    decision_reason: str | None = Field(default=None, min_length=1, max_length=2000)

    @field_validator("decision_reason")
    @classmethod
    def strip_decision_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("A decision reason cannot be blank")
        return value

    model_config = ConfigDict(extra="forbid")


class ApplicationConversionRead(BaseModel):
    application_id: int
    borrower_id: int
    loan_id: int
    status: Literal["converted"]


class VehicleInspection(BaseModel):
    status: Literal["pending", "passed", "failed"] = "pending"
    inspector_name: str | None = Field(default=None, max_length=160)
    inspected_at: datetime | None = None
    findings: str | None = Field(default=None, max_length=4000)

    model_config = ConfigDict(extra="forbid")


class SupportingDocument(BaseModel):
    document_type: Literal["identity", "income", "vehicle_registration"]
    status: Literal["pending", "received", "verified", "rejected"] = "pending"
    # UUID references are opaque IDs from an approved private document store.
    # Public URLs and filesystem paths are deliberately not accepted here.
    storage_ref: UUID | None = None
    checked_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=1000)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def verified_document_has_private_reference(self):
        if self.status in {"received", "verified"} and self.storage_ref is None:
            raise ValueError("Received documents require a private storage reference")
        if self.status == "verified" and self.checked_at is None:
            raise ValueError("Verified documents require a check date")
        return self


class ApplicationReference(BaseModel):
    full_name: str = Field(min_length=1, max_length=160)
    relationship: str = Field(min_length=1, max_length=80)
    phone: str = Field(min_length=1, max_length=40)
    status: Literal["pending", "contacted", "unreachable"] = "pending"
    outcome_notes: str | None = Field(default=None, max_length=2000)

    model_config = ConfigDict(extra="forbid")

    @field_validator("full_name", "relationship", "phone")
    @classmethod
    def strip_reference_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Reference fields cannot be blank")
        return value


class CreditAssessment(BaseModel):
    income_source: str = Field(min_length=2, max_length=160)
    monthly_net_income: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    monthly_obligations: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    affordability_summary: str = Field(min_length=10, max_length=4000)
    recommendation: Literal["approve", "decline"]

    model_config = ConfigDict(extra="forbid")

    @field_validator("income_source", "affordability_summary")
    @classmethod
    def strip_assessment_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Assessment fields cannot be blank")
        return value


class ContractFormalization(BaseModel):
    status: Literal["draft", "prepared", "signed"] = "draft"
    template_version: str | None = Field(default=None, max_length=80)
    signed_at: datetime | None = None
    signed_copy_ref: UUID | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("template_version")
    @classmethod
    def strip_template_version(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Template version cannot be blank")
        return value

    @model_validator(mode="after")
    def signed_contract_has_evidence(self):
        if self.status == "signed" and (
            self.template_version is None
            or self.signed_at is None
            or self.signed_copy_ref is None
        ):
            raise ValueError("Signed contracts require version, date, and private copy reference")
        return self


class ApplicationReviewPacketRead(BaseModel):
    inspection: VehicleInspection = Field(default_factory=VehicleInspection)
    documents: list[SupportingDocument] = Field(default_factory=list)
    references: list[ApplicationReference] = Field(default_factory=list)
    assessment: CreditAssessment | None = None
    contract: ContractFormalization = Field(default_factory=ContractFormalization)

    model_config = ConfigDict(extra="forbid")


class ApplicationReviewEventRead(BaseModel):
    id: int
    event_type: str
    details: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


ApplicationRead.model_rebuild()
