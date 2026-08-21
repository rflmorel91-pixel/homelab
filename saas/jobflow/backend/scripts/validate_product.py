import argparse
import os
from pathlib import Path
import sys


BACKEND_ROOT = (
    Path(__file__).resolve().parents[1]
)

backend_path = str(BACKEND_ROOT)

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)


os.environ.setdefault(
    "DATABASE_URL",
    "sqlite+pysqlite:///:memory:",
)
os.environ.setdefault(
    "JWT_SECRET",
    "product-validator-local-secret-at-least-32-bytes",
)


from app.platform import (
    discover_product_migration_locations,
    discover_product_models,
    discover_products,
    list_products,
)
from app.platform.installed_product_migrations import (
    installed_product_migration_locations,
)
from app.platform.product_discovery import (
    ProductDiscoveryError,
)
from app.platform.product_validation import (
    ProductValidationError,
    validate_product_definitions,
)


def _package_name(slug: str) -> str:
    return slug.replace("-", "_")


def _migration_count(
    package: str,
    locations: tuple[Path, ...],
) -> int:
    return sum(
        1
        for location in locations
        if (
            len(location.parents) >= 2
            and location.parents[1].name
            == package
        )
    )


def validate_products(
    *,
    backend_root: Path,
    target_slug: str | None = None,
) -> int:
    discovered_packages = discover_products(
        root=backend_root
    )

    model_packages = discover_product_models(
        root=backend_root
    )

    migration_locations = (
        discover_product_migration_locations(
            backend_root
        )
        + installed_product_migration_locations()
    )

    products = validate_product_definitions(
        list_products(),
        target_slug=target_slug,
    )

    for product in products:
        package = _package_name(product.slug)

        if package not in discovered_packages:
            raise ProductValidationError(
                (
                    f"{product.slug} definition is "
                    "registered but its package was "
                    "not discovered",
                )
            )

        router_count = len(product.routers)
        tenant_router_count = len(
            product.tenant_routers
        )

        has_models = (
            package in model_packages
        )

        migration_count = _migration_count(
            package,
            migration_locations,
        )

        print(
            "VALID "
            f"product={product.slug} "
            f"version={product.version} "
            "contract="
            f"{product.platform_contract_version} "
            f"public_routers={router_count} "
            "tenant_routers="
            f"{tenant_router_count} "
            "models="
            f"{'yes' if has_models else 'no'} "
            f"migration_locations={migration_count}"
        )

    print(
        "Validated "
        f"{len(products)} product"
        f"{'' if len(products) == 1 else 's'}."
    )

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate SaaS products against the "
            "platform contract before deployment."
        )
    )

    parser.add_argument(
        "slug",
        nargs="?",
        default=None,
        help=(
            "Optional product slug. "
            "When omitted, validate all products."
        ),
    )

    parser.add_argument(
        "--root",
        type=Path,
        default=BACKEND_ROOT,
        help=(
            "Backend workspace root "
            "(default: installed platform root)."
        ),
    )

    args = parser.parse_args()

    try:
        return validate_products(
            backend_root=args.root.resolve(),
            target_slug=args.slug,
        )

    except (
        ProductDiscoveryError,
        ProductValidationError,
    ) as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
