from sqlalchemy import select

from app.models import Customer, Job, Tenant


def create_tenant(db_session, name, slug):
    tenant = Tenant(
        product_id=1,
        name=name,
        slug=slug,
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


def test_public_request_creates_customer_and_job_without_auth(
    raw_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        "Public Request Tenant",
        "public-request-tenant",
    )

    response = raw_client.post(
        "/api/v1/public/tenants/public-request-tenant/requests",
        json={
            "name": "Public Customer",
            "phone": "555-4100",
            "email": "public@example.com",
            "address": "4100 Customer Avenue",
            "project_title": "Replace front steps",
            "project_description": (
                "Existing steps are damaged and need replacement."
            ),
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "received"

    customer = db_session.scalar(
        select(Customer).where(
            Customer.email == "public@example.com"
        )
    )

    assert customer is not None
    assert customer.tenant_id == tenant.id
    assert customer.name == "Public Customer"

    job = db_session.scalar(
        select(Job).where(
            Job.id == response.json()["request_id"]
        )
    )

    assert job is not None
    assert job.customer_id == customer.id
    assert job.title == "Replace front steps"
    assert job.status == "customer_requested"


def test_public_request_resolves_tenant_from_slug(
    raw_client,
    db_session,
):
    tenant_a = create_tenant(
        db_session,
        "Public Tenant A",
        "public-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Public Tenant B",
        "public-tenant-b",
    )

    response = raw_client.post(
        "/api/v1/public/tenants/public-tenant-b/requests",
        json={
            "name": "Tenant B Public Customer",
            "email": "tenant-b-public@example.com",
            "project_title": "Fence repair",
        },
    )

    assert response.status_code == 201

    customer = db_session.scalar(
        select(Customer).where(
            Customer.email == "tenant-b-public@example.com"
        )
    )

    assert customer is not None
    assert customer.tenant_id == tenant_b.id
    assert customer.tenant_id != tenant_a.id


def test_public_request_rejects_unknown_tenant(
    raw_client,
    db_session,
):
    response = raw_client.post(
        "/api/v1/public/tenants/does-not-exist/requests",
        json={
            "name": "Unknown Tenant Customer",
            "project_title": "Unknown project",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Request page not found"

    assert db_session.scalar(
        select(Customer.id)
    ) is None

    assert db_session.scalar(
        select(Job.id)
    ) is None


def test_public_request_rejects_server_controlled_fields(
    raw_client,
    db_session,
):
    create_tenant(
        db_session,
        "Protected Public Tenant",
        "protected-public-tenant",
    )

    response = raw_client.post(
        "/api/v1/public/tenants/protected-public-tenant/requests",
        json={
            "name": "Malicious Customer",
            "project_title": "Attempted override",
            "status": "paid",
            "tenant_id": 999,
            "customer_id": 999,
        },
    )

    assert response.status_code == 422

    assert db_session.scalar(
        select(Customer.id)
    ) is None

    assert db_session.scalar(
        select(Job.id)
    ) is None
