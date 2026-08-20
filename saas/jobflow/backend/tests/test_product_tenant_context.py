from sqlalchemy import select

from app.models import Product, Tenant


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


def test_public_product_router_requires_no_tenant(
    raw_client,
):
    response = raw_client.get(
        "/api/v1/products/proofvault/status"
    )

    assert response.status_code == 200


def test_jobflow_tenant_router_accepts_jobflow_tenant(
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
        "JobFlow Product Tenant",
        "jobflow-product-tenant",
    )

    response = client.get(
        "/api/v1/customers/",
        headers=client.auth_headers(tenant),
    )

    assert response.status_code == 200


def test_jobflow_tenant_router_rejects_other_product(
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
        "RenewalDesk Product Tenant",
        "renewaldesk-product-tenant",
    )

    response = client.get(
        "/api/v1/customers/",
        headers=client.auth_headers(tenant),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Tenant does not belong to this product"
    )
