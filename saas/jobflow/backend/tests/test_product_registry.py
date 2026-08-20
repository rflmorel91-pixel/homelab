import pytest

from app.platform.products import (
    ProductDefinition,
    ProductRegistry,
)
from app.products import JOBFLOW_PRODUCT


def test_jobflow_product_definition():
    assert JOBFLOW_PRODUCT.slug == "jobflow"
    assert JOBFLOW_PRODUCT.name == "JobFlow"
    assert JOBFLOW_PRODUCT.version == "1.0.0"
    assert JOBFLOW_PRODUCT.workspace_key == "jobflow"
    assert JOBFLOW_PRODUCT.landing_route == "/"
    assert JOBFLOW_PRODUCT.workspace_route == "/app"
    assert JOBFLOW_PRODUCT.api_prefix == "/api/v1"


def test_registry_registers_and_gets_product():
    registry = ProductRegistry()

    product = ProductDefinition(
        slug="example-product",
        name="Example Product",
        version="1.0.0",
        workspace_key="example-product",
        landing_route="/example",
        workspace_route="/example/app",
        api_prefix="/api/v1/products/example-product",
    )

    registry.register(product)

    assert registry.get(
        "example-product"
    ) is product

    assert registry.list() == (product,)


def test_registry_rejects_duplicate_slug():
    registry = ProductRegistry()

    product = ProductDefinition(
        slug="duplicate",
        name="Duplicate",
        version="1.0.0",
        workspace_key="duplicate-one",
        landing_route="/duplicate",
        workspace_route="/duplicate/app",
        api_prefix="/api/v1/products/duplicate",
    )

    registry.register(product)

    with pytest.raises(
        ValueError,
        match="slug already registered",
    ):
        registry.register(
            ProductDefinition(
                slug="duplicate",
                name="Duplicate Two",
                version="1.0.0",
                workspace_key="duplicate-two",
                landing_route="/duplicate-two",
                workspace_route="/duplicate-two/app",
                api_prefix="/api/v1/products/duplicate-two",
            )
        )


def test_registry_rejects_duplicate_workspace_key():
    registry = ProductRegistry()

    registry.register(
        ProductDefinition(
            slug="product-one",
            name="Product One",
            version="1.0.0",
            workspace_key="shared-workspace",
            landing_route="/one",
            workspace_route="/one/app",
            api_prefix="/api/v1/products/one",
        )
    )

    with pytest.raises(
        ValueError,
        match="workspace_key already registered",
    ):
        registry.register(
            ProductDefinition(
                slug="product-two",
                name="Product Two",
                version="1.0.0",
                workspace_key="shared-workspace",
                landing_route="/two",
                workspace_route="/two/app",
                api_prefix="/api/v1/products/two",
            )
        )


@pytest.mark.parametrize(
    "slug",
    [
        "",
        "JobFlow",
        "job flow",
        "job_flow",
        "-jobflow",
    ],
)
def test_product_definition_rejects_invalid_slug(
    slug,
):
    with pytest.raises(ValueError):
        ProductDefinition(
            slug=slug,
            name="Invalid",
            version="1.0.0",
            workspace_key="invalid",
            landing_route="/",
            workspace_route="/app",
            api_prefix="/api/v1",
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("landing_route", "landing"),
        ("workspace_route", "app"),
        ("api_prefix", "api/v1"),
    ],
)
def test_product_definition_requires_absolute_routes(
    field,
    value,
):
    values = {
        "slug": "test-product",
        "name": "Test Product",
        "version": "1.0.0",
        "workspace_key": "test-product",
        "landing_route": "/",
        "workspace_route": "/app",
        "api_prefix": "/api/v1",
    }

    values[field] = value

    with pytest.raises(ValueError):
        ProductDefinition(**values)
