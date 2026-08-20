from fastapi import FastAPI

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.leads import router as leads_router
from app.api.public_leads import router as public_leads_router
from app import products as installed_products
from app.platform import list_products



app = FastAPI(
    title="JobFlow API",
    version="0.1.0",
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
        )

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "jobflow-api",
    }
