from sqlalchemy import select

from app.models import Product
from app.platform import get_product


def test_assettrack_is_discovered():
    definition = get_product("assettrack")

    assert definition is not None
    assert definition.name == "AssetTrack"
    assert definition.workspace_key == "assettrack"


def test_assettrack_router_is_composed(
    raw_client,
):
    response = raw_client.get(
        "/api/v1/products/assettrack/status"
    )

    assert response.status_code == 200
    assert response.json() == {
        "product": "assettrack",
        "status": "available",
    }


def test_assettrack_synchronizes_to_database(
    raw_client,
    db_session,
):
    response = raw_client.get(
        "/api/v1/products/assettrack/status"
    )
    assert response.status_code == 200

    product = db_session.scalar(
        select(Product).where(
            Product.slug == "assettrack"
        )
    )

    assert product is not None
    assert product.name == "AssetTrack"
    assert product.status == "active"


def test_assettrack_inherits_lifecycle(
    raw_client,
    db_session,
):
    product = db_session.scalar(
        select(Product).where(
            Product.slug == "assettrack"
        )
    )

    assert product is not None

    product.status = "suspended"
    db_session.commit()

    response = raw_client.get(
        "/api/v1/products/assettrack/status"
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Product is suspended"
    )
