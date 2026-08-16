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


def test_cannot_create_job_for_another_tenants_customer(
    client,
    db_session,
):
    tenant_a = create_tenant(
        db_session,
        "Job Tenant A",
        "job-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Job Tenant B",
        "job-tenant-b",
    )

    customer_b_response = client.post(
        "/api/v1/customers/",
        headers={
            "X-Tenant-ID": str(tenant_b.id),
        },
        json={
            "name": "Tenant B Job Customer",
            "phone": "555-2300",
            "email": "job-b@example.com",
            "address": "2300 Tenant B Street",
        },
    )

    assert customer_b_response.status_code == 201
    customer_b = customer_b_response.json()

    create_job_response = client.post(
        "/api/v1/jobs/",
        headers={
            "X-Tenant-ID": str(tenant_a.id),
        },
        json={
            "customer_id": customer_b["id"],
            "title": "Cross Tenant Job",
            "description": "This must not be created",
        },
    )

    assert create_job_response.status_code == 404
    assert create_job_response.json()["detail"] == (
        "Customer not found"
    )


def test_cross_tenant_job_read_is_hidden(
    client,
    db_session,
):
    tenant_a = create_tenant(
        db_session,
        "Job Read Tenant A",
        "job-read-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Job Read Tenant B",
        "job-read-tenant-b",
    )

    customer_b_response = client.post(
        "/api/v1/customers/",
        headers={
            "X-Tenant-ID": str(tenant_b.id),
        },
        json={
            "name": "Tenant B Read Customer",
            "phone": "555-2400",
            "email": "job-read-b@example.com",
            "address": "2400 Tenant B Street",
        },
    )

    assert customer_b_response.status_code == 201
    customer_b = customer_b_response.json()

    job_b_response = client.post(
        "/api/v1/jobs/",
        headers={
            "X-Tenant-ID": str(tenant_b.id),
        },
        json={
            "customer_id": customer_b["id"],
            "title": "Tenant B Private Job",
            "description": "Private to Tenant B",
        },
    )

    assert job_b_response.status_code == 201
    job_b = job_b_response.json()

    cross_tenant_get = client.get(
        f"/api/v1/jobs/{job_b['id']}",
        headers={
            "X-Tenant-ID": str(tenant_a.id),
        },
    )

    assert cross_tenant_get.status_code == 404
    assert cross_tenant_get.json()["detail"] == (
        "Job not found"
    )


