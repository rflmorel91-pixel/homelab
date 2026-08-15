def test_create_customer(client):
    response = client.post(
        "/api/v1/customers/",
        json={
            "name": "Test Customer",
            "phone": "555-0100",
            "email": "test@example.com",
            "address": "123 Test Street",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] > 0
    assert data["name"] == "Test Customer"
    assert data["phone"] == "555-0100"
    assert data["email"] == "test@example.com"
    assert data["address"] == "123 Test Street"
    assert "created_at" in data


def test_customer_crud(client):
    create_response = client.post(
        "/api/v1/customers/",
        json={
            "name": "CRUD Customer",
            "phone": "555-0200",
            "email": "crud@example.com",
            "address": "100 CRUD Street",
        },
    )

    assert create_response.status_code == 201

    customer_id = create_response.json()["id"]

    get_response = client.get(
        f"/api/v1/customers/{customer_id}"
    )

    assert get_response.status_code == 200
    assert get_response.json()["name"] == "CRUD Customer"

    list_response = client.get("/api/v1/customers/")

    assert list_response.status_code == 200
    assert any(
        customer["id"] == customer_id
        for customer in list_response.json()
    )

    update_response = client.put(
        f"/api/v1/customers/{customer_id}",
        json={
            "name": "Updated CRUD Customer",
            "phone": "555-0299",
            "email": "updated-crud@example.com",
            "address": "200 Updated Street",
        },
    )

    assert update_response.status_code == 200

    updated_data = update_response.json()

    assert updated_data["name"] == "Updated CRUD Customer"
    assert updated_data["phone"] == "555-0299"
    assert updated_data["email"] == "updated-crud@example.com"
    assert updated_data["address"] == "200 Updated Street"

    delete_response = client.delete(
        f"/api/v1/customers/{customer_id}"
    )

    assert delete_response.status_code == 204

    missing_response = client.get(
        f"/api/v1/customers/{customer_id}"
    )

    assert missing_response.status_code == 404
    assert missing_response.json() == {
        "detail": "Customer not found"
    }
