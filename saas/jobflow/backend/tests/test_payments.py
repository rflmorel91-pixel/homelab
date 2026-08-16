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


def test_full_payment_automatically_pays_invoice_and_job(client):
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

    invoice_response = client.post(
        "/api/v1/invoices/",
        json={
            "job_id": job["id"],
            "description": "Automatic payment invoice",
            "amount": "1000.00",
            "status": "draft",
        },
    )

    assert invoice_response.status_code == 201
    invoice = invoice_response.json()

    sent_response = client.put(
        f"/api/v1/invoices/{invoice['id']}",
        json={
            "job_id": job["id"],
            "description": "Automatic payment invoice",
            "amount": "1000.00",
            "status": "sent",
        },
    )

    assert sent_response.status_code == 200

    job_response = client.get(
        f"/api/v1/jobs/{job['id']}"
    )

    assert job_response.status_code == 200
    assert job_response.json()["status"] == "invoiced"

    partial_response = client.post(
        "/api/v1/payments/",
        json={
            "invoice_id": invoice["id"],
            "amount": "400.00",
            "method": "card",
            "reference": "PARTIAL-001",
        },
    )

    assert partial_response.status_code == 201

    invoice_after_partial = client.get(
        f"/api/v1/invoices/{invoice['id']}"
    )

    job_after_partial = client.get(
        f"/api/v1/jobs/{job['id']}"
    )

    assert invoice_after_partial.status_code == 200
    assert invoice_after_partial.json()["status"] == "sent"
    assert job_after_partial.status_code == 200
    assert job_after_partial.json()["status"] == "invoiced"

    final_payment_response = client.post(
        "/api/v1/payments/",
        json={
            "invoice_id": invoice["id"],
            "amount": "600.00",
            "method": "card",
            "reference": "FINAL-001",
        },
    )

    assert final_payment_response.status_code == 201

    final_invoice = client.get(
        f"/api/v1/invoices/{invoice['id']}"
    )

    final_job = client.get(
        f"/api/v1/jobs/{job['id']}"
    )

    assert final_invoice.status_code == 200
    assert final_invoice.json()["status"] == "paid"
    assert final_job.status_code == 200
    assert final_job.json()["status"] == "paid"


def test_payment_rejects_overpayment(client):
    customer = create_customer(client)
    job = create_job(client, customer["id"])
    invoice = create_invoice(client, job["id"])

    first_payment = client.post(
        "/api/v1/payments/",
        json={
            "invoice_id": invoice["id"],
            "amount": "1000.00",
            "method": "card",
            "reference": "OVERPAY-001",
        },
    )

    assert first_payment.status_code == 201

    overpayment = client.post(
        "/api/v1/payments/",
        json={
            "invoice_id": invoice["id"],
            "amount": "300.00",
            "method": "card",
            "reference": "OVERPAY-002",
        },
    )

    assert overpayment.status_code == 400
    assert overpayment.json()["detail"] == (
        "Payment exceeds remaining invoice balance"
    )

    payments_response = client.get("/api/v1/payments/")

    assert payments_response.status_code == 200

    invoice_payments = [
        payment
        for payment in payments_response.json()
        if payment["invoice_id"] == invoice["id"]
    ]

    assert len(invoice_payments) == 1
    assert invoice_payments[0]["amount"] == "1000.00"


def create_payable_invoice(client, amount="1000.00"):
    customer = create_customer(client)
    job = create_job(client, customer["id"])

    for status in [
        "quoted",
        "approved",
        "scheduled",
        "in_progress",
        "completed",
    ]:
        response = client.put(
            f"/api/v1/jobs/{job['id']}",
            json={
                "customer_id": customer["id"],
                "title": job["title"],
                "description": job["description"],
                "status": status,
            },
        )
        assert response.status_code == 200

    invoice_response = client.post(
        "/api/v1/invoices/",
        json={
            "job_id": job["id"],
            "description": "Payment mutation invoice",
            "amount": amount,
            "status": "draft",
        },
    )
    assert invoice_response.status_code == 201
    invoice = invoice_response.json()

    sent_response = client.put(
        f"/api/v1/invoices/{invoice['id']}",
        json={
            "job_id": job["id"],
            "description": "Payment mutation invoice",
            "amount": amount,
            "status": "sent",
        },
    )
    assert sent_response.status_code == 200

    return job, invoice


def test_reducing_payment_reopens_paid_invoice_and_job(client):
    job, invoice = create_payable_invoice(client)

    payment_response = client.post(
        "/api/v1/payments/",
        json={
            "invoice_id": invoice["id"],
            "amount": "1000.00",
            "method": "card",
            "reference": "REDUCE-001",
        },
    )
    assert payment_response.status_code == 201
    payment = payment_response.json()

    assert client.get(
        f"/api/v1/invoices/{invoice['id']}"
    ).json()["status"] == "paid"

    assert client.get(
        f"/api/v1/jobs/{job['id']}"
    ).json()["status"] == "paid"

    update_response = client.put(
        f"/api/v1/payments/{payment['id']}",
        json={
            "invoice_id": invoice["id"],
            "amount": "600.00",
            "method": "card",
            "reference": "REDUCE-002",
        },
    )

    assert update_response.status_code == 200

    assert client.get(
        f"/api/v1/invoices/{invoice['id']}"
    ).json()["status"] == "sent"

    assert client.get(
        f"/api/v1/jobs/{job['id']}"
    ).json()["status"] == "invoiced"


def test_deleting_payment_reopens_paid_invoice_and_job(client):
    job, invoice = create_payable_invoice(client)

    payment_response = client.post(
        "/api/v1/payments/",
        json={
            "invoice_id": invoice["id"],
            "amount": "1000.00",
            "method": "card",
            "reference": "DELETE-001",
        },
    )
    assert payment_response.status_code == 201
    payment = payment_response.json()

    delete_response = client.delete(
        f"/api/v1/payments/{payment['id']}"
    )

    assert delete_response.status_code == 204

    assert client.get(
        f"/api/v1/invoices/{invoice['id']}"
    ).json()["status"] == "sent"

    assert client.get(
        f"/api/v1/jobs/{job['id']}"
    ).json()["status"] == "invoiced"


def test_updating_payment_rejects_overpayment(client):
    _, invoice = create_payable_invoice(client)

    first_response = client.post(
        "/api/v1/payments/",
        json={
            "invoice_id": invoice["id"],
            "amount": "400.00",
            "method": "card",
            "reference": "UPDATE-OVERPAY-001",
        },
    )
    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/payments/",
        json={
            "invoice_id": invoice["id"],
            "amount": "500.00",
            "method": "card",
            "reference": "UPDATE-OVERPAY-002",
        },
    )
    assert second_response.status_code == 201
    second_payment = second_response.json()

    update_response = client.put(
        f"/api/v1/payments/{second_payment['id']}",
        json={
            "invoice_id": invoice["id"],
            "amount": "700.00",
            "method": "card",
            "reference": "UPDATE-OVERPAY-003",
        },
    )

    assert update_response.status_code == 400
    assert update_response.json()["detail"] == (
        "Payment exceeds remaining invoice balance"
    )

    unchanged = client.get(
        f"/api/v1/payments/{second_payment['id']}"
    )

    assert unchanged.status_code == 200
    assert unchanged.json()["amount"] == "500.00"
