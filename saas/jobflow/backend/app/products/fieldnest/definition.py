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
        routers=(status_router,),
        tenant_routers=(workspace_router,),
        description="Coordinate property maintenance, residents, and service vendors.",
    )
)
