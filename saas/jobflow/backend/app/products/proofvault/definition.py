from app.platform import (
    ProductDefinition,
    register_product,
)
from app.products.proofvault.api import router


PROOFVAULT_PRODUCT = register_product(
    ProductDefinition(
        slug="proofvault",
        name="ProofVault",
        version="0.1.0",

        platform_contract_version=1,
        workspace_key="proofvault",
        landing_route="/proofvault",
        workspace_route="/proofvault/app",
        api_prefix="/api/v1/products/proofvault",
        routers=(
            router,
        ),
        description=(
            "Operational evidence and work "
            "handoff records."
        ),
    )
)
