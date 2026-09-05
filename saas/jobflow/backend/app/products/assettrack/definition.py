from app.platform import (
    ProductDefinition,
    register_product,
)
from app.products.assettrack.api import (
    router as status_router,
)
from app.products.assettrack.assets_api import (
    router as assets_router,
)
from app.products.assettrack.service_events_api import (
    router as service_events_router,
)
from app.products.assettrack.api_keys_api import (
    router as api_keys_router,
)
from app.products.assettrack.developer_api import (
    router as developer_router,
)


ASSETTRACK_PRODUCT = register_product(
    ProductDefinition(
        slug="assettrack",
        name="AssetTrack",
        version="0.2.0",

        platform_contract_version=1,
        workspace_key="assettrack",
        landing_route="/assettrack",
        workspace_route="/assettrack/app",
        api_prefix="/api/v1/products/assettrack",
        routers=(
            status_router,
            developer_router,
        ),
        tenant_routers=(
            assets_router,
            service_events_router,
            api_keys_router,
        ),
        description='Track customer assets and service history.',
    )
)
