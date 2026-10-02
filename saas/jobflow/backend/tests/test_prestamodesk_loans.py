from datetime import date
from decimal import Decimal

from sqlalchemy import func, select

from app.models import Product, Tenant
from app.products.prestamodesk.models import (
    Borrower,
    Installment,
    LateFeePolicy,
    Loan,
)


LOANS_URL = "/api/v1/products/prestamodesk/loans"


def get_product(db_session, slug):
    product = db_session.scalar(
        select(Product).where(Product.slug == slug)
    )
    assert product is not None
    return product


def create_tenant(db_session, product, name, slug):
    tenant = Tenant(
        product_id=product.id,
        name=name,
        slug=slug,
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


def create_borrower(db_session, tenant, name="Ana Pérez"):
    borrower = Borrower(
        tenant_id=tenant.id,
        full_name=name,
        document_type="cedula",
        status="active",
    )
    db_session.add(borrower)
    db_session.commit()
    db_session.refresh(borrower)
    return borrower


def loan_payload(borrower_id):
    return {
        "borrower_id": borrower_id,
        "principal_amount": "10000.00",
        "flat_interest_rate_percent": "10.0000",
        "installment_count": 5,
        "payment_frequency": "weekly",
        "start_date": "2026-09-25",
        "first_payment_date": "2026-10-02",
        "notes": "Préstamo piloto",
    }


def test_create_loan_generates_fixed_schedule(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session, "prestamodesk")
    tenant = create_tenant(
        db_session,
        product,
        "PréstamoDesk Loan Tenant",
        "prestamodesk-loan-tenant",
    )
    borrower = create_borrower(db_session, tenant)

    response = client.post(
        LOANS_URL,
        headers=client.owner_headers(tenant),
        json=loan_payload(borrower.id),
    )

    assert response.status_code == 201
    body = response.json()

    assert Decimal(body["principal_amount"]) == Decimal(
        "10000.00"
    )
    assert Decimal(body["total_interest"]) == Decimal(
        "1000.00"
    )
    assert Decimal(body["total_due"]) == Decimal("11000.00")
    assert body["currency"] == "DOP"
    assert body["status"] == "active"
    assert body["late_fee_enabled"] is False
    assert len(body["installments"]) == 5

    assert [
        item["due_date"]
        for item in body["installments"]
    ] == [
        "2026-10-02",
        "2026-10-09",
        "2026-10-16",
        "2026-10-23",
        "2026-10-30",
    ]

    assert all(
        Decimal(item["total_due"]) == Decimal("2200.00")
        for item in body["installments"]
    )

    loan = db_session.get(Loan, body["id"])
    assert loan is not None
    assert loan.tenant_id == tenant.id
    assert loan.late_fee_enabled is False

    installment_count = db_session.scalar(
        select(func.count(Installment.id)).where(
            Installment.loan_id == loan.id
        )
    )
    assert installment_count == 5


def test_loans_are_isolated_by_tenant(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session, "prestamodesk")

    tenant_a = create_tenant(
        db_session,
        product,
        "Loan Tenant A",
        "prestamodesk-loan-a",
    )
    tenant_b = create_tenant(
        db_session,
        product,
        "Loan Tenant B",
        "prestamodesk-loan-b",
    )
    borrower_a = create_borrower(
        db_session,
        tenant_a,
        "Borrower A",
    )

    create_response = client.post(
        LOANS_URL,
        headers=client.owner_headers(tenant_a),
        json=loan_payload(borrower_a.id),
    )
    assert create_response.status_code == 201
    loan_id = create_response.json()["id"]

    get_response = client.get(
        f"{LOANS_URL}/{loan_id}",
        headers=client.owner_headers(tenant_b),
    )
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Loan not found"

    create_for_wrong_tenant = client.post(
        LOANS_URL,
        headers=client.owner_headers(tenant_b),
        json=loan_payload(borrower_a.id),
    )
    assert create_for_wrong_tenant.status_code == 404
    assert create_for_wrong_tenant.json()["detail"] == (
        "Borrower not found"
    )


def test_inactive_borrower_cannot_receive_loan(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session, "prestamodesk")
    tenant = create_tenant(
        db_session,
        product,
        "Inactive Borrower Tenant",
        "prestamodesk-inactive-borrower",
    )
    borrower = create_borrower(db_session, tenant)
    borrower.status = "inactive"
    db_session.commit()

    response = client.post(
        LOANS_URL,
        headers=client.owner_headers(tenant),
        json=loan_payload(borrower.id),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Borrower is inactive"
    assert db_session.scalars(select(Loan)).all() == []


def test_first_payment_cannot_precede_start_date(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session, "prestamodesk")
    tenant = create_tenant(
        db_session,
        product,
        "Invalid Date Tenant",
        "prestamodesk-invalid-date",
    )
    borrower = create_borrower(db_session, tenant)
    payload = loan_payload(borrower.id)
    payload["first_payment_date"] = "2026-09-24"

    response = client.post(
        LOANS_URL,
        headers=client.owner_headers(tenant),
        json=payload,
    )

    assert response.status_code == 422
    assert "before the loan start date" in (
        response.json()["detail"]
    )
    assert db_session.scalars(select(Loan)).all() == []


def vehicle_loan_payload(borrower_id):
    payload = loan_payload(borrower_id)
    payload.update(
        {
            "loan_type": "vehicle",
            "principal_amount": "800000.00",
            "vehicle_cash_price": "1000000.00",
            "vehicle_down_payment": "200000.00",
            "vehicle_make": "Toyota",
            "vehicle_model": "Corolla",
            "vehicle_year": 2022,
            "vehicle_color": "Blanco",
            "vehicle_vin": "SYNTHETIC-CHASSIS-001",
            "vehicle_license_plate": "TEST001",
            "vehicle_seller": "Dealer sintético",
            "vehicle_notes": "Vehículo de prueba",
        }
    )
    return payload


def test_create_vehicle_loan_preserves_vehicle_details(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session, "prestamodesk")
    tenant = create_tenant(
        db_session,
        product,
        "Vehicle Loan Tenant",
        "prestamodesk-vehicle-loan",
    )
    borrower = create_borrower(db_session, tenant)

    response = client.post(
        LOANS_URL,
        headers=client.owner_headers(tenant),
        json=vehicle_loan_payload(borrower.id),
    )

    assert response.status_code == 201
    body = response.json()

    assert body["loan_type"] == "vehicle"
    assert Decimal(body["vehicle_cash_price"]) == Decimal(
        "1000000.00"
    )
    assert Decimal(body["vehicle_down_payment"]) == Decimal(
        "200000.00"
    )
    assert body["vehicle_make"] == "Toyota"
    assert body["vehicle_model"] == "Corolla"
    assert body["vehicle_year"] == 2022
    assert body["vehicle_color"] == "Blanco"
    assert body["vehicle_vin"] == "SYNTHETIC-CHASSIS-001"
    assert body["vehicle_license_plate"] == "TEST001"
    assert body["vehicle_seller"] == "Dealer sintético"
    assert body["vehicle_notes"] == "Vehículo de prueba"
    assert Decimal(body["principal_amount"]) == Decimal(
        "800000.00"
    )

    loan = db_session.get(Loan, body["id"])
    assert loan is not None
    assert loan.tenant_id == tenant.id
    assert loan.loan_type == "vehicle"


def test_vehicle_loan_requires_core_vehicle_details(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session, "prestamodesk")
    tenant = create_tenant(
        db_session,
        product,
        "Incomplete Vehicle Tenant",
        "prestamodesk-incomplete-vehicle",
    )
    borrower = create_borrower(db_session, tenant)

    payload = loan_payload(borrower.id)
    payload["loan_type"] = "vehicle"

    response = client.post(
        LOANS_URL,
        headers=client.owner_headers(tenant),
        json=payload,
    )

    assert response.status_code == 422


def test_vehicle_financed_amount_must_match_principal(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session, "prestamodesk")
    tenant = create_tenant(
        db_session,
        product,
        "Vehicle Amount Tenant",
        "prestamodesk-vehicle-amount",
    )
    borrower = create_borrower(db_session, tenant)

    payload = vehicle_loan_payload(borrower.id)
    payload["principal_amount"] = "799999.99"

    response = client.post(
        LOANS_URL,
        headers=client.owner_headers(tenant),
        json=payload,
    )

    assert response.status_code == 422


def test_personal_loan_rejects_vehicle_fields(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session, "prestamodesk")
    tenant = create_tenant(
        db_session,
        product,
        "Personal Loan Validation Tenant",
        "prestamodesk-personal-validation",
    )
    borrower = create_borrower(db_session, tenant)

    payload = loan_payload(borrower.id)
    payload["vehicle_make"] = "Toyota"

    response = client.post(
        LOANS_URL,
        headers=client.owner_headers(tenant),
        json=payload,
    )

    assert response.status_code == 422

def test_late_fee_requires_enabled_tenant_policy(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session, "prestamodesk")
    tenant = create_tenant(
        db_session,
        product,
        "Loan Mora Requirement Tenant",
        "prestamodesk-loan-mora-requirement",
    )
    borrower = create_borrower(db_session, tenant)
    payload = loan_payload(borrower.id)
    payload["late_fee_enabled"] = True

    response = client.post(
        LOANS_URL,
        headers=client.owner_headers(tenant),
        json=payload,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Configure and enable the tenant "
        "late-fee policy first"
    )
    assert db_session.scalars(select(Loan)).all() == []


def test_owner_selects_mora_for_individual_loan(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session, "prestamodesk")
    tenant = create_tenant(
        db_session,
        product,
        "Per Loan Mora Tenant",
        "prestamodesk-per-loan-mora",
    )
    borrower = create_borrower(db_session, tenant)

    created = client.post(
        LOANS_URL,
        headers=client.owner_headers(tenant),
        json=loan_payload(borrower.id),
    )
    assert created.status_code == 201
    loan_id = created.json()["id"]
    assert created.json()["late_fee_enabled"] is False

    db_session.add(
        LateFeePolicy(
            tenant_id=tenant.id,
            enabled=True,
            daily_rate_percent=Decimal("0.1000"),
            grace_days=5,
            cap_percent=Decimal("25.0000"),
            effective_date=date(2026, 10, 1),
        )
    )
    db_session.commit()

    member_attempt = client.put(
        f"{LOANS_URL}/{loan_id}/late-fee",
        headers=client.auth_headers(tenant),
        json={"late_fee_enabled": True},
    )
    assert member_attempt.status_code == 403
    assert member_attempt.json()["detail"] == (
        "Tenant owner access required"
    )

    enabled = client.put(
        f"{LOANS_URL}/{loan_id}/late-fee",
        headers=client.owner_headers(tenant),
        json={"late_fee_enabled": True},
    )
    assert enabled.status_code == 200
    assert enabled.json()["late_fee_enabled"] is True

    stored = db_session.get(Loan, loan_id)
    assert stored is not None
    db_session.refresh(stored)
    assert stored.late_fee_enabled is True

    disabled = client.put(
        f"{LOANS_URL}/{loan_id}/late-fee",
        headers=client.owner_headers(tenant),
        json={"late_fee_enabled": False},
    )
    assert disabled.status_code == 200
    assert disabled.json()["late_fee_enabled"] is False

    db_session.refresh(stored)
    assert stored.late_fee_enabled is False


def test_owner_can_create_selected_mora_loan(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session, "prestamodesk")
    tenant = create_tenant(
        db_session,
        product,
        "Selected Mora Creation Tenant",
        "prestamodesk-selected-mora-creation",
    )
    borrower = create_borrower(db_session, tenant)

    db_session.add(
        LateFeePolicy(
            tenant_id=tenant.id,
            enabled=True,
            daily_rate_percent=Decimal("0.1000"),
            grace_days=5,
            cap_percent=Decimal("25.0000"),
            effective_date=date(2026, 10, 1),
        )
    )
    db_session.commit()

    payload = loan_payload(borrower.id)
    payload["late_fee_enabled"] = True

    response = client.post(
        LOANS_URL,
        headers=client.owner_headers(tenant),
        json=payload,
    )

    assert response.status_code == 201
    assert response.json()["late_fee_enabled"] is True

    stored = db_session.get(
        Loan,
        response.json()["id"],
    )
    assert stored is not None
    assert stored.late_fee_enabled is True
