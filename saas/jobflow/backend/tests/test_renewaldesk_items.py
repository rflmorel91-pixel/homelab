from sqlalchemy import select

from app.models import Product, Tenant
from app.products.renewaldesk.models import RenewalItem


ITEMS_URL = "/api/v1/products/renewaldesk/items"


def get_product(
    db_session,
    slug,
):
    product = db_session.scalar(
        select(Product).where(
            Product.slug == slug
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


def test_renewaldesk_tenant_can_crud_items(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    renewaldesk = get_product(
        db_session,
        "renewaldesk",
    )

    tenant = create_tenant(
        db_session,
        renewaldesk,
        "RenewalDesk CRUD Tenant",
        "renewaldesk-crud-tenant",
    )

    headers = client.auth_headers(tenant)

    create_response = client.post(
        ITEMS_URL,
        headers=headers,
        json={
            "name": "Contractor License",
            "renewal_date": "2027-03-15",
        },
    )

    assert create_response.status_code == 201

    created = create_response.json()

    assert created["name"] == (
        "Contractor License"
    )
    assert created["renewal_date"] == (
        "2027-03-15"
    )

    item_id = created["id"]

    stored = db_session.get(
        RenewalItem,
        item_id,
    )

    assert stored is not None
    assert stored.tenant_id == tenant.id

    list_response = client.get(
        ITEMS_URL,
        headers=headers,
    )

    assert list_response.status_code == 200
    assert [
        item["id"]
        for item in list_response.json()
    ] == [item_id]

    get_response = client.get(
        f"{ITEMS_URL}/{item_id}",
        headers=headers,
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == item_id

    update_response = client.put(
        f"{ITEMS_URL}/{item_id}",
        headers=headers,
        json={
            "name": "Updated Contractor License",
            "renewal_date": "2027-04-20",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == (
        "Updated Contractor License"
    )

    delete_response = client.delete(
        f"{ITEMS_URL}/{item_id}",
        headers=headers,
    )

    assert delete_response.status_code == 204

    missing = client.get(
        f"{ITEMS_URL}/{item_id}",
        headers=headers,
    )

    assert missing.status_code == 404


def test_renewaldesk_items_are_isolated_by_tenant(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    renewaldesk = get_product(
        db_session,
        "renewaldesk",
    )

    tenant_a = create_tenant(
        db_session,
        renewaldesk,
        "RenewalDesk Tenant A",
        "renewaldesk-tenant-a",
    )

    tenant_b = create_tenant(
        db_session,
        renewaldesk,
        "RenewalDesk Tenant B",
        "renewaldesk-tenant-b",
    )

    create_response = client.post(
        ITEMS_URL,
        headers=client.auth_headers(
            tenant_a
        ),
        json={
            "name": "Tenant A License",
            "renewal_date": "2027-01-01",
        },
    )

    assert create_response.status_code == 201

    item_id = create_response.json()["id"]

    response = client.get(
        f"{ITEMS_URL}/{item_id}",
        headers=client.auth_headers(
            tenant_b
        ),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Renewal item not found"
    )

    list_response = client.get(
        ITEMS_URL,
        headers=client.auth_headers(
            tenant_b
        ),
    )

    assert list_response.status_code == 200
    assert list_response.json() == []


def test_jobflow_tenant_cannot_use_renewaldesk_items(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    jobflow = get_product(
        db_session,
        "jobflow",
    )

    tenant = create_tenant(
        db_session,
        jobflow,
        "JobFlow Wrong Product Tenant",
        "jobflow-wrong-product-tenant",
    )

    response = client.get(
        ITEMS_URL,
        headers=client.auth_headers(tenant),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Tenant does not belong to this product"
    )


def test_suspended_renewaldesk_tenant_is_blocked(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    renewaldesk = get_product(
        db_session,
        "renewaldesk",
    )

    tenant = create_tenant(
        db_session,
        renewaldesk,
        "Suspended RenewalDesk Tenant",
        "suspended-renewaldesk-tenant",
    )

    tenant.status = "suspended"
    db_session.commit()

    response = client.get(
        ITEMS_URL,
        headers=client.auth_headers(tenant),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Tenant is suspended"
    )


def test_suspended_renewaldesk_product_is_blocked(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    renewaldesk = get_product(
        db_session,
        "renewaldesk",
    )

    tenant = create_tenant(
        db_session,
        renewaldesk,
        "Product Suspension Tenant",
        "product-suspension-tenant",
    )

    renewaldesk.status = "suspended"
    db_session.commit()

    response = client.get(
        ITEMS_URL,
        headers=client.auth_headers(tenant),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Product is suspended"
    )


def test_client_cannot_supply_tenant_id(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    renewaldesk = get_product(
        db_session,
        "renewaldesk",
    )

    tenant_a = create_tenant(
        db_session,
        renewaldesk,
        "Trusted Tenant",
        "trusted-renewaldesk-tenant",
    )

    tenant_b = create_tenant(
        db_session,
        renewaldesk,
        "Target Tenant",
        "target-renewaldesk-tenant",
    )

    response = client.post(
        ITEMS_URL,
        headers=client.auth_headers(
            tenant_a
        ),
        json={
            "name": "Attempted Tenant Override",
            "renewal_date": "2027-06-01",
            "tenant_id": tenant_b.id,
        },
    )

    assert response.status_code == 422

    stored = db_session.scalars(
        select(RenewalItem)
    ).all()

    assert stored == []
