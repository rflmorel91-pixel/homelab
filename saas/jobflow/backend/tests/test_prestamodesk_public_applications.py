from decimal import Decimal

from sqlalchemy import select

from app.models import Product, Tenant
from app.products.prestamodesk.models import (
    Borrower,
    Loan,
    LoanApplication,
)


BASE_URL = (
    "/api/v1/products/prestamodesk"
    "/public/tenants"
)


def create_tenant(db_session, *, slug, client_number=61):
    product = db_session.scalar(
        select(Product).where(
            Product.slug == "prestamodesk"
        )
    )
    assert product is not None

    tenant = Tenant(
        product_id=product.id,
        client_number=client_number,
        name="Applications Tenant",
        slug=slug,
        status="active",
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


def terms():
    return {
        "vehicle_cash_price": "1000000.00",
        "vehicle_down_payment": "200000.00",
        "vehicle_make": "Toyota",
        "vehicle_model": "Corolla",
        "vehicle_year": 2022,
        "vehicle_color": "Blanco",
        "vehicle_vin": "SYNTHETIC-CHASSIS-002",
        "vehicle_license_plate": "TEST002",
        "vehicle_seller": "Dealer Sintético Staging",
        "principal_amount": "800000.00",
        "flat_interest_rate_percent": "10.0000",
        "installment_count": 12,
        "payment_frequency": "monthly",
        "start_date": "2026-09-30",
        "first_payment_date": "2026-10-29",
    }


def application_payload():
    return {
        **terms(),
        "full_name": "Pedro Sanchez",
        "document_type": "cedula",
        "document_number": "001-0000000-1",
        "phone": "809-555-0102",
        "email": "pedro.sanchez@example.com",
        "municipality": "Santo Domingo Este",
        "province": "Santo Domingo",
        "consent_to_contact": True,
    }


def test_quote_calculates_without_database_rows(
    raw_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        slug="quote-tenant",
    )

    response = raw_client.post(
        f"{BASE_URL}/{tenant.slug}/quote",
        json=terms(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["estimate_only"] is True
    assert body["currency"] == "DOP"
    assert Decimal(body["principal_amount"]) == Decimal(
        "800000.00"
    )
    assert Decimal(body["total_interest"]) == Decimal(
        "80000.00"
    )
    assert Decimal(body["total_due"]) == Decimal(
        "880000.00"
    )
    assert len(body["installments"]) == 12

    assert db_session.scalar(
        select(LoanApplication.id)
    ) is None
    assert db_session.scalar(select(Borrower.id)) is None
    assert db_session.scalar(select(Loan.id)) is None


def test_public_application_is_stored_as_new_only(
    raw_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        slug="application-tenant",
    )

    response = raw_client.post(
        f"{BASE_URL}/{tenant.slug}/applications",
        json=application_payload(),
    )

    assert response.status_code == 201
    assert response.json()["status"] == "received"

    application = db_session.get(
        LoanApplication,
        response.json()["application_id"],
    )
    assert application is not None
    assert application.tenant_id == tenant.id
    assert application.status == "new"
    assert application.full_name == "Pedro Sanchez"
    assert application.currency == "DOP"
    assert application.principal_amount == Decimal(
        "800000.00"
    )
    assert application.total_interest == Decimal(
        "80000.00"
    )
    assert application.total_due == Decimal("880000.00")
    assert application.converted_borrower_id is None
    assert application.converted_loan_id is None

    assert db_session.scalar(select(Borrower.id)) is None
    assert db_session.scalar(select(Loan.id)) is None


def test_public_application_resolves_exact_tenant(
    raw_client,
    db_session,
):
    tenant_a = create_tenant(
        db_session,
        slug="application-tenant-a",
        client_number=62,
    )
    tenant_b = create_tenant(
        db_session,
        slug="application-tenant-b",
        client_number=63,
    )

    response = raw_client.post(
        f"{BASE_URL}/{tenant_b.slug}/applications",
        json=application_payload(),
    )

    assert response.status_code == 201

    application = db_session.get(
        LoanApplication,
        response.json()["application_id"],
    )
    assert application is not None
    assert application.tenant_id == tenant_b.id
    assert application.tenant_id != tenant_a.id


def test_public_application_rejects_unknown_tenant(
    raw_client,
    db_session,
):
    response = raw_client.post(
        f"{BASE_URL}/missing-tenant/applications",
        json=application_payload(),
    )

    assert response.status_code == 404
    assert db_session.scalar(
        select(LoanApplication.id)
    ) is None


def test_public_application_requires_consent(
    raw_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        slug="application-consent-tenant",
    )
    payload = application_payload()
    payload["consent_to_contact"] = False

    response = raw_client.post(
        f"{BASE_URL}/{tenant.slug}/applications",
        json=payload,
    )

    assert response.status_code == 422
    assert db_session.scalar(
        select(LoanApplication.id)
    ) is None


def test_public_application_rejects_server_fields(
    raw_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        slug="application-protected-tenant",
    )
    payload = application_payload()
    payload.update(
        {
            "tenant_id": 999,
            "status": "converted",
            "converted_loan_id": 999,
            "total_due": "1.00",
        }
    )

    response = raw_client.post(
        f"{BASE_URL}/{tenant.slug}/applications",
        json=payload,
    )

    assert response.status_code == 422
    assert db_session.scalar(
        select(LoanApplication.id)
    ) is None
