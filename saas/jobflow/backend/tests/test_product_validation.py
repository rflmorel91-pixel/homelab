import os
from pathlib import Path
import subprocess
import sys

from pathlib import Path

from fastapi import APIRouter
import pytest

from app.platform.products import (
    PLATFORM_CONTRACT_VERSION,
    ProductDefinition,
)
from app.platform.product_validation import (
    ProductValidationError,
    validate_product_definitions,
)
from scripts.validate_product import (
    validate_products,
)


def make_product(
    slug: str,
    *,
    routers: tuple[object, ...] | None = None,
    tenant_routers: (
        tuple[object, ...] | None
    ) = None,
    landing_route: str | None = None,
    workspace_route: str | None = None,
    api_prefix: str | None = None,
) -> ProductDefinition:
    if routers is None:
        routers = (
            APIRouter(prefix="/status"),
        )

    if tenant_routers is None:
        tenant_routers = ()

    return ProductDefinition(
        slug=slug,
        name=slug.replace("-", " ").title(),
        version="0.1.0",
        platform_contract_version=(
            PLATFORM_CONTRACT_VERSION
        ),
        workspace_key=slug,
        landing_route=(
            landing_route
            if landing_route is not None
            else f"/{slug}"
        ),
        workspace_route=(
            workspace_route
            if workspace_route is not None
            else f"/{slug}/app"
        ),
        api_prefix=(
            api_prefix
            if api_prefix is not None
            else f"/api/v1/products/{slug}"
        ),
        routers=routers,
        tenant_routers=tenant_routers,
    )


def test_validation_accepts_valid_products():
    products = (
        make_product("product-two"),
        make_product("product-one"),
    )

    validated = validate_product_definitions(
        products
    )

    assert tuple(
        product.slug
        for product in validated
    ) == (
        "product-one",
        "product-two",
    )


def test_validation_selects_target_product():
    products = (
        make_product("product-one"),
        make_product("product-two"),
    )

    validated = validate_product_definitions(
        products,
        target_slug="product-two",
    )

    assert len(validated) == 1
    assert validated[0].slug == "product-two"


def test_validation_rejects_missing_target():
    with pytest.raises(
        ProductValidationError,
        match="product not found: missing",
    ):
        validate_product_definitions(
            (make_product("product-one"),),
            target_slug="missing",
        )


def test_validation_rejects_product_without_routers():
    product = make_product(
        "no-routes",
        routers=(),
        tenant_routers=(),
    )

    with pytest.raises(
        ProductValidationError,
        match="no-routes has no routers",
    ):
        validate_product_definitions(
            (product,)
        )


def test_validation_rejects_duplicate_web_route():
    first = make_product("first")

    second = make_product(
        "second",
        landing_route=first.workspace_route,
    )

    with pytest.raises(
        ProductValidationError,
        match="web route",
    ):
        validate_product_definitions(
            (first, second)
        )


def test_validation_rejects_duplicate_api_prefix():
    first = make_product("first")

    second = make_product(
        "second",
        api_prefix=first.api_prefix,
    )

    with pytest.raises(
        ProductValidationError,
        match="API prefix",
    ):
        validate_product_definitions(
            (first, second)
        )


def test_validation_rejects_shared_router_scope():
    router = APIRouter(prefix="/records")

    product = make_product(
        "shared-router",
        routers=(router,),
        tenant_routers=(router,),
    )

    with pytest.raises(
        ProductValidationError,
        match=(
            "same router as both public "
            "and tenant-scoped"
        ),
    ):
        validate_product_definitions(
            (product,)
        )


def test_validation_rejects_non_router():
    product = make_product(
        "bad-router",
        routers=(object(),),
    )

    with pytest.raises(
        ProductValidationError,
        match="is not an APIRouter",
    ):
        validate_product_definitions(
            (product,)
        )


def test_validation_rejects_matching_page_routes():
    product = make_product(
        "same-page",
        landing_route="/same",
        workspace_route="/same",
    )

    with pytest.raises(
        ProductValidationError,
        match=(
            "landing_route and "
            "workspace_route must be different"
        ),
    ):
        validate_product_definitions(
            (product,)
        )


def test_cli_validator_validates_real_product(
    capsys,
):
    backend_root = (
        Path(__file__).resolve().parents[1]
    )

    result = validate_products(
        backend_root=backend_root,
        target_slug="renewaldesk",
    )

    output = capsys.readouterr().out

    assert result == 0
    assert "VALID product=renewaldesk" in output
    assert "contract=1" in output
    assert "models=yes" in output
    assert "Validated 1 product." in output

def test_validator_runs_without_application_environment():
    backend_root = (
        Path(__file__).resolve().parents[1]
    )
    environment = os.environ.copy()
    environment.pop(
        "DATABASE_URL",
        None,
    )
    environment.pop(
        "JWT_SECRET",
        None,
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/validate_product.py",
        ],
        cwd=backend_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        result.stdout + result.stderr
    )
    assert "Validated 5 products." in (
        result.stdout
    )
