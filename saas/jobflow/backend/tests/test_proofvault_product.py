def test_proofvault_router_is_registered(raw_client):
    response = raw_client.get(
        "/api/v1/products/proofvault/status"
    )

    assert response.status_code == 200
    assert response.json() == {
        "product": "proofvault",
        "status": "available",
    }


def test_jobflow_routes_still_coexist(raw_client):
    response = raw_client.get(
        "/api/v1/customers/"
    )

    # Route exists. Authentication is expected to reject
    # an unauthenticated request before workspace access.
    assert response.status_code == 401
