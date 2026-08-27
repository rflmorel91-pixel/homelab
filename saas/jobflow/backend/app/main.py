from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.invitations import (
    admin_router as invitation_admin_router,
    client_admin_router as invitation_client_admin_router,
    client_owner_router as invitation_client_owner_router,
    public_router as invitation_public_router,
)
from app.api.password_reset import router as password_reset_router
from app.api.leads import router as leads_router
from app.api.public_leads import router as public_leads_router
from app.database import DATABASE_URL, SessionLocal
from app.platform.readiness import (
    Readiness, expected_migration_heads, router as readiness_router,
)
from app.platform import (
    discover_product_models,
    discover_products,
    list_products,
    require_active_product,
    require_product_tenant,
    synchronize_products,
)



discover_products()
discover_product_models()


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.platform_readiness = None
    db = SessionLocal()

    try:
        synchronize_products(
            db,
            list_products(),
        )
    finally:
        db.close()

    application.state.platform_readiness = Readiness(
        DATABASE_URL,
        expected_migration_heads(),
        list_products(),
        list_products,
    )
    try:
        yield
    finally:
        application.state.platform_readiness = None


app = FastAPI(
    title="SaaS Platform API",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(readiness_router)

app.include_router(
    admin_router,
    prefix="/api/v1",
)

app.include_router(
    auth_router,
    prefix="/api/v1",
)

app.include_router(
    password_reset_router,
    prefix="/api/v1",
)

app.include_router(
    leads_router,
    prefix="/api/v1",
)

app.include_router(
    public_leads_router,
    prefix="/api/v1",
)


app.include_router(
    invitation_admin_router,
    prefix="/api/v1",
)

app.include_router(
    invitation_client_admin_router,
    prefix="/api/v1",
)

app.include_router(
    invitation_public_router,
    prefix="/api/v1",
)

app.include_router(
    invitation_client_owner_router,
    prefix="/api/v1",
)

for product in list_products():
    for router in product.routers:
        app.include_router(
            router,
            prefix=product.api_prefix,
            dependencies=[
                Depends(
                    require_active_product(
                        product.slug
                    )
                )
            ],
        )

    for router in product.tenant_routers:
        app.include_router(
            router,
            prefix=product.api_prefix,
            dependencies=[
                Depends(
                    require_active_product(
                        product.slug
                    )
                ),
                Depends(
                    require_product_tenant(
                        product.slug
                    )
                ),
            ],
        )

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "jobflow-api",
    }
