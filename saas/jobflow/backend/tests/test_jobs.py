def test_create_job(client):
    customer_response = client.post(
        "/api/v1/customers/",
        json={
            "name": "Job Test Customer",
            "phone": "555-0300",
            "email": "job@example.com",
            "address": "100 Job Street",
        },
    )

    assert customer_response.status_code == 201

    customer = customer_response.json()

    response = client.post(
        "/api/v1/jobs/",
        json={
            "customer_id": customer["id"],
            "title": "Install New Equipment",
            "description": "Install and configure new equipment.",
        },
    )

    assert response.status_code == 201

    job = response.json()

    assert job["customer_id"] == customer["id"]
    assert job["title"] == "Install New Equipment"
    assert job["description"] == "Install and configure new equipment."
    assert job["status"] == "customer_requested"
    assert "id" in job
    assert "created_at" in job


def test_job_crud(client):
    customer_response = client.post(
        "/api/v1/customers/",
        json={
            "name": "CRUD Job Customer",
            "phone": "555-0400",
            "email": "crudjob@example.com",
            "address": "200 CRUD Job Street",
        },
    )

    assert customer_response.status_code == 201

    customer = customer_response.json()

    create_response = client.post(
        "/api/v1/jobs/",
        json={
            "customer_id": customer["id"],
            "title": "Initial Job",
            "description": "Initial description",
        },
    )

    assert create_response.status_code == 201

    job = create_response.json()
    job_id = job["id"]

    get_response = client.get(
        f"/api/v1/jobs/{job_id}"
    )

    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Initial Job"

    update_response = client.put(
        f"/api/v1/jobs/{job_id}",
        json={
            "customer_id": customer["id"],
            "title": "Updated Job",
            "description": "Updated description",
            "status": "quoted",
        },
    )

    assert update_response.status_code == 200

    updated_job = update_response.json()

    assert updated_job["title"] == "Updated Job"
    assert updated_job["description"] == "Updated description"
    assert updated_job["status"] == "quoted"

    list_response = client.get(
        "/api/v1/jobs/"
    )

    assert list_response.status_code == 200
    assert any(
        item["id"] == job_id
        for item in list_response.json()
    )

    delete_response = client.delete(
        f"/api/v1/jobs/{job_id}"
    )

    assert delete_response.status_code == 204

    missing_response = client.get(
        f"/api/v1/jobs/{job_id}"
    )

    assert missing_response.status_code == 404


def test_create_job_requires_existing_customer(client):
    response = client.post(
        "/api/v1/jobs/",
        json={
            "customer_id": 999999,
            "title": "Invalid Job",
            "description": "This should fail.",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"


def test_create_job_rejects_invalid_status(client):
    response = client.post(
        "/api/v1/jobs/",
        json={
            "customer_id": 1,
            "title": "Invalid Status Job",
            "description": "Should be rejected",
            "status": "not_a_real_status",
        },
    )

    assert response.status_code == 422


def test_job_rejects_invalid_status_transition(client):
    customer_response = client.post(
        "/api/v1/customers/",
        json={
            "name": "Transition Test Customer",
            "phone": "555-0500",
            "email": "transition@example.com",
            "address": "400 Transition Street",
        },
    )

    assert customer_response.status_code == 201
    customer = customer_response.json()

    create_response = client.post(
        "/api/v1/jobs/",
        json={
            "customer_id": customer["id"],
            "title": "Transition Test Job",
            "description": "Job transition testing",
        },
    )

    assert create_response.status_code == 201
    job = create_response.json()

    response = client.put(
        f"/api/v1/jobs/{job['id']}",
        json={
            "customer_id": customer["id"],
            "title": "Transition Test Job",
            "description": "Job transition testing",
            "status": "scheduled",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid job status transition: "
        "customer_requested -> scheduled"
    )


def test_job_status_progression(client):
    customer_response = client.post(
        "/api/v1/customers/",
        json={
            "name": "Status Progression Customer",
            "phone": "555-0600",
            "email": "progression@example.com",
            "address": "500 Progression Street",
        },
    )

    assert customer_response.status_code == 201
    customer = customer_response.json()

    create_response = client.post(
        "/api/v1/jobs/",
        json={
            "customer_id": customer["id"],
            "title": "Status Progression Job",
            "description": "Testing the complete job lifecycle.",
        },
    )

    assert create_response.status_code == 201
    job = create_response.json()

    statuses = [
        "quoted",
        "approved",
        "scheduled",
        "in_progress",
        "completed",
        "invoiced",
        "paid",
    ]

    for status in statuses:
        response = client.put(
            f"/api/v1/jobs/{job['id']}",
            json={
                "customer_id": customer["id"],
                "title": "Status Progression Job",
                "description": "Testing the complete job lifecycle.",
                "status": status,
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == status
