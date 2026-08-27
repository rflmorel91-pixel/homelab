from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "jobflow-api",
    }

def test_readiness_after_startup(raw_client):
    response = raw_client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "service": "jobflow-api",
        "checks": {
            "database": "passed",
            "migrations": "passed",
            "products": "passed",
        },
    }
    assert response.headers["cache-control"] == "no-store"


def test_liveness_survives_readiness_database_failure(raw_client, monkeypatch):
    from app.platform import readiness

    async def unavailable(*args, **kwargs):
        raise RuntimeError("PRIVATE_TEST_CONNECTION_VALUE")

    monkeypatch.setattr(readiness.psycopg.AsyncConnection, "connect", unavailable)
    app.state.platform_readiness._cached_until = 0
    response = raw_client.get("/api/v1/ready")
    assert response.status_code == 503
    assert response.json()["checks"]["database"] == "failed"
    assert "PRIVATE_TEST_CONNECTION_VALUE" not in response.text
    assert raw_client.get("/api/v1/health").status_code == 200
