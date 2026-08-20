from dataclasses import dataclass
import re

from fastapi import APIRouter


SLUG_PATTERN = re.compile(
    r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
)


PLATFORM_CONTRACT_VERSION = 1


@dataclass(frozen=True)
class ProductDefinition:
    slug: str
    name: str
    version: str
    platform_contract_version: int
    workspace_key: str
    landing_route: str
    workspace_route: str
    api_prefix: str
    routers: tuple[APIRouter, ...] = ()
    tenant_routers: tuple[APIRouter, ...] = ()
    description: str = ""

    def __post_init__(self) -> None:
        if not self.slug:
            raise ValueError(
                "Product slug is required"
            )

        if not SLUG_PATTERN.fullmatch(self.slug):
            raise ValueError(
                "Product slug must use lowercase "
                "letters, numbers, and hyphens"
            )

        if not self.name.strip():
            raise ValueError(
                "Product name is required"
            )

        if not self.version.strip():
            raise ValueError(
                "Product version is required"
            )

        if (
            self.platform_contract_version
            != PLATFORM_CONTRACT_VERSION
        ):
            raise ValueError(
                "Product requires platform contract "
                f"version "
                f"{self.platform_contract_version}; "
                "this platform provides version "
                f"{PLATFORM_CONTRACT_VERSION}"
            )

        if not self.workspace_key.strip():
            raise ValueError(
                "Product workspace_key is required"
            )

        for field_name in (
            "landing_route",
            "workspace_route",
            "api_prefix",
        ):
            value = getattr(self, field_name)

            if not value.startswith("/"):
                raise ValueError(
                    f"{field_name} must begin with /"
                )


class ProductRegistry:
    def __init__(self) -> None:
        self._products: dict[str, ProductDefinition] = {}
        self._workspace_keys: set[str] = set()

    def register(
        self,
        product: ProductDefinition,
    ) -> ProductDefinition:
        if product.slug in self._products:
            raise ValueError(
                f"Product slug already registered: "
                f"{product.slug}"
            )

        if product.workspace_key in self._workspace_keys:
            raise ValueError(
                f"Product workspace_key already registered: "
                f"{product.workspace_key}"
            )

        self._products[product.slug] = product
        self._workspace_keys.add(
            product.workspace_key
        )

        return product

    def get(
        self,
        slug: str,
    ) -> ProductDefinition | None:
        return self._products.get(slug)

    def list(
        self,
    ) -> tuple[ProductDefinition, ...]:
        return tuple(
            self._products[slug]
            for slug in sorted(self._products)
        )


_registry = ProductRegistry()


def register_product(
    product: ProductDefinition,
) -> ProductDefinition:
    return _registry.register(product)


def get_product(
    slug: str,
) -> ProductDefinition | None:
    return _registry.get(slug)


def list_products() -> tuple[ProductDefinition, ...]:
    return _registry.list()
