from sqlalchemy import select

from app.models import Product
from app.platform import get_product


def test_permitpulse_was_discovered():
    product = get_product("permitpulse")

    assert product is not None
    assert product.name == "PermitPulse"
    assert product.version == "0.1.0"
    assert product.workspace_key == "permitpulse"
    assert (
        product.api_prefix
        == "/api/v1/products/permitpulse"
    )


def test_permitpulse_router_was_composed(
    raw_client,
):
    response = raw_client.get(
        "/api/v1/products/permitpulse/status"
    )

    assert response.status_code == 200
    assert response.json() == {
        "product": "permitpulse",
        "status": "available",
    }


def test_permitpulse_synchronizes_to_database(
    raw_client,
    db_session,
):
    # Entering raw_client runs application lifespan,
    # including installed-product synchronization.
    response = raw_client.get(
        "/api/v1/products/permitpulse/status"
    )
    assert response.status_code == 200

    product = db_session.scalar(
        select(Product).where(
            Product.slug == "permitpulse"
        )
    )

    assert product is not None
    assert product.name == "PermitPulse"
    assert product.workspace_key == "permitpulse"
    assert product.status == "active"


def test_permitpulse_inherits_lifecycle_enforcement(
    raw_client,
    db_session,
):
    product = db_session.scalar(
        select(Product).where(
            Product.slug == "permitpulse"
        )
    )

    assert product is not None

    product.status = "suspended"
    db_session.commit()

    response = raw_client.get(
        "/api/v1/products/permitpulse/status"
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Product is suspended"
    )
