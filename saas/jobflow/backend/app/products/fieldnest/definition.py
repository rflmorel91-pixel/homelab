from app.products.fieldnest.resident_tracking import public_tracking_router, tracking_router, owner_tracking_router
from app.products.fieldnest.resident_requests import public_router, link_router
from app.platform import ProductDefinition, register_product
from app.products.fieldnest.api import router as workspace_router, status_router


FIELDNEST_PRODUCT = register_product(
    ProductDefinition(
        slug="fieldnest",
        name="FieldNest",
        version="0.1.0",
        platform_contract_version=1,
        workspace_key="fieldnest",
        landing_route="/fieldnest",
        workspace_route="/fieldnest/workspace",
        api_prefix="/api/v1/products/fieldnest",
        routers=(status_router, public_router, public_tracking_router),
        tenant_routers=(workspace_router, link_router, tracking_router, owner_tracking_router),
        description="Coordinate property maintenance, residents, and service vendors.",
    )
)
