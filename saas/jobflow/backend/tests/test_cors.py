import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.cors import (
    configured_cors_origins,
    configure_cors,
)


SITES_ORIGIN = (
    "https://prestamodesk-simulador"
    ".rflmorel91.chatgpt.site"
)


def create_test_client() -> TestClient:
    application = FastAPI()

    @application.post("/quote")
    def quote():
        return {"status": "ok"}

    configure_cors(application)
    return TestClient(application)


def test_cors_is_disabled_without_configuration(monkeypatch):
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    client = create_test_client()

    response = client.options(
        "/quote",
        headers={
            "Origin": SITES_ORIGIN,
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 405
    assert "access-control-allow-origin" not in response.headers


def test_configured_origin_receives_cors_headers(monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", SITES_ORIGIN)
    client = create_test_client()

    response = client.options(
        "/quote",
        headers={
            "Origin": SITES_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == SITES_ORIGIN
    assert response.headers["access-control-allow-credentials"] == "true"


def test_unconfigured_origin_is_rejected(monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", SITES_ORIGIN)
    client = create_test_client()

    response = client.options(
        "/quote",
        headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize(
    "value",
    [
        "*",
        "https://*.example.com",
        "javascript:alert(1)",
        "https://example.com/path",
        "https://example.com?query=yes",
    ],
)
def test_invalid_origins_are_rejected(monkeypatch, value):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", value)

    with pytest.raises(RuntimeError):
        configured_cors_origins()


def test_origins_are_trimmed_and_deduplicated(monkeypatch):
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS",
        f" {SITES_ORIGIN}/, {SITES_ORIGIN} ",
    )

    assert configured_cors_origins() == [SITES_ORIGIN]
