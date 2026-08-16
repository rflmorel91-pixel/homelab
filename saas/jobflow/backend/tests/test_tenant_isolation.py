from app.models import Tenant


def create_tenant(db_session, name, slug):
    tenant = Tenant(
        name=name,
        slug=slug,
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


def test_customer_api_requires_tenant_context(
    raw_client,
):
    response = raw_client.get(
        "/api/v1/customers/",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Tenant context required"
    )


def test_customers_are_isolated_by_tenant(
    client,
    db_session,
):
    tenant_a = create_tenant(
        db_session,
        "Tenant A",
        "tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Tenant B",
        "tenant-b",
    )

    create_a = client.post(
        "/api/v1/customers/",
        headers={
            "X-Tenant-ID": str(tenant_a.id),
        },
        json={
            "name": "Tenant A Customer",
            "phone": "555-2001",
            "email": "a@example.com",
            "address": "1 Tenant A Street",
        },
    )

    assert create_a.status_code == 201
    customer_a = create_a.json()

    create_b = client.post(
        "/api/v1/customers/",
        headers={
            "X-Tenant-ID": str(tenant_b.id),
        },
        json={
            "name": "Tenant B Customer",
            "phone": "555-2002",
            "email": "b@example.com",
            "address": "2 Tenant B Street",
        },
    )

    assert create_b.status_code == 201
    customer_b = create_b.json()

    list_a = client.get(
        "/api/v1/customers/",
        headers={
            "X-Tenant-ID": str(tenant_a.id),
        },
    )

    assert list_a.status_code == 200
    assert [
        item["id"]
        for item in list_a.json()
    ] == [customer_a["id"]]

    list_b = client.get(
        "/api/v1/customers/",
        headers={
            "X-Tenant-ID": str(tenant_b.id),
        },
    )

    assert list_b.status_code == 200
    assert [
        item["id"]
        for item in list_b.json()
    ] == [customer_b["id"]]

    cross_tenant_get = client.get(
        f"/api/v1/customers/{customer_b['id']}",
        headers={
            "X-Tenant-ID": str(tenant_a.id),
        },
    )

    assert cross_tenant_get.status_code == 404
    assert cross_tenant_get.json()["detail"] == (
        "Customer not found"
    )


def test_cross_tenant_customer_update_is_hidden(
    client,
    db_session,
):
    tenant_a = create_tenant(
        db_session,
        "Update Tenant A",
        "update-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Update Tenant B",
        "update-tenant-b",
    )

    create_b = client.post(
        "/api/v1/customers/",
        headers={
            "X-Tenant-ID": str(tenant_b.id),
        },
        json={
            "name": "Protected Tenant B Customer",
            "phone": "555-2100",
            "email": "protected-b@example.com",
            "address": "2100 Tenant B Street",
        },
    )

    assert create_b.status_code == 201
    customer_b = create_b.json()

    update_response = client.put(
        f"/api/v1/customers/{customer_b['id']}",
        headers={
            "X-Tenant-ID": str(tenant_a.id),
        },
        json={
            "name": "Illegitimate Update",
            "phone": "555-9999",
            "email": "hijacked@example.com",
            "address": "Wrong Tenant",
        },
    )

    assert update_response.status_code == 404
    assert update_response.json()["detail"] == (
        "Customer not found"
    )

    original = client.get(
        f"/api/v1/customers/{customer_b['id']}",
        headers={
            "X-Tenant-ID": str(tenant_b.id),
        },
    )

    assert original.status_code == 200
    assert original.json()["name"] == (
        "Protected Tenant B Customer"
    )


def test_cross_tenant_customer_delete_is_hidden(
    client,
    db_session,
):
    tenant_a = create_tenant(
        db_session,
        "Delete Tenant A",
        "delete-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Delete Tenant B",
        "delete-tenant-b",
    )

    create_b = client.post(
        "/api/v1/customers/",
        headers={
            "X-Tenant-ID": str(tenant_b.id),
        },
        json={
            "name": "Undeletable Tenant B Customer",
            "phone": "555-2200",
            "email": "undeletable-b@example.com",
            "address": "2200 Tenant B Street",
        },
    )

    assert create_b.status_code == 201
    customer_b = create_b.json()

    delete_response = client.delete(
        f"/api/v1/customers/{customer_b['id']}",
        headers={
            "X-Tenant-ID": str(tenant_a.id),
        },
    )

    assert delete_response.status_code == 404
    assert delete_response.json()["detail"] == (
        "Customer not found"
    )

    original = client.get(
        f"/api/v1/customers/{customer_b['id']}",
        headers={
            "X-Tenant-ID": str(tenant_b.id),
        },
    )

    assert original.status_code == 200
