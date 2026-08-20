import pytest
from sqlalchemy import select

from app.models import Product
from app.platform import (
    PLATFORM_CONTRACT_VERSION,
    ProductDefinition,
    ProductSyncError,
    synchronize_products,
)


def make_definition(
    *,
    slug="sync-product",
    name="Sync Product",
    workspace_key="sync-product",
):
    return ProductDefinition(
        slug=slug,
        name=name,
        version="1.0.0",
        platform_contract_version=(
            PLATFORM_CONTRACT_VERSION
        ),
        workspace_key=workspace_key,
        landing_route=f"/{slug}",
        workspace_route=f"/{slug}/app",
        api_prefix=f"/api/v1/products/{slug}",
    )


def test_sync_creates_missing_product(db_session):
    definition = make_definition()

    synchronized = synchronize_products(
        db_session,
        (definition,),
    )

    assert len(synchronized) == 1

    product = db_session.scalar(
        select(Product).where(
            Product.slug == "sync-product"
        )
    )

    assert product is not None
    assert product.name == "Sync Product"
    assert product.workspace_key == "sync-product"
    assert product.status == "active"


def test_sync_is_idempotent(db_session):
    definition = make_definition()

    synchronize_products(
        db_session,
        (definition,),
    )

    first = db_session.scalar(
        select(Product).where(
            Product.slug == definition.slug
        )
    )

    assert first is not None
    first_id = first.id

    synchronize_products(
        db_session,
        (definition,),
    )

    products = db_session.scalars(
        select(Product).where(
            Product.slug == definition.slug
        )
    ).all()

    assert len(products) == 1
    assert products[0].id == first_id


def test_sync_updates_developer_metadata(db_session):
    definition = make_definition()

    synchronize_products(
        db_session,
        (definition,),
    )

    updated = make_definition(
        name="Renamed Product",
        workspace_key="renamed-workspace",
    )

    synchronize_products(
        db_session,
        (updated,),
    )

    product = db_session.scalar(
        select(Product).where(
            Product.slug == "sync-product"
        )
    )

    assert product is not None
    assert product.name == "Renamed Product"
    assert product.workspace_key == "renamed-workspace"


def test_sync_preserves_operational_status(db_session):
    definition = make_definition()

    synchronize_products(
        db_session,
        (definition,),
    )

    product = db_session.scalar(
        select(Product).where(
            Product.slug == definition.slug
        )
    )

    assert product is not None

    product.status = "suspended"
    db_session.commit()

    synchronize_products(
        db_session,
        (definition,),
    )

    db_session.refresh(product)

    assert product.status == "suspended"


def test_sync_rejects_workspace_conflict(db_session):
    db_session.add(
        Product(
            name="Existing Product",
            slug="existing-product",
            status="active",
            workspace_key="claimed-workspace",
        )
    )
    db_session.commit()

    conflicting = make_definition(
        slug="different-product",
        workspace_key="claimed-workspace",
    )

    with pytest.raises(
        ProductSyncError,
        match="workspace_key conflicts",
    ):
        synchronize_products(
            db_session,
            (conflicting,),
        )

    db_session.rollback()
