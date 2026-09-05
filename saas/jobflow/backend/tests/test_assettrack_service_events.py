from sqlalchemy import select

from app.models import Product, Tenant
from app.products.assettrack.models import (
    Asset,
    AssetServiceEvent,
)


def create_tenant(
    db_session,
    name,
    slug,
):
    product = db_session.scalar(
        select(Product).where(
            Product.slug == "assettrack"
        )
    )

    assert product is not None

    tenant = Tenant(
        product_id=product.id,
        name=name,
        slug=slug,
    )

    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    return tenant


def create_asset(
    db_session,
    tenant,
    name,
):
    asset = Asset(
        tenant_id=tenant.id,
        name=name,
    )

    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)

    return asset


def events_url(asset_id):
    return (
        "/api/v1/products/assettrack/"
        f"assets/{asset_id}/service-events"
    )


def test_assettrack_tenant_can_append_service_history(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        "Service History Tenant",
        "service-history-tenant",
    )
    asset = create_asset(
        db_session,
        tenant,
        "Managed server",
    )
    headers = authenticated_client.auth_headers(
        tenant
    )

    created = authenticated_client.post(
        events_url(asset.id),
        headers=headers,
        json={
            "event_type": "maintenance",
            "occurred_at": "2026-09-05T15:30:00Z",
            "summary": "Installed security updates",
            "details": {
                "ticket": "MSP-1042",
            },
        },
    )

    assert created.status_code == 201

    payload = created.json()
    assert payload["asset_id"] == asset.id
    assert payload["event_type"] == "maintenance"
    assert payload["details"] == {
        "ticket": "MSP-1042",
    }

    stored = db_session.get(
        AssetServiceEvent,
        payload["id"],
    )

    assert stored is not None
    assert stored.tenant_id == tenant.id

    listed = authenticated_client.get(
        events_url(asset.id),
        headers=headers,
    )

    assert listed.status_code == 200
    assert [
        event["id"]
        for event in listed.json()
    ] == [payload["id"]]

    fetched = authenticated_client.get(
        f"{events_url(asset.id)}/{payload['id']}",
        headers=headers,
    )

    assert fetched.status_code == 200


def test_service_history_is_tenant_isolated(
    authenticated_client,
    db_session,
):
    tenant_a = create_tenant(
        db_session,
        "Service Tenant A",
        "service-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Service Tenant B",
        "service-tenant-b",
    )
    asset = create_asset(
        db_session,
        tenant_a,
        "Tenant A router",
    )

    response = authenticated_client.get(
        events_url(asset.id),
        headers=authenticated_client.auth_headers(
            tenant_b
        ),
    )

    assert response.status_code == 404


def test_service_event_rejects_client_tenant_id(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        "Trusted Service Tenant",
        "trusted-service-tenant",
    )
    asset = create_asset(
        db_session,
        tenant,
        "Trusted asset",
    )

    response = authenticated_client.post(
        events_url(asset.id),
        headers=authenticated_client.auth_headers(
            tenant
        ),
        json={
            "event_type": "inspection",
            "occurred_at": "2026-09-05T15:30:00Z",
            "summary": "Inspected asset",
            "tenant_id": 999999,
        },
    )

    assert response.status_code == 422
