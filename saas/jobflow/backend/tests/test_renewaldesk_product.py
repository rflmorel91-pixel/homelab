from sqlalchemy import select

from app.models import Product
from app.platform import get_product


def test_renewaldesk_is_discovered():
    definition = get_product("renewaldesk")

    assert definition is not None
    assert definition.name == "RenewalDesk"
    assert definition.workspace_key == "renewaldesk"


def test_renewaldesk_router_is_composed(
    raw_client,
):
    response = raw_client.get(
        "/api/v1/products/renewaldesk/status"
    )

    assert response.status_code == 200
    assert response.json() == {
        "product": "renewaldesk",
        "status": "available",
    }


def test_renewaldesk_synchronizes_to_database(
    raw_client,
    db_session,
):
    response = raw_client.get(
        "/api/v1/products/renewaldesk/status"
    )
    assert response.status_code == 200

    product = db_session.scalar(
        select(Product).where(
            Product.slug == "renewaldesk"
        )
    )

    assert product is not None
    assert product.name == "RenewalDesk"
    assert product.status == "active"


def test_renewaldesk_inherits_lifecycle(
    raw_client,
    db_session,
):
    product = db_session.scalar(
        select(Product).where(
            Product.slug == "renewaldesk"
        )
    )

    assert product is not None

    product.status = "suspended"
    db_session.commit()

    response = raw_client.get(
        "/api/v1/products/renewaldesk/status"
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Product is suspended"
    )
