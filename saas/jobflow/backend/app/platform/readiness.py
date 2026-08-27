"""Read-only dependency probes; public results contain no internal identifiers."""
import asyncio
from collections.abc import Callable
import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import psycopg
from sqlalchemy.engine import make_url


router = APIRouter()
PROBE_TIMEOUT = 3.0
CACHE_SECONDS = 1.0


def product_keys(products):
    keys = tuple(sorted((p.slug, p.workspace_key) for p in products))
    if (not keys or len({p[0] for p in keys}) != len(keys)
            or len({p[1] for p in keys}) != len(keys)):
        raise ValueError("Invalid initialized registry")
    return keys


def expected_migration_heads():
    # Use the same bundled/workspace/installed migration locations as deployment.
    # ScriptDirectory reads revision files; it does not run env.py or migrations.
    from alembic.script import ScriptDirectory
    from scripts.platform_alembic import build_config

    heads = frozenset(ScriptDirectory.from_config(build_config()).get_heads())
    if not heads:
        raise ValueError("No migration heads")
    return heads


class Readiness:
    def __init__(self, database_url: str, heads, products, get_products: Callable):
        url = make_url(database_url)
        if url.get_backend_name() != "postgresql" or not heads:
            raise ValueError("Unsupported readiness configuration")
        self._conninfo = url.set(drivername="postgresql").render_as_string(hide_password=False)
        self._heads = frozenset(heads)
        self._products = product_keys(products)
        self._get_products = get_products
        self._lock = asyncio.Lock()
        self._cached = None
        self._cached_until = 0.0

    async def check(self):
        checks = {"database": "not_checked", "migrations": "not_checked", "products": "failed"}
        try:
            if product_keys(self._get_products()) != self._products:
                return checks
        except Exception:
            return checks
        # The registry is checked on every request, even while DB evidence is cached.
        checks["products"] = "not_checked"
        stage = "database"
        try:
            async with asyncio.timeout(PROBE_TIMEOUT):
                async with self._lock:
                    if self._cached is not None and time.monotonic() < self._cached_until:
                        return dict(self._cached)
                    try:
                        connection = await psycopg.AsyncConnection.connect(
                            self._conninfo, autocommit=True, connect_timeout=2,
                            options="-c statement_timeout=1000 -c default_transaction_read_only=on",
                        )
                        async with connection:
                            cursor = await connection.execute("SELECT 1")
                            if await cursor.fetchone() != (1,):
                                raise ValueError("Database probe failed")
                            checks["database"] = "passed"
                            stage = "migrations"
                            cursor = await connection.execute("SELECT version_num FROM public.alembic_version")
                            rows = await cursor.fetchall()
                            applied = frozenset(row[0] for row in rows)
                            if applied != self._heads or len(rows) != len(applied):
                                raise ValueError("Migration state differs")
                            checks["migrations"] = "passed"
                            stage = "products"
                            cursor = await connection.execute("SELECT slug, workspace_key FROM public.products")
                            rows = await cursor.fetchall()
                            registered = {row[0]: row[1] for row in rows}
                            if (len(rows) != len(registered)
                                    or any(registered.get(slug) != key for slug, key in self._products)):
                                raise ValueError("Product synchronization differs")
                            checks["products"] = "passed"
                    except Exception:
                        checks[stage] = "failed"
                    self._cached = dict(checks)
                    self._cached_until = time.monotonic() + CACHE_SECONDS
        except Exception:
            # Includes the total deadline, connection failures and lock wait timeout.
            checks[stage] = "failed"
        return checks


@router.get("/api/v1/ready")
async def readiness_check(request: Request):
    state = getattr(request.app.state, "platform_readiness", None)
    checks = {"database": "not_checked", "migrations": "not_checked", "products": "failed"}
    try:
        if state is not None:
            checks = await state.check()
    except Exception:
        pass
    ready = all(value == "passed" for value in checks.values())
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ready" if ready else "not_ready", "service": "jobflow-api", "checks": checks},
        headers={"Cache-Control": "no-store"},
    )
