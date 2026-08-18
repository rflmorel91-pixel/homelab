from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.customers import router as customers_router
from app.api.estimates import router as estimates_router
from app.api.jobs import router as jobs_router
from app.api.invoices import router as invoices_router
from app.api.payments import router as payments_router
from app.api.schedules import router as schedules_router



app = FastAPI(
    title="JobFlow API",
    version="0.1.0",
)


app.include_router(
    auth_router,
    prefix="/api/v1",
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

app.include_router(
    invoices_router,
    prefix="/api/v1",
)

app.include_router(
    payments_router,
    prefix="/api/v1",
)

app.include_router(
    schedules_router,
    prefix="/api/v1",
)

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "jobflow-api",
    }
