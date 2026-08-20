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


ASSETTRACK_PRODUCT = register_product(
    ProductDefinition(
        slug="assettrack",
        name="AssetTrack",
        version="0.1.0",

        platform_contract_version=1,
        workspace_key="assettrack",
        landing_route="/assettrack",
        workspace_route="/assettrack/app",
        api_prefix="/api/v1/products/assettrack",
        routers=(
            status_router,
        ),
        tenant_routers=(
            assets_router,
        ),
        description='Track customer assets and service history.',
    )
)
