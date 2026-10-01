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


def test_cashier_search_returns_minimum_payment_data(
    authenticated_client,
    db_session,
):
    tenant, borrower, loan, installment = (
        create_cashier_test_records(db_session)
    )
    headers = authenticated_client.auth_headers(tenant)
    url = f"{BASE_URL}/cashier/loans"

    by_name = authenticated_client.get(
        url,
        headers=headers,
        params={"query": "Sintético de Caja"},
    )

    assert by_name.status_code == 200
    assert len(by_name.json()) == 1

    summary = by_name.json()[0]

    assert summary["id"] == loan.id
    assert summary["borrower_full_name"] == (
        borrower.full_name
    )
    assert summary["borrower_document_type"] == "cedula"
    assert summary["borrower_document_number"] == (
        borrower.document_number
    )
    assert summary["vehicle_make"] == "Toyota"
    assert summary["vehicle_model"] == "Corolla"
    assert summary["vehicle_year"] == 2022
    assert Decimal(summary["total_due"]) == Decimal(
        "11000.00"
    )
    assert Decimal(summary["paid_amount"]) == Decimal(
        "0.00"
    )
    assert Decimal(summary["balance_due"]) == Decimal(
        "11000.00"
    )
    assert summary["next_due_date"] == "2026-11-01"

    by_document = authenticated_client.get(
        url,
        headers=headers,
        params={"query": borrower.document_number},
    )
    assert by_document.status_code == 200
    assert [
        item["id"]
        for item in by_document.json()
    ] == [loan.id]

    by_loan_number = authenticated_client.get(
        url,
        headers=headers,
        params={"query": str(loan.id)},
    )
    assert by_loan_number.status_code == 200
    assert [
        item["id"]
        for item in by_loan_number.json()
    ] == [loan.id]

    payment = authenticated_client.post(
        f"{BASE_URL}/payments",
        headers=headers,
        json={
            "installment_id": installment.id,
            "amount": "100.00",
            "payment_method": "cash",
            "reference": "CASHIER-SEARCH-TEST",
            "paid_at": "2026-10-01T12:00:00Z",
        },
    )
    assert payment.status_code == 201

    detail = authenticated_client.get(
        f"{url}/{loan.id}",
        headers=headers,
    )

    assert detail.status_code == 200
    payload = detail.json()

    assert Decimal(payload["paid_amount"]) == Decimal(
        "100.00"
    )
    assert Decimal(payload["balance_due"]) == Decimal(
        "10900.00"
    )
    assert len(payload["installments"]) == 1
    assert Decimal(
        payload["installments"][0]["paid_amount"]
    ) == Decimal("100.00")
    assert payload["installments"][0]["status"] == (
        "partial"
    )


def test_cashier_api_cannot_cross_tenant_boundary(
    authenticated_client,
    db_session,
):
    tenant, _, loan, _ = (
        create_cashier_test_records(db_session)
    )

    product = db_session.scalar(
        select(Product).where(
            Product.slug == "prestamodesk"
        )
    )
    assert product is not None

    other_tenant = Tenant(
        product_id=product.id,
        client_number=702,
        name="Other Cashier Tenant",
        slug="other-cashier-tenant",
        status="active",
    )
    db_session.add(other_tenant)
    db_session.commit()
    db_session.refresh(other_tenant)

    headers = authenticated_client.auth_headers(
        other_tenant
    )

    listed = authenticated_client.get(
        f"{BASE_URL}/cashier/loans",
        headers=headers,
    )
    assert listed.status_code == 200
    assert listed.json() == []

    detail = authenticated_client.get(
        f"{BASE_URL}/cashier/loans/{loan.id}",
        headers=headers,
    )
    assert detail.status_code == 404
    assert detail.json()["detail"] == "Loan not found"
