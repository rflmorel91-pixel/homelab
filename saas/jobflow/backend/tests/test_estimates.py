def create_customer(client):
    response = client.post(
        "/api/v1/customers/",
        json={
            "name": "Estimate Test Customer",
            "phone": "555-0300",
            "email": "estimate@example.com",
            "address": "300 Estimate Street",
        },
    )

    assert response.status_code == 201
    return response.json()


def create_job(client, customer_id):
    response = client.post(
        "/api/v1/jobs/",
        json={
            "customer_id": customer_id,
            "title": "Estimate Test Job",
            "description": "Job for estimate testing",
            "status": "customer_requested",
        },
    )

    assert response.status_code == 201
    return response.json()


def test_create_estimate(client):
    customer = create_customer(client)
    job = create_job(client, customer["id"])

    response = client.post(
        "/api/v1/estimates/",
        json={
            "job_id": job["id"],
            "description": "Initial estimate",
            "amount": "1250.00",
            "status": "draft",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["job_id"] == job["id"]
    assert data["description"] == "Initial estimate"
    assert data["amount"] == "1250.00"
    assert data["status"] == "draft"
    assert "id" in data
    assert "created_at" in data


def test_estimate_crud(client):
    customer = create_customer(client)
    job = create_job(client, customer["id"])

    create_response = client.post(
        "/api/v1/estimates/",
        json={
            "job_id": job["id"],
            "description": "CRUD estimate",
            "amount": "2500.00",
            "status": "draft",
        },
    )

    assert create_response.status_code == 201

    estimate_id = create_response.json()["id"]

    get_response = client.get(
        f"/api/v1/estimates/{estimate_id}"
    )

    assert get_response.status_code == 200
    assert get_response.json()["amount"] == "2500.00"

    send_response = client.put(
        f"/api/v1/estimates/{estimate_id}",
        json={
            "job_id": job["id"],
            "description": "Updated estimate",
            "amount": "2750.00",
            "status": "sent",
        },
    )

    assert send_response.status_code == 200

    update_response = client.put(
        f"/api/v1/estimates/{estimate_id}",
        json={
            "job_id": job["id"],
            "description": "Updated estimate",
            "amount": "2750.00",
            "status": "approved",
        },
    )

    assert update_response.status_code == 200

    updated = update_response.json()

    assert updated["description"] == "Updated estimate"
    assert updated["amount"] == "2750.00"
    assert updated["status"] == "approved"

    list_response = client.get("/api/v1/estimates/")

    assert list_response.status_code == 200
    assert any(
        estimate["id"] == estimate_id
        for estimate in list_response.json()
    )

    delete_response = client.delete(
        f"/api/v1/estimates/{estimate_id}"
    )

    assert delete_response.status_code == 409
    assert delete_response.json()["detail"] == (
        "Cannot delete terminal estimate"
    )

    get_after_delete = client.get(
        f"/api/v1/estimates/{estimate_id}"
    )

    assert get_after_delete.status_code == 200

def test_create_estimate_requires_existing_job(client):
    response = client.post(
        "/api/v1/estimates/",
        json={
            "job_id": 999999,
            "description": "Invalid estimate",
            "amount": "100.00",
            "status": "draft",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_create_estimate_rejects_invalid_status(client):
    response = client.post(
        "/api/v1/estimates/",
        json={
            "job_id": 1,
            "description": "Invalid status estimate",
            "amount": 100.00,
            "status": "not_a_real_status",
        },
    )

    assert response.status_code == 422


def test_estimate_rejects_invalid_status_transition(client):
    customer = create_customer(client)
    job = create_job(client, customer["id"])

    create_response = client.post(
        "/api/v1/estimates/",
        json={
            "job_id": job["id"],
            "description": "Transition test estimate",
            "amount": "500.00",
            "status": "draft",
        },
    )

    assert create_response.status_code == 201
    estimate = create_response.json()

    response = client.put(
        f"/api/v1/estimates/{estimate['id']}",
        json={
            "job_id": job["id"],
            "description": "Transition test estimate",
            "amount": "500.00",
            "status": "approved",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid estimate status transition: "
        "draft -> approved"
    )


def test_estimate_status_declined_progression(client):
    customer = create_customer(client)
    job = create_job(client, customer["id"])

    create_response = client.post(
        "/api/v1/estimates/",
        json={
            "job_id": job["id"],
            "description": "Declined estimate",
            "amount": "750.00",
        },
    )

    assert create_response.status_code == 201
    estimate = create_response.json()

    send_response = client.put(
        f"/api/v1/estimates/{estimate['id']}",
        json={
            "job_id": job["id"],
            "description": "Declined estimate",
            "amount": "750.00",
            "status": "sent",
        },
    )

    assert send_response.status_code == 200
    assert send_response.json()["status"] == "sent"

    decline_response = client.put(
        f"/api/v1/estimates/{estimate['id']}",
        json={
            "job_id": job["id"],
            "description": "Declined estimate",
            "amount": "750.00",
            "status": "declined",
        },
    )

    assert decline_response.status_code == 200
    assert decline_response.json()["status"] == "declined"


def test_approving_estimate_automatically_approves_quoted_job(client):
    customer = create_customer(client)
    job = create_job(client, customer["id"])

    quoted_job_response = client.put(
        f"/api/v1/jobs/{job['id']}",
        json={
            "customer_id": customer["id"],
            "title": job["title"],
            "description": job["description"],
            "status": "quoted",
        },
    )

    assert quoted_job_response.status_code == 200
    assert quoted_job_response.json()["status"] == "quoted"

    create_response = client.post(
        "/api/v1/estimates/",
        json={
            "job_id": job["id"],
            "description": "Auto approval estimate",
            "amount": "600.00",
            "status": "draft",
        },
    )

    assert create_response.status_code == 201
    estimate = create_response.json()

    sent_response = client.put(
        f"/api/v1/estimates/{estimate['id']}",
        json={
            "job_id": job["id"],
            "description": "Auto approval estimate",
            "amount": "600.00",
            "status": "sent",
        },
    )

    assert sent_response.status_code == 200
    assert sent_response.json()["status"] == "sent"

    approved_response = client.put(
        f"/api/v1/estimates/{estimate['id']}",
        json={
            "job_id": job["id"],
            "description": "Auto approval estimate",
            "amount": "600.00",
            "status": "approved",
        },
    )

    assert approved_response.status_code == 200
    assert approved_response.json()["status"] == "approved"

    job_response = client.get(
        f"/api/v1/jobs/{job['id']}"
    )

    assert job_response.status_code == 200
    assert job_response.json()["status"] == "approved"


def test_cannot_move_estimate_to_different_job(client):
    customer = create_customer(client)

    job1 = create_job(client, customer["id"])
    job2 = create_job(client, customer["id"])

    estimate_response = client.post(
        "/api/v1/estimates/",
        json={
            "job_id": job1["id"],
            "description": "Immovable estimate",
            "amount": "750.00",
            "status": "draft",
        },
    )

    assert estimate_response.status_code == 201
    estimate = estimate_response.json()

    move_response = client.put(
        f"/api/v1/estimates/{estimate['id']}",
        json={
            "job_id": job2["id"],
            "description": "Immovable estimate",
            "amount": "750.00",
            "status": "draft",
        },
    )

    assert move_response.status_code == 409
    assert move_response.json()["detail"] == (
        "Estimate cannot be moved to a different job"
    )

    estimate_after = client.get(
        f"/api/v1/estimates/{estimate['id']}"
    )

    assert estimate_after.status_code == 200
    assert estimate_after.json()["job_id"] == job1["id"]


def test_cannot_delete_approved_estimate(client):
    customer = create_customer(client)
    job = create_job(client, customer["id"])

    quoted_response = client.put(
        f"/api/v1/jobs/{job['id']}",
        json={
            "customer_id": customer["id"],
            "title": job["title"],
            "description": job["description"],
            "status": "quoted",
        },
    )

    assert quoted_response.status_code == 200

    estimate_response = client.post(
        "/api/v1/estimates/",
        json={
            "job_id": job["id"],
            "description": "Protected approved estimate",
            "amount": "900.00",
            "status": "draft",
        },
    )

    assert estimate_response.status_code == 201
    estimate = estimate_response.json()

    sent_response = client.put(
        f"/api/v1/estimates/{estimate['id']}",
        json={
            "job_id": job["id"],
            "description": "Protected approved estimate",
            "amount": "900.00",
            "status": "sent",
        },
    )

    assert sent_response.status_code == 200

    approved_response = client.put(
        f"/api/v1/estimates/{estimate['id']}",
        json={
            "job_id": job["id"],
            "description": "Protected approved estimate",
            "amount": "900.00",
            "status": "approved",
        },
    )

    assert approved_response.status_code == 200

    delete_response = client.delete(
        f"/api/v1/estimates/{estimate['id']}"
    )

    assert delete_response.status_code == 409
    assert delete_response.json()["detail"] == (
        "Cannot delete terminal estimate"
    )

    estimate_after = client.get(
        f"/api/v1/estimates/{estimate['id']}"
    )

    assert estimate_after.status_code == 200
    assert estimate_after.json()["status"] == "approved"



def test_delete_draft_estimate(client):
    customer = create_customer(client)
    job = create_job(client, customer["id"])

    create_response = client.post(
        "/api/v1/estimates/",
        json={
            "job_id": job["id"],
            "description": "Deletable draft estimate",
            "amount": "400.00",
            "status": "draft",
        },
    )

    assert create_response.status_code == 201
    estimate = create_response.json()

    delete_response = client.delete(
        f"/api/v1/estimates/{estimate['id']}"
    )

    assert delete_response.status_code == 204

    get_response = client.get(
        f"/api/v1/estimates/{estimate['id']}"
    )

    assert get_response.status_code == 404