def test_job_lists_are_isolated_by_tenant(
    client,
    db_session,
):
    tenant_a = create_tenant(
        db_session,
        "Job List Tenant A",
        "job-list-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Job List Tenant B",
        "job-list-tenant-b",
    )

    customer_a = client.post(
        "/api/v1/customers/",
        headers={"X-Tenant-ID": str(tenant_a.id)},
        json={
            "name": "Job List Customer A",
            "phone": "555-2501",
            "email": "job-list-a@example.com",
            "address": "2501 Tenant A Street",
        },
    ).json()

    customer_b = client.post(
        "/api/v1/customers/",
        headers={"X-Tenant-ID": str(tenant_b.id)},
        json={
            "name": "Job List Customer B",
            "phone": "555-2502",
            "email": "job-list-b@example.com",
            "address": "2502 Tenant B Street",
        },
    ).json()

    job_a = client.post(
        "/api/v1/jobs/",
        headers={"X-Tenant-ID": str(tenant_a.id)},
        json={
            "customer_id": customer_a["id"],
            "title": "Tenant A Job",
            "description": "Visible only to Tenant A",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers={"X-Tenant-ID": str(tenant_b.id)},
        json={
            "customer_id": customer_b["id"],
            "title": "Tenant B Job",
            "description": "Visible only to Tenant B",
        },
    ).json()

    list_a = client.get(
        "/api/v1/jobs/",
        headers={"X-Tenant-ID": str(tenant_a.id)},
    )

    assert list_a.status_code == 200
    assert [item["id"] for item in list_a.json()] == [job_a["id"]]

    list_b = client.get(
        "/api/v1/jobs/",
        headers={"X-Tenant-ID": str(tenant_b.id)},
    )

    assert list_b.status_code == 200
    assert [item["id"] for item in list_b.json()] == [job_b["id"]]


def test_cross_tenant_job_update_is_hidden(
    client,
    db_session,
):
    tenant_a = create_tenant(
        db_session,
        "Job Update Tenant A",
        "job-update-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Job Update Tenant B",
        "job-update-tenant-b",
    )

    customer_b = client.post(
        "/api/v1/customers/",
        headers={"X-Tenant-ID": str(tenant_b.id)},
        json={
            "name": "Job Update Customer B",
            "phone": "555-2600",
            "email": "job-update-b@example.com",
            "address": "2600 Tenant B Street",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers={"X-Tenant-ID": str(tenant_b.id)},
        json={
            "customer_id": customer_b["id"],
            "title": "Protected Tenant B Job",
            "description": "Must not be changed by Tenant A",
        },
    ).json()

    response = client.put(
        f"/api/v1/jobs/{job_b['id']}",
        headers={"X-Tenant-ID": str(tenant_a.id)},
        json={
            "customer_id": customer_b["id"],
            "title": "Hijacked Job",
            "description": "Wrong tenant",
            "status": "quoted",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"

    original = client.get(
        f"/api/v1/jobs/{job_b['id']}",
        headers={"X-Tenant-ID": str(tenant_b.id)},
    )

    assert original.status_code == 200
    assert original.json()["title"] == "Protected Tenant B Job"
    assert original.json()["status"] == "customer_requested"


def test_cross_tenant_job_delete_is_hidden(
    client,
    db_session,
):
    tenant_a = create_tenant(
        db_session,
        "Job Delete Tenant A",
        "job-delete-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Job Delete Tenant B",
        "job-delete-tenant-b",
    )

    customer_b = client.post(
        "/api/v1/customers/",
        headers={"X-Tenant-ID": str(tenant_b.id)},
        json={
            "name": "Job Delete Customer B",
            "phone": "555-2700",
            "email": "job-delete-b@example.com",
            "address": "2700 Tenant B Street",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers={"X-Tenant-ID": str(tenant_b.id)},
        json={
            "customer_id": customer_b["id"],
            "title": "Undeletable Tenant B Job",
            "description": "Tenant A must not delete this",
        },
    ).json()

    response = client.delete(
        f"/api/v1/jobs/{job_b['id']}",
        headers={"X-Tenant-ID": str(tenant_a.id)},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"

    original = client.get(
        f"/api/v1/jobs/{job_b['id']}",
        headers={"X-Tenant-ID": str(tenant_b.id)},
    )

    assert original.status_code == 200


def test_cannot_create_estimate_for_another_tenants_job(
    client,
    db_session,
):
    tenant_a = create_tenant(
        db_session,
        "Estimate Tenant A",
        "estimate-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Estimate Tenant B",
        "estimate-tenant-b",
    )

    customer_b = client.post(
        "/api/v1/customers/",
        headers={"X-Tenant-ID": str(tenant_b.id)},
        json={
            "name": "Estimate Customer B",
            "phone": "555-2800",
            "email": "estimate-b@example.com",
            "address": "2800 Tenant B Street",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers={"X-Tenant-ID": str(tenant_b.id)},
        json={
            "customer_id": customer_b["id"],
            "title": "Estimate Tenant B Job",
            "description": "Private Tenant B job",
        },
    ).json()

    response = client.post(
        "/api/v1/estimates/",
        headers={"X-Tenant-ID": str(tenant_a.id)},
        json={
            "job_id": job_b["id"],
            "description": "Cross Tenant Estimate",
            "amount": "500.00",
            "status": "draft",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_cross_tenant_estimate_read_is_hidden(
    client,
    db_session,
):
    tenant_a = create_tenant(
        db_session,
        "Estimate Read Tenant A",
        "estimate-read-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Estimate Read Tenant B",
        "estimate-read-tenant-b",
    )

    customer_b = client.post(
        "/api/v1/customers/",
        headers={"X-Tenant-ID": str(tenant_b.id)},
        json={
            "name": "Estimate Read Customer B",
            "phone": "555-2900",
            "email": "estimate-read-b@example.com",
            "address": "2900 Tenant B Street",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers={"X-Tenant-ID": str(tenant_b.id)},
        json={
            "customer_id": customer_b["id"],
            "title": "Private Estimate Job",
            "description": "Private to Tenant B",
        },
    ).json()

    estimate_b = client.post(
        "/api/v1/estimates/",
        headers={"X-Tenant-ID": str(tenant_b.id)},
        json={
            "job_id": job_b["id"],
            "description": "Tenant B Private Estimate",
            "amount": "725.00",
            "status": "draft",
        },
    ).json()

    response = client.get(
        f"/api/v1/estimates/{estimate_b['id']}",
        headers={"X-Tenant-ID": str(tenant_a.id)},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Estimate not found"


def test_estimate_lists_are_isolated_by_tenant(
    client,
    db_session,
):
    tenant_a = create_tenant(
        db_session,
        "Estimate List Tenant A",
        "estimate-list-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Estimate List Tenant B",
        "estimate-list-tenant-b",
    )

    customer_a = client.post(
        "/api/v1/customers/",
        headers={"X-Tenant-ID": str(tenant_a.id)},
        json={
            "name": "Estimate List Customer A",
            "phone": "555-3001",
            "email": "estimate-list-a@example.com",
            "address": "3001 Tenant A Street",
        },
    ).json()

    customer_b = client.post(
        "/api/v1/customers/",
        headers={"X-Tenant-ID": str(tenant_b.id)},
        json={
            "name": "Estimate List Customer B",
            "phone": "555-3002",
            "email": "estimate-list-b@example.com",
            "address": "3002 Tenant B Street",
        },
    ).json()

    job_a = client.post(
        "/api/v1/jobs/",
        headers={"X-Tenant-ID": str(tenant_a.id)},
        json={
            "customer_id": customer_a["id"],
            "title": "Estimate List Job A",
            "description": "Tenant A",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers={"X-Tenant-ID": str(tenant_b.id)},
        json={
            "customer_id": customer_b["id"],
            "title": "Estimate List Job B",
            "description": "Tenant B",
        },
    ).json()

    estimate_a = client.post(
        "/api/v1/estimates/",
        headers={"X-Tenant-ID": str(tenant_a.id)},
        json={
            "job_id": job_a["id"],
            "description": "Estimate A",
            "amount": "100.00",
            "status": "draft",
        },
    ).json()

    estimate_b = client.post(
        "/api/v1/estimates/",
        headers={"X-Tenant-ID": str(tenant_b.id)},
        json={
            "job_id": job_b["id"],
            "description": "Estimate B",
            "amount": "200.00",
            "status": "draft",
        },
    ).json()

    list_a = client.get(
        "/api/v1/estimates/",
        headers={"X-Tenant-ID": str(tenant_a.id)},
    )
    assert list_a.status_code == 200
    assert [item["id"] for item in list_a.json()] == [estimate_a["id"]]

    list_b = client.get(
        "/api/v1/estimates/",
        headers={"X-Tenant-ID": str(tenant_b.id)},
    )
    assert list_b.status_code == 200
    assert [item["id"] for item in list_b.json()] == [estimate_b["id"]]


def test_cross_tenant_estimate_update_is_hidden(
    client,
    db_session,
):
    tenant_a = create_tenant(
        db_session,
        "Estimate Update Tenant A",
        "estimate-update-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Estimate Update Tenant B",
        "estimate-update-tenant-b",
    )

    customer_b = client.post(
        "/api/v1/customers/",
        headers={"X-Tenant-ID": str(tenant_b.id)},
        json={
            "name": "Estimate Update Customer B",
            "phone": "555-3100",
            "email": "estimate-update-b@example.com",
            "address": "3100 Tenant B Street",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers={"X-Tenant-ID": str(tenant_b.id)},
        json={
            "customer_id": customer_b["id"],
            "title": "Estimate Update Job B",
            "description": "Protected",
        },
    ).json()

    estimate_b = client.post(
        "/api/v1/estimates/",
        headers={"X-Tenant-ID": str(tenant_b.id)},
        json={
            "job_id": job_b["id"],
            "description": "Protected Estimate",
            "amount": "400.00",
            "status": "draft",
        },
    ).json()

    response = client.put(
        f"/api/v1/estimates/{estimate_b['id']}",
        headers={"X-Tenant-ID": str(tenant_a.id)},
        json={
            "job_id": job_b["id"],
            "description": "Hijacked Estimate",
            "amount": "999.00",
            "status": "sent",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Estimate not found"

    original = client.get(
        f"/api/v1/estimates/{estimate_b['id']}",
        headers={"X-Tenant-ID": str(tenant_b.id)},
    )
    assert original.status_code == 200
    assert original.json()["description"] == "Protected Estimate"
    assert original.json()["amount"] == "400.00"
    assert original.json()["status"] == "draft"


def test_cross_tenant_estimate_delete_is_hidden(
    client,
    db_session,
):
    tenant_a = create_tenant(
        db_session,
        "Estimate Delete Tenant A",
        "estimate-delete-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Estimate Delete Tenant B",
        "estimate-delete-tenant-b",
    )

    customer_b = client.post(
        "/api/v1/customers/",
        headers={"X-Tenant-ID": str(tenant_b.id)},
        json={
            "name": "Estimate Delete Customer B",
            "phone": "555-3200",
            "email": "estimate-delete-b@example.com",
            "address": "3200 Tenant B Street",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers={"X-Tenant-ID": str(tenant_b.id)},
        json={
            "customer_id": customer_b["id"],
            "title": "Estimate Delete Job B",
            "description": "Protected",
        },
    ).json()

    estimate_b = client.post(
        "/api/v1/estimates/",
        headers={"X-Tenant-ID": str(tenant_b.id)},
        json={
            "job_id": job_b["id"],
            "description": "Undeletable Estimate",
            "amount": "450.00",
            "status": "draft",
        },
    ).json()

    response = client.delete(
        f"/api/v1/estimates/{estimate_b['id']}",
        headers={"X-Tenant-ID": str(tenant_a.id)},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Estimate not found"

    original = client.get(
        f"/api/v1/estimates/{estimate_b['id']}",
        headers={"X-Tenant-ID": str(tenant_b.id)},
    )
    assert original.status_code == 200
