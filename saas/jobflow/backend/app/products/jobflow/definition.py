from app.api.customers import router as customers_router
from app.api.estimates import router as estimates_router
from app.api.invoices import router as invoices_router
from app.api.jobs import router as jobs_router
from app.api.payments import router as payments_router
from app.api.public_requests import router as public_requests_router
from app.api.schedules import router as schedules_router
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
        routers=(
            customers_router,
            jobs_router,
            estimates_router,
            schedules_router,
            invoices_router,
            payments_router,
            public_requests_router,
        ),
        description=(
            "Workflow management for "
            "home-service businesses."
        ),
    )
)
