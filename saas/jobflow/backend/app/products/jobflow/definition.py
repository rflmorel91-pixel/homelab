from app.products.jobflow.api.customers import router as customers_router
from app.products.jobflow.api.estimates import router as estimates_router
from app.products.jobflow.api.invoices import router as invoices_router
from app.products.jobflow.api.jobs import router as jobs_router
from app.products.jobflow.api.payments import router as payments_router
from app.products.jobflow.api.public_requests import router as public_requests_router
from app.products.jobflow.api.schedules import router as schedules_router
from app.platform import (
    ProductDefinition,
    register_product,
)


JOBFLOW_PRODUCT = register_product(
    ProductDefinition(
        slug="jobflow",
        name="JobFlow",
        version="1.0.0",

        platform_contract_version=1,
        workspace_key="jobflow",
        landing_route="/",
        workspace_route="/app",
        api_prefix="/api/v1",
        routers=(
            public_requests_router,
        ),
        tenant_routers=(
            customers_router,
            jobs_router,
            estimates_router,
            schedules_router,
            invoices_router,
            payments_router,
        ),
        description=(
            "Workflow management for "
            "home-service businesses."
        ),
    )
)
