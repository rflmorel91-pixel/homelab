from collections import defaultdict
from collections.abc import Iterable

from fastapi import APIRouter

from app.platform.products import ProductDefinition


class ProductValidationError(RuntimeError):
    def __init__(
        self,
        errors: Iterable[str],
    ) -> None:
        self.errors = tuple(errors)

        super().__init__(
            "Product validation failed:\n"
            + "\n".join(
                f"- {error}"
                for error in self.errors
            )
        )


def _duplicate_values(
    values: Iterable[
        tuple[str, str]
    ],
) -> dict[str, tuple[str, ...]]:
    grouped: dict[str, list[str]] = defaultdict(
        list
    )

    for value, owner in values:
        grouped[value].append(owner)

    return {
        value: tuple(owners)
        for value, owners in grouped.items()
        if len(owners) > 1
    }


def _validate_platform_routes(
    products: tuple[ProductDefinition, ...],
) -> list[str]:
    errors: list[str] = []

    web_routes = _duplicate_values(
        (
            route,
            f"{product.slug}.{field_name}",
        )
        for product in products
        for field_name, route in (
            (
                "landing_route",
                product.landing_route,
            ),
            (
                "workspace_route",
                product.workspace_route,
            ),
        )
        if route is not None
    )

    for route, owners in sorted(
        web_routes.items()
    ):
        errors.append(
            "web route "
            f"{route!r} is shared by "
            + ", ".join(owners)
        )

    api_prefixes = _duplicate_values(
        (
            product.api_prefix,
            product.slug,
        )
        for product in products
    )

    for prefix, owners in sorted(
        api_prefixes.items()
    ):
        errors.append(
            "API prefix "
            f"{prefix!r} is shared by "
            + ", ".join(owners)
        )

    return errors


def _validate_router(
    *,
    product: ProductDefinition,
    router: object,
    router_class: str,
    index: int,
) -> list[str]:
    errors: list[str] = []

    if not isinstance(router, APIRouter):
        errors.append(
            f"{product.slug} {router_class} "
            f"router #{index} is not an APIRouter"
        )

        return errors

    if (
        router.prefix
        and not router.prefix.startswith("/")
    ):
        errors.append(
            f"{product.slug} {router_class} "
            f"router #{index} prefix must begin "
            "with /"
        )

    return errors


def _validate_product(
    product: ProductDefinition,
) -> list[str]:
    errors: list[str] = []

    if not (
        product.routers
        or product.tenant_routers
    ):
        errors.append(
            f"{product.slug} has no routers"
        )

    if (
        product.workspace_route is not None
        and product.landing_route
        == product.workspace_route
    ):
        errors.append(
            f"{product.slug} landing_route and "
            "workspace_route must be different"
        )

    public_router_ids = {
        id(router)
        for router in product.routers
    }

    shared_routers = [
        router
        for router in product.tenant_routers
        if id(router) in public_router_ids
    ]

    if shared_routers:
        errors.append(
            f"{product.slug} registers the same "
            "router as both public and tenant-scoped"
        )

    for index, router in enumerate(
        product.routers,
        start=1,
    ):
        errors.extend(
            _validate_router(
                product=product,
                router=router,
                router_class="public",
                index=index,
            )
        )

    for index, router in enumerate(
        product.tenant_routers,
        start=1,
    ):
        errors.extend(
            _validate_router(
                product=product,
                router=router,
                router_class="tenant",
                index=index,
            )
        )

    return errors


def validate_product_definitions(
    products: Iterable[ProductDefinition],
    *,
    target_slug: str | None = None,
) -> tuple[ProductDefinition, ...]:
    product_list = tuple(products)
    errors: list[str] = []

    if not product_list:
        raise ProductValidationError(
            ("no products were discovered",)
        )

    errors.extend(
        _validate_platform_routes(product_list)
    )

    selected = product_list

    if target_slug is not None:
        selected = tuple(
            product
            for product in product_list
            if product.slug == target_slug
        )

        if not selected:
            errors.append(
                f"product not found: {target_slug}"
            )

    for product in selected:
        errors.extend(
            _validate_product(product)
        )

    if errors:
        raise ProductValidationError(errors)

    return tuple(
        sorted(
            selected,
            key=lambda product: product.slug,
        )
    )
