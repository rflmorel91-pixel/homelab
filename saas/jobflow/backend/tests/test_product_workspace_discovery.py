from pathlib import Path

from app.platform import (
    discover_product_models,
    discover_products,
)


def write_product(
    root: Path,
    package: str,
    *,
    with_models: bool = False,
):
    product_dir = (
        root
        / "app"
        / "products"
        / package
    )

    product_dir.mkdir(
        parents=True,
    )

    (
        product_dir
        / "__init__.py"
    ).write_text("")

    product_slug = package.replace(
        "_",
        "-",
    )

    (
        product_dir
        / "definition.py"
    ).write_text(
        f"""
from app.platform import (
    PLATFORM_CONTRACT_VERSION,
    ProductDefinition,
    register_product,
)

WORKSPACE_PRODUCT = register_product(
    ProductDefinition(
        slug="{product_slug}",
        name="Workspace Product",
        version="0.1.0",
        platform_contract_version=(
            PLATFORM_CONTRACT_VERSION
        ),
        workspace_key="{product_slug}",
        landing_route="/{product_slug}",
        workspace_route="/{product_slug}/app",
        api_prefix="/api/v1/products/{product_slug}",
    )
)
"""
    )

    if with_models:
        models_dir = (
            product_dir
            / "models"
        )

        models_dir.mkdir()

        (
            models_dir
            / "__init__.py"
        ).write_text(
            """
from app.database import Base
"""
        )


def test_discovers_product_from_workspace(
    tmp_path,
):
    write_product(
        tmp_path,
        "workspace_product",
    )

    discovered = discover_products(
        root=tmp_path
    )

    assert "workspace_product" in discovered


def test_discovers_models_from_workspace(
    tmp_path,
):
    write_product(
        tmp_path,
        "workspace_product_models",
        with_models=True,
    )

    discovered = discover_product_models(
        root=tmp_path
    )

    assert (
        "workspace_product_models"
        in discovered
    )


def test_workspace_discovery_does_not_leak_path(
    tmp_path,
):
    import app.products

    write_product(
        tmp_path,
        "workspace_no_leak",
    )

    products_path = str(
        (
            tmp_path
            / "app"
            / "products"
        ).resolve()
    )

    assert (
        products_path
        not in app.products.__path__
    )

    discover_products(
        root=tmp_path
    )

    assert (
        products_path
        not in app.products.__path__
    )
