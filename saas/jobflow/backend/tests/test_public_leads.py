from sqlalchemy import select

from app.models import Lead


def test_public_lead_can_be_created_without_auth(
    raw_client,
    db_session,
):
    response = raw_client.post(
        "/api/v1/public/products/jobflow/leads",
        json={
            "business_name": "Morel Home Services",
            "contact_name": "Rafael Morel",
            "email": "pilot@example.com",
            "phone": "555-2000",
            "service_type": "Handyman",
            "message": (
                "Looking for a simpler way to manage jobs "
                "and customer requests."
            ),
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "received"
    assert response.json()["lead_id"] > 0

    lead = db_session.scalar(
        select(Lead).where(
            Lead.email == "pilot@example.com"
        )
    )

    assert lead is not None
    assert lead.business_name == "Morel Home Services"
    assert lead.contact_name == "Rafael Morel"
    assert lead.service_type == "Handyman"
    assert lead.status == "new"


def test_public_lead_optional_fields_can_be_omitted(
    raw_client,
    db_session,
):
    response = raw_client.post(
        "/api/v1/public/products/jobflow/leads",
        json={
            "business_name": "Simple Landscaping",
            "contact_name": "Test Prospect",
            "email": "simple@example.com",
            "service_type": "Landscaping",
        },
    )

    assert response.status_code == 201

    lead = db_session.scalar(
        select(Lead).where(
            Lead.email == "simple@example.com"
        )
    )

    assert lead is not None
    assert lead.phone is None
    assert lead.message is None
    assert lead.status == "new"


def test_public_lead_rejects_server_controlled_fields(
    raw_client,
    db_session,
):
    response = raw_client.post(
        "/api/v1/public/products/jobflow/leads",
        json={
            "business_name": "Malicious Prospect",
            "contact_name": "Bad Actor",
            "email": "bad@example.com",
            "service_type": "Testing",
            "status": "converted",
            "id": 999,
        },
    )

    assert response.status_code == 422

    assert db_session.scalar(
        select(Lead).where(
            Lead.email == "bad@example.com"
        )
    ) is None


def test_public_lead_rejects_blank_required_fields(
    raw_client,
    db_session,
):
    response = raw_client.post(
        "/api/v1/public/products/jobflow/leads",
        json={
            "business_name": "   ",
            "contact_name": "Test Prospect",
            "email": "test@example.com",
            "service_type": "Handyman",
        },
    )

    assert response.status_code == 422

    assert db_session.scalar(
        select(Lead).where(
            Lead.email == "test@example.com"
        )
    ) is None


def test_public_lead_is_owned_by_requested_product(
    raw_client,
    db_session,
):
    from sqlalchemy import select

    from app.models import Lead, Product

    response = raw_client.post(
        "/api/v1/public/products/proofvault/leads",
        json={
            "business_name": "ProofVault Prospect",
            "contact_name": "PV Contact",
            "email": "proofvault-prospect@example.com",
            "phone": None,
            "service_type": "Evidence Management",
            "message": "Interested in ProofVault.",
        },
    )

    assert response.status_code == 201

    proofvault = db_session.scalar(
        select(Product).where(
            Product.slug == "proofvault"
        )
    )

    assert proofvault is not None

    lead = db_session.get(
        Lead,
        response.json()["lead_id"],
    )

    assert lead is not None
    assert lead.product_id == proofvault.id


def test_public_lead_rejects_unknown_product(
    raw_client,
):
    response = raw_client.post(
        "/api/v1/public/products/not-installed/leads",
        json={
            "business_name": "Unknown Product Prospect",
            "contact_name": "Unknown Contact",
            "email": "unknown-product@example.com",
            "phone": None,
            "service_type": "Unknown",
            "message": None,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Product not found or unavailable"
    )


def test_public_lead_rejects_inactive_product(
    raw_client,
    db_session,
):
    from sqlalchemy import select

    from app.models import Product

    product = db_session.scalar(
        select(Product).where(
            Product.slug == "proofvault"
        )
    )

    assert product is not None

    product.status = "inactive"
    db_session.commit()

    response = raw_client.post(
        "/api/v1/public/products/proofvault/leads",
        json={
            "business_name": "Inactive Product Prospect",
            "contact_name": "Inactive Contact",
            "email": "inactive-product@example.com",
            "phone": None,
            "service_type": "Evidence Management",
            "message": None,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Product not found or unavailable"
    )


def test_provisioned_tenant_preserves_lead_product(
    client,
    db_session,
):
    from sqlalchemy import select

    from app.models import Lead, Product, Tenant, User

    operator = db_session.scalar(
        select(User).where(
            User.email == "default-test-user@example.com"
        )
    )

    assert operator is not None
    operator.is_platform_admin = True

    owner = User(
        email="proofvault-owner@example.com",
        display_name="ProofVault Owner",
        is_active=True,
    )

    db_session.add(owner)
    db_session.commit()
    db_session.refresh(owner)

    proofvault = db_session.scalar(
        select(Product).where(
            Product.slug == "proofvault"
        )
    )

    assert proofvault is not None

    lead = Lead(
        product_id=proofvault.id,
        business_name="ProofVault Tenant",
        contact_name="ProofVault Contact",
        email="proofvault-tenant@example.com",
        service_type="Evidence Management",
        status="qualified",
    )

    db_session.add(lead)
    db_session.commit()
    db_session.refresh(lead)

    response = client.post(
        f"/api/v1/leads/{lead.id}/provision",
        json={
            "owner_user_id": owner.id,
            "tenant_slug": "proofvault-tenant",
        },
    )

    assert response.status_code == 201

    tenant = db_session.get(
        Tenant,
        response.json()["tenant"]["id"],
    )

    assert tenant is not None
    assert tenant.product_id == proofvault.id
    assert tenant.product_id == lead.product_id


def test_renewaldesk_public_pilot_request_is_product_owned(
    raw_client,
    db_session,
):
    from app.models import Product

    response = raw_client.post(
        "/api/v1/public/products/renewaldesk/leads",
        json={
            "business_name": "Renewal Test Office",
            "contact_name": "Renewal Contact",
            "email": "renewal-pilot@example.com",
            "phone": "555-0199",
            "service_type": "Professional Office",
            "message": (
                "We manage insurance, licenses, "
                "and certification renewals."
            ),
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "received"

    renewaldesk = db_session.scalar(
        select(Product).where(
            Product.slug == "renewaldesk"
        )
    )

    assert renewaldesk is not None

    lead = db_session.get(
        Lead,
        response.json()["lead_id"],
    )

    assert lead is not None
    assert lead.product_id == renewaldesk.id
    assert lead.business_name == "Renewal Test Office"
    assert lead.service_type == "Professional Office"
    assert lead.status == "new"
