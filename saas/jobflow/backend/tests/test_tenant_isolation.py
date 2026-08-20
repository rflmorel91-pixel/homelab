from app.models import Tenant, TenantMembership, User


def create_tenant(db_session, name, slug):
    tenant = Tenant(
        name=name,
        slug=slug,
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


def create_user(
    db_session,
    email,
    display_name,
    is_active=True,
):
    user = User(
        email=email,
        display_name=display_name,
        is_active=is_active,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def add_membership(
    db_session,
    tenant,
    user,
    role="member",
):
    membership = TenantMembership(
        tenant_id=tenant.id,
        user_id=user.id,
        role=role,
    )
    db_session.add(membership)
    db_session.commit()
    db_session.refresh(membership)
    return membership


def auth_headers(user, tenant):
    return {
        "X-User-ID": str(user.id),
        "X-Tenant-ID": str(tenant.id),
    }


def test_customer_api_requires_tenant_context(
    raw_client,
):
    response = raw_client.get(
        "/api/v1/customers/",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Authentication required"
    )


def test_customers_are_isolated_by_tenant(
    authenticated_client,
    db_session,
):
    client = authenticated_client

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
        headers=client.auth_headers(tenant_a),
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
        headers=client.auth_headers(tenant_b),
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
        headers=client.auth_headers(tenant_a),
    )

    assert list_a.status_code == 200
    assert [
        item["id"]
        for item in list_a.json()
    ] == [customer_a["id"]]

    list_b = client.get(
        "/api/v1/customers/",
        headers=client.auth_headers(tenant_b),
    )

    assert list_b.status_code == 200
    assert [
        item["id"]
        for item in list_b.json()
    ] == [customer_b["id"]]

    cross_tenant_get = client.get(
        f"/api/v1/customers/{customer_b['id']}",
        headers=client.auth_headers(tenant_a),
    )

    assert cross_tenant_get.status_code == 404
    assert cross_tenant_get.json()["detail"] == (
        "Customer not found"
    )


def test_cross_tenant_customer_update_is_hidden(
    authenticated_client,
    db_session,
):
    client = authenticated_client

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
        headers=client.auth_headers(tenant_b),
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
        headers=client.auth_headers(tenant_a),
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
        headers=client.auth_headers(tenant_b),
    )

    assert original.status_code == 200
    assert original.json()["name"] == (
        "Protected Tenant B Customer"
    )


def test_cross_tenant_customer_delete_is_hidden(
    authenticated_client,
    db_session,
):
    client = authenticated_client

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
        headers=client.auth_headers(tenant_b),
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
        headers=client.auth_headers(tenant_a),
    )

    assert delete_response.status_code == 404
    assert delete_response.json()["detail"] == (
        "Customer not found"
    )

    original = client.get(
        f"/api/v1/customers/{customer_b['id']}",
        headers=client.auth_headers(tenant_b),
    )

    assert original.status_code == 200


def test_cannot_create_job_for_another_tenants_customer(
    authenticated_client,
    db_session,
):
    client = authenticated_client

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
        headers=client.auth_headers(tenant_b),
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
        headers=client.auth_headers(tenant_a),
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
    authenticated_client,
    db_session,
):
    client = authenticated_client

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
        headers=client.auth_headers(tenant_b),
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
        headers=client.auth_headers(tenant_b),
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
        headers=client.auth_headers(tenant_a),
    )

    assert cross_tenant_get.status_code == 404
    assert cross_tenant_get.json()["detail"] == (
        "Job not found"
    )


def test_job_lists_are_isolated_by_tenant(
    authenticated_client,
    db_session,
):
    client = authenticated_client

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
        headers=client.auth_headers(tenant_a),
        json={
            "name": "Job List Customer A",
            "phone": "555-2501",
            "email": "job-list-a@example.com",
            "address": "2501 Tenant A Street",
        },
    ).json()

    customer_b = client.post(
        "/api/v1/customers/",
        headers=client.auth_headers(tenant_b),
        json={
            "name": "Job List Customer B",
            "phone": "555-2502",
            "email": "job-list-b@example.com",
            "address": "2502 Tenant B Street",
        },
    ).json()

    job_a = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_a),
        json={
            "customer_id": customer_a["id"],
            "title": "Tenant A Job",
            "description": "Visible only to Tenant A",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_b),
        json={
            "customer_id": customer_b["id"],
            "title": "Tenant B Job",
            "description": "Visible only to Tenant B",
        },
    ).json()

    list_a = client.get(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_a),
    )

    assert list_a.status_code == 200
    assert [item["id"] for item in list_a.json()] == [job_a["id"]]

    list_b = client.get(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_b),
    )

    assert list_b.status_code == 200
    assert [item["id"] for item in list_b.json()] == [job_b["id"]]


