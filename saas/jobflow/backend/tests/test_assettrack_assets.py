from sqlalchemy import select

from app.models import Product, Tenant
from app.products.assettrack.models import Asset


ASSETS_URL = "/api/v1/products/assettrack/assets"


def get_product(db_session, slug):
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


def test_assettrack_tenant_can_crud_assets(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    assettrack = get_product(
        db_session,
        "assettrack",
    )

    tenant = create_tenant(
        db_session,
        assettrack,
        "AssetTrack CRUD Tenant",
        "assettrack-crud-tenant",
    )

    headers = client.auth_headers(tenant)

    create_response = client.post(
        ASSETS_URL,
        headers=headers,
        json={
            "external_id": "customer-asset-001",
            "name": "HVAC Unit",
            "asset_type": "hvac",
            "manufacturer": "Carrier",
            "model": "WeatherMaker",
            "serial_number": "SN-10001",
            "status": "active",
            "attributes": {
                "location": "Roof",
            },
        },
    )

    assert create_response.status_code == 201

    created = create_response.json()
    assert created["name"] == "HVAC Unit"
    assert created["external_id"] == "customer-asset-001"
    assert created["asset_type"] == "hvac"
    assert created["manufacturer"] == "Carrier"
    assert created["model"] == "WeatherMaker"
    assert created["serial_number"] == "SN-10001"
    assert created["status"] == "active"
    assert created["attributes"] == {
        "location": "Roof",
    }
    assert created["updated_at"] is not None

    asset_id = created["id"]

    stored = db_session.get(
        Asset,
        asset_id,
    )

    assert stored is not None
    assert stored.tenant_id == tenant.id

    list_response = client.get(
        ASSETS_URL,
        headers=headers,
    )

    assert list_response.status_code == 200
    assert [
        item["id"]
        for item in list_response.json()
    ] == [asset_id]

    get_response = client.get(
        f"{ASSETS_URL}/{asset_id}",
        headers=headers,
    )

    assert get_response.status_code == 200

    update_response = client.put(
        f"{ASSETS_URL}/{asset_id}",
        headers=headers,
        json={
            "external_id": "customer-asset-001",
            "name": "Updated HVAC Unit",
            "asset_type": "hvac",
            "manufacturer": "Carrier",
            "model": "WeatherMaker 2",
            "serial_number": "SN-10001",
            "status": "inactive",
            "attributes": {
                "location": "Warehouse",
            },
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == (
        "Updated HVAC Unit"
    )

    delete_response = client.delete(
        f"{ASSETS_URL}/{asset_id}",
        headers=headers,
    )

    assert delete_response.status_code == 204

    missing = client.get(
        f"{ASSETS_URL}/{asset_id}",
        headers=headers,
    )

    assert missing.status_code == 404


def test_assettrack_assets_are_tenant_isolated(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    assettrack = get_product(
        db_session,
        "assettrack",
    )

    tenant_a = create_tenant(
        db_session,
        assettrack,
        "AssetTrack Tenant A",
        "assettrack-tenant-a",
    )

    tenant_b = create_tenant(
        db_session,
        assettrack,
        "AssetTrack Tenant B",
        "assettrack-tenant-b",
    )

    created = client.post(
        ASSETS_URL,
        headers=client.auth_headers(
            tenant_a
        ),
        json={
            "name": "Tenant A Asset",
        },
    )

    assert created.status_code == 201
    asset_id = created.json()["id"]

    cross_tenant = client.get(
        f"{ASSETS_URL}/{asset_id}",
        headers=client.auth_headers(
            tenant_b
        ),
    )

    assert cross_tenant.status_code == 404

    list_b = client.get(
        ASSETS_URL,
        headers=client.auth_headers(
            tenant_b
        ),
    )

    assert list_b.status_code == 200
    assert list_b.json() == []


def test_jobflow_tenant_cannot_use_assettrack(
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
        "Wrong Product Tenant",
        "assettrack-wrong-product",
    )

    response = client.get(
        ASSETS_URL,
        headers=client.auth_headers(tenant),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Tenant does not belong to this product"
    )


def test_assettrack_rejects_client_tenant_id(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    assettrack = get_product(
        db_session,
        "assettrack",
    )

    tenant = create_tenant(
        db_session,
        assettrack,
        "Trusted Asset Tenant",
        "trusted-asset-tenant",
    )

    response = client.post(
        ASSETS_URL,
        headers=client.auth_headers(tenant),
        json={
            "name": "Injected Asset",
            "tenant_id": 999999,
        },
    )

    assert response.status_code == 422

    rows = db_session.scalars(
        select(Asset)
    ).all()

    assert rows == []
