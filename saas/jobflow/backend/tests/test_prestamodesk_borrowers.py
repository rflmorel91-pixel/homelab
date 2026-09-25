from sqlalchemy import select

from app.models import Product, Tenant
from app.products.prestamodesk.models import Borrower


BORROWERS_URL = "/api/v1/products/prestamodesk/borrowers"


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


def test_prestamodesk_tenant_can_crud_borrowers(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session, "prestamodesk")
    tenant = create_tenant(
        db_session,
        product,
        "PréstamoDesk CRUD Tenant",
        "prestamodesk-crud-tenant",
    )
    headers = client.auth_headers(tenant)

    create_response = client.post(
        BORROWERS_URL,
        headers=headers,
        json={
            "full_name": "María Rodríguez",
            "document_type": "cedula",
            "document_number": "001-1234567-8",
            "phone": "809-555-0101",
            "municipality": "Santo Domingo Este",
            "province": "Santo Domingo",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["full_name"] == "María Rodríguez"
    assert created["document_type"] == "cedula"
    borrower_id = created["id"]

    stored = db_session.get(Borrower, borrower_id)
    assert stored is not None
    assert stored.tenant_id == tenant.id

    list_response = client.get(
        BORROWERS_URL,
        headers=headers,
    )
    assert list_response.status_code == 200
    assert [
        borrower["id"]
        for borrower in list_response.json()
    ] == [borrower_id]

    get_response = client.get(
        f"{BORROWERS_URL}/{borrower_id}",
        headers=headers,
    )
    assert get_response.status_code == 200

    update_response = client.put(
        f"{BORROWERS_URL}/{borrower_id}",
        headers=headers,
        json={
            "full_name": "María Rodríguez Peña",
            "document_type": "cedula",
            "document_number": "001-1234567-8",
            "phone": "809-555-0102",
            "municipality": "Santo Domingo Este",
            "province": "Santo Domingo",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["full_name"] == (
        "María Rodríguez Peña"
    )


def test_prestamodesk_borrowers_are_isolated_by_tenant(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session, "prestamodesk")

    tenant_a = create_tenant(
        db_session,
        product,
        "PréstamoDesk Tenant A",
        "prestamodesk-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        product,
        "PréstamoDesk Tenant B",
        "prestamodesk-tenant-b",
    )

    create_response = client.post(
        BORROWERS_URL,
        headers=client.auth_headers(tenant_a),
        json={"full_name": "Cliente del Tenant A"},
    )
    assert create_response.status_code == 201
    borrower_id = create_response.json()["id"]

    get_response = client.get(
        f"{BORROWERS_URL}/{borrower_id}",
        headers=client.auth_headers(tenant_b),
    )
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Borrower not found"

    list_response = client.get(
        BORROWERS_URL,
        headers=client.auth_headers(tenant_b),
    )
    assert list_response.status_code == 200
    assert list_response.json() == []


def test_other_product_tenant_cannot_use_prestamodesk(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    jobflow = get_product(db_session, "jobflow")
    tenant = create_tenant(
        db_session,
        jobflow,
        "Wrong Product Tenant",
        "prestamodesk-wrong-product",
    )

    response = client.get(
        BORROWERS_URL,
        headers=client.auth_headers(tenant),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Tenant does not belong to this product"
    )


def test_client_cannot_supply_borrower_tenant_id(
    authenticated_client,
    db_session,
):
    client = authenticated_client
    product = get_product(db_session, "prestamodesk")
    tenant_a = create_tenant(
        db_session,
        product,
        "Trusted PréstamoDesk Tenant",
        "trusted-prestamodesk-tenant",
    )
    tenant_b = create_tenant(
        db_session,
        product,
        "Target PréstamoDesk Tenant",
        "target-prestamodesk-tenant",
    )

    response = client.post(
        BORROWERS_URL,
        headers=client.auth_headers(tenant_a),
        json={
            "full_name": "Attempted Override",
            "tenant_id": tenant_b.id,
        },
    )

    assert response.status_code == 422
    assert db_session.scalars(select(Borrower)).all() == []
