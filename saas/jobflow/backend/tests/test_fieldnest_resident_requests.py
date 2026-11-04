"""Resident intake checks against isolated SQLite tables; no customer data."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import unittest
from uuid import uuid4

if __name__ == "__main__":
    os.environ["DATABASE_URL"] = "sqlite://"
    os.environ.setdefault("JWT_SECRET", "synthetic-resident-request-tests-32-bytes")
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models import Product, Tenant, User
from app.products.fieldnest.models import FieldNestProperty, FieldNestResident, FieldNestVendor, FieldNestWorkOrder
from app.products.fieldnest.resident_requests import public_router, link_router
from app.tenant_context import get_current_tenant, require_current_tenant_owner

PREFIX = "/api/v1/products/fieldnest"


class ResidentRequests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        tables = [Product.__table__, Tenant.__table__, User.__table__, FieldNestProperty.__table__,
                  FieldNestResident.__table__, FieldNestVendor.__table__, FieldNestWorkOrder.__table__]
        Base.metadata.create_all(self.engine, tables=tables)
        self.db = Session(self.engine)
        product = Product(name="FieldNest", slug="fieldnest", status="active", workspace_key="fieldnest")
        self.db.add(product); self.db.flush()
        self.product = product
        self.tenant = Tenant(product_id=product.id, name="Demo", slug="resident-demo", status="active")
        self.other = Tenant(product_id=product.id, name="Other", slug="other-demo", status="active")
        self.db.add_all([self.tenant, self.other]); self.db.flush()
        self.prop = FieldNestProperty(tenant_id=self.tenant.id, name="Maple Court", address="Synthetic address", total_units=12)
        self.other_prop = FieldNestProperty(tenant_id=self.other.id, name="Other property", address="Synthetic other", total_units=2)
        self.db.add_all([self.prop, self.other_prop]); self.db.commit()
        self.is_owner = True
        app = FastAPI()
        app.include_router(public_router, prefix=PREFIX)
        app.include_router(link_router, prefix=PREFIX)
        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[get_current_tenant] = lambda: self.tenant
        def owner():
            if not self.is_owner:
                raise HTTPException(403, "Tenant owner access required")
        app.dependency_overrides[require_current_tenant_owner] = owner
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close(); self.db.close(); self.engine.dispose()

    def link(self, prop=None):
        response = self.client.post(f"{PREFIX}/properties/{(prop or self.prop).id}/request-link")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers["cache-control"], "no-store")
        return response.json()["path"].split("#")[1]

    def issue(self, token):
        return {"token": token, "submission_id": str(uuid4()), "name": "Demo Resident",
                "contact": "resident@example.test", "unit": "3B", "title": "Slow sink",
                "description": "Synthetic report: kitchen sink drains slowly."}

    def test_resident_form_client_flow(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node is required for resident form JavaScript checks")
        root = Path(__file__).resolve().parents[2]
        subprocess.run([node, str(root / "scripts/tests/test_fieldnest_resident_form.cjs")], check=True)

    def test_submit_routes_to_link_property_and_returns_no_private_data(self):
        token = self.link()
        context = self.client.post(f"{PREFIX}/public/maintenance/context", json={"token": token})
        self.assertEqual(context.json(), {"property_name": "Maple Court"})
        payload = self.issue(token)
        response = self.client.post(f"{PREFIX}/public/maintenance", json=payload)
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(set(response.json()), {"reference", "status"})
        row = self.db.scalar(select(FieldNestWorkOrder))
        self.assertEqual((row.tenant_id, row.property_id), (self.tenant.id, self.prop.id))
        self.assertEqual((row.status, row.priority), ("open", "normal"))
        self.assertIsNone(row.created_by_user_id)
        self.assertIsNone(row.resident_id)
        self.assertIn("resident@example.test", row.description)
        self.assertNotEqual(self.prop.request_token_hash, token)
        self.assertEqual(self.prop.request_token_hash, sha256(token.encode()).hexdigest())

    def test_retries_do_not_duplicate_work_orders(self):
        payload = self.issue(self.link())
        first = self.client.post(f"{PREFIX}/public/maintenance", json=payload)
        second = self.client.post(f"{PREFIX}/public/maintenance", json=payload)
        self.assertEqual(first.json(), second.json())
        self.assertEqual(self.db.scalar(select(func.count()).select_from(FieldNestWorkOrder)), 1)

    def test_rotation_and_revocation_disable_previous_links(self):
        old = self.link()
        current = self.link()
        self.assertNotEqual(old, current)
        self.assertEqual(self.client.post(f"{PREFIX}/public/maintenance", json=self.issue(old)).status_code, 404)
        response = self.client.delete(f"{PREFIX}/properties/{self.prop.id}/request-link")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.client.post(f"{PREFIX}/public/maintenance/context", json={"token": current}).status_code, 404)

    def test_expired_suspended_and_inactive_product_links_fail(self):
        token = self.link()
        self.prop.request_token_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        self.db.commit()
        self.assertEqual(self.client.post(f"{PREFIX}/public/maintenance", json=self.issue(token)).status_code, 404)
        token = self.link()
        self.tenant.status = "suspended"; self.db.commit()
        self.assertEqual(self.client.post(f"{PREFIX}/public/maintenance", json=self.issue(token)).status_code, 404)
        self.tenant.status = "active"; self.product.status = "inactive"; self.db.commit()
        self.assertEqual(self.client.post(f"{PREFIX}/public/maintenance", json=self.issue(token)).status_code, 404)

    def test_owner_and_cross_company_link_controls(self):
        self.assertEqual(self.client.post(f"{PREFIX}/properties/{self.other_prop.id}/request-link").status_code, 404)
        self.assertEqual(self.client.delete(f"{PREFIX}/properties/{self.other_prop.id}/request-link").status_code, 404)
        self.is_owner = False
        self.assertEqual(self.client.post(f"{PREFIX}/properties/{self.prop.id}/request-link").status_code, 403)
        self.assertEqual(self.client.delete(f"{PREFIX}/properties/{self.prop.id}/request-link").status_code, 403)

    def test_public_input_cannot_set_tenant_vendor_status_or_priority(self):
        payload = self.issue(self.link())
        for field, value in [("tenant_id", self.other.id), ("property_id", self.other_prop.id),
                             ("vendor_id", 1), ("status", "completed"), ("priority", "emergency")]:
            response = self.client.post(f"{PREFIX}/public/maintenance", json={**payload, field: value})
            self.assertEqual(response.status_code, 422)
        self.assertEqual(self.db.scalar(select(func.count()).select_from(FieldNestWorkOrder)), 0)

    def test_invalid_link_and_blank_fields_fail(self):
        self.assertEqual(self.client.post(f"{PREFIX}/public/maintenance", json=self.issue(secrets.token_urlsafe(32))).status_code, 404)
        payload = self.issue(self.link())
        for field in ["name", "contact", "unit", "title", "description"]:
            self.assertEqual(self.client.post(f"{PREFIX}/public/maintenance", json={**payload, field: " "}).status_code, 422)

    def test_reusing_submission_id_from_another_property_fails(self):
        payload = self.issue(self.link())
        self.assertEqual(self.client.post(f"{PREFIX}/public/maintenance", json=payload).status_code, 201)
        original = self.tenant
        self.tenant = self.other
        payload["token"] = self.link(self.other_prop)
        response = self.client.post(f"{PREFIX}/public/maintenance", json=payload)
        self.assertEqual(response.status_code, 409)
        self.tenant = original


if __name__ == "__main__":
    unittest.main()
