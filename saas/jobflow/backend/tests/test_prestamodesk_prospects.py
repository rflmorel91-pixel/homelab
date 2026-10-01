from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from app.models import Product, Tenant
from app.products.prestamodesk.models import (
    Borrower,
    Prospect,
)


PROSPECTS_URL = (
    "/api/v1/products/prestamodesk/prospects"
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


def create_prospect(
    db_session,
    tenant,
    *,
    name="Prospecto Sintético",
    status="new",
):
    prospect = Prospect(
        tenant_id=tenant.id,
        full_name=name,
        phone="809-555-0120",
        email="prospect@example.com",
        municipality="Santo Domingo Este",
        province="Santo Domingo",
        requested_amount=Decimal("30000.00"),
        preferred_contact="whatsapp",
        message="Solicitud sintética.",
        status=status,
        consented_at=datetime.now(timezone.utc),
        consent_notice_version="2026-09-29",
    )
    db_session.add(prospect)
    db_session.commit()
    db_session.refresh(prospect)
    return prospect


def test_tenant_can_list_and_view_own_prospects(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant = create_tenant(
        db_session,
        product,
        "Prospect List Tenant",
        "prospect-list-tenant",
    )
    prospect = create_prospect(
        db_session,
        tenant,
    )
    headers = client.owner_headers(tenant)

    list_response = client.get(
        PROSPECTS_URL,
        headers=headers,
    )
    assert list_response.status_code == 200
    assert [
        item["id"]
        for item in list_response.json()
    ] == [prospect.id]

    get_response = client.get(
        f"{PROSPECTS_URL}/{prospect.id}",
        headers=headers,
    )
    assert get_response.status_code == 200
    assert get_response.json()["full_name"] == (
        "Prospecto Sintético"
    )


def test_prospects_are_isolated_by_tenant(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant_a = create_tenant(
        db_session,
        product,
        "Prospect Tenant A",
        "managed-prospect-a",
    )
    tenant_b = create_tenant(
        db_session,
        product,
        "Prospect Tenant B",
        "managed-prospect-b",
    )
    prospect = create_prospect(
        db_session,
        tenant_a,
    )

    response = client.get(
        f"{PROSPECTS_URL}/{prospect.id}",
        headers=client.owner_headers(tenant_b),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Prospect not found"
    )


def test_tenant_can_update_prospect_status(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant = create_tenant(
        db_session,
        product,
        "Prospect Update Tenant",
        "prospect-update-tenant",
    )
    prospect = create_prospect(
        db_session,
        tenant,
    )

    response = client.put(
        f"{PROSPECTS_URL}/{prospect.id}",
        headers=client.owner_headers(tenant),
        json={"status": "qualified"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "qualified"

    db_session.refresh(prospect)
    assert prospect.status == "qualified"


def test_unqualified_prospect_cannot_be_converted(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant = create_tenant(
        db_session,
        product,
        "Unqualified Prospect Tenant",
        "unqualified-prospect-tenant",
    )
    prospect = create_prospect(
        db_session,
        tenant,
    )

    response = client.post(
        (
            f"{PROSPECTS_URL}/{prospect.id}"
            "/convert"
        ),
        headers=client.owner_headers(tenant),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Prospect must be qualified before conversion"
    )
    assert db_session.scalar(
        select(Borrower.id).where(
            Borrower.tenant_id == tenant.id
        )
    ) is None


def test_qualified_prospect_converts_to_borrower(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant = create_tenant(
        db_session,
        product,
        "Conversion Prospect Tenant",
        "conversion-prospect-tenant",
    )
    prospect = create_prospect(
        db_session,
        tenant,
        name="María Prospecto",
        status="qualified",
    )

    response = client.post(
        (
            f"{PROSPECTS_URL}/{prospect.id}"
            "/convert"
        ),
        headers=client.owner_headers(tenant),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["prospect_id"] == prospect.id
    assert body["status"] == "converted"

    borrower = db_session.get(
        Borrower,
        body["borrower_id"],
    )
    assert borrower is not None
    assert borrower.tenant_id == tenant.id
    assert borrower.full_name == "María Prospecto"
    assert borrower.phone == prospect.phone

    db_session.refresh(prospect)
    assert prospect.status == "converted"
    assert prospect.converted_borrower_id == borrower.id


def test_prospect_conversion_cannot_repeat(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant = create_tenant(
        db_session,
        product,
        "Repeat Conversion Tenant",
        "repeat-conversion-tenant",
    )
    prospect = create_prospect(
        db_session,
        tenant,
        status="qualified",
    )
    headers = client.owner_headers(tenant)
    url = (
        f"{PROSPECTS_URL}/{prospect.id}/convert"
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
        "Prospect has already been converted"
    )

    borrowers = db_session.scalars(
        select(Borrower).where(
            Borrower.tenant_id == tenant.id
        )
    ).all()
    assert len(borrowers) == 1


def test_conversion_cannot_cross_tenant_boundary(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant_a = create_tenant(
        db_session,
        product,
        "Conversion Tenant A",
        "conversion-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        product,
        "Conversion Tenant B",
        "conversion-tenant-b",
    )
    prospect = create_prospect(
        db_session,
        tenant_a,
        status="qualified",
    )

    response = client.post(
        (
            f"{PROSPECTS_URL}/{prospect.id}"
            "/convert"
        ),
        headers=client.owner_headers(tenant_b),
    )

    assert response.status_code == 404
    assert db_session.scalar(
        select(Borrower.id).where(
            Borrower.tenant_id == tenant_b.id
        )
    ) is None


def test_tenant_can_get_public_prospect_page(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session)
    tenant = Tenant(
        product_id=product.id,
        client_number=37,
        name="Página Pública PréstamoDesk",
        slug="pagina-publica-prestamodesk",
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    response = client.get(
        f"{PROSPECTS_URL}/public-page",
        headers=client.owner_headers(tenant),
    )

    assert response.status_code == 200
    assert response.json() == {
        "tenant_slug": "pagina-publica-prestamodesk",
        "business_name": "Página Pública PréstamoDesk",
        "client_number": 37,
    }
