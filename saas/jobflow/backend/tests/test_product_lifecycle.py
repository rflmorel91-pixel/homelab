from sqlalchemy import select

from app.models import Product


def get_proofvault(db_session):
    product = db_session.scalar(
        select(Product).where(
            Product.slug == "proofvault"
        )
    )

    assert product is not None
    return product


def test_active_product_api_is_available(
    raw_client,
    db_session,
):
    product = get_proofvault(db_session)
    assert product.status == "active"

    response = raw_client.get(
        "/api/v1/products/proofvault/status"
    )

    assert response.status_code == 200
    assert response.json() == {
        "product": "proofvault",
        "status": "available",
    }


def test_suspended_product_api_is_blocked(
    raw_client,
    db_session,
):
    product = get_proofvault(db_session)

    product.status = "suspended"
    db_session.commit()

    response = raw_client.get(
        "/api/v1/products/proofvault/status"
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Product is suspended"
    )


def test_inactive_product_api_is_blocked(
    raw_client,
    db_session,
):
    product = get_proofvault(db_session)

    product.status = "inactive"
    db_session.commit()

    response = raw_client.get(
        "/api/v1/products/proofvault/status"
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Product is inactive"
    )


def test_platform_health_survives_product_suspension(
    raw_client,
    db_session,
):
    product = get_proofvault(db_session)

    product.status = "suspended"
    db_session.commit()

    response = raw_client.get(
        "/api/v1/health"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_admin_api_survives_product_suspension(
    client,
    db_session,
):
    product = get_proofvault(db_session)
    product.status = "suspended"

    from app.models import User

    user = db_session.scalar(
        select(User).where(
            User.email
            == "default-test-user@example.com"
        )
    )

    assert user is not None
    user.is_platform_admin = True
    db_session.commit()

    response = client.get(
        "/api/v1/admin/overview"
    )

    assert response.status_code == 200

    proofvault = next(
        item
        for item in response.json()["products"]
        if item["slug"] == "proofvault"
    )

    assert proofvault["status"] == "suspended"
