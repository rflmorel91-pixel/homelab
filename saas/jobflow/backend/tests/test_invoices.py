def create_customer(client):
    response = client.post(
        "/api/v1/customers/",
        json={
            "name": "Invoice Test Customer",
            "phone": "555-0400",
            "email": "invoice@example.com",
            "address": "400 Invoice Street",
        },
    )

    assert response.status_code == 201
    return response.json()


def create_job(client, customer_id):
    response = client.post(
        "/api/v1/jobs/",
        json={
            "customer_id": customer_id,
            "title": "Invoice Test Job",
            "description": "Job for invoice testing",
            "status": "customer_requested",
        },
    )

    assert response.status_code == 201
    return response.json()


def test_create_invoice(client):
    customer = create_customer(client)
    job = create_job(client, customer["id"])

    response = client.post(
        "/api/v1/invoices/",
        json={
            "job_id": job["id"],
            "description": "Initial invoice",
            "amount": "1500.00",
            "status": "draft",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["job_id"] == job["id"]
    assert data["description"] == "Initial invoice"
    assert data["amount"] == "1500.00"
    assert data["status"] == "draft"
    assert "id" in data
    assert "created_at" in data


def test_invoice_crud(client):
    customer = create_customer(client)
    job = create_job(client, customer["id"])

    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "job_id": job["id"],
            "description": "CRUD invoice",
            "amount": "2000.00",
            "status": "draft",
        },
    )

    assert create_response.status_code == 201

    invoice_id = create_response.json()["id"]

    get_response = client.get(
        f"/api/v1/invoices/{invoice_id}"
    )

    assert get_response.status_code == 200
    assert get_response.json()["amount"] == "2000.00"

    send_response = client.put(
        f"/api/v1/invoices/{invoice_id}",
        json={
            "job_id": job["id"],
            "description": "Updated invoice",
            "amount": "2250.00",
            "status": "sent",
        },
    )

    assert send_response.status_code == 200
    assert send_response.json()["status"] == "sent"

    paid_response = client.put(
        f"/api/v1/invoices/{invoice_id}",
        json={
            "job_id": job["id"],
            "description": "Updated invoice",
            "amount": "2250.00",
            "status": "paid",
        },
    )

    assert paid_response.status_code == 200

    updated = paid_response.json()

    assert updated["description"] == "Updated invoice"
    assert updated["amount"] == "2250.00"
    assert updated["status"] == "paid"

    list_response = client.get("/api/v1/invoices/")

    assert list_response.status_code == 200
    assert any(
        invoice["id"] == invoice_id
        for invoice in list_response.json()
    )

    delete_response = client.delete(
        f"/api/v1/invoices/{invoice_id}"
    )

    assert delete_response.status_code == 204

    get_deleted_response = client.get(
        f"/api/v1/invoices/{invoice_id}"
    )

    assert get_deleted_response.status_code == 404


def test_create_invoice_requires_existing_job(client):
    response = client.post(
        "/api/v1/invoices/",
        json={
            "job_id": 999999,
            "description": "Invalid invoice",
            "amount": "100.00",
            "status": "draft",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_create_invoice_rejects_invalid_status(client):
    response = client.post(
        "/api/v1/invoices/",
        json={
            "job_id": 1,
            "description": "Invalid status invoice",
            "amount": "100.00",
            "status": "not_a_real_status",
        },
    )

    assert response.status_code == 422


def test_invoice_rejects_invalid_status_transition(client):
    customer = create_customer(client)
    job = create_job(client, customer["id"])

    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "job_id": job["id"],
            "description": "Transition test invoice",
            "amount": "500.00",
            "status": "draft",
        },
    )

    assert create_response.status_code == 201
    invoice = create_response.json()

    response = client.put(
        f"/api/v1/invoices/{invoice['id']}",
        json={
            "job_id": job["id"],
            "description": "Transition test invoice",
            "amount": "500.00",
            "status": "paid",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid invoice status transition: "
        "draft -> paid"
    )


def test_invoice_status_progression(client):
    customer = create_customer(client)
    job = create_job(client, customer["id"])

    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "job_id": job["id"],
            "description": "Lifecycle invoice",
            "amount": "900.00",
        },
    )

    assert create_response.status_code == 201
    invoice = create_response.json()

    send_response = client.put(
        f"/api/v1/invoices/{invoice['id']}",
        json={
            "job_id": job["id"],
            "description": "Lifecycle invoice",
            "amount": "900.00",
            "status": "sent",
        },
    )

    assert send_response.status_code == 200
    assert send_response.json()["status"] == "sent"

    paid_response = client.put(
        f"/api/v1/invoices/{invoice['id']}",
        json={
            "job_id": job["id"],
            "description": "Lifecycle invoice",
            "amount": "900.00",
            "status": "paid",
        },
    )

    assert paid_response.status_code == 200
    assert paid_response.json()["status"] == "paid"


