from pathlib import Path

from app.platform.installed_product_discovery import (
    installed_product_packages,
)


def test_no_installed_products_is_valid():
    packages = installed_product_packages()

    assert isinstance(
        packages,
        tuple,
    )


def test_installed_namespace_products_are_found(
    tmp_path,
    monkeypatch,
):
    namespace_root = (
        tmp_path
        / "saas_products"
    )

    product_dir = (
        namespace_root
        / "external_product"
    )

    product_dir.mkdir(
        parents=True,
    )

    (
        product_dir
        / "__init__.py"
    ).write_text("")

    (
        product_dir
        / "definition.py"
    ).write_text(
        """
from app.platform import (
    PLATFORM_CONTRACT_VERSION,
    ProductDefinition,
    register_product,
)

EXTERNAL_PRODUCT = register_product(
    ProductDefinition(
        slug="external-product",
        name="External Product",
        version="0.1.0",
        platform_contract_version=(
            PLATFORM_CONTRACT_VERSION
        ),
        workspace_key="external-product",
        landing_route="/external-product",
        workspace_route="/external-product/app",
        api_prefix="/api/v1/products/external-product",
    )
)
"""
    )

    monkeypatch.syspath_prepend(
        str(tmp_path)
    )

    import saas_products

    monkeypatch.setattr(
        saas_products,
        "__path__",
        [
            *saas_products.__path__,
            str(namespace_root),
        ],
    )

    packages = installed_product_packages()

    assert (
        "external_product"
        in packages
    )


def test_discover_products_includes_installed_namespace_product(
    tmp_path,
    monkeypatch,
):
    namespace_root = (
        tmp_path
        / "saas_products"
    )

    product_dir = (
        namespace_root
        / "installed_runtime"
    )

    product_dir.mkdir(
        parents=True,
    )

    (
        product_dir
        / "__init__.py"
    ).write_text("")

    (
        product_dir
        / "definition.py"
    ).write_text(
        """
from app.platform import (
    PLATFORM_CONTRACT_VERSION,
    ProductDefinition,
    register_product,
)

INSTALLED_RUNTIME = register_product(
    ProductDefinition(
        slug="installed-runtime",
        name="Installed Runtime",
        version="0.1.0",
        platform_contract_version=(
            PLATFORM_CONTRACT_VERSION
        ),
        workspace_key="installed-runtime",
        landing_route="/installed-runtime",
        workspace_route="/installed-runtime/app",
        api_prefix="/api/v1/products/installed-runtime",
    )
)
"""
    )

    monkeypatch.syspath_prepend(
        str(tmp_path)
    )

    import saas_products

    monkeypatch.setattr(
        saas_products,
        "__path__",
        [
            *saas_products.__path__,
            str(namespace_root),
        ],
    )

    from app.platform import (
        discover_products,
        get_product,
    )

    discovered = discover_products()

    assert (
        "installed_runtime"
        in discovered
    )

    assert (
        get_product(
            "installed-runtime"
        )
        is not None
    )


def test_discover_models_includes_installed_namespace_product(
    tmp_path,
    monkeypatch,
):
    namespace_root = (
        tmp_path
        / "saas_products"
    )

    product_dir = (
        namespace_root
        / "installed_models"
    )

    models_dir = (
        product_dir
        / "models"
    )

    models_dir.mkdir(
        parents=True,
    )

    (
        product_dir
        / "__init__.py"
    ).write_text("")

    (
        product_dir
        / "definition.py"
    ).write_text(
        """
from app.platform import (
    PLATFORM_CONTRACT_VERSION,
    ProductDefinition,
    register_product,
)

INSTALLED_MODELS_PRODUCT = register_product(
    ProductDefinition(
        slug="installed-models",
        name="Installed Models",
        version="0.1.0",
        platform_contract_version=(
            PLATFORM_CONTRACT_VERSION
        ),
        workspace_key="installed-models",
        landing_route="/installed-models",
        workspace_route="/installed-models/app",
        api_prefix="/api/v1/products/installed-models",
    )
)
"""
    )

    (
        models_dir
        / "__init__.py"
    ).write_text(
        """
from app.database import Base
"""
    )

    monkeypatch.syspath_prepend(
        str(tmp_path)
    )

    import saas_products

    monkeypatch.setattr(
        saas_products,
        "__path__",
        [
            *saas_products.__path__,
            str(namespace_root),
        ],
    )

    from app.platform import (
        discover_product_models,
    )

    discovered = (
        discover_product_models()
    )

    assert (
        "installed_models"
        in discovered
    )


def test_namespace_package_without_definition_is_ignored(
    tmp_path,
    monkeypatch,
):
    namespace_root = (
        tmp_path
        / "saas_products"
    )

    package_dir = (
        namespace_root
        / "not_a_product"
    )

    package_dir.mkdir(
        parents=True,
    )

    (
        package_dir
        / "__init__.py"
    ).write_text("")

    monkeypatch.syspath_prepend(
        str(tmp_path)
    )

    import saas_products

    monkeypatch.setattr(
        saas_products,
        "__path__",
        [
            *saas_products.__path__,
            str(namespace_root),
        ],
    )

    packages = installed_product_packages()

    assert "not_a_product" not in packages