def test_cross_tenant_job_update_is_hidden(
    authenticated_client,
    db_session,
):
    client = authenticated_client

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
        headers=client.auth_headers(tenant_b),
        json={
            "name": "Job Update Customer B",
            "phone": "555-2600",
            "email": "job-update-b@example.com",
            "address": "2600 Tenant B Street",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_b),
        json={
            "customer_id": customer_b["id"],
            "title": "Protected Tenant B Job",
            "description": "Must not be changed by Tenant A",
        },
    ).json()

    response = client.put(
        f"/api/v1/jobs/{job_b['id']}",
        headers=client.auth_headers(tenant_a),
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
        headers=client.auth_headers(tenant_b),
    )

    assert original.status_code == 200
    assert original.json()["title"] == "Protected Tenant B Job"
    assert original.json()["status"] == "customer_requested"


def test_cross_tenant_job_delete_is_hidden(
    authenticated_client,
    db_session,
):
    client = authenticated_client

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
        headers=client.auth_headers(tenant_b),
        json={
            "name": "Job Delete Customer B",
            "phone": "555-2700",
            "email": "job-delete-b@example.com",
            "address": "2700 Tenant B Street",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_b),
        json={
            "customer_id": customer_b["id"],
            "title": "Undeletable Tenant B Job",
            "description": "Tenant A must not delete this",
        },
    ).json()

    response = client.delete(
        f"/api/v1/jobs/{job_b['id']}",
        headers=client.auth_headers(tenant_a),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"

    original = client.get(
        f"/api/v1/jobs/{job_b['id']}",
        headers=client.auth_headers(tenant_b),
    )

    assert original.status_code == 200


def test_cannot_create_estimate_for_another_tenants_job(
    authenticated_client,
    db_session,
):
    client = authenticated_client

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
        headers=client.auth_headers(tenant_b),
        json={
            "name": "Estimate Customer B",
            "phone": "555-2800",
            "email": "estimate-b@example.com",
            "address": "2800 Tenant B Street",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_b),
        json={
            "customer_id": customer_b["id"],
            "title": "Estimate Tenant B Job",
            "description": "Private Tenant B job",
        },
    ).json()

    response = client.post(
        "/api/v1/estimates/",
        headers=client.auth_headers(tenant_a),
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
    authenticated_client,
    db_session,
):
    client = authenticated_client

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
        headers=client.auth_headers(tenant_b),
        json={
            "name": "Estimate Read Customer B",
            "phone": "555-2900",
            "email": "estimate-read-b@example.com",
            "address": "2900 Tenant B Street",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_b),
        json={
            "customer_id": customer_b["id"],
            "title": "Private Estimate Job",
            "description": "Private to Tenant B",
        },
    ).json()

    estimate_b = client.post(
        "/api/v1/estimates/",
        headers=client.auth_headers(tenant_b),
        json={
            "job_id": job_b["id"],
            "description": "Tenant B Private Estimate",
            "amount": "725.00",
            "status": "draft",
        },
    ).json()

    response = client.get(
        f"/api/v1/estimates/{estimate_b['id']}",
        headers=client.auth_headers(tenant_a),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Estimate not found"


def test_estimate_lists_are_isolated_by_tenant(
    authenticated_client,
    db_session,
):
    client = authenticated_client

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
        headers=client.auth_headers(tenant_a),
        json={
            "name": "Estimate List Customer A",
            "phone": "555-3001",
            "email": "estimate-list-a@example.com",
            "address": "3001 Tenant A Street",
        },
    ).json()

    customer_b = client.post(
        "/api/v1/customers/",
        headers=client.auth_headers(tenant_b),
        json={
            "name": "Estimate List Customer B",
            "phone": "555-3002",
            "email": "estimate-list-b@example.com",
            "address": "3002 Tenant B Street",
        },
    ).json()

    job_a = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_a),
        json={
            "customer_id": customer_a["id"],
            "title": "Estimate List Job A",
            "description": "Tenant A",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_b),
        json={
            "customer_id": customer_b["id"],
            "title": "Estimate List Job B",
            "description": "Tenant B",
        },
    ).json()

    estimate_a = client.post(
        "/api/v1/estimates/",
        headers=client.auth_headers(tenant_a),
        json={
            "job_id": job_a["id"],
            "description": "Estimate A",
            "amount": "100.00",
            "status": "draft",
        },
    ).json()

    estimate_b = client.post(
        "/api/v1/estimates/",
        headers=client.auth_headers(tenant_b),
        json={
            "job_id": job_b["id"],
            "description": "Estimate B",
            "amount": "200.00",
            "status": "draft",
        },
    ).json()

    list_a = client.get(
        "/api/v1/estimates/",
        headers=client.auth_headers(tenant_a),
    )
    assert list_a.status_code == 200
    assert [item["id"] for item in list_a.json()] == [estimate_a["id"]]

    list_b = client.get(
        "/api/v1/estimates/",
        headers=client.auth_headers(tenant_b),
    )
    assert list_b.status_code == 200
    assert [item["id"] for item in list_b.json()] == [estimate_b["id"]]


