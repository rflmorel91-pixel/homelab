"""Dependency probes are mocked; these tests never stop a live database."""
import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

spec = importlib.util.spec_from_file_location(
    "readiness_under_test", Path(__file__).resolve().parents[1] / "app/platform/readiness.py")
readiness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(readiness)


class ProbeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.products = [SimpleNamespace(slug="example", workspace_key="example")]
        self.state = readiness.Readiness(
            "postgresql+psycopg://user:PRIVATE_PASSWORD@localhost/test", {"head"},
            self.products, lambda: self.products,
        )
        self.connection = AsyncMock()
        self.connection.__aenter__.return_value = self.connection
        self.cursor = AsyncMock()
        self.cursor.fetchone.return_value = (1,)
        self.cursor.fetchall.side_effect = [[("head",)], [("example", "example")]]
        self.connection.execute.return_value = self.cursor
        self.connect = self.enterContext(patch.object(
            readiness.psycopg.AsyncConnection, "connect", new_callable=AsyncMock))
        self.connect.return_value = self.connection

    async def test_healthy_and_connection_closed(self):
        self.assertEqual(await self.state.check(), dict.fromkeys(("database", "migrations", "products"), "passed"))
        self.connection.__aexit__.assert_awaited_once()
        kwargs = self.connect.call_args.kwargs
        self.assertIn("default_transaction_read_only=on", kwargs["options"])
        self.assertIn("statement_timeout=1000", kwargs["options"])
        self.assertEqual(kwargs["connect_timeout"], 2)

    async def test_database_unavailable(self):
        self.connect.side_effect = RuntimeError("PRIVATE_PASSWORD")
        result = await self.state.check()
        self.assertEqual(result["database"], "failed")
        self.assertNotIn("PRIVATE_PASSWORD", str(result))

    async def test_migration_mismatch_empty_unknown_or_duplicate(self):
        for rows in ([], [("old",)], [("unknown",)], [("head",), ("head",)]):
            self.state._cached_until = 0
            self.cursor.fetchall.side_effect = [rows]
            result = await self.state.check()
            self.assertEqual(result["migrations"], "failed")
            self.assertEqual(result["database"], "passed")

    async def test_multiple_heads_require_exact_set(self):
        self.state._heads = frozenset({"a", "b"})
        self.cursor.fetchall.side_effect = [[("b",), ("a",)], [("example", "example")]]
        self.assertEqual((await self.state.check())["migrations"], "passed")

    async def test_missing_version_table_fails(self):
        self.connection.execute.side_effect = [self.cursor, RuntimeError("private SQL details")]
        result = await self.state.check()
        self.assertEqual(result["migrations"], "failed")
        self.assertNotIn("private SQL", str(result))

    async def test_missing_product_or_wrong_workspace_fails(self):
        for rows in ([], [("example", "wrong")]):
            self.state._cached_until = 0
            self.cursor.fetchall.side_effect = [[("head",)], rows]
            self.assertEqual((await self.state.check())["products"], "failed")

    async def test_product_status_is_not_used_as_health(self):
        result = await self.state.check()
        query = self.connection.execute.call_args.args[0]
        self.assertNotIn("status", query)
        self.assertEqual(result["products"], "passed")

    async def test_empty_or_changed_registry_does_not_connect(self):
        for products in ([], [SimpleNamespace(slug="different", workspace_key="different")]):
            self.products = products
            self.assertEqual((await self.state.check())["products"], "failed")
        self.connect.assert_not_called()

    async def test_registry_checked_even_with_cached_success(self):
        await self.state.check()
        self.products = []
        self.assertEqual((await self.state.check())["products"], "failed")

    async def test_probe_cache_limits_repeated_connections(self):
        await self.state.check()
        await self.state.check()
        self.connect.assert_awaited_once()

    async def test_total_deadline_cancels_connect(self):
        async def hanging(*args, **kwargs):
            await asyncio.sleep(10)
        self.connect.side_effect = hanging
        with patch.object(readiness, "PROBE_TIMEOUT", 0.02):
            result = await asyncio.wait_for(self.state.check(), timeout=0.5)
        self.assertEqual(result["database"], "failed")

    async def test_query_deadline_closes_connection(self):
        async def hanging(*args, **kwargs):
            await asyncio.sleep(10)
        self.connection.execute.side_effect = hanging
        with patch.object(readiness, "PROBE_TIMEOUT", 0.02):
            self.assertEqual((await asyncio.wait_for(self.state.check(), timeout=0.5))["database"], "failed")
        self.connection.__aexit__.assert_awaited_once()

    async def test_concurrent_requests_share_probe(self):
        results = await asyncio.gather(self.state.check(), self.state.check())
        self.assertEqual(results[0], results[1])
        self.connect.assert_awaited_once()


class EndpointTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(readiness.router)
        self.client = TestClient(self.app)

    def test_startup_incomplete_returns_503(self):
        result = self.client.get("/api/v1/ready")
        self.assertEqual(result.status_code, 503)
        self.assertEqual(result.json()["status"], "not_ready")
        self.assertEqual(result.headers["cache-control"], "no-store")

    def test_healthy_returns_200(self):
        self.app.state.platform_readiness = SimpleNamespace(check=AsyncMock(
            return_value=dict.fromkeys(("database", "migrations", "products"), "passed")))
        result = self.client.get("/api/v1/ready")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["status"], "ready")

    def test_dependency_failures_return_503(self):
        for failed in ("database", "migrations", "products"):
            checks = dict.fromkeys(("database", "migrations", "products"), "passed")
            checks[failed] = "failed"
            self.app.state.platform_readiness = SimpleNamespace(check=AsyncMock(return_value=checks))
            self.assertEqual(self.client.get("/api/v1/ready").status_code, 503)

    def test_unexpected_error_is_sanitized(self):
        self.app.state.platform_readiness = SimpleNamespace(check=AsyncMock(side_effect=RuntimeError("SECRET_CUSTOMER")))
        response = self.client.get("/api/v1/ready")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("SECRET_CUSTOMER", response.text)


if __name__ == "__main__":
    unittest.main()
