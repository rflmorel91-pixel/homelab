def create_customer(client):
    response = client.post(
        "/api/v1/customers/",
        json={
            "name": "Schedule Test Customer",
            "phone": "555-0600",
            "email": "schedule@example.com",
            "address": "600 Schedule Street",
        },
    )

    assert response.status_code == 201
    return response.json()


def create_job(client, customer_id):
    response = client.post(
        "/api/v1/jobs/",
        json={
            "customer_id": customer_id,
            "title": "Schedule Test Job",
            "description": "Job for schedule testing",
            "status": "customer_requested",
        },
    )

    assert response.status_code == 201
    return response.json()


def test_create_schedule(client):
    customer = create_customer(client)
    job = create_job(client, customer["id"])

    response = client.post(
        "/api/v1/schedules/",
        json={
            "job_id": job["id"],
            "scheduled_start": "2026-08-20T09:00:00",
            "scheduled_end": "2026-08-20T11:00:00",
            "notes": "Morning appointment",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["job_id"] == job["id"]
    assert data["scheduled_start"] == "2026-08-20T09:00:00"
    assert data["scheduled_end"] == "2026-08-20T11:00:00"
    assert data["notes"] == "Morning appointment"
    assert "id" in data
    assert "created_at" in data


def test_schedule_crud(client):
    customer = create_customer(client)
    job = create_job(client, customer["id"])

    create_response = client.post(
        "/api/v1/schedules/",
        json={
            "job_id": job["id"],
            "scheduled_start": "2026-08-21T10:00:00",
            "scheduled_end": "2026-08-21T12:00:00",
            "notes": "Initial schedule",
        },
    )

    assert create_response.status_code == 201

    schedule_id = create_response.json()["id"]

    get_response = client.get(
        f"/api/v1/schedules/{schedule_id}"
    )

    assert get_response.status_code == 200

    update_response = client.put(
        f"/api/v1/schedules/{schedule_id}",
        json={
            "job_id": job["id"],
            "scheduled_start": "2026-08-21T13:00:00",
            "scheduled_end": "2026-08-21T15:00:00",
            "notes": "Updated schedule",
        },
    )

    assert update_response.status_code == 200

    updated = update_response.json()

    assert updated["scheduled_start"] == "2026-08-21T13:00:00"
    assert updated["scheduled_end"] == "2026-08-21T15:00:00"
    assert updated["notes"] == "Updated schedule"

    list_response = client.get("/api/v1/schedules/")

    assert list_response.status_code == 200
    assert any(
        schedule["id"] == schedule_id
        for schedule in list_response.json()
    )

    delete_response = client.delete(
        f"/api/v1/schedules/{schedule_id}"
    )

    assert delete_response.status_code == 204

    get_deleted_response = client.get(
        f"/api/v1/schedules/{schedule_id}"
    )

    assert get_deleted_response.status_code == 404


def test_create_schedule_requires_existing_job(client):
    response = client.post(
        "/api/v1/schedules/",
        json={
            "job_id": 999999,
            "scheduled_start": "2026-08-22T09:00:00",
            "scheduled_end": "2026-08-22T10:00:00",
            "notes": "Invalid job",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_schedule_rejects_end_before_start(client):
    customer = create_customer(client)
    job = create_job(client, customer["id"])

    response = client.post(
        "/api/v1/schedules/",
        json={
            "job_id": job["id"],
            "scheduled_start": "2026-08-23T15:00:00",
            "scheduled_end": "2026-08-23T14:00:00",
            "notes": "Invalid time range",
        },
    )

    assert response.status_code == 422


def test_creating_schedule_automatically_schedules_approved_job(client):
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

    approved_response = client.put(
        f"/api/v1/jobs/{job['id']}",
        json={
            "customer_id": customer["id"],
            "title": job["title"],
            "description": job["description"],
            "status": "approved",
        },
    )

    assert approved_response.status_code == 200
    assert approved_response.json()["status"] == "approved"

    schedule_response = client.post(
        "/api/v1/schedules/",
        json={
            "job_id": job["id"],
            "scheduled_start": "2026-08-25T09:00:00",
            "scheduled_end": "2026-08-25T11:00:00",
            "notes": "Automatic scheduling test",
        },
    )

    assert schedule_response.status_code == 201

    job_response = client.get(
        f"/api/v1/jobs/{job['id']}"
    )

    assert job_response.status_code == 200
    assert job_response.json()["status"] == "scheduled"


def test_cannot_move_schedule_to_different_job(client):
    customer = create_customer(client)

    job1 = create_job(client, customer["id"])
    job2 = create_job(client, customer["id"])

    schedule_response = client.post(
        "/api/v1/schedules/",
        json={
            "job_id": job1["id"],
            "scheduled_start": "2026-08-26T09:00:00",
            "scheduled_end": "2026-08-26T11:00:00",
            "notes": "Immovable schedule",
        },
    )

    assert schedule_response.status_code == 201
    schedule = schedule_response.json()

    move_response = client.put(
        f"/api/v1/schedules/{schedule['id']}",
        json={
            "job_id": job2["id"],
            "scheduled_start": "2026-08-26T09:00:00",
            "scheduled_end": "2026-08-26T11:00:00",
            "notes": "Immovable schedule",
        },
    )

    assert move_response.status_code == 409
    assert move_response.json()["detail"] == (
        "Schedule cannot be moved to a different job"
    )

    schedule_after = client.get(
        f"/api/v1/schedules/{schedule['id']}"
    )

    assert schedule_after.status_code == 200
    assert schedule_after.json()["job_id"] == job1["id"]


def test_deleting_last_schedule_reopens_scheduled_job(client):
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

    approved_response = client.put(
        f"/api/v1/jobs/{job['id']}",
        json={
            "customer_id": customer["id"],
            "title": job["title"],
            "description": job["description"],
            "status": "approved",
        },
    )
    assert approved_response.status_code == 200

    schedule_response = client.post(
        "/api/v1/schedules/",
        json={
            "job_id": job["id"],
            "scheduled_start": "2026-08-27T09:00:00",
            "scheduled_end": "2026-08-27T11:00:00",
            "notes": "Schedule deletion lifecycle test",
        },
    )

    assert schedule_response.status_code == 201
    schedule = schedule_response.json()

    scheduled_job = client.get(
        f"/api/v1/jobs/{job['id']}"
    )

    assert scheduled_job.status_code == 200
    assert scheduled_job.json()["status"] == "scheduled"

    delete_response = client.delete(
        f"/api/v1/schedules/{schedule['id']}"
    )

    assert delete_response.status_code == 204

    job_after = client.get(
        f"/api/v1/jobs/{job['id']}"
    )

    assert job_after.status_code == 200
    assert job_after.json()["status"] == "approved"


def test_deleting_schedule_does_not_rewind_in_progress_job(client):
    customer = create_customer(client)
    job = create_job(client, customer["id"])

    for status in ["quoted", "approved"]:
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

    schedule_response = client.post(
        "/api/v1/schedules/",
        json={
            "job_id": job["id"],
            "scheduled_start": "2026-08-28T09:00:00",
            "scheduled_end": "2026-08-28T11:00:00",
            "notes": "In-progress deletion test",
        },
    )
    assert schedule_response.status_code == 201
    schedule = schedule_response.json()

    start_response = client.put(
        f"/api/v1/jobs/{job['id']}",
        json={
            "customer_id": customer["id"],
            "title": job["title"],
            "description": job["description"],
            "status": "in_progress",
        },
    )
    assert start_response.status_code == 200

    delete_response = client.delete(
        f"/api/v1/schedules/{schedule['id']}"
    )
    assert delete_response.status_code == 204

    job_after = client.get(
        f"/api/v1/jobs/{job['id']}"
    )

    assert job_after.status_code == 200
    assert job_after.json()["status"] == "in_progress"


def test_deleting_one_of_multiple_schedules_keeps_job_scheduled(client):
    customer = create_customer(client)
    job = create_job(client, customer["id"])

    for status in ["quoted", "approved"]:
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

    first_schedule = client.post(
        "/api/v1/schedules/",
        json={
            "job_id": job["id"],
            "scheduled_start": "2026-08-29T09:00:00",
            "scheduled_end": "2026-08-29T11:00:00",
            "notes": "First schedule",
        },
    )
    assert first_schedule.status_code == 201

    second_schedule = client.post(
        "/api/v1/schedules/",
        json={
            "job_id": job["id"],
            "scheduled_start": "2026-08-30T09:00:00",
            "scheduled_end": "2026-08-30T11:00:00",
            "notes": "Second schedule",
        },
    )
    assert second_schedule.status_code == 201

    delete_response = client.delete(
        f"/api/v1/schedules/{first_schedule.json()['id']}"
    )
    assert delete_response.status_code == 204

    job_after = client.get(
        f"/api/v1/jobs/{job['id']}"
    )

    assert job_after.status_code == 200
    assert job_after.json()["status"] == "scheduled"
