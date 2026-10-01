from app.platform import (
    ProductDefinition,
    register_product,
)
from app.products.prestamodesk.api import (
    router as status_router,
)
from app.products.prestamodesk.applications_public_api import (
    router as applications_public_router,
)
from app.products.prestamodesk.applications_api import (
    router as applications_router,
)
from app.products.prestamodesk.borrowers_api import (
    router as borrowers_router,
)
from app.products.prestamodesk.cashier_api import (
    router as cashier_router,
)
from app.products.prestamodesk.late_fee_policy_api import (
    router as late_fee_policy_router,
)
from app.products.prestamodesk.loans_api import (
    router as loans_router,
)
from app.products.prestamodesk.payments_api import (
    router as payments_router,
)
from app.products.prestamodesk.prospects_public_api import (
    router as prospects_public_router,
)
from app.products.prestamodesk.prospects_api import (
    router as prospects_router,
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
        routers=(
            status_router,
            prospects_public_router,
            applications_public_router,
        ),
        tenant_routers=(
            applications_router,
            borrowers_router,
            cashier_router,
            late_fee_policy_router,
            loans_router,
            payments_router,
            prospects_router,
        ),
        description=(
            "Administra prestatarios, préstamos, "
            "cuotas y cobros en DOP."
        ),
    )
)
