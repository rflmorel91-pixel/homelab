import os
from urllib.parse import urlsplit

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


CORS_ALLOWED_ORIGINS = "CORS_ALLOWED_ORIGINS"


def configured_cors_origins() -> list[str]:
    raw_value = os.getenv(
        CORS_ALLOWED_ORIGINS,
        "",
    )
    origins: list[str] = []

    for candidate in raw_value.split(","):
        value = candidate.strip()

        if not value:
            continue

        parsed = urlsplit(value)

        if (
            "*" in value
            or parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise RuntimeError(
                "CORS_ALLOWED_ORIGINS must contain "
                "comma-separated HTTP(S) origins"
            )

        origin = f"{parsed.scheme}://{parsed.netloc}"

        if origin not in origins:
            origins.append(origin)

    return origins


def configure_cors(application: FastAPI) -> None:
    origins = configured_cors_origins()

    if not origins:
        return

    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )
