def test_complete_jobflow_workflow(client):
    customer_response = client.post(
        "/api/v1/customers/",
        json={
            "name": "Workflow Test Customer",
            "phone": "555-0800",
            "email": "workflow@example.com",
            "address": "800 Workflow Street",
        },
    )

    assert customer_response.status_code == 201
    customer = customer_response.json()

    job_response = client.post(
        "/api/v1/jobs/",
        json={
            "customer_id": customer["id"],
            "title": "Workflow Test Job",
            "description": "Complete automated JobFlow workflow",
            "status": "customer_requested",
        },
    )

    assert job_response.status_code == 201
    job = job_response.json()

    job_id = job["id"]

    quoted_response = client.put(
        f"/api/v1/jobs/{job_id}",
        json={
            "customer_id": customer["id"],
            "title": "Workflow Test Job",
            "description": "Complete automated JobFlow workflow",
            "status": "quoted",
        },
    )

    assert quoted_response.status_code == 200
    assert quoted_response.json()["status"] == "quoted"

    estimate_response = client.post(
        "/api/v1/estimates/",
        json={
            "job_id": job_id,
            "description": "Workflow Test Estimate",
            "amount": "1250.00",
            "status": "draft",
        },
    )

    assert estimate_response.status_code == 201
    estimate = estimate_response.json()

    sent_estimate_response = client.put(
        f"/api/v1/estimates/{estimate['id']}",
        json={
            "job_id": job_id,
            "description": "Workflow Test Estimate",
            "amount": "1250.00",
            "status": "sent",
        },
    )

    assert sent_estimate_response.status_code == 200
    assert sent_estimate_response.json()["status"] == "sent"

    approved_estimate_response = client.put(
        f"/api/v1/estimates/{estimate['id']}",
        json={
            "job_id": job_id,
            "description": "Workflow Test Estimate",
            "amount": "1250.00",
            "status": "approved",
        },
    )

    assert approved_estimate_response.status_code == 200
    assert approved_estimate_response.json()["status"] == "approved"

    approved_job_response = client.get(
        f"/api/v1/jobs/{job_id}"
    )

    assert approved_job_response.status_code == 200
    assert approved_job_response.json()["status"] == "approved"

    schedule_response = client.post(
        "/api/v1/schedules/",
        json={
            "job_id": job_id,
            "scheduled_start": "2026-08-24T09:00:00",
            "scheduled_end": "2026-08-24T12:00:00",
            "notes": "Workflow Test Schedule",
        },
    )

    assert schedule_response.status_code == 201

    scheduled_job_response = client.get(
        f"/api/v1/jobs/{job_id}"
    )

    assert scheduled_job_response.status_code == 200
    assert scheduled_job_response.json()["status"] == "scheduled"

    in_progress_response = client.put(
        f"/api/v1/jobs/{job_id}",
        json={
            "customer_id": customer["id"],
            "title": "Workflow Test Job",
            "description": "Complete automated JobFlow workflow",
            "status": "in_progress",
        },
    )

    assert in_progress_response.status_code == 200
    assert in_progress_response.json()["status"] == "in_progress"

    completed_response = client.put(
        f"/api/v1/jobs/{job_id}",
        json={
            "customer_id": customer["id"],
            "title": "Workflow Test Job",
            "description": "Complete automated JobFlow workflow",
            "status": "completed",
        },
    )

    assert completed_response.status_code == 200
    assert completed_response.json()["status"] == "completed"

    invoice_response = client.post(
        "/api/v1/invoices/",
        json={
            "job_id": job_id,
            "description": "Workflow Test Invoice",
            "amount": "1250.00",
            "status": "draft",
        },
    )

    assert invoice_response.status_code == 201
    invoice = invoice_response.json()

    sent_invoice_response = client.put(
        f"/api/v1/invoices/{invoice['id']}",
        json={
            "job_id": job_id,
            "description": "Workflow Test Invoice",
            "amount": "1250.00",
            "status": "sent",
        },
    )

    assert sent_invoice_response.status_code == 200
    assert sent_invoice_response.json()["status"] == "sent"

    invoiced_job_response = client.get(
        f"/api/v1/jobs/{job_id}"
    )

    assert invoiced_job_response.status_code == 200
    assert invoiced_job_response.json()["status"] == "invoiced"

    payment_response = client.post(
        "/api/v1/payments/",
        json={
            "invoice_id": invoice["id"],
            "amount": "1250.00",
            "method": "card",
            "reference": "WORKFLOW-PAY-001",
        },
    )

    assert payment_response.status_code == 201
    payment = payment_response.json()

    assert payment["amount"] == "1250.00"
    assert payment["method"] == "card"

    paid_invoice_response = client.put(
        f"/api/v1/invoices/{invoice['id']}",
        json={
            "job_id": job_id,
            "description": "Workflow Test Invoice",
            "amount": "1250.00",
            "status": "paid",
        },
    )

    assert paid_invoice_response.status_code == 200
    assert paid_invoice_response.json()["status"] == "paid"

    paid_job_response = client.put(
        f"/api/v1/jobs/{job_id}",
        json={
            "customer_id": customer["id"],
            "title": "Workflow Test Job",
            "description": "Complete automated JobFlow workflow",
            "status": "paid",
        },
    )

    assert paid_job_response.status_code == 200
    assert paid_job_response.json()["status"] == "paid"

    final_job = client.get(
        f"/api/v1/jobs/{job_id}"
    )

    final_estimate = client.get(
        f"/api/v1/estimates/{estimate['id']}"
    )

    final_invoice = client.get(
        f"/api/v1/invoices/{invoice['id']}"
    )

    final_payment = client.get(
        f"/api/v1/payments/{payment['id']}"
    )

    assert final_job.status_code == 200
    assert final_estimate.status_code == 200
    assert final_invoice.status_code == 200
    assert final_payment.status_code == 200

    assert final_job.json()["status"] == "paid"
    assert final_estimate.json()["status"] == "approved"
    assert final_invoice.json()["status"] == "paid"
    assert final_payment.json()["amount"] == "1250.00"
