from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.products.prestamodesk.application_schemas import (
    ApplicationQuoteCreate,
    PublicApplicationCreate,
)


def vehicle_terms() -> dict:
    return {
        "vehicle_cash_price": Decimal("1000000.00"),
        "vehicle_down_payment": Decimal("200000.00"),
        "vehicle_make": "Toyota",
        "vehicle_model": "Corolla",
        "vehicle_year": 2022,
        "vehicle_color": "Blanco",
        "vehicle_vin": "SYNTHETIC-CHASSIS-002",
        "vehicle_license_plate": "TEST002",
        "vehicle_seller": "Dealer Sintético Staging",
        "principal_amount": Decimal("800000.00"),
        "flat_interest_rate_percent": Decimal("10.0000"),
        "installment_count": 12,
        "payment_frequency": "monthly",
        "start_date": date(2026, 9, 30),
        "first_payment_date": date(2026, 10, 29),
    }


def test_quote_accepts_valid_vehicle_terms():
    payload = ApplicationQuoteCreate(**vehicle_terms())

    assert payload.loan_type == "vehicle"
    assert payload.principal_amount == Decimal("800000.00")
    assert payload.flat_interest_rate_percent == Decimal("10.0000")


def test_application_normalizes_identity_fields():
    payload = PublicApplicationCreate(
        **vehicle_terms(),
        full_name="  Pedro Sanchez  ",
        document_type="cedula",
        document_number="001-0000000-1",
        phone="809-555-0102",
        email="  PEDRO@example.com  ",
        consent_to_contact=True,
    )

    assert payload.full_name == "Pedro Sanchez"
    assert payload.email == "pedro@example.com"


def test_application_rejects_inconsistent_principal():
    values = vehicle_terms()
    values["principal_amount"] = Decimal("700000.00")

    with pytest.raises(
        ValidationError,
        match="Principal amount must equal",
    ):
        PublicApplicationCreate(
            **values,
            full_name="Pedro Sanchez",
            consent_to_contact=True,
        )


def test_application_rejects_payment_before_start():
    values = vehicle_terms()
    values["first_payment_date"] = date(2026, 9, 29)

    with pytest.raises(
        ValidationError,
        match="First payment date cannot be before",
    ):
        PublicApplicationCreate(
            **values,
            full_name="Pedro Sanchez",
            consent_to_contact=True,
        )


def test_application_requires_consent():
    with pytest.raises(ValidationError):
        PublicApplicationCreate(
            **vehicle_terms(),
            full_name="Pedro Sanchez",
            consent_to_contact=False,
        )


def test_application_forbids_unknown_fields():
    with pytest.raises(ValidationError):
        PublicApplicationCreate(
            **vehicle_terms(),
            full_name="Pedro Sanchez",
            consent_to_contact=True,
            unexpected="not allowed",
        )
