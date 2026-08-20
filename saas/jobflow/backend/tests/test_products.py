import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Product


def test_create_product(db_session):
    product = Product(
        name="Test Product",
        slug="test-product",
        status="active",
        workspace_key="test-product",
    )

    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    stored = db_session.scalar(
        select(Product).where(
            Product.slug == "test-product"
        )
    )

    assert stored is not None
    assert stored.id == product.id
    assert stored.name == "Test Product"
    assert stored.status == "active"
    assert stored.workspace_key == "test-product"


def test_product_slug_must_be_unique(db_session):
    db_session.add(
        Product(
            name="Product One",
            slug="shared-product",
            status="active",
            workspace_key="workspace-one",
        )
    )
    db_session.commit()

    db_session.add(
        Product(
            name="Product Two",
            slug="shared-product",
            status="active",
            workspace_key="workspace-two",
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_product_workspace_key_must_be_unique(db_session):
    db_session.add(
        Product(
            name="Product One",
            slug="product-one",
            status="active",
            workspace_key="shared-workspace",
        )
    )
    db_session.commit()

    db_session.add(
        Product(
            name="Product Two",
            slug="product-two",
            status="active",
            workspace_key="shared-workspace",
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()
