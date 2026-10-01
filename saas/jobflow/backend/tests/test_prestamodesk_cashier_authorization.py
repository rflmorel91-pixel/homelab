from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.models import Product, Tenant
from app.products.prestamodesk.models import (
    Borrower,
    Installment,
    Loan,
    Payment,
)


BASE_URL = "/api/v1/products/prestamodesk"


def create_cashier_test_records(db_session):
    product = db_session.scalar(
        select(Product).where(
            Product.slug == "prestamodesk"
        )
    )
    assert product is not None

    tenant = Tenant(
        product_id=product.id,
        client_number=701,
        name="PréstamoDesk Cashier Tenant",
        slug="prestamodesk-cashier-tenant",
        status="active",
    )
    db_session.add(tenant)
    db_session.flush()

    borrower = Borrower(
        tenant_id=tenant.id,
        full_name="Cliente Sintético de Caja",
        document_type="cedula",
        document_number="000-0000701-0",
        status="active",
    )
    db_session.add(borrower)
    db_session.flush()

    loan = Loan(
        tenant_id=tenant.id,
        borrower_id=borrower.id,
        principal_amount=Decimal("10000.00"),
        flat_interest_rate_percent=Decimal("10.0000"),
        total_interest=Decimal("1000.00"),
        total_due=Decimal("11000.00"),
        installment_count=2,
        payment_frequency="monthly",
        start_date=date(2026, 10, 1),
        first_payment_date=date(2026, 11, 1),
        currency="DOP",
        status="active",
        loan_type="vehicle",
        vehicle_cash_price=Decimal("12000.00"),
        vehicle_down_payment=Decimal("2000.00"),
        vehicle_make="Toyota",
        vehicle_model="Corolla",
        vehicle_year=2022,
    )
    db_session.add(loan)
    db_session.flush()

    installment = Installment(
        tenant_id=tenant.id,
        loan_id=loan.id,
        sequence_number=1,
        due_date=date(2026, 11, 1),
        principal_due=Decimal("5000.00"),
        interest_due=Decimal("500.00"),
        total_due=Decimal("5500.00"),
        paid_amount=Decimal("0.00"),
        status="pending",
    )
    db_session.add(installment)
    db_session.commit()

    return tenant, borrower, loan, installment


def test_cashier_can_read_loans_and_record_payment(
    authenticated_client,
    db_session,
):
    tenant, _, loan, installment = (
        create_cashier_test_records(db_session)
    )
    headers = authenticated_client.auth_headers(tenant)

    listed = authenticated_client.get(
        f"{BASE_URL}/loans",
        headers=headers,
    )
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [
        loan.id
    ]

    detail = authenticated_client.get(
        f"{BASE_URL}/loans/{loan.id}",
        headers=headers,
    )
    assert detail.status_code == 200
    assert detail.json()["id"] == loan.id

    paid = authenticated_client.post(
        f"{BASE_URL}/payments",
        headers=headers,
        json={
            "installment_id": installment.id,
            "amount": "100.00",
            "payment_method": "cash",
            "reference": "CASHIER-AUTH-TEST",
            "paid_at": "2026-10-01T12:00:00Z",
        },
    )
    assert paid.status_code == 201
    assert paid.json()["recorded_by_user_id"] == (
        authenticated_client.auth_user.id
    )

    payment = db_session.scalar(
        select(Payment).where(
            Payment.reference == "CASHIER-AUTH-TEST"
        )
    )
    assert payment is not None
    assert payment.amount == Decimal("100.00")


def test_cashier_cannot_access_administration(
    authenticated_client,
    db_session,
):
    tenant, borrower, _, _ = (
        create_cashier_test_records(db_session)
    )
    headers = authenticated_client.auth_headers(tenant)

    requests = (
        (
            "get",
            f"{BASE_URL}/borrowers",
            None,
        ),
        (
            "get",
            f"{BASE_URL}/applications",
            None,
        ),
        (
            "get",
            f"{BASE_URL}/prospects",
            None,
        ),
        (
            "post",
            f"{BASE_URL}/loans",
            {
                "borrower_id": borrower.id,
                "principal_amount": "1000.00",
                "flat_interest_rate_percent": "10.0000",
                "installment_count": 1,
                "payment_frequency": "monthly",
                "start_date": "2026-10-01",
                "first_payment_date": "2026-11-01",
            },
        ),
    )

    for method, url, payload in requests:
        response = authenticated_client.request(
            method,
            url,
            headers=headers,
            json=payload,
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Tenant owner access required"
        )
