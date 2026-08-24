from app.platform import (
    ProductDefinition,
    register_product,
)
from app.products.workflow_automation.api import (
    router,
)


WORKFLOW_AUTOMATION_PRODUCT = register_product(
    ProductDefinition(
        slug="workflow-automation",
        name="Workflow Automation Package",
        version="0.1.0",
        platform_contract_version=1,
        workspace_key="workflow-automation",
        landing_route="/workflow-automation",
        workspace_route=None,
        api_prefix=(
            "/api/v1/products/workflow-automation"
        ),
        routers=(
            router,
        ),
        description=(
            "Fixed-scope implementation of one "
            "documented small-business workflow."
        ),
        offering_type="service",
    )
)
