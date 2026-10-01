from decimal import Decimal

from sqlalchemy import func, select

from app.models import Product, Tenant
from app.products.prestamodesk.models import (
    Borrower,
    Installment,
    Loan,
    Payment,
)


LOANS_URL = "/api/v1/products/prestamodesk/loans"
PAYMENTS_URL = "/api/v1/products/prestamodesk/payments"


def get_product(db_session):
    product = db_session.scalar(
        select(Product).where(
            Product.slug == "prestamodesk"
        )
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


def create_borrower(db_session, tenant, name):
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


def create_two_installment_loan(
    client,
    tenant,
    borrower,
):
    response = client.post(
        LOANS_URL,
        headers=client.owner_headers(tenant),
        json={
            "borrower_id": borrower.id,
            "principal_amount": "10000.00",
            "flat_interest_rate_percent": "10.0000",
            "installment_count": 2,
            "payment_frequency": "weekly",
            "start_date": "2026-09-25",
            "first_payment_date": "2026-10-02",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_partial_and_final_payments_update_balances(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant = create_tenant(
        db_session,
        product,
        "PréstamoDesk Payment Tenant",
        "prestamodesk-payment-tenant",
    )
    borrower = create_borrower(
        db_session,
        tenant,
        "Luis Martínez",
    )
    loan = create_two_installment_loan(
        client,
        tenant,
        borrower,
    )
    first = loan["installments"][0]
    second = loan["installments"][1]
    headers = client.auth_headers(tenant)

    partial = client.post(
        PAYMENTS_URL,
        headers=headers,
        json={
            "installment_id": first["id"],
            "amount": "1000.00",
            "payment_method": "cash",
            "paid_at": "2026-09-30T12:00:00Z",
        },
    )

    assert partial.status_code == 201
    receipt = partial.json()
    assert receipt["recorded_by_user_id"] > 0
    assert receipt["receipt_number"].startswith("PM-")
    assert receipt["paid_at"].startswith(
        "2026-09-30T12:00:00"
    )
    assert Decimal(receipt["installment_paid"]) == Decimal(
        "1000.00"
    )
    assert Decimal(receipt["installment_balance"]) == Decimal(
        "4500.00"
    )
    assert Decimal(receipt["loan_balance"]) == Decimal(
        "10000.00"
    )
    assert receipt["installment_status"] == "partial"
    assert receipt["loan_status"] == "active"

    overpayment = client.post(
        PAYMENTS_URL,
        headers=headers,
        json={
            "installment_id": first["id"],
            "amount": "4500.01",
        },
    )
    assert overpayment.status_code == 409
    assert overpayment.json()["detail"] == (
        "Payment exceeds installment balance"
    )

    complete_first = client.post(
        PAYMENTS_URL,
        headers=headers,
        json={
            "installment_id": first["id"],
            "amount": "4500.00",
            "payment_method": "bank_transfer",
            "reference": "TEST-TRANSFER-001",
        },
    )
    assert complete_first.status_code == 201
    assert complete_first.json()["installment_status"] == "paid"
    assert complete_first.json()["loan_status"] == "active"

    complete_second = client.post(
        PAYMENTS_URL,
        headers=headers,
        json={
            "installment_id": second["id"],
            "amount": "5500.00",
        },
    )
    assert complete_second.status_code == 201
    assert complete_second.json()["loan_status"] == "paid"
    assert Decimal(
        complete_second.json()["loan_balance"]
    ) == Decimal("0.00")

    stored_loan = db_session.get(Loan, loan["id"])
    assert stored_loan is not None
    db_session.refresh(stored_loan)
    assert stored_loan.status == "paid"

    stored_first = db_session.get(
        Installment,
        first["id"],
    )
    assert stored_first is not None
    db_session.refresh(stored_first)
    assert stored_first.status == "paid"
    assert stored_first.paid_amount == Decimal("5500.00")

    payment_count = db_session.scalar(
        select(func.count(Payment.id)).where(
            Payment.loan_id == loan["id"]
        )
    )
    assert payment_count == 3

    listed = client.get(
        f"{PAYMENTS_URL}/loan/{loan['id']}",
        headers=headers,
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 3


def test_payment_cannot_cross_tenant_boundary(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)

    tenant_a = create_tenant(
        db_session,
        product,
        "Payment Tenant A",
        "prestamodesk-payment-a",
    )
    tenant_b = create_tenant(
        db_session,
        product,
        "Payment Tenant B",
        "prestamodesk-payment-b",
    )
    borrower_a = create_borrower(
        db_session,
        tenant_a,
        "Borrower A",
    )
    loan = create_two_installment_loan(
        client,
        tenant_a,
        borrower_a,
    )
    installment_id = loan["installments"][0]["id"]

    response = client.post(
        PAYMENTS_URL,
        headers=client.auth_headers(tenant_b),
        json={
            "installment_id": installment_id,
            "amount": "100.00",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Installment not found"
    )
    assert db_session.scalars(select(Payment)).all() == []
