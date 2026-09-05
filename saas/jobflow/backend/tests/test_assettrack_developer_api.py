from sqlalchemy import select

from app.models import Product, Tenant, TenantMembership
from app.products.assettrack.api_key_security import hash_api_key
from app.products.assettrack.models import (
    Asset,
    AssetServiceEvent,
    AssetTrackApiKey,
)


KEYS_URL = (
    "/api/v1/products/assettrack/"
    "developer-api-keys"
)
DEVELOPER_URL = (
    "/api/v1/products/assettrack/"
    "developer/v1"
)


def create_assettrack_tenant(
    db_session,
):
    product = db_session.scalar(
        select(Product).where(
            Product.slug == "assettrack"
        )
    )

    assert product is not None

    tenant = Tenant(
        product_id=product.id,
        name="AssetTrack Developer Tenant",
        slug="assettrack-developer-tenant",
    )

    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    return tenant


def owner_headers(
    authenticated_client,
    db_session,
    tenant,
):
    headers = authenticated_client.auth_headers(
        tenant
    )

    membership = db_session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant.id,
            TenantMembership.user_id
            == authenticated_client.auth_user.id,
        )
    )

    assert membership is not None

    membership.role = "owner"
    db_session.commit()

    return headers


def create_key(
    authenticated_client,
    db_session,
):
    tenant = create_assettrack_tenant(
        db_session
    )
    headers = owner_headers(
        authenticated_client,
        db_session,
        tenant,
    )

    response = authenticated_client.post(
        KEYS_URL,
        headers=headers,
        json={"name": "Integration test"},
    )

    assert response.status_code == 201

    return tenant, headers, response.json()


def developer_headers(created):
    return {
        "Authorization": (
            f"Bearer {created['api_key']}"
        )
    }


def test_owner_creates_hashed_assettrack_key(
    authenticated_client,
    db_session,
):
    tenant, headers, created = create_key(
        authenticated_client,
        db_session,
    )

    token = created["api_key"]

    assert token.startswith("flk_at_")
    assert created["key_prefix"] == token[:16]

    record = db_session.get(
        AssetTrackApiKey,
        created["id"],
    )

    assert record is not None
    assert record.tenant_id == tenant.id
    assert record.token_hash == hash_api_key(token)
    assert record.token_hash != token

    listed = authenticated_client.get(
        KEYS_URL,
        headers=headers,
    )

    assert listed.status_code == 200
    assert "api_key" not in listed.json()[0]


def test_developer_key_creates_asset_and_service_event(
    authenticated_client,
    raw_client,
    db_session,
):
    tenant, _, created = create_key(
        authenticated_client,
        db_session,
    )
    headers = developer_headers(created)

    status = raw_client.get(
        f"{DEVELOPER_URL}/status",
        headers=headers,
    )

    assert status.status_code == 200

    created_asset = raw_client.post(
        f"{DEVELOPER_URL}/assets",
        headers=headers,
        json={
            "external_id": "msp-device-100",
            "name": "Customer firewall",
            "asset_type": "network_device",
            "manufacturer": "Netgate",
            "model": "6100",
            "serial_number": "FW-6100-100",
            "attributes": {
                "site": "Main office",
            },
        },
    )

    assert created_asset.status_code == 201

    asset_payload = created_asset.json()
    asset_id = asset_payload["id"]

    stored_asset = db_session.get(
        Asset,
        asset_id,
    )

    assert stored_asset is not None
    assert stored_asset.tenant_id == tenant.id

    created_event = raw_client.post(
        (
            f"{DEVELOPER_URL}/assets/{asset_id}"
            "/service-events"
        ),
        headers=headers,
        json={
            "event_type": "maintenance",
            "occurred_at": "2026-09-05T18:00:00Z",
            "summary": "Updated firewall firmware",
            "details": {
                "ticket": "MSP-2001",
            },
        },
    )

    assert created_event.status_code == 201

    event_payload = created_event.json()

    stored_event = db_session.get(
        AssetServiceEvent,
        event_payload["id"],
    )

    assert stored_event is not None
    assert stored_event.tenant_id == tenant.id

    events = raw_client.get(
        (
            f"{DEVELOPER_URL}/assets/{asset_id}"
            "/service-events"
        ),
        headers=headers,
    )

    assert events.status_code == 200
    assert [
        event["id"]
        for event in events.json()
    ] == [event_payload["id"]]


def test_revoked_key_is_rejected(
    authenticated_client,
    raw_client,
    db_session,
):
    _, owner, created = create_key(
        authenticated_client,
        db_session,
    )
    headers = developer_headers(created)

    revoked = authenticated_client.delete(
        f"{KEYS_URL}/{created['id']}",
        headers=owner,
    )

    assert revoked.status_code == 204

    response = raw_client.get(
        f"{DEVELOPER_URL}/status",
        headers=headers,
    )

    assert response.status_code == 401


def test_developer_api_rejects_missing_key(
    raw_client,
):
    response = raw_client.get(
        f"{DEVELOPER_URL}/status"
    )

    assert response.status_code == 401


def test_only_owner_can_create_api_key(
    authenticated_client,
    db_session,
):
    tenant = create_assettrack_tenant(
        db_session
    )
    headers = authenticated_client.auth_headers(
        tenant
    )

    response = authenticated_client.post(
        KEYS_URL,
        headers=headers,
        json={"name": "Unauthorized key"},
    )

    assert response.status_code == 403
