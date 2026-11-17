"""Vendor updates against the real API router and an isolated database."""
import unittest
from datetime import date
from unittest.mock import patch

from sqlalchemy.orm import Session

import test_fieldnest_property_edit as property_fixture
from app.products.fieldnest.models import (
    FieldNestVendor, FieldNestWorkOrder, FieldNestMaintenancePlan,
)


class VendorEditTests(unittest.TestCase):
    def setUp(self):
        property_fixture.PropertyEditTests.setUp(self)
        with Session(self.engine) as db:
            db.add_all([
                FieldNestVendor(
                    id=i, tenant_id=i, name=f"Vendor {i}", trade="Plumbing",
                    phone="555-0100", email="vendor@example.test",
                    insurance_expires=date(2026, 12, 1),
                ) for i in (1, 2)
            ])
            db.flush()
            db.get(FieldNestWorkOrder, 1).vendor_id = 1
            db.get(FieldNestMaintenancePlan, 1).vendor_id = 1
            db.commit()

    def tearDown(self):
        property_fixture.PropertyEditTests.tearDown(self)

    def update(self, data, vendor_id=1):
        return self.client.patch(f"/vendors/{vendor_id}", json=data)

    def test_partial_update_preserves_identity_and_assignments(self):
        before = self.client.get("/vendors").json()[0]
        response = self.update({"name": "  Corrected Vendor  "})
        self.assertEqual(response.status_code, 200, response.text)
        after = response.json()
        self.assertEqual(after["name"], "Corrected Vendor")
        for key in ("id", "trade", "phone", "email", "insurance_expires", "created_at"):
            self.assertEqual(after[key], before[key])
        self.assertEqual(len(self.client.get("/vendors").json()), 1)
        with Session(self.engine) as db:
            self.assertEqual(db.get(FieldNestVendor, 1).tenant_id, 1)
            self.assertEqual(db.get(FieldNestWorkOrder, 1).vendor_id, 1)
            self.assertEqual(db.get(FieldNestMaintenancePlan, 1).vendor_id, 1)

    def test_update_and_clear_optional_fields(self):
        response = self.update({
            "trade": "  Electrical  ", "phone": " 555-0200 ",
            "email": " corrected@example.test ", "insurance_expires": "2028-02-29",
        })
        self.assertEqual(response.status_code, 200, response.text)
        row = response.json()
        self.assertEqual(row["trade"], "Electrical")
        self.assertEqual(row["phone"], "555-0200")
        self.assertEqual(row["email"], "corrected@example.test")
        self.assertEqual(row["insurance_expires"], "2028-02-29")
        response = self.update({"phone": " ", "email": "", "insurance_expires": None})
        self.assertEqual(response.status_code, 200, response.text)
        for key in ("phone", "email", "insurance_expires"):
            self.assertIsNone(response.json()[key])

    def test_tenant_isolation_and_missing_vendor(self):
        for vendor_id in (2, 999):
            self.assertEqual(self.update({"name": "Wrong company"}, vendor_id).status_code, 404)
        self.tenant = 2
        self.assertEqual(self.update({"name": "Wrong company"}).status_code, 404)
        self.assertEqual(self.client.get("/vendors").json()[0]["name"], "Vendor 2")

    def test_invalid_updates_leave_record_unchanged(self):
        before = self.client.get("/vendors").json()
        invalid = [
            {"name": None}, {"trade": None}, {"name": " "}, {"trade": "\t"},
            {"name": "x" * 181}, {"trade": "x" * 101},
            {"phone": "x" * 61}, {"email": "x" * 321},
            {"insurance_expires": "2026-02-29"}, {"insurance_expires": "invalid"},
            {"tenant_id": 2}, {"id": 2}, {"created_at": "2026-01-01"},
        ]
        for data in invalid:
            with self.subTest(data=data):
                self.assertEqual(self.update(data).status_code, 422)
        self.assertEqual(self.client.get("/vendors").json(), before)

    def test_empty_patch_is_noop(self):
        before = self.client.get("/vendors").json()
        self.assertEqual(self.update({}).status_code, 200)
        self.assertEqual(self.client.get("/vendors").json(), before)

    def test_commit_failure_does_not_persist(self):
        with patch.object(Session, "commit", side_effect=RuntimeError("Simulated failure")):
            with self.assertRaisesRegex(RuntimeError, "Simulated failure"):
                self.update({"name": "Do not persist"})
        self.assertEqual(self.client.get("/vendors").json()[0]["name"], "Vendor 1")


if __name__ == "__main__":
    unittest.main()
