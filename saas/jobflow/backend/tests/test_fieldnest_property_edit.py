"""Property edits against a real isolated database and the workspace API router."""
import os
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET", "property-edit-tests-only-secret-at-least-32-bytes")

import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models import Product, Tenant, User
from app.tenant_context import get_current_tenant
from app.products.fieldnest.api import router
from app.products.fieldnest.models import (
    FieldNestProperty, FieldNestResident, FieldNestWorkOrder, FieldNestMaintenancePlan,
)


class PropertyEditTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        @event.listens_for(self.engine, "connect")
        def foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
        names = ["products", "tenants", "users", "fieldnest_properties", "fieldnest_residents", "fieldnest_vendors", "fieldnest_work_orders", "fieldnest_maintenance_plans"]
        Base.metadata.create_all(self.engine, tables=[Base.metadata.tables[name] for name in names])
        with Session(self.engine) as db:
            db.add(Product(id=1, name="FieldNest", slug="fieldnest", status="active", workspace_key="fieldnest")); db.flush()
            db.add_all([Tenant(id=i, product_id=1, name=f"Company {i}", slug=f"company-{i}") for i in (1, 2)])
            db.add(User(id=1, email="sample@example.test", display_name="Sample")); db.flush()
            db.add_all([FieldNestProperty(id=i, tenant_id=i, name=f"Building {i}", address=f"Address {i}", total_units=12, request_token_hash=f"test-only-hash-{i}") for i in (1, 2)])
            db.flush()
            db.add(FieldNestResident(id=1, tenant_id=1, property_id=1, name="Sample Resident", unit="1A"))
            db.add(FieldNestWorkOrder(id=1, tenant_id=1, property_id=1, title="Sample repair", created_by_user_id=1))
            db.add(FieldNestMaintenancePlan(id=1, tenant_id=1, property_id=1, title="Inspection", interval_months=1, anchor_day=15, next_due=date(2026, 12, 15)))
            db.commit()
        self.tenant = 1
        app = FastAPI(); app.include_router(router)
        def session():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_db] = session
        app.dependency_overrides[get_current_tenant] = lambda: SimpleNamespace(id=self.tenant)
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close(); self.engine.dispose()

    def update(self, data, property_id=1):
        return self.client.patch(f"/properties/{property_id}", json=data)

    def test_partial_patch_preserves_identity_other_fields_and_request_link(self):
        before = self.client.get("/properties").json()[0]
        response = self.update({"name": "  Corrected Building  "})
        self.assertEqual(response.status_code, 200, response.text)
        row = response.json()
        self.assertEqual(row["name"], "Corrected Building")
        for field in ["id", "address", "total_units", "property_type", "created_at"]:
            self.assertEqual(row[field], before[field])
        with Session(self.engine) as db:
            prop = db.get(FieldNestProperty, 1)
            self.assertEqual(prop.tenant_id, 1)
            self.assertEqual(prop.request_token_hash, "test-only-hash-1")
        self.assertNotIn("request_token_hash", row)

    def test_address_units_and_type_update_in_place(self):
        response = self.update({"address": "  Correct address  ", "total_units": 15, "property_type": "multifamily"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["address"], "Correct address")
        self.assertEqual(response.json()["total_units"], 15)
        self.assertEqual(response.json()["property_type"], "multifamily")
        self.assertEqual(len(self.client.get("/properties").json()), 1)
        with Session(self.engine) as db:
            for model in [FieldNestResident, FieldNestWorkOrder, FieldNestMaintenancePlan]:
                self.assertEqual(db.get(model, 1).property_id, 1)

    def test_other_company_and_missing_ids_are_404(self):
        for property_id in [2, 999]:
            self.assertEqual(self.update({"name": "Wrong company"}, property_id).status_code, 404)
        self.tenant = 2
        self.assertEqual(self.update({"address": "Wrong company"}).status_code, 404)
        self.assertEqual(self.client.get("/properties").json()[0]["name"], "Building 2")

    def test_null_blank_bounds_and_unknown_fields_are_rejected(self):
        invalid = [{field: None} for field in ["name", "address", "total_units", "property_type"]]
        invalid += [{"name": "   "}, {"address": "\t"}, {"name": "x" * 161}, {"address": "x" * 301}, {"total_units": 0}, {"total_units": 10001}, {"total_units": 1.5}, {"property_type": "unknown"}, {"tenant_id": 2}, {"id": 2}, {"request_token_hash": "replacement"}]
        for data in invalid:
            with self.subTest(data=data):
                self.assertEqual(self.update(data).status_code, 422)
        self.assertEqual(self.client.get("/properties").json()[0]["name"], "Building 1")

    def test_empty_patch_preserves_property(self):
        before = self.client.get("/properties").json()
        self.assertEqual(self.update({}).status_code, 200)
        self.assertEqual(self.client.get("/properties").json(), before)

    def test_commit_failure_rolls_back(self):
        with patch.object(Session, "commit", side_effect=RuntimeError("Simulated commit failure")):
            with self.assertRaisesRegex(RuntimeError, "Simulated commit failure"):
                self.update({"name": "Do not persist"})
        self.assertEqual(self.client.get("/properties").json()[0]["name"], "Building 1")


if __name__ == "__main__":
    unittest.main()
