from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select

from app.models import Product, Tenant
from app.products.prestamodesk.models import (
    Borrower,
    Installment,
    Loan,
    LoanApplication,
)


APPLICATIONS_URL = (
    "/api/v1/products/prestamodesk/applications"
)


def get_product(db_session):
    product = db_session.scalar(
        select(Product).where(
            Product.slug == "prestamodesk"
        )
    )
    assert product is not None
    return product


def create_tenant(
    db_session,
    product,
    name,
    slug,
):
    tenant = Tenant(
        product_id=product.id,
        name=name,
        slug=slug,
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


def create_application(
    db_session,
    tenant,
    *,
    status="new",
    name="Solicitante Sintético",
):
    application = LoanApplication(
        tenant_id=tenant.id,
        full_name=name,
        document_type="cedula",
        document_number="001-0000000-1",
        phone="809-555-0102",
        email="solicitante@example.test",
        address="Dirección sintética",
        municipality="Santo Domingo Este",
        province="Santo Domingo",
        loan_type="vehicle",
        vehicle_cash_price=Decimal("1000000.00"),
        vehicle_down_payment=Decimal("200000.00"),
        vehicle_make="Toyota",
        vehicle_model="Corolla",
        vehicle_year=2022,
        vehicle_color="Blanco",
        vehicle_vin="SYNTHETIC-APPLICATION-001",
        vehicle_license_plate="TEST002",
        vehicle_seller="Dealer Sintético",
        vehicle_notes="Vehículo sintético",
        principal_amount=Decimal("800000.00"),
        flat_interest_rate_percent=Decimal("10.0000"),
        total_interest=Decimal("80000.00"),
        total_due=Decimal("880000.00"),
        installment_count=12,
        payment_frequency="monthly",
        start_date=date(2026, 9, 30),
        first_payment_date=date(2026, 10, 29),
        currency="DOP",
        status=status,
        notes="Solicitud sintética",
        consented_at=datetime.now(timezone.utc),
        consent_notice_version="2026-09-30",
    )
    db_session.add(application)
    db_session.commit()
    db_session.refresh(application)
    return application


def test_tenant_can_list_and_view_own_applications(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant = create_tenant(
        db_session,
        product,
        "Application List Tenant",
        "application-list-tenant",
    )
    application = create_application(
        db_session,
        tenant,
    )
    headers = client.auth_headers(tenant)

    list_response = client.get(
        APPLICATIONS_URL,
        headers=headers,
    )
    assert list_response.status_code == 200
    assert [
        item["id"]
        for item in list_response.json()
    ] == [application.id]

    get_response = client.get(
        f"{APPLICATIONS_URL}/{application.id}",
        headers=headers,
    )
    assert get_response.status_code == 200
    assert get_response.json()["full_name"] == (
        "Solicitante Sintético"
    )


def test_applications_are_isolated_by_tenant(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant_a = create_tenant(
        db_session,
        product,
        "Application Tenant A",
        "application-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        product,
        "Application Tenant B",
        "application-tenant-b",
    )
    application = create_application(
        db_session,
        tenant_a,
    )

    response = client.get(
        f"{APPLICATIONS_URL}/{application.id}",
        headers=client.auth_headers(tenant_b),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Application not found"
    )


def test_application_follows_review_and_approval_flow(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant = create_tenant(
        db_session,
        product,
        "Application Workflow Tenant",
        "application-workflow-tenant",
    )
    application = create_application(
        db_session,
        tenant,
    )
    headers = client.auth_headers(tenant)
    url = f"{APPLICATIONS_URL}/{application.id}"

    reviewing = client.put(
        url,
        headers=headers,
        json={"status": "reviewing"},
    )
    assert reviewing.status_code == 200
    assert reviewing.json()["status"] == "reviewing"
    assert reviewing.json()["reviewed_at"] is not None

    approved = client.put(
        url,
        headers=headers,
        json={"status": "approved"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["approved_at"] is not None


def test_application_cannot_skip_review(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant = create_tenant(
        db_session,
        product,
        "Application Transition Tenant",
        "application-transition-tenant",
    )
    application = create_application(
        db_session,
        tenant,
    )

    response = client.put(
        f"{APPLICATIONS_URL}/{application.id}",
        headers=client.auth_headers(tenant),
        json={"status": "approved"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Application cannot move from new to approved"
    )

    db_session.refresh(application)
    assert application.status == "new"


def test_unapproved_application_cannot_be_converted(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant = create_tenant(
        db_session,
        product,
        "Unapproved Application Tenant",
        "unapproved-application-tenant",
    )
    application = create_application(
        db_session,
        tenant,
        status="reviewing",
    )

    response = client.post(
        (
            f"{APPLICATIONS_URL}/{application.id}"
            "/convert"
        ),
        headers=client.auth_headers(tenant),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Application must be approved before conversion"
    )
    assert db_session.scalar(
        select(Borrower.id).where(
            Borrower.tenant_id == tenant.id
        )
    ) is None
    assert db_session.scalar(
        select(Loan.id).where(
            Loan.tenant_id == tenant.id
        )
    ) is None


def test_approved_application_converts_atomically(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant = create_tenant(
        db_session,
        product,
        "Application Conversion Tenant",
        "application-conversion-tenant",
    )
    application = create_application(
        db_session,
        tenant,
        status="approved",
        name="Pedro Sánchez",
    )

    response = client.post(
        (
            f"{APPLICATIONS_URL}/{application.id}"
            "/convert"
        ),
        headers=client.auth_headers(tenant),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["application_id"] == application.id
    assert body["status"] == "converted"

    borrower = db_session.get(
        Borrower,
        body["borrower_id"],
    )
    loan = db_session.get(
        Loan,
        body["loan_id"],
    )

    assert borrower is not None
    assert borrower.tenant_id == tenant.id
    assert borrower.full_name == "Pedro Sánchez"
    assert borrower.document_number == "001-0000000-1"

    assert loan is not None
    assert loan.tenant_id == tenant.id
    assert loan.borrower_id == borrower.id
    assert loan.loan_type == "vehicle"
    assert loan.vehicle_make == "Toyota"
    assert loan.vehicle_model == "Corolla"
    assert loan.principal_amount == Decimal("800000.00")
    assert loan.total_interest == Decimal("80000.00")
    assert loan.total_due == Decimal("880000.00")
    assert loan.status == "active"

    installment_count = db_session.scalar(
        select(func.count(Installment.id)).where(
            Installment.loan_id == loan.id
        )
    )
    assert installment_count == 12

    installment_total = db_session.scalar(
        select(func.sum(Installment.total_due)).where(
            Installment.loan_id == loan.id
        )
    )
    assert installment_total == Decimal("880000.00")

    db_session.refresh(application)
    assert application.status == "converted"
    assert application.converted_borrower_id == borrower.id
    assert application.converted_loan_id == loan.id
    assert application.converted_at is not None


def test_application_conversion_cannot_repeat(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant = create_tenant(
        db_session,
        product,
        "Repeat Application Conversion Tenant",
        "repeat-application-conversion-tenant",
    )
    application = create_application(
        db_session,
        tenant,
        status="approved",
    )
    headers = client.auth_headers(tenant)
    url = (
        f"{APPLICATIONS_URL}/{application.id}/convert"
    )

    first = client.post(
        url,
        headers=headers,
    )
    assert first.status_code == 201

    second = client.post(
        url,
        headers=headers,
    )
    assert second.status_code == 409
    assert second.json()["detail"] == (
        "Application has already been converted"
    )

    assert db_session.scalar(
        select(func.count(Borrower.id)).where(
            Borrower.tenant_id == tenant.id
        )
    ) == 1
    assert db_session.scalar(
        select(func.count(Loan.id)).where(
            Loan.tenant_id == tenant.id
        )
    ) == 1


def test_application_conversion_cannot_cross_tenant(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant_a = create_tenant(
        db_session,
        product,
        "Conversion Application Tenant A",
        "conversion-application-a",
    )
    tenant_b = create_tenant(
        db_session,
        product,
        "Conversion Application Tenant B",
        "conversion-application-b",
    )
    application = create_application(
        db_session,
        tenant_a,
        status="approved",
    )

    response = client.post(
        (
            f"{APPLICATIONS_URL}/{application.id}"
            "/convert"
        ),
        headers=client.auth_headers(tenant_b),
    )

    assert response.status_code == 404
    assert db_session.scalar(
        select(Borrower.id).where(
            Borrower.tenant_id == tenant_b.id
        )
    ) is None
    assert db_session.scalar(
        select(Loan.id).where(
            Loan.tenant_id == tenant_b.id
        )
    ) is None
