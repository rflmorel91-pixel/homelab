from sqlalchemy import select

from app.models import Product, Tenant
from app.products.prestamodesk.models import LateFeePolicy


BASE_URL = (
    "/api/v1/products/prestamodesk"
    "/late-fee-policy"
)


def create_tenant(
    db_session,
    *,
    name,
    slug,
    client_number,
):
    product = db_session.scalar(
        select(Product).where(
            Product.slug == "prestamodesk"
        )
    )
    assert product is not None

    tenant = Tenant(
        product_id=product.id,
        client_number=client_number,
        name=name,
        slug=slug,
        status="active",
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


def valid_policy():
    return {
        "enabled": True,
        "daily_rate_percent": "0.1000",
        "grace_days": 5,
        "cap_percent": "25.0000",
        "effective_date": "2026-10-01",
    }


def test_owner_can_configure_and_update_policy(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        name="Late Fee Policy Tenant",
        slug="late-fee-policy-tenant",
        client_number=801,
    )
    headers = authenticated_client.owner_headers(
        tenant
    )

    missing = authenticated_client.get(
        BASE_URL,
        headers=headers,
    )
    assert missing.status_code == 404

    created = authenticated_client.put(
        BASE_URL,
        headers=headers,
        json=valid_policy(),
    )

    assert created.status_code == 200
    assert created.json()["tenant_id"] == tenant.id
    assert created.json()["enabled"] is True
    assert created.json()["daily_rate_percent"] == (
        "0.1000"
    )
    assert created.json()["grace_days"] == 5
    assert created.json()["cap_percent"] == "25.0000"
    assert created.json()["effective_date"] == (
        "2026-10-01"
    )

    payload = valid_policy()
    payload["daily_rate_percent"] = "0.0500"
    payload["grace_days"] = 10

    updated = authenticated_client.put(
        BASE_URL,
        headers=headers,
        json=payload,
    )

    assert updated.status_code == 200
    assert updated.json()["id"] == created.json()["id"]
    assert updated.json()["daily_rate_percent"] == (
        "0.0500"
    )
    assert updated.json()["grace_days"] == 10

    policies = db_session.scalars(
        select(LateFeePolicy).where(
            LateFeePolicy.tenant_id == tenant.id
        )
    ).all()
    assert len(policies) == 1


def test_member_cannot_manage_policy(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        name="Cashier Policy Tenant",
        slug="cashier-policy-tenant",
        client_number=802,
    )
    headers = authenticated_client.auth_headers(
        tenant
    )

    for method in ("get", "put"):
        response = authenticated_client.request(
            method,
            BASE_URL,
            headers=headers,
            json=(
                valid_policy()
                if method == "put"
                else None
            ),
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Tenant owner access required"
        )


def test_policy_is_isolated_by_tenant(
    authenticated_client,
    db_session,
):
    tenant_a = create_tenant(
        db_session,
        name="Policy Tenant A",
        slug="policy-tenant-a",
        client_number=803,
    )
    tenant_b = create_tenant(
        db_session,
        name="Policy Tenant B",
        slug="policy-tenant-b",
        client_number=804,
    )

    created = authenticated_client.put(
        BASE_URL,
        headers=authenticated_client.owner_headers(
            tenant_a
        ),
        json=valid_policy(),
    )
    assert created.status_code == 200

    missing = authenticated_client.get(
        BASE_URL,
        headers=authenticated_client.owner_headers(
            tenant_b
        ),
    )
    assert missing.status_code == 404


def test_invalid_enabled_policy_is_rejected(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        name="Invalid Policy Tenant",
        slug="invalid-policy-tenant",
        client_number=805,
    )
    payload = valid_policy()
    payload["daily_rate_percent"] = "0.0000"

    response = authenticated_client.put(
        BASE_URL,
        headers=authenticated_client.owner_headers(
            tenant
        ),
        json=payload,
    )

    assert response.status_code == 422
