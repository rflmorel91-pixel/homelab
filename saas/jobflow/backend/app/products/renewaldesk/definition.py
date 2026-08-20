from app.platform import (
    ProductDefinition,
    register_product,
)
from app.products.renewaldesk.api import router


RENEWALDESK_PRODUCT = register_product(
    ProductDefinition(
        slug="renewaldesk",
        name="RenewalDesk",
        version="0.1.0",
        workspace_key="renewaldesk",
        landing_route="/renewaldesk",
        workspace_route="/renewaldesk/app",
        api_prefix="/api/v1/products/renewaldesk",
        routers=(
            router,
        ),
        description='Track recurring licenses, certifications, and renewal deadlines.',
    )
)
