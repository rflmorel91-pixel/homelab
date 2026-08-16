def create_customer(client):
    response = client.post(
        "/api/v1/customers/",
        json={
            "name": "Payment Test Customer",
            "phone": "555-0500",
            "email": "payment@example.com",
            "address": "500 Payment Street",
        },
    )

    assert response.status_code == 201
    return response.json()


def create_job(client, customer_id):
    response = client.post(
        "/api/v1/jobs/",
        json={
            "customer_id": customer_id,
            "title": "Payment Test Job",
            "description": "Job for payment testing",
            "status": "customer_requested",
        },
    )

    assert response.status_code == 201
    return response.json()


def create_invoice(client, job_id):
    response = client.post(
        "/api/v1/invoices/",
        json={
            "job_id": job_id,
            "description": "Payment Test Invoice",
            "amount": "1200.00",
            "status": "draft",
        },
    )

    assert response.status_code == 201
    return response.json()


def test_create_payment(client):
    customer = create_customer(client)
    job = create_job(client, customer["id"])
    invoice = create_invoice(client, job["id"])

    response = client.post(
        "/api/v1/payments/",
        json={
            "invoice_id": invoice["id"],
            "amount": "1200.00",
            "method": "card",
            "reference": "PAY-001",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["invoice_id"] == invoice["id"]
    assert data["amount"] == "1200.00"
    assert data["method"] == "card"
    assert data["reference"] == "PAY-001"
    assert "id" in data
    assert "created_at" in data


def test_payment_crud(client):
    customer = create_customer(client)
    job = create_job(client, customer["id"])
    invoice = create_invoice(client, job["id"])

    create_response = client.post(
        "/api/v1/payments/",
        json={
            "invoice_id": invoice["id"],
            "amount": "500.00",
            "method": "cash",
            "reference": "CASH-001",
        },
    )

    assert create_response.status_code == 201

    payment_id = create_response.json()["id"]

    get_response = client.get(
        f"/api/v1/payments/{payment_id}"
    )

    assert get_response.status_code == 200
    assert get_response.json()["amount"] == "500.00"

    update_response = client.put(
        f"/api/v1/payments/{payment_id}",
        json={
            "invoice_id": invoice["id"],
            "amount": "600.00",
            "method": "bank_transfer",
            "reference": "BANK-002",
        },
    )

    assert update_response.status_code == 200

    updated = update_response.json()

    assert updated["amount"] == "600.00"
    assert updated["method"] == "bank_transfer"
    assert updated["reference"] == "BANK-002"

    list_response = client.get("/api/v1/payments/")

    assert list_response.status_code == 200
    assert any(
        payment["id"] == payment_id
        for payment in list_response.json()
    )

    delete_response = client.delete(
        f"/api/v1/payments/{payment_id}"
    )

    assert delete_response.status_code == 204

    get_deleted_response = client.get(
        f"/api/v1/payments/{payment_id}"
    )

    assert get_deleted_response.status_code == 404


def test_create_payment_requires_existing_invoice(client):
    response = client.post(
        "/api/v1/payments/",
        json={
            "invoice_id": 999999,
            "amount": "100.00",
            "method": "cash",
            "reference": None,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Invoice not found"


def test_create_payment_rejects_invalid_method(client):
    customer = create_customer(client)
    job = create_job(client, customer["id"])
    invoice = create_invoice(client, job["id"])

    response = client.post(
        "/api/v1/payments/",
        json={
            "invoice_id": invoice["id"],
            "amount": "100.00",
            "method": "crypto",
            "reference": "INVALID-001",
        },
    )

    assert response.status_code == 422
