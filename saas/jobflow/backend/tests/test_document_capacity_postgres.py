"""PostgreSQL concurrency checks collected by the normal CI test suite."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier
from uuid import uuid4

from fastapi import HTTPException
import pytest
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models import Product, Tenant
from app.products.prestamodesk import document_capacity
from app.products.prestamodesk.models import ApplicationReviewDocument
from tests.test_document_storage_limits import PDF, synthetic_application


@pytest.mark.parametrize("limit,same_application,same_type,rejected_status", [
    ("tenant_bytes", False, False, 413),
    ("tenant_documents", False, False, 409),
    ("application_documents", True, False, 409),
    ("document_versions", True, True, 409),
])
def test_two_workers_cannot_claim_the_last_slot(
    raw_client, db_session, monkeypatch, limit, same_application, same_type, rejected_status,
):
    product = db_session.scalar(select(Product).where(Product.slug == "prestamodesk"))
    tenant = Tenant(product_id=product.id, name="Capacity race", slug="capacity-race", status="active")
    db_session.add(tenant); db_session.flush()
    applications = [synthetic_application(tenant.id), synthetic_application(tenant.id)]
    db_session.add_all(applications); db_session.flush()
    tenant_id = tenant.id
    application_ids = [a.id for a in applications]
    db_session.commit()
    # Independent transactions model separate API workers; SQLite cannot prove
    # PostgreSQL FOR UPDATE behavior, so these tests require the normal PG fixture.
    engine = db_session.get_bind()
    assert engine.dialect.name == "postgresql"
    maximum = len(PDF) if limit == "tenant_bytes" else 1
    monkeypatch.setattr(document_capacity, "DOCUMENT_LIMITS",
                        replace(document_capacity.DOCUMENT_LIMITS, **{limit: maximum}))
    barrier = Barrier(2)

    def upload(index):
        application_id = application_ids[0 if same_application else index]
        kind = "identity" if same_type or index == 0 else "income"
        with Session(engine) as db:
            db.execute(text("SET LOCAL lock_timeout = '5s'"))
            db.execute(text("SET LOCAL statement_timeout = '10s'"))
            barrier.wait(timeout=5)
            try:
                document_capacity.require_document_capacity(
                    db, tenant_id, application_id, kind, len(PDF),
                )
                reference = str(uuid4())
                db.add(ApplicationReviewDocument(
                    tenant_id=tenant_id, application_id=application_id,
                    document_type=kind, storage_ref=reference,
                    content_type="application/pdf", byte_size=len(PDF), sha256="0" * 64,
                    file_key=f"{tenant_id}/{application_id}/{reference}.pdf",
                ))
                db.commit()
                return 201
            except HTTPException as error:
                db.rollback()
                return error.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(upload, range(2)))
    assert sorted(results) == sorted([201, rejected_status])
    assert db_session.scalar(select(func.count()).select_from(ApplicationReviewDocument).where(
        ApplicationReviewDocument.tenant_id == tenant_id,
    )) == 1


def test_capacity_lock_refreshes_suspended_tenant(raw_client, db_session):
    product = db_session.scalar(select(Product).where(Product.slug == "prestamodesk"))
    tenant = Tenant(product_id=product.id, name="Suspended capacity", slug="suspended-capacity", status="suspended")
    db_session.add(tenant); db_session.commit()
    with pytest.raises(HTTPException) as error:
        document_capacity.require_document_capacity(db_session, tenant.id, 1, "identity", len(PDF))
    assert error.value.status_code == 403
    db_session.rollback()
