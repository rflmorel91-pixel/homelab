from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from app.models import Product, Tenant, User
from app.products.prestamodesk.models import (
    Borrower,
    CashClosing,
    Installment,
    Loan,
    Payment,
)


BASE_URL = "/api/v1/products/prestamodesk/cashier"


def create_records(db_session):
    product = db_session.scalar(
        select(Product).where(
            Product.slug == "prestamodesk"
        )
    )
    assert product is not None

    tenant = Tenant(
        product_id=product.id,
        client_number=770,
        name="PréstamoDesk Cierre Tenant",
        slug="prestamodesk-cierre-tenant",
        status="active",
    )
    db_session.add(tenant)
    db_session.flush()

    borrower = Borrower(
        tenant_id=tenant.id,
        full_name="Cliente Sintético de Cierre",
        document_type="cedula",
        document_number="000-0000770-0",
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
        principal_due=Decimal("10000.00"),
        interest_due=Decimal("1000.00"),
        total_due=Decimal("11000.00"),
        paid_amount=Decimal("0.00"),
        status="pending",
    )
    db_session.add(installment)
    db_session.commit()

    return tenant, loan, installment


def add_payment(
    db_session,
    *,
    tenant,
    loan,
    installment,
    user_id,
    amount,
    method,
    reference,
):
    payment = Payment(
        tenant_id=tenant.id,
        loan_id=loan.id,
        installment_id=installment.id,
        recorded_by_user_id=user_id,
        amount=Decimal(amount),
        principal_amount=Decimal(amount),
        interest_amount=Decimal("0.00"),
        late_fee_amount=Decimal("0.00"),
        payment_method=method,
        reference=reference,
        paid_at=datetime(
            2026,
            10,
            1,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)
    return payment


def test_cashier_closing_totals_and_prevents_double_count(
    authenticated_client,
    db_session,
):
    tenant, loan, installment = create_records(db_session)
    headers = authenticated_client.auth_headers(tenant)

    payments = [
        add_payment(
            db_session,
            tenant=tenant,
            loan=loan,
            installment=installment,
            user_id=authenticated_client.auth_user.id,
            amount=amount,
            method=method,
            reference=f"CLOSE-{index}",
        )
        for index, (amount, method) in enumerate(
            [
                ("100.00", "cash"),
                ("50.00", "bank_transfer"),
                ("25.00", "card"),
                ("5.00", "other"),
            ],
            start=1,
        )
    ]

    other_user = User(
        email="other-cashier@example.com",
        display_name="Other Cashier",
        is_active=True,
    )
    db_session.add(other_user)
    db_session.commit()
    db_session.refresh(other_user)

    other_payment = add_payment(
        db_session,
        tenant=tenant,
        loan=loan,
        installment=installment,
        user_id=other_user.id,
        amount="999.00",
        method="cash",
        reference="OTHER-CASHIER",
    )

    preview = authenticated_client.get(
        f"{BASE_URL}/closing-preview",
        headers=headers,
    )
    assert preview.status_code == 200
    assert preview.json()["payment_count"] == 4
    assert Decimal(
        preview.json()["total_collected"]
    ) == Decimal("180.00")
    assert Decimal(
        preview.json()["cash_expected"]
    ) == Decimal("100.00")
    assert Decimal(
        preview.json()["bank_transfer_total"]
    ) == Decimal("50.00")
    assert Decimal(
        preview.json()["card_total"]
    ) == Decimal("25.00")
    assert Decimal(
        preview.json()["other_total"]
    ) == Decimal("5.00")

    closed = authenticated_client.post(
        f"{BASE_URL}/closings",
        headers=headers,
        json={
            "cash_counted": "98.00",
            "notes": "Faltante sintético",
        },
    )
    assert closed.status_code == 201
    payload = closed.json()
    assert payload["payment_count"] == 4
    assert Decimal(
        payload["cash_difference"]
    ) == Decimal("-2.00")
    assert payload["cashier_user_id"] == (
        authenticated_client.auth_user.id
    )

    closing_id = payload["id"]
    db_session.expire_all()

    for payment in payments:
        stored = db_session.get(Payment, payment.id)
        assert stored.cash_closing_id == closing_id

    stored_other = db_session.get(
        Payment,
        other_payment.id,
    )
    assert stored_other.cash_closing_id is None

    next_preview = authenticated_client.get(
        f"{BASE_URL}/closing-preview",
        headers=headers,
    )
    assert next_preview.status_code == 200
    assert next_preview.json()["payment_count"] == 0
    assert Decimal(
        next_preview.json()["total_collected"]
    ) == Decimal("0.00")

    listed = authenticated_client.get(
        f"{BASE_URL}/closings",
        headers=headers,
    )
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [
        closing_id
    ]


def test_owner_cannot_close_cashier_register(
    authenticated_client,
    db_session,
):
    tenant, _, _ = create_records(db_session)
    headers = authenticated_client.owner_headers(tenant)

    preview = authenticated_client.get(
        f"{BASE_URL}/closing-preview",
        headers=headers,
    )
    assert preview.status_code == 403

    closed = authenticated_client.post(
        f"{BASE_URL}/closings",
        headers=headers,
        json={"cash_counted": "0.00"},
    )
    assert closed.status_code == 403


def test_cash_counted_cannot_be_negative(
    authenticated_client,
    db_session,
):
    tenant, _, _ = create_records(db_session)
    headers = authenticated_client.auth_headers(tenant)

    response = authenticated_client.post(
        f"{BASE_URL}/closings",
        headers=headers,
        json={"cash_counted": "-0.01"},
    )
    assert response.status_code == 422


def test_cashier_closing_is_tenant_scoped(
    authenticated_client,
    db_session,
):
    tenant, _, _ = create_records(db_session)
    headers = authenticated_client.auth_headers(tenant)

    other_tenant = Tenant(
        product_id=tenant.product_id,
        client_number=771,
        name="Otro Tenant de Cierre",
        slug="otro-tenant-de-cierre",
        status="active",
    )
    db_session.add(other_tenant)
    db_session.flush()

    hidden = CashClosing(
        tenant_id=other_tenant.id,
        cashier_user_id=authenticated_client.auth_user.id,
        opened_at=datetime.now(timezone.utc),
        closed_at=datetime.now(timezone.utc),
        payment_count=0,
        total_collected=Decimal("0.00"),
        cash_expected=Decimal("0.00"),
        cash_counted=Decimal("0.00"),
        cash_difference=Decimal("0.00"),
        bank_transfer_total=Decimal("0.00"),
        card_total=Decimal("0.00"),
        other_total=Decimal("0.00"),
    )
    db_session.add(hidden)
    db_session.commit()

    listed = authenticated_client.get(
        f"{BASE_URL}/closings",
        headers=headers,
    )
    assert listed.status_code == 200
    assert listed.json() == []
