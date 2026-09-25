from app.platform import (
    ProductDefinition,
    register_product,
)
from app.products.prestamodesk.api import (
    router as status_router,
)
from app.products.prestamodesk.borrowers_api import (
    router as borrowers_router,
)


PRESTAMODESK_PRODUCT = register_product(
    ProductDefinition(
        slug="prestamodesk",
        name="PréstamoDesk",
        version="0.1.0",
        platform_contract_version=1,
        workspace_key="prestamodesk",
        landing_route="/prestamodesk",
        workspace_route="/prestamodesk/app",
        api_prefix="/api/v1/products/prestamodesk",
        routers=(status_router,),
        tenant_routers=(borrowers_router,),
        description=(
            "Administra prestatarios, préstamos, "
            "cuotas y cobros en DOP."
        ),
    )
)
