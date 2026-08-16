from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.customers import router as customers_router
from app.api.estimates import router as estimates_router
from app.api.jobs import router as jobs_router
from app.api.invoices import router as invoices_router
from app.api.payments import router as payments_router



app = FastAPI(
    title="JobFlow API",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://192.168.1.92:8084",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "jobflow-api",
    }
