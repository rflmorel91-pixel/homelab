from decimal import Decimal

from sqlalchemy import select

from app.models import Product, Tenant
from app.products.prestamodesk.models import Prospect


BASE_URL = (
    "/api/v1/products/prestamodesk"
    "/public/tenants"
)


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
    *,
    product_slug="prestamodesk",
    name="Prospect Tenant",
    slug="prospect-tenant",
    status="active",
    client_number=1,
):
    product = get_product(
        db_session,
        product_slug,
    )

    tenant = Tenant(
        product_id=product.id,
        client_number=client_number,
        name=name,
        slug=slug,
        status=status,
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


def valid_payload():
    return {
        "full_name": "Ana Pérez",
        "phone": "809-555-0110",
        "email": "ana@example.com",
        "municipality": "Santo Domingo Este",
        "province": "Santo Domingo",
        "requested_amount": "25000.00",
        "preferred_contact": "whatsapp",
        "message": "Deseo información sobre los requisitos.",
        "consent_to_contact": True,
    }


def test_public_prospect_is_created_for_requested_tenant(
    raw_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        slug="public-prestamodesk-tenant",
    )

    response = raw_client.post(
        (
            f"{BASE_URL}/"
            f"{tenant.slug}/prospects"
        ),
        json=valid_payload(),
    )

    assert response.status_code == 201
    assert response.json()["status"] == "received"

    prospect = db_session.get(
        Prospect,
        response.json()["prospect_id"],
    )

    assert prospect is not None
    assert prospect.tenant_id == tenant.id
    assert prospect.full_name == "Ana Pérez"
    assert prospect.phone == "809-555-0110"
    assert prospect.email == "ana@example.com"
    assert prospect.requested_amount == Decimal(
        "25000.00"
    )
    assert prospect.preferred_contact == "whatsapp"
    assert prospect.status == "new"
    assert prospect.consented_at is not None
    assert (
        prospect.consent_notice_version
        == "2026-09-29"
    )
    assert prospect.converted_borrower_id is None


def test_public_prospect_resolves_exact_tenant(
    raw_client,
    db_session,
):
    tenant_a = create_tenant(
        db_session,
        name="Prospect Tenant A",
        slug="prospect-tenant-a",
        client_number=10,
    )
    tenant_b = create_tenant(
        db_session,
        name="Prospect Tenant B",
        slug="prospect-tenant-b",
        client_number=11,
    )

    payload = valid_payload()
    payload["email"] = "tenant-b@example.com"

    response = raw_client.post(
        (
            f"{BASE_URL}/"
            f"{tenant_b.slug}/prospects"
        ),
        json=payload,
    )

    assert response.status_code == 201

    prospect = db_session.get(
        Prospect,
        response.json()["prospect_id"],
    )
    assert prospect is not None
    assert prospect.tenant_id == tenant_b.id
    assert prospect.tenant_id != tenant_a.id


def test_public_prospect_rejects_unknown_tenant(
    raw_client,
    db_session,
):
    response = raw_client.post(
        f"{BASE_URL}/missing-tenant/prospects",
        json=valid_payload(),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Solicitud no disponible"
    )
    assert db_session.scalar(
        select(Prospect.id)
    ) is None


def test_public_prospect_rejects_suspended_tenant(
    raw_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        slug="suspended-prospect-tenant",
        status="suspended",
    )

    response = raw_client.post(
        (
            f"{BASE_URL}/"
            f"{tenant.slug}/prospects"
        ),
        json=valid_payload(),
    )

    assert response.status_code == 404
    assert db_session.scalar(
        select(Prospect.id)
    ) is None


def test_public_prospect_rejects_other_product_tenant(
    raw_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        product_slug="jobflow",
        name="Wrong Product Tenant",
        slug="wrong-product-prospect-tenant",
        client_number=91,
    )

    response = raw_client.post(
        (
            f"{BASE_URL}/"
            f"{tenant.slug}/prospects"
        ),
        json=valid_payload(),
    )

    assert response.status_code == 404
    assert db_session.scalar(
        select(Prospect.id)
    ) is None


def test_public_prospect_requires_contact_consent(
    raw_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        slug="consent-prospect-tenant",
    )
    payload = valid_payload()
    payload["consent_to_contact"] = False

    response = raw_client.post(
        (
            f"{BASE_URL}/"
            f"{tenant.slug}/prospects"
        ),
        json=payload,
    )

    assert response.status_code == 422
    assert db_session.scalar(
        select(Prospect.id)
    ) is None


def test_public_prospect_rejects_server_fields(
    raw_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        slug="protected-prospect-tenant",
    )
    payload = valid_payload()
    payload.update(
        {
            "tenant_id": 999,
            "status": "converted",
            "converted_borrower_id": 999,
            "consented_at": "2020-01-01T00:00:00",
        }
    )

    response = raw_client.post(
        (
            f"{BASE_URL}/"
            f"{tenant.slug}/prospects"
        ),
        json=payload,
    )

    assert response.status_code == 422
    assert db_session.scalar(
        select(Prospect.id)
    ) is None


def test_public_prospect_rejects_blank_identity(
    raw_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        slug="blank-prospect-tenant",
    )
    payload = valid_payload()
    payload["full_name"] = "   "

    response = raw_client.post(
        (
            f"{BASE_URL}/"
            f"{tenant.slug}/prospects"
        ),
        json=payload,
    )

    assert response.status_code == 422
    assert db_session.scalar(
        select(Prospect.id)
    ) is None


def test_public_page_returns_active_tenant_branding(
    raw_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        name="Préstamos Ejemplo SRL",
        slug="prestamos-ejemplo",
        client_number=28,
    )

    response = raw_client.get(
        f"{BASE_URL}/{tenant.slug}"
    )

    assert response.status_code == 200
    assert response.json() == {
        "tenant_slug": "prestamos-ejemplo",
        "business_name": "Préstamos Ejemplo SRL",
        "client_number": 28,
    }


def test_public_page_hides_unavailable_tenants(
    raw_client,
    db_session,
):
    suspended = create_tenant(
        db_session,
        name="Suspended Public Page",
        slug="suspended-public-page",
        status="suspended",
        client_number=29,
    )
    wrong_product = create_tenant(
        db_session,
        product_slug="jobflow",
        name="Wrong Product Public Page",
        slug="wrong-product-public-page",
        client_number=30,
    )

    for tenant in (
        suspended,
        wrong_product,
    ):
        response = raw_client.get(
            f"{BASE_URL}/{tenant.slug}"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == (
            "Solicitud no disponible"
        )
