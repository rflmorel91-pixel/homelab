from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.leads import router as leads_router
from app.api.public_leads import router as public_leads_router
from app.database import SessionLocal
from app.platform import (
    discover_product_models,
    discover_products,
    list_products,
    require_active_product,
    synchronize_products,
)



discover_products()
discover_product_models()


@asynccontextmanager
async def lifespan(_: FastAPI):
    db = SessionLocal()

    try:
        synchronize_products(
            db,
            list_products(),
        )
    finally:
        db.close()

    yield


app = FastAPI(
    title="SaaS Platform API",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(
    admin_router,
    prefix="/api/v1",
)

app.include_router(
    auth_router,
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

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "jobflow-api",
    }
