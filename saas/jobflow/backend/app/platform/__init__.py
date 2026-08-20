from app.platform.product_context import (
    require_active_product,
)
from app.platform.product_tenant_context import (
    require_product_tenant,
)
from app.platform.product_discovery import (
    ProductDiscoveryError,
    discover_products,
)
from app.platform.product_model_discovery import (
    discover_product_models,
)
from app.platform.product_migration_discovery import (
    discover_product_migration_locations,
)
from app.platform.product_sync import (
    ProductSyncError,
    synchronize_products,
)
from app.platform.products import (
    PLATFORM_CONTRACT_VERSION,
    ProductDefinition,
    ProductRegistry,
    get_product,
    list_products,
    register_product,
)

__all__ = [
    "require_active_product",
    "require_product_tenant",
    "ProductDiscoveryError",
    "discover_products",
    "discover_product_models",
    "discover_product_migration_locations",
    "ProductSyncError",
    "synchronize_products",
    "PLATFORM_CONTRACT_VERSION",
    "ProductDefinition",
    "ProductRegistry",
    "get_product",
    "list_products",
    "register_product",
]
