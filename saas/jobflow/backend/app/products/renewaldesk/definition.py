from app.platform import (
    ProductDefinition,
    register_product,
)
from app.products.renewaldesk.api import (
    router as status_router,
)
from app.products.renewaldesk.items_api import (
    router as items_router,
)


RENEWALDESK_PRODUCT = register_product(
    ProductDefinition(
        slug="renewaldesk",
        name="RenewalDesk",
        version="0.1.0",

        platform_contract_version=1,
        workspace_key="renewaldesk",
        landing_route="/renewaldesk",
        workspace_route="/renewaldesk/app",
        api_prefix="/api/v1/products/renewaldesk",
        routers=(
            status_router,
        ),
        tenant_routers=(
            items_router,
        ),
        description='Track recurring licenses, certifications, and renewal deadlines.',
    )
)
