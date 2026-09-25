from sqlalchemy import select

from app.models import Product
from app.platform import get_product


def test_prestamodesk_is_discovered():
    definition = get_product("prestamodesk")

    assert definition is not None
    assert definition.name == "PréstamoDesk"
    assert definition.workspace_key == "prestamodesk"
    assert definition.landing_route == "/prestamodesk"
    assert definition.workspace_route == "/prestamodesk/app"


def test_prestamodesk_router_is_composed(
    raw_client,
):
    response = raw_client.get(
        "/api/v1/products/prestamodesk/status"
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["product"] == "prestamodesk"
    assert payload["name"] == "PréstamoDesk"
    assert payload["status"] == "available"
    assert payload["currency"] == "DOP"
    assert payload["language"] == "es"


def test_prestamodesk_synchronizes_to_database(
    raw_client,
    db_session,
):
    response = raw_client.get(
        "/api/v1/products/prestamodesk/status"
    )
    assert response.status_code == 200

    product = db_session.scalar(
        select(Product).where(
            Product.slug == "prestamodesk"
        )
    )

    assert product is not None
    assert product.name == "PréstamoDesk"
    assert product.status == "active"


def test_prestamodesk_inherits_lifecycle(
    raw_client,
    db_session,
):
    product = db_session.scalar(
        select(Product).where(
            Product.slug == "prestamodesk"
        )
    )

    assert product is not None

    product.status = "suspended"
    db_session.commit()

    response = raw_client.get(
        "/api/v1/products/prestamodesk/status"
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Product is suspended"
    )
