from fastapi import FastAPI

from app.api.customers import router as customers_router
from app.api.estimates import router as estimates_router
from app.api.jobs import router as jobs_router


app = FastAPI(
    title="JobFlow API",
    version="0.1.0",
)


app.include_router(
    customers_router,
    prefix="/api/v1",
)

app.include_router(
    jobs_router,
    prefix="/api/v1",
)

app.include_router(
    estimates_router,
    prefix="/api/v1",
)


@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "jobflow-api",
    }
