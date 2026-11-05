"""Synthetic upload endpoint checks; python -B tests/test_document_storage_limits.py."""
from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

if __name__ == "__main__":
    os.environ["DATABASE_URL"] = "sqlite://"
    os.environ["JWT_SECRET"] = "synthetic-document-capacity-secret-32-bytes"
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, update
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth_context import get_current_user_id
from app.database import Base, get_db
from app.models import Product, Tenant, TenantMembership, User
from app.products.prestamodesk import applications_api, document_capacity
from app.products.prestamodesk.models import (
    ApplicationReviewDocument, ApplicationReviewEvent, LoanApplication,
)

PREFIX = "/api/v1/products/prestamodesk/applications"
PDF = b"%PDF-1.4\nSynthetic capacity test\n"


def synthetic_application(tenant_id):
    return LoanApplication(
        tenant_id=tenant_id, full_name="Synthetic applicant",
        principal_amount=Decimal("1000"), flat_interest_rate_percent=Decimal("10"),
        total_interest=Decimal("100"), total_due=Decimal("1100"),
        installment_count=1, start_date=date(2026, 11, 1),
        first_payment_date=date(2026, 12, 1), consented_at=datetime.now(timezone.utc),
        consent_notice_version="synthetic-test", status="new",
    )


class DocumentStorageLimits(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.addCleanup(self.engine.dispose)
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.storage = Path(self.directory.name) / "documents"
        env = patch.dict(os.environ, {"PRESTAMODESK_PRIVATE_STORAGE_PATH": str(self.storage)})
        env.start()
        self.addCleanup(env.stop)
        with Session(self.engine) as db:
            product = Product(name="PréstamoDesk", slug="prestamodesk", workspace_key="prestamodesk")
            user = User(email="capacity@example.test", display_name="Synthetic owner", is_active=True)
            db.add_all([product, user]); db.flush()
            tenants = [Tenant(product_id=product.id, name=name, slug=name, status="active")
                       for name in ("capacity-one", "capacity-two")]
            db.add_all(tenants); db.flush()
            db.add_all([TenantMembership(tenant_id=t.id, user_id=user.id, role="owner") for t in tenants])
            applications = [synthetic_application(tenants[0].id), synthetic_application(tenants[0].id),
                            synthetic_application(tenants[1].id)]
            db.add_all(applications); db.flush()
            self.user_id = user.id
            self.tenants = [t.id for t in tenants]
            self.applications = [a.id for a in applications]
            db.commit()
        app = FastAPI()
        app.include_router(applications_api.router, prefix="/api/v1/products/prestamodesk")

        def session():
            with Session(self.engine) as db:
                yield db

        app.dependency_overrides[get_db] = session
        app.dependency_overrides[get_current_user_id] = lambda: self.user_id
        self.client = TestClient(app, raise_server_exceptions=False)
        self.addCleanup(self.client.close)

    def limits(self, **changes):
        patched = patch.object(document_capacity, "DOCUMENT_LIMITS",
                               replace(document_capacity.DOCUMENT_LIMITS, **changes))
        patched.start()
        self.addCleanup(patched.stop)

    def upload(self, index=0, kind="identity", content=PDF, tenant_index=0):
        return self.client.put(
            f"{PREFIX}/{self.applications[index]}/documents/{kind}", content=content,
            headers={"Content-Type": "application/pdf", "X-Tenant-ID": str(self.tenants[tenant_index])},
        )

    def counts(self):
        with Session(self.engine) as db:
            return tuple(db.scalar(select(func.count()).select_from(model))
                         for model in (ApplicationReviewDocument, ApplicationReviewEvent))

    def files(self):
        return sorted(p for p in self.storage.rglob("*") if p.is_file())

    def test_exact_byte_limit_then_rejection_preserves_existing_download(self):
        self.limits(tenant_bytes=2 * len(PDF))
        first = self.upload(); self.assertEqual(first.status_code, 201, first.text)
        self.assertEqual(self.upload(index=1).status_code, 201)
        self.assertEqual(self.upload().status_code, 413)
        self.assertEqual(self.counts(), (2, 2))
        self.assertEqual(len(self.files()), 2)
        ref = first.json()["storage_ref"]
        downloaded = self.client.get(f"{PREFIX}/{self.applications[0]}/documents/identity/{ref}",
                                     headers={"X-Tenant-ID": str(self.tenants[0])})
        self.assertEqual(downloaded.status_code, 200)
        self.assertEqual(downloaded.content, PDF)

    def test_tenant_document_limit_spans_applications(self):
        self.limits(tenant_documents=2)
        self.assertEqual(self.upload().status_code, 201)
        self.assertEqual(self.upload(index=1).status_code, 201)
        self.assertEqual(self.upload(index=1, kind="income").status_code, 409)
        self.assertEqual(self.counts(), (2, 2))

    def test_application_limit_spans_document_types(self):
        self.limits(application_documents=2)
        self.assertEqual(self.upload().status_code, 201)
        self.assertEqual(self.upload(kind="income").status_code, 201)
        self.assertEqual(self.upload(kind="contract").status_code, 409)
        self.assertEqual(self.upload(index=1).status_code, 201)

    def test_version_limit_rejects_repeated_same_document(self):
        self.limits(document_versions=2)
        for _ in range(2):
            self.assertEqual(self.upload().status_code, 201)
        self.assertEqual(self.upload().status_code, 409)
        self.assertEqual(self.upload(kind="income").status_code, 201)
        self.assertEqual(self.upload(index=1).status_code, 201)

    def test_exhausted_tenant_does_not_consume_other_tenant_allocation(self):
        self.limits(tenant_bytes=len(PDF), tenant_documents=1)
        self.assertEqual(self.upload().status_code, 201)
        self.assertEqual(self.upload(index=1).status_code, 413)
        self.assertEqual(self.upload(index=2, tenant_index=1).status_code, 201)

    def test_cross_tenant_application_is_rejected_without_storage(self):
        self.assertEqual(self.upload(index=2).status_code, 404)
        self.assertEqual(self.counts(), (0, 0))
        self.assertEqual(self.files(), [])

    def test_invalid_and_oversized_uploads_leave_no_rows_or_files(self):
        self.assertEqual(self.upload(content=b"not a pdf").status_code, 415)
        self.assertEqual(self.upload(content=b"%PDF-" + b"x" * (8 * 1024 * 1024)).status_code, 413)
        self.assertEqual(self.counts(), (0, 0))
        self.assertEqual(self.files(), [])

    def test_metadata_failure_removes_file_and_releases_capacity(self):
        self.limits(tenant_bytes=len(PDF))
        with patch.object(applications_api, "write_review_event", side_effect=RuntimeError("synthetic")):
            self.assertEqual(self.upload().status_code, 500)
        self.assertEqual(self.counts(), (0, 0))
        self.assertEqual(self.files(), [])
        self.assertEqual(self.upload().status_code, 201)

    def test_commit_failure_removes_file_and_releases_capacity(self):
        self.limits(tenant_bytes=len(PDF))
        with patch.object(Session, "commit", side_effect=RuntimeError("synthetic commit")):
            self.assertEqual(self.upload().status_code, 500)
        self.assertEqual(self.counts(), (0, 0))
        self.assertEqual(self.files(), [])
        self.assertEqual(self.upload().status_code, 201)

    def test_application_status_is_refreshed_after_streaming(self):
        def content():
            with Session(self.engine) as db:
                db.execute(update(LoanApplication).where(LoanApplication.id == self.applications[0])
                           .values(status="approved"))
                db.commit()
            yield PDF
        self.assertEqual(self.upload(content=content()).status_code, 409)
        self.assertEqual(self.counts(), (0, 0))
        self.assertEqual(self.files(), [])

    def test_suspended_tenant_cannot_upload(self):
        with Session(self.engine) as db:
            db.execute(update(Tenant).where(Tenant.id == self.tenants[0]).values(status="suspended"))
            db.commit()
        self.assertEqual(self.upload().status_code, 403)
        self.assertEqual(self.files(), [])


if __name__ == "__main__":
    unittest.main()
