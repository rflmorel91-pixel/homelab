from app.platform import (
    ProductDefinition,
    register_product,
)


JOBFLOW_PRODUCT = register_product(
    ProductDefinition(
        slug="jobflow",
        name="JobFlow",
        version="1.0.0",
        workspace_key="jobflow",
        landing_route="/",
        workspace_route="/app",
        api_prefix="/api/v1",
        description=(
            "Workflow management for "
            "home-service businesses."
        ),
    )
)
