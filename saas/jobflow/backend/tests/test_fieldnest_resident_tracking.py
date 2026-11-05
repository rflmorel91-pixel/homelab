import base64
from datetime import datetime, timedelta, timezone
import importlib.util
from io import BytesIO
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import struct
import sys
import unittest
from unittest.mock import patch
import zlib

if __name__ == "__main__":
    os.environ["DATABASE_URL"] = "sqlite://"
    os.environ.setdefault("JWT_SECRET", "synthetic-resident-tracking-tests-32-bytes")
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image
from sqlalchemy import select, func
from app.products.fieldnest.models import FieldNestPhoto, FieldNestWorkOrder
from app.products.fieldnest.resident_tracking import public_tracking_router, tracking_router, owner_tracking_router

spec = importlib.util.spec_from_file_location("_tracking_fixture", Path(__file__).with_name("test_fieldnest_resident_requests.py"))
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
PREFIX = fixture.PREFIX


class ResidentTracking(unittest.TestCase):
    def setUp(self):
        self.fx = fixture.ResidentRequests()
        self.fx.setUp()
        for router in [public_tracking_router, tracking_router, owner_tracking_router]:
            self.fx.client.app.include_router(router, prefix=PREFIX)
        self.client, self.db = self.fx.client, self.fx.db

    def tearDown(self):
        self.fx.tearDown()

    def photo(self, kind="PNG"):
        stream = BytesIO()
        image = Image.new("RGB", (12, 10), "green")
        if kind == "JPEG":
            exif = Image.Exif(); exif[315] = "Private camera owner"
            image.save(stream, format=kind, exif=exif)
        else:
            image.save(stream, format=kind)
        return {"data": base64.b64encode(stream.getvalue()).decode()}

    def report(self, photos=True):
        token = self.fx.link()
        payload = self.fx.issue(token)
        secret = secrets.token_urlsafe(32)
        payload["tracking_secret"] = secret
        payload["photos"] = [self.photo()] if photos else []
        response = self.client.post(f"{PREFIX}/public/maintenance", json=payload)
        self.assertEqual(response.status_code, 201, response.text)
        order = self.db.scalar(select(FieldNestWorkOrder).order_by(FieldNestWorkOrder.id.desc()))
        return secret, payload, order, response

    def context(self, secret):
        return self.client.post(f"{PREFIX}/public/resident/context", json={"token": secret})

    def test_tracking_page_client_flow(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node is required for private tracking page checks")
        root = Path(__file__).resolve().parents[2]
        subprocess.run([node, str(root / "scripts/tests/test_fieldnest_resident_tracking.cjs")], check=True)

    def test_private_page_contains_only_one_request_and_no_contacts(self):
        secret, payload, order, response = self.report()
        self.assertEqual(response.json()["tracking_path"], f"/fieldnest/resident#{secret}")
        context = self.context(secret)
        self.assertEqual(context.status_code, 200)
        data = context.json()
        self.assertEqual(set(data), {"reference", "title", "unit", "status", "received_at", "updated_at", "photos"})
        self.assertEqual((data["reference"], data["unit"], data["status"]), (f"FN-{order.id}", "3B", "open"))
        self.assertNotIn(payload["contact"], context.text)
        self.assertNotIn(order.tracking_token_hash, context.text)
        self.assertEqual(context.headers["cache-control"], "no-store")

    def test_shared_property_link_cannot_read_private_requests(self):
        secret, payload, order, response = self.report()
        self.assertEqual(self.context(payload["token"]).status_code, 404)
        self.assertEqual(self.context(secrets.token_urlsafe(32)).status_code, 404)
        self.assertEqual(self.client.post(f"{PREFIX}/public/resident/context",
                         json={"token": secret, "work_order_id": order.id + 1}).status_code, 422)

    def test_latest_status_reflects_manager_change(self):
        secret, _, order, _ = self.report(False)
        order.status = "completed"; self.db.commit()
        self.assertEqual(self.context(secret).json()["status"], "completed")

    def test_photo_is_normalized_and_metadata_is_removed(self):
        payload = self.fx.issue(self.fx.link())
        payload["tracking_secret"] = secrets.token_urlsafe(32)
        payload["photos"] = [self.photo("JPEG")]
        self.assertEqual(self.client.post(f"{PREFIX}/public/maintenance", json=payload).status_code, 201)
        photo = self.db.scalar(select(FieldNestPhoto))
        self.assertLessEqual(photo.byte_size, 512 * 1024)
        with Image.open(BytesIO(photo.content)) as image:
            self.assertEqual(image.format, "JPEG")
            self.assertEqual(dict(image.getexif()), {})
            self.assertNotIn("Private camera owner", str(image.info))

    def test_photo_access_is_scoped_to_request_and_company(self):
        secret, _, order, _ = self.report()
        photo_id = self.context(secret).json()["photos"][0]["id"]
        path = f"{PREFIX}/public/resident/photos/{photo_id}"
        response = self.client.post(path, json={"token": secret})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"\xff\xd8"))
        self.assertEqual(response.headers["content-type"], "image/jpeg")
        other_secret, _, _, _ = self.report(False)
        self.assertEqual(self.client.post(path, json={"token": other_secret}).status_code, 404)
        self.fx.tenant = self.fx.other
        self.assertEqual(self.client.get(f"{PREFIX}/work-orders/{order.id}/photos/{photo_id}").status_code, 404)

    def test_duplicate_submission_does_not_duplicate_photos(self):
        secret, payload, _, first = self.report()
        second = self.client.post(f"{PREFIX}/public/maintenance", json=payload)
        self.assertEqual(first.json(), second.json())
        self.assertEqual(self.db.scalar(select(func.count()).select_from(FieldNestPhoto)), 1)

    def test_owner_rotation_and_revocation(self):
        secret, _, order, _ = self.report()
        result = self.client.post(f"{PREFIX}/work-orders/{order.id}/tracking-link")
        self.assertEqual(result.status_code, 200)
        replacement = result.json()["path"].split("#")[1]
        self.assertEqual(self.context(secret).status_code, 404)
        self.assertEqual(self.context(replacement).status_code, 200)
        self.assertEqual(self.client.delete(f"{PREFIX}/work-orders/{order.id}/tracking-link").status_code, 204)
        self.assertEqual(self.context(replacement).status_code, 404)

    def test_expiry_and_suspended_tenant_block_tracking(self):
        secret, _, order, _ = self.report()
        order.tracking_token_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1); self.db.commit()
        self.assertEqual(self.context(secret).status_code, 404)
        order.tracking_token_expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        self.fx.tenant.status = "suspended"; self.db.commit()
        self.assertEqual(self.context(secret).status_code, 404)

    def test_owner_controls_deny_members_and_other_companies(self):
        secret, _, order, _ = self.report(False)
        self.fx.is_owner = False
        self.assertEqual(self.client.post(f"{PREFIX}/work-orders/{order.id}/tracking-link").status_code, 403)
        self.fx.is_owner = True; self.fx.tenant = self.fx.other
        self.assertEqual(self.client.delete(f"{PREFIX}/work-orders/{order.id}/tracking-link").status_code, 404)

    def test_invalid_or_excess_photos_create_no_work_order(self):
        payload = self.fx.issue(self.fx.link())
        for photos, status in [
            ([{"data": "not-base64"}], 422),
            ([{"data": base64.b64encode(b"<svg>not a photo</svg>").decode()}], 415),
            ([self.photo("GIF")], 415),
            ([self.photo()] * 4, 422),
            ([{"data": base64.b64encode(b"x" * (2 * 1024 * 1024 + 1)).decode()}], 413),
        ]:
            response = self.client.post(f"{PREFIX}/public/maintenance", json={**payload, "photos": photos})
            self.assertEqual(response.status_code, status, response.text)
        self.assertEqual(self.db.scalar(select(func.count()).select_from(FieldNestWorkOrder)), 0)

    def test_oversized_dimensions_are_rejected_before_decode(self):
        raw = base64.b64decode(self.photo()["data"])
        ihdr = struct.pack(">II", 4000, 4000) + raw[24:29]
        raw = raw[:16] + ihdr + struct.pack(">I", zlib.crc32(b"IHDR" + ihdr)) + raw[33:]
        payload = self.fx.issue(self.fx.link())
        response = self.client.post(f"{PREFIX}/public/maintenance",
                                   json={**payload, "photos": [{"data": base64.b64encode(raw).decode()}]})
        self.assertEqual(response.status_code, 413)

    def test_photo_storage_quota_is_enforced(self):
        payload = self.fx.issue(self.fx.link())
        with patch("app.products.fieldnest.resident_tracking.MAX_TENANT_BYTES", 10):
            response = self.client.post(f"{PREFIX}/public/maintenance", json={**payload, "photos": [self.photo()]})
        self.assertEqual(response.status_code, 413)
        self.assertEqual(self.db.scalar(select(func.count()).select_from(FieldNestWorkOrder)), 0)


if __name__ == "__main__":
    unittest.main()