def test_sending_invoice_automatically_invoices_completed_job(client):
    customer = create_customer(client)
    job = create_job(client, customer["id"])

    statuses = [
        "quoted",
        "approved",
        "scheduled",
        "in_progress",
        "completed",
    ]

    current_job = job

    for status in statuses:
        response = client.put(
            f"/api/v1/jobs/{job['id']}",
            json={
                "customer_id": customer["id"],
                "title": current_job["title"],
                "description": current_job["description"],
                "status": status,
            },
        )

        assert response.status_code == 200
        current_job = response.json()

    assert current_job["status"] == "completed"

    invoice_response = client.post(
        "/api/v1/invoices/",
        json={
            "job_id": job["id"],
            "description": "Automatic invoice test",
            "amount": "700.00",
            "status": "draft",
        },
    )

    assert invoice_response.status_code == 201
    invoice = invoice_response.json()

    sent_response = client.put(
        f"/api/v1/invoices/{invoice['id']}",
        json={
            "job_id": job["id"],
            "description": "Automatic invoice test",
            "amount": "700.00",
            "status": "sent",
        },
    )

    assert sent_response.status_code == 200
    assert sent_response.json()["status"] == "sent"

    job_response = client.get(
        f"/api/v1/jobs/{job['id']}"
    )

    assert job_response.status_code == 200
    assert job_response.json()["status"] == "invoiced"


def test_cannot_delete_invoice_with_payments(client):
    customer = create_customer(client)
    job = create_job(client, customer["id"])

    invoice_response = client.post(
        "/api/v1/invoices/",
        json={
            "job_id": job["id"],
            "description": "Protected invoice",
            "amount": "500.00",
            "status": "draft",
        },
    )

    assert invoice_response.status_code == 201
    invoice = invoice_response.json()

    payment_response = client.post(
        "/api/v1/payments/",
        json={
            "invoice_id": invoice["id"],
            "amount": "100.00",
            "method": "card",
            "reference": "PROTECTED-001",
        },
    )

    assert payment_response.status_code == 201

    delete_response = client.delete(
        f"/api/v1/invoices/{invoice['id']}"
    )

    assert delete_response.status_code == 409
    assert delete_response.json()["detail"] == (
        "Cannot delete invoice with existing payments"
    )

    invoice_after = client.get(
        f"/api/v1/invoices/{invoice['id']}"
    )

    assert invoice_after.status_code == 200


def test_cannot_move_invoice_to_different_job(client):
    customer = create_customer(client)

    job1 = create_job(client, customer["id"])
    job2 = create_job(client, customer["id"])

    invoice_response = client.post(
        "/api/v1/invoices/",
        json={
            "job_id": job1["id"],
            "description": "Immovable invoice",
            "amount": "750.00",
            "status": "draft",
        },
    )

    assert invoice_response.status_code == 201
    invoice = invoice_response.json()

    move_response = client.put(
        f"/api/v1/invoices/{invoice['id']}",
        json={
            "job_id": job2["id"],
            "description": "Immovable invoice",
            "amount": "750.00",
            "status": "draft",
        },
    )

    assert move_response.status_code == 409
    assert move_response.json()["detail"] == (
        "Invoice cannot be moved to a different job"
    )

    invoice_after = client.get(
        f"/api/v1/invoices/{invoice['id']}"
    )

    assert invoice_after.status_code == 200
    assert invoice_after.json()["job_id"] == job1["id"]