def test_cross_tenant_estimate_update_is_hidden(
    authenticated_client,
    db_session,
):
    client = authenticated_client

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
        headers=client.auth_headers(tenant_b),
        json={
            "name": "Estimate Update Customer B",
            "phone": "555-3100",
            "email": "estimate-update-b@example.com",
            "address": "3100 Tenant B Street",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_b),
        json={
            "customer_id": customer_b["id"],
            "title": "Estimate Update Job B",
            "description": "Protected",
        },
    ).json()

    estimate_b = client.post(
        "/api/v1/estimates/",
        headers=client.auth_headers(tenant_b),
        json={
            "job_id": job_b["id"],
            "description": "Protected Estimate",
            "amount": "400.00",
            "status": "draft",
        },
    ).json()

    response = client.put(
        f"/api/v1/estimates/{estimate_b['id']}",
        headers=client.auth_headers(tenant_a),
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
        headers=client.auth_headers(tenant_b),
    )
    assert original.status_code == 200
    assert original.json()["description"] == "Protected Estimate"
    assert original.json()["amount"] == "400.00"
    assert original.json()["status"] == "draft"


def test_cross_tenant_estimate_delete_is_hidden(
    authenticated_client,
    db_session,
):
    client = authenticated_client

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
        headers=client.auth_headers(tenant_b),
        json={
            "name": "Estimate Delete Customer B",
            "phone": "555-3200",
            "email": "estimate-delete-b@example.com",
            "address": "3200 Tenant B Street",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_b),
        json={
            "customer_id": customer_b["id"],
            "title": "Estimate Delete Job B",
            "description": "Protected",
        },
    ).json()

    estimate_b = client.post(
        "/api/v1/estimates/",
        headers=client.auth_headers(tenant_b),
        json={
            "job_id": job_b["id"],
            "description": "Undeletable Estimate",
            "amount": "450.00",
            "status": "draft",
        },
    ).json()

    response = client.delete(
        f"/api/v1/estimates/{estimate_b['id']}",
        headers=client.auth_headers(tenant_a),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Estimate not found"

    original = client.get(
        f"/api/v1/estimates/{estimate_b['id']}",
        headers=client.auth_headers(tenant_b),
    )
    assert original.status_code == 200


def test_cannot_create_schedule_for_another_tenants_job(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    tenant_a = create_tenant(
        db_session,
        "Schedule Tenant A",
        "schedule-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Schedule Tenant B",
        "schedule-tenant-b",
    )

    customer_b = client.post(
        "/api/v1/customers/",
        headers=client.auth_headers(tenant_b),
        json={
            "name": "Schedule Customer B",
            "phone": "555-3300",
            "email": "schedule-b@example.com",
            "address": "3300 Tenant B Street",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_b),
        json={
            "customer_id": customer_b["id"],
            "title": "Schedule Tenant B Job",
            "description": "Private Tenant B job",
        },
    ).json()

    response = client.post(
        "/api/v1/schedules/",
        headers=client.auth_headers(tenant_a),
        json={
            "job_id": job_b["id"],
            "scheduled_start": "2026-09-01T09:00:00",
            "scheduled_end": "2026-09-01T11:00:00",
            "notes": "Cross tenant schedule",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_cross_tenant_schedule_read_is_hidden(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    tenant_a = create_tenant(
        db_session,
        "Schedule Read Tenant A",
        "schedule-read-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Schedule Read Tenant B",
        "schedule-read-tenant-b",
    )

    customer_b = client.post(
        "/api/v1/customers/",
        headers=client.auth_headers(tenant_b),
        json={
            "name": "Schedule Read Customer B",
            "phone": "555-3400",
            "email": "schedule-read-b@example.com",
            "address": "3400 Tenant B Street",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_b),
        json={
            "customer_id": customer_b["id"],
            "title": "Private Schedule Job",
            "description": "Private to Tenant B",
        },
    ).json()

    schedule_b = client.post(
        "/api/v1/schedules/",
        headers=client.auth_headers(tenant_b),
        json={
            "job_id": job_b["id"],
            "scheduled_start": "2026-09-02T09:00:00",
            "scheduled_end": "2026-09-02T11:00:00",
            "notes": "Tenant B Private Schedule",
        },
    ).json()

    response = client.get(
        f"/api/v1/schedules/{schedule_b['id']}",
        headers=client.auth_headers(tenant_a),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Schedule not found"


def test_schedule_lists_are_isolated_by_tenant(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    tenant_a = create_tenant(
        db_session,
        "Schedule List Tenant A",
        "schedule-list-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Schedule List Tenant B",
        "schedule-list-tenant-b",
    )

    customer_a = client.post(
        "/api/v1/customers/",
        headers=client.auth_headers(tenant_a),
        json={
            "name": "Schedule List Customer A",
            "phone": "555-3501",
            "email": "schedule-list-a@example.com",
            "address": "3501 Tenant A Street",
        },
    ).json()

    customer_b = client.post(
        "/api/v1/customers/",
        headers=client.auth_headers(tenant_b),
        json={
            "name": "Schedule List Customer B",
            "phone": "555-3502",
            "email": "schedule-list-b@example.com",
            "address": "3502 Tenant B Street",
        },
    ).json()

    job_a = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_a),
        json={
            "customer_id": customer_a["id"],
            "title": "Schedule List Job A",
            "description": "Tenant A",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_b),
        json={
            "customer_id": customer_b["id"],
            "title": "Schedule List Job B",
            "description": "Tenant B",
        },
    ).json()

    schedule_a = client.post(
        "/api/v1/schedules/",
        headers=client.auth_headers(tenant_a),
        json={
            "job_id": job_a["id"],
            "scheduled_start": "2026-09-03T09:00:00",
            "scheduled_end": "2026-09-03T11:00:00",
            "notes": "Schedule A",
        },
    ).json()

    schedule_b = client.post(
        "/api/v1/schedules/",
        headers=client.auth_headers(tenant_b),
        json={
            "job_id": job_b["id"],
            "scheduled_start": "2026-09-04T09:00:00",
            "scheduled_end": "2026-09-04T11:00:00",
            "notes": "Schedule B",
        },
    ).json()

    list_a = client.get(
        "/api/v1/schedules/",
        headers=client.auth_headers(tenant_a),
    )
    assert list_a.status_code == 200
    assert [item["id"] for item in list_a.json()] == [schedule_a["id"]]

    list_b = client.get(
        "/api/v1/schedules/",
        headers=client.auth_headers(tenant_b),
    )
    assert list_b.status_code == 200
    assert [item["id"] for item in list_b.json()] == [schedule_b["id"]]


def test_cross_tenant_schedule_update_is_hidden(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    tenant_a = create_tenant(
        db_session,
        "Schedule Update Tenant A",
        "schedule-update-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Schedule Update Tenant B",
        "schedule-update-tenant-b",
    )

    customer_b = client.post(
        "/api/v1/customers/",
        headers=client.auth_headers(tenant_b),
        json={
            "name": "Schedule Update Customer B",
            "phone": "555-3600",
            "email": "schedule-update-b@example.com",
            "address": "3600 Tenant B Street",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_b),
        json={
            "customer_id": customer_b["id"],
            "title": "Schedule Update Job B",
            "description": "Protected",
        },
    ).json()

    schedule_b = client.post(
        "/api/v1/schedules/",
        headers=client.auth_headers(tenant_b),
        json={
            "job_id": job_b["id"],
            "scheduled_start": "2026-09-05T09:00:00",
            "scheduled_end": "2026-09-05T11:00:00",
            "notes": "Protected Schedule",
        },
    ).json()

    response = client.put(
        f"/api/v1/schedules/{schedule_b['id']}",
        headers=client.auth_headers(tenant_a),
        json={
            "job_id": job_b["id"],
            "scheduled_start": "2026-09-05T13:00:00",
            "scheduled_end": "2026-09-05T15:00:00",
            "notes": "Hijacked Schedule",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Schedule not found"

    original = client.get(
        f"/api/v1/schedules/{schedule_b['id']}",
        headers=client.auth_headers(tenant_b),
    )
    assert original.status_code == 200
    assert original.json()["notes"] == "Protected Schedule"


def test_cross_tenant_schedule_delete_is_hidden(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    tenant_a = create_tenant(
        db_session,
        "Schedule Delete Tenant A",
        "schedule-delete-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Schedule Delete Tenant B",
        "schedule-delete-tenant-b",
    )

    customer_b = client.post(
        "/api/v1/customers/",
        headers=client.auth_headers(tenant_b),
        json={
            "name": "Schedule Delete Customer B",
            "phone": "555-3700",
            "email": "schedule-delete-b@example.com",
            "address": "3700 Tenant B Street",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_b),
        json={
            "customer_id": customer_b["id"],
            "title": "Schedule Delete Job B",
            "description": "Protected",
        },
    ).json()

    schedule_b = client.post(
        "/api/v1/schedules/",
        headers=client.auth_headers(tenant_b),
        json={
            "job_id": job_b["id"],
            "scheduled_start": "2026-09-06T09:00:00",
            "scheduled_end": "2026-09-06T11:00:00",
            "notes": "Undeletable Schedule",
        },
    ).json()

    response = client.delete(
        f"/api/v1/schedules/{schedule_b['id']}",
        headers=client.auth_headers(tenant_a),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Schedule not found"

    original = client.get(
        f"/api/v1/schedules/{schedule_b['id']}",
        headers=client.auth_headers(tenant_b),
    )
    assert original.status_code == 200


def test_cannot_create_invoice_for_another_tenants_job(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    tenant_a = create_tenant(
        db_session,
        "Invoice Tenant A",
        "invoice-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Invoice Tenant B",
        "invoice-tenant-b",
    )

    customer_b = client.post(
        "/api/v1/customers/",
        headers=client.auth_headers(tenant_b),
        json={
            "name": "Invoice Customer B",
            "phone": "555-3800",
            "email": "invoice-b@example.com",
            "address": "3800 Tenant B Street",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_b),
        json={
            "customer_id": customer_b["id"],
            "title": "Invoice Tenant B Job",
            "description": "Private Tenant B job",
        },
    ).json()

    response = client.post(
        "/api/v1/invoices/",
        headers=client.auth_headers(tenant_a),
        json={
            "job_id": job_b["id"],
            "description": "Cross Tenant Invoice",
            "amount": "800.00",
            "status": "draft",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_cross_tenant_invoice_read_is_hidden(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    tenant_a = create_tenant(
        db_session,
        "Invoice Read Tenant A",
        "invoice-read-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Invoice Read Tenant B",
        "invoice-read-tenant-b",
    )

    customer_b = client.post(
        "/api/v1/customers/",
        headers=client.auth_headers(tenant_b),
        json={
            "name": "Invoice Read Customer B",
            "phone": "555-3900",
            "email": "invoice-read-b@example.com",
            "address": "3900 Tenant B Street",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_b),
        json={
            "customer_id": customer_b["id"],
            "title": "Private Invoice Job",
            "description": "Private to Tenant B",
        },
    ).json()

    invoice_b = client.post(
        "/api/v1/invoices/",
        headers=client.auth_headers(tenant_b),
        json={
            "job_id": job_b["id"],
            "description": "Tenant B Private Invoice",
            "amount": "925.00",
            "status": "draft",
        },
    ).json()

    response = client.get(
        f"/api/v1/invoices/{invoice_b['id']}",
        headers=client.auth_headers(tenant_a),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Invoice not found"


def test_invoice_lists_are_isolated_by_tenant(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    tenant_a = create_tenant(
        db_session,
        "Invoice List Tenant A",
        "invoice-list-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Invoice List Tenant B",
        "invoice-list-tenant-b",
    )

    customer_a = client.post(
        "/api/v1/customers/",
        headers=client.auth_headers(tenant_a),
        json={
            "name": "Invoice List Customer A",
            "phone": "555-4001",
            "email": "invoice-list-a@example.com",
            "address": "4001 Tenant A Street",
        },
    ).json()

    customer_b = client.post(
        "/api/v1/customers/",
        headers=client.auth_headers(tenant_b),
        json={
            "name": "Invoice List Customer B",
            "phone": "555-4002",
            "email": "invoice-list-b@example.com",
            "address": "4002 Tenant B Street",
        },
    ).json()

    job_a = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_a),
        json={
            "customer_id": customer_a["id"],
            "title": "Invoice List Job A",
            "description": "Tenant A",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_b),
        json={
            "customer_id": customer_b["id"],
            "title": "Invoice List Job B",
            "description": "Tenant B",
        },
    ).json()

    invoice_a = client.post(
        "/api/v1/invoices/",
        headers=client.auth_headers(tenant_a),
        json={
            "job_id": job_a["id"],
            "description": "Invoice A",
            "amount": "600.00",
            "status": "draft",
        },
    ).json()

    invoice_b = client.post(
        "/api/v1/invoices/",
        headers=client.auth_headers(tenant_b),
        json={
            "job_id": job_b["id"],
            "description": "Invoice B",
            "amount": "700.00",
            "status": "draft",
        },
    ).json()

    list_a = client.get(
        "/api/v1/invoices/",
        headers=client.auth_headers(tenant_a),
    )
    assert list_a.status_code == 200
    assert [item["id"] for item in list_a.json()] == [invoice_a["id"]]

    list_b = client.get(
        "/api/v1/invoices/",
        headers=client.auth_headers(tenant_b),
    )
    assert list_b.status_code == 200
    assert [item["id"] for item in list_b.json()] == [invoice_b["id"]]


def test_cross_tenant_invoice_update_is_hidden(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    tenant_a = create_tenant(
        db_session,
        "Invoice Update Tenant A",
        "invoice-update-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Invoice Update Tenant B",
        "invoice-update-tenant-b",
    )

    customer_b = client.post(
        "/api/v1/customers/",
        headers=client.auth_headers(tenant_b),
        json={
            "name": "Invoice Update Customer B",
            "phone": "555-4100",
            "email": "invoice-update-b@example.com",
            "address": "4100 Tenant B Street",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_b),
        json={
            "customer_id": customer_b["id"],
            "title": "Invoice Update Job B",
            "description": "Protected",
        },
    ).json()

    invoice_b = client.post(
        "/api/v1/invoices/",
        headers=client.auth_headers(tenant_b),
        json={
            "job_id": job_b["id"],
            "description": "Protected Invoice",
            "amount": "800.00",
            "status": "draft",
        },
    ).json()

    response = client.put(
        f"/api/v1/invoices/{invoice_b['id']}",
        headers=client.auth_headers(tenant_a),
        json={
            "job_id": job_b["id"],
            "description": "Hijacked Invoice",
            "amount": "999.00",
            "status": "sent",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Invoice not found"

    original = client.get(
        f"/api/v1/invoices/{invoice_b['id']}",
        headers=client.auth_headers(tenant_b),
    )

    assert original.status_code == 200
    assert original.json()["description"] == "Protected Invoice"
    assert original.json()["amount"] == "800.00"
    assert original.json()["status"] == "draft"


def test_cross_tenant_invoice_delete_is_hidden(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    tenant_a = create_tenant(
        db_session,
        "Invoice Delete Tenant A",
        "invoice-delete-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Invoice Delete Tenant B",
        "invoice-delete-tenant-b",
    )

    customer_b = client.post(
        "/api/v1/customers/",
        headers=client.auth_headers(tenant_b),
        json={
            "name": "Invoice Delete Customer B",
            "phone": "555-4200",
            "email": "invoice-delete-b@example.com",
            "address": "4200 Tenant B Street",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_b),
        json={
            "customer_id": customer_b["id"],
            "title": "Invoice Delete Job B",
            "description": "Protected",
        },
    ).json()

    invoice_b = client.post(
        "/api/v1/invoices/",
        headers=client.auth_headers(tenant_b),
        json={
            "job_id": job_b["id"],
            "description": "Undeletable Invoice",
            "amount": "850.00",
            "status": "draft",
        },
    ).json()

    response = client.delete(
        f"/api/v1/invoices/{invoice_b['id']}",
        headers=client.auth_headers(tenant_a),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Invoice not found"

    original = client.get(
        f"/api/v1/invoices/{invoice_b['id']}",
        headers=client.auth_headers(tenant_b),
    )

    assert original.status_code == 200


def test_cannot_create_payment_for_another_tenants_invoice(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    tenant_a = create_tenant(
        db_session,
        "Payment Tenant A",
        "payment-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Payment Tenant B",
        "payment-tenant-b",
    )

    customer_b = client.post(
        "/api/v1/customers/",
        headers=client.auth_headers(tenant_b),
        json={
            "name": "Payment Customer B",
            "phone": "555-4300",
            "email": "payment-b@example.com",
            "address": "4300 Tenant B Street",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_b),
        json={
            "customer_id": customer_b["id"],
            "title": "Payment Tenant B Job",
            "description": "Private Tenant B job",
        },
    ).json()

    invoice_b = client.post(
        "/api/v1/invoices/",
        headers=client.auth_headers(tenant_b),
        json={
            "job_id": job_b["id"],
            "description": "Private Tenant B Invoice",
            "amount": "1000.00",
            "status": "draft",
        },
    ).json()

    response = client.post(
        "/api/v1/payments/",
        headers=client.auth_headers(tenant_a),
        json={
            "invoice_id": invoice_b["id"],
            "amount": "500.00",
            "method": "card",
            "reference": "CROSS-TENANT-001",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Invoice not found"


def test_cross_tenant_payment_read_is_hidden(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    tenant_a = create_tenant(
        db_session,
        "Payment Read Tenant A",
        "payment-read-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Payment Read Tenant B",
        "payment-read-tenant-b",
    )

    customer_b = client.post(
        "/api/v1/customers/",
        headers=client.auth_headers(tenant_b),
        json={
            "name": "Payment Read Customer B",
            "phone": "555-4400",
            "email": "payment-read-b@example.com",
            "address": "4400 Tenant B Street",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_b),
        json={
            "customer_id": customer_b["id"],
            "title": "Payment Read Job B",
            "description": "Private",
        },
    ).json()

    invoice_b = client.post(
        "/api/v1/invoices/",
        headers=client.auth_headers(tenant_b),
        json={
            "job_id": job_b["id"],
            "description": "Payment Read Invoice",
            "amount": "1100.00",
            "status": "draft",
        },
    ).json()

    payment_b = client.post(
        "/api/v1/payments/",
        headers=client.auth_headers(tenant_b),
        json={
            "invoice_id": invoice_b["id"],
            "amount": "400.00",
            "method": "card",
            "reference": "PAYMENT-READ-001",
        },
    ).json()

    response = client.get(
        f"/api/v1/payments/{payment_b['id']}",
        headers=client.auth_headers(tenant_a),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found"


def test_payment_lists_are_isolated_by_tenant(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    tenant_a = create_tenant(
        db_session,
        "Payment List Tenant A",
        "payment-list-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Payment List Tenant B",
        "payment-list-tenant-b",
    )

    customer_a = client.post(
        "/api/v1/customers/",
        headers=client.auth_headers(tenant_a),
        json={
            "name": "Payment List Customer A",
            "phone": "555-4501",
            "email": "payment-list-a@example.com",
            "address": "4501 Tenant A Street",
        },
    ).json()

    customer_b = client.post(
        "/api/v1/customers/",
        headers=client.auth_headers(tenant_b),
        json={
            "name": "Payment List Customer B",
            "phone": "555-4502",
            "email": "payment-list-b@example.com",
            "address": "4502 Tenant B Street",
        },
    ).json()

    job_a = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_a),
        json={
            "customer_id": customer_a["id"],
            "title": "Payment List Job A",
            "description": "Tenant A",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_b),
        json={
            "customer_id": customer_b["id"],
            "title": "Payment List Job B",
            "description": "Tenant B",
        },
    ).json()

    invoice_a = client.post(
        "/api/v1/invoices/",
        headers=client.auth_headers(tenant_a),
        json={
            "job_id": job_a["id"],
            "description": "Invoice A",
            "amount": "900.00",
            "status": "draft",
        },
    ).json()

    invoice_b = client.post(
        "/api/v1/invoices/",
        headers=client.auth_headers(tenant_b),
        json={
            "job_id": job_b["id"],
            "description": "Invoice B",
            "amount": "1000.00",
            "status": "draft",
        },
    ).json()

    payment_a = client.post(
        "/api/v1/payments/",
        headers=client.auth_headers(tenant_a),
        json={
            "invoice_id": invoice_a["id"],
            "amount": "300.00",
            "method": "card",
            "reference": "LIST-A-001",
        },
    ).json()

    payment_b = client.post(
        "/api/v1/payments/",
        headers=client.auth_headers(tenant_b),
        json={
            "invoice_id": invoice_b["id"],
            "amount": "400.00",
            "method": "card",
            "reference": "LIST-B-001",
        },
    ).json()

    response_a = client.get(
        "/api/v1/payments/",
        headers=client.auth_headers(tenant_a),
    )

    assert response_a.status_code == 200
    assert [item["id"] for item in response_a.json()] == [payment_a["id"]]

    response_b = client.get(
        "/api/v1/payments/",
        headers=client.auth_headers(tenant_b),
    )

    assert response_b.status_code == 200
    assert [item["id"] for item in response_b.json()] == [payment_b["id"]]


def test_cross_tenant_payment_update_is_hidden(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    tenant_a = create_tenant(
        db_session,
        "Payment Update Tenant A",
        "payment-update-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Payment Update Tenant B",
        "payment-update-tenant-b",
    )

    customer_b = client.post(
        "/api/v1/customers/",
        headers=client.auth_headers(tenant_b),
        json={
            "name": "Payment Update Customer B",
            "phone": "555-4600",
            "email": "payment-update-b@example.com",
            "address": "4600 Tenant B Street",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_b),
        json={
            "customer_id": customer_b["id"],
            "title": "Payment Update Job B",
            "description": "Protected",
        },
    ).json()

    invoice_b = client.post(
        "/api/v1/invoices/",
        headers=client.auth_headers(tenant_b),
        json={
            "job_id": job_b["id"],
            "description": "Protected Invoice",
            "amount": "1200.00",
            "status": "draft",
        },
    ).json()

    payment_b = client.post(
        "/api/v1/payments/",
        headers=client.auth_headers(tenant_b),
        json={
            "invoice_id": invoice_b["id"],
            "amount": "300.00",
            "method": "card",
            "reference": "UPDATE-B-001",
        },
    ).json()

    response = client.put(
        f"/api/v1/payments/{payment_b['id']}",
        headers=client.auth_headers(tenant_a),
        json={
            "invoice_id": invoice_b["id"],
            "amount": "500.00",
            "method": "cash",
            "reference": "HIJACKED",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found"

    original = client.get(
        f"/api/v1/payments/{payment_b['id']}",
        headers=client.auth_headers(tenant_b),
    )

    assert original.status_code == 200
    assert original.json()["amount"] == "300.00"
    assert original.json()["method"] == "card"
    assert original.json()["reference"] == "UPDATE-B-001"


def test_cross_tenant_payment_delete_is_hidden(
    authenticated_client,
    db_session,
):
    client = authenticated_client

    tenant_a = create_tenant(
        db_session,
        "Payment Delete Tenant A",
        "payment-delete-tenant-a",
    )
    tenant_b = create_tenant(
        db_session,
        "Payment Delete Tenant B",
        "payment-delete-tenant-b",
    )

    customer_b = client.post(
        "/api/v1/customers/",
        headers=client.auth_headers(tenant_b),
        json={
            "name": "Payment Delete Customer B",
            "phone": "555-4700",
            "email": "payment-delete-b@example.com",
            "address": "4700 Tenant B Street",
        },
    ).json()

    job_b = client.post(
        "/api/v1/jobs/",
        headers=client.auth_headers(tenant_b),
        json={
            "customer_id": customer_b["id"],
            "title": "Payment Delete Job B",
            "description": "Protected",
        },
    ).json()

    invoice_b = client.post(
        "/api/v1/invoices/",
        headers=client.auth_headers(tenant_b),
        json={
            "job_id": job_b["id"],
            "description": "Protected Invoice",
            "amount": "1300.00",
            "status": "draft",
        },
    ).json()

    payment_b = client.post(
        "/api/v1/payments/",
        headers=client.auth_headers(tenant_b),
        json={
            "invoice_id": invoice_b["id"],
            "amount": "350.00",
            "method": "card",
            "reference": "DELETE-B-001",
        },
    ).json()

    response = client.delete(
        f"/api/v1/payments/{payment_b['id']}",
        headers=client.auth_headers(tenant_a),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found"

    original = client.get(
        f"/api/v1/payments/{payment_b['id']}",
        headers=client.auth_headers(tenant_b),
    )

    assert original.status_code == 200


def test_tenant_header_alone_does_not_prove_membership(
    raw_client,
    db_session,
):
    tenant_a = create_tenant(
        db_session,
        "Authorization Tenant A",
        "authorization-tenant-a",
    )

    tenant_b = create_tenant(
        db_session,
        "Authorization Tenant B",
        "authorization-tenant-b",
    )

    response = raw_client.get(
        "/api/v1/customers/",
        headers={
            "X-Tenant-ID": str(tenant_b.id),
        },
    )

    # A tenant header alone does not authenticate the caller.
    # Authentication is required before tenant membership can be checked.
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_suspended_tenant_cannot_access_tenant_api(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        "Suspended Tenant",
        "suspended-tenant",
    )

    tenant.status = "suspended"
    db_session.commit()

    response = authenticated_client.get(
        "/api/v1/customers/",
        headers=authenticated_client.auth_headers(
            tenant
        ),
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "Tenant is suspended"
    )


def test_reactivated_tenant_can_access_tenant_api(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        "Reactivated Tenant",
        "reactivated-tenant",
    )

    tenant.status = "suspended"
    db_session.commit()

    blocked = authenticated_client.get(
        "/api/v1/customers/",
        headers=authenticated_client.auth_headers(
            tenant
        ),
    )

    assert blocked.status_code == 403

    tenant.status = "active"
    tenant.suspended_at = None
    db_session.commit()

    response = authenticated_client.get(
        "/api/v1/customers/",
        headers=authenticated_client.auth_headers(
            tenant
        ),
    )

    assert response.status_code == 200
