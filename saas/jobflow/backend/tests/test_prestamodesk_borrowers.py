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
    headers = client.owner_headers(tenant)

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
        headers=client.owner_headers(tenant_a),
        json={"full_name": "Cliente del Tenant A"},
    )
    assert create_response.status_code == 201
    borrower_id = create_response.json()["id"]

    get_response = client.get(
        f"{BORROWERS_URL}/{borrower_id}",
        headers=client.owner_headers(tenant_b),
    )
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Borrower not found"

    list_response = client.get(
        BORROWERS_URL,
        headers=client.owner_headers(tenant_b),
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
        headers=client.owner_headers(tenant),
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
        headers=client.owner_headers(tenant_a),
        json={
            "full_name": "Attempted Override",
            "tenant_id": tenant_b.id,
        },
    )

    assert response.status_code == 422
    assert db_session.scalars(select(Borrower)).all() == []


def conflict_test_tenant(client, db, slug):
    tenant = create_tenant(
        db, get_product(db, "prestamodesk"), slug, slug
    )
    return tenant, client.owner_headers(tenant)


def test_duplicate_document_create_returns_conflict(
    authenticated_client, db_session
):
    client = authenticated_client
    _, headers = conflict_test_tenant(client, db_session, "duplicate-create")
    payload = {
        "full_name": "Cliente Original",
        "document_number": "TEST-DUPLICATE-001",
    }
    first = client.post(BORROWERS_URL, headers=headers, json=payload)
    assert first.status_code == 201

    duplicate = client.post(BORROWERS_URL, headers=headers, json=payload)
    assert duplicate.status_code == 409
    assert "número de documento" in duplicate.json()["detail"]

    listed = client.get(BORROWERS_URL, headers=headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [first.json()["id"]]

    payload["document_number"] = "TEST-DUPLICATE-002"
    assert client.post(
        BORROWERS_URL, headers=headers, json=payload
    ).status_code == 201


def test_duplicate_document_update_preserves_original(
    authenticated_client, db_session
):
    client = authenticated_client
    _, headers = conflict_test_tenant(client, db_session, "duplicate-update")
    records = []
    for name, document in [
        ("Cliente Primero", "TEST-UPDATE-001"),
        ("Cliente Segundo", "TEST-UPDATE-002"),
    ]:
        response = client.post(
            BORROWERS_URL, headers=headers,
            json={"full_name": name, "document_number": document},
        )
        assert response.status_code == 201
        records.append(response.json())

    url = f"{BORROWERS_URL}/{records[1]['id']}"
    response = client.put(
        url, headers=headers,
        json={
            "full_name": "Cambio No Guardado",
            "document_number": "TEST-UPDATE-001",
        },
    )
    assert response.status_code == 409
    stored = client.get(url, headers=headers)
    assert stored.status_code == 200
    assert stored.json()["document_number"] == "TEST-UPDATE-002"
    assert stored.json()["full_name"] == "Cliente Segundo"


def test_same_document_allowed_in_different_tenants(
    authenticated_client, db_session
):
    client = authenticated_client
    for slug in ["document-tenant-one", "document-tenant-two"]:
        _, headers = conflict_test_tenant(client, db_session, slug)
        response = client.post(
            BORROWERS_URL, headers=headers,
            json={
                "full_name": "Cliente de Prueba",
                "document_number": "TEST-SHARED-001",
            },
        )
        assert response.status_code == 201


def test_borrower_with_loan_cannot_be_deleted(
    authenticated_client, db_session
):
    client = authenticated_client
    _, headers = conflict_test_tenant(client, db_session, "delete-loan-history")
    borrower = client.post(
        BORROWERS_URL, headers=headers,
        json={"full_name": "Cliente Con Historial"},
    )
    assert borrower.status_code == 201
    borrower_id = borrower.json()["id"]

    loan = client.post(
        "/api/v1/products/prestamodesk/loans",
        headers=headers,
        json={
            "borrower_id": borrower_id,
            "principal_amount": "1000.00",
            "flat_interest_rate_percent": "10",
            "installment_count": 2,
            "payment_frequency": "monthly",
            "start_date": "2026-10-01",
            "first_payment_date": "2026-11-01",
        },
    )
    assert loan.status_code == 201
    url = f"{BORROWERS_URL}/{borrower_id}"
    deleted = client.delete(url, headers=headers)
    assert deleted.status_code == 409
    assert "historial" in deleted.json()["detail"]
    assert client.get(url, headers=headers).status_code == 200
    assert client.get(
        f"/api/v1/products/prestamodesk/loans/{loan.json()['id']}",
        headers=headers,
    ).status_code == 200


def test_borrower_without_history_can_be_deleted(
    authenticated_client, db_session
):
    client = authenticated_client
    _, headers = conflict_test_tenant(client, db_session, "delete-empty-borrower")
    created = client.post(
        BORROWERS_URL, headers=headers,
        json={"full_name": "Cliente Sin Historial"},
    )
    assert created.status_code == 201
    url = f"{BORROWERS_URL}/{created.json()['id']}"
    assert client.delete(url, headers=headers).status_code == 204
    assert client.get(url, headers=headers).status_code == 404
