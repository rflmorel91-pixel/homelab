import argparse
from pathlib import Path
import re
import sys


SLUG_PATTERN = re.compile(
    r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$"
)


def python_package_name(slug: str) -> str:
    return slug.replace("-", "_")


def constant_name(slug: str) -> str:
    return (
        slug.replace("-", "_").upper()
        + "_PRODUCT"
    )


def create_product(
    *,
    root: Path,
    slug: str,
    name: str,
    description: str,
) -> Path:
    if not SLUG_PATTERN.fullmatch(slug):
        raise ValueError(
            "slug must use lowercase letters, "
            "numbers, and hyphens"
        )

    package = python_package_name(slug)

    if not package.isidentifier():
        raise ValueError(
            "slug does not produce a valid Python package"
        )

    product_dir = (
        root
        / "app"
        / "products"
        / package
    )

    if product_dir.exists():
        raise FileExistsError(
            f"product package already exists: {product_dir}"
        )

    tests_dir = root / "tests"

    product_dir.mkdir(
        parents=True,
    )
    tests_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    constant = constant_name(slug)

    api_prefix = (
        f"/api/v1/products/{slug}"
    )

    (product_dir / "__init__.py").write_text(
        f'''from app.products.{package}.definition import (
    {constant},
)

__all__ = [
    "{constant}",
]
'''
    )

    (product_dir / "api.py").write_text(
        f'''from fastapi import APIRouter


router = APIRouter(
    prefix="/status",
    tags=["{name}"],
)


@router.get("")
def {package}_status():
    return {{
        "product": "{slug}",
        "status": "available",
    }}
'''
    )

    (product_dir / "definition.py").write_text(
        f'''from app.platform import (
    ProductDefinition,
    register_product,
)
from app.products.{package}.api import router


{constant} = register_product(
    ProductDefinition(
        slug="{slug}",
        name="{name}",
        version="0.1.0",
        workspace_key="{slug}",
        landing_route="/{slug}",
        workspace_route="/{slug}/app",
        api_prefix="{api_prefix}",
        routers=(
            router,
        ),
        description={description!r},
    )
)
'''
    )

    test_path = (
        tests_dir
        / f"test_{package}_product.py"
    )

    test_path.write_text(
        f'''from sqlalchemy import select

from app.models import Product
from app.platform import get_product


def test_{package}_is_discovered():
    definition = get_product("{slug}")

    assert definition is not None
    assert definition.name == "{name}"
    assert definition.workspace_key == "{slug}"


def test_{package}_router_is_composed(
    raw_client,
):
    response = raw_client.get(
        "{api_prefix}/status"
    )

    assert response.status_code == 200
    assert response.json() == {{
        "product": "{slug}",
        "status": "available",
    }}


def test_{package}_synchronizes_to_database(
    raw_client,
    db_session,
):
    response = raw_client.get(
        "{api_prefix}/status"
    )
    assert response.status_code == 200

    product = db_session.scalar(
        select(Product).where(
            Product.slug == "{slug}"
        )
    )

    assert product is not None
    assert product.name == "{name}"
    assert product.status == "active"


def test_{package}_inherits_lifecycle(
    raw_client,
    db_session,
):
    product = db_session.scalar(
        select(Product).where(
            Product.slug == "{slug}"
        )
    )

    assert product is not None

    product.status = "suspended"
    db_session.commit()

    response = raw_client.get(
        "{api_prefix}/status"
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Product is suspended"
    )
'''
    )

    return product_dir


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Create a product package for "
            "the SaaS platform."
        )
    )

    parser.add_argument(
        "slug",
        help="Product slug, e.g. client-portal",
    )

    parser.add_argument(
        "name",
        help="Human-readable product name",
    )

    parser.add_argument(
        "--description",
        default="SaaS product.",
    )

    args = parser.parse_args()

    backend_root = (
        Path(__file__)
        .resolve()
        .parents[1]
    )

    try:
        product_dir = create_product(
            root=backend_root,
            slug=args.slug,
            name=args.name,
            description=args.description,
        )

    except (
        ValueError,
        FileExistsError,
    ) as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        return 1

    print(f"Created product: {product_dir}")
    print(
        "No platform-core registration changes "
        "are required."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
