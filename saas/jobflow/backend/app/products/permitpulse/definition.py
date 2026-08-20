from app.platform import (
    ProductDefinition,
    register_product,
)
from app.products.permitpulse.api import router


PERMITPULSE_PRODUCT = register_product(
    ProductDefinition(
        slug="permitpulse",
        name="PermitPulse",
        version="0.1.0",

        platform_contract_version=1,
        workspace_key="permitpulse",
        landing_route="/permitpulse",
        workspace_route="/permitpulse/app",
        api_prefix="/api/v1/products/permitpulse",
        routers=(
            router,
        ),
        description=(
            "Permit, license, inspection, "
            "and renewal tracking."
        ),
    )
)
