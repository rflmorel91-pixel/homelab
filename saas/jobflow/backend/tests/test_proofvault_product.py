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


def test_startup_synchronizes_installed_products(
    raw_client,
    db_session,
):
    # Entering raw_client runs the application lifespan.
    response = raw_client.get(
        "/api/v1/products/proofvault/status"
    )
    assert response.status_code == 200

    from sqlalchemy import select
    from app.models import Product

    products = db_session.scalars(
        select(Product).order_by(Product.slug)
    ).all()

    by_slug = {
        product.slug: product
        for product in products
    }

    assert "jobflow" in by_slug
    assert "proofvault" in by_slug

    assert (
        by_slug["proofvault"].workspace_key
        == "proofvault"
    )
