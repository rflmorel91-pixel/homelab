"""Independent PostgreSQL transactions prove dispatch and pending-slot locking."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from hashlib import sha256
from threading import Barrier, Lock
from uuid import uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.models import Product, Tenant, TenantMembership, User
from app.products.fieldnest import email_limits
from app.products.fieldnest.models import (
    FieldNestEmailAttempt, FieldNestNotification, FieldNestProperty, FieldNestWorkOrder,
)
from app.products.fieldnest.notifications import deliver_one, queue_request_notifications


def setup_businesses(db, same_tenant=False):
    product = db.scalar(select(Product).where(Product.slug == "fieldnest"))
    owner = User(email="concurrency-owner@example.test", display_name="Synthetic owner", is_active=True)
    db.add(owner); db.flush()
    tenants = [Tenant(product_id=product.id, name=f"Synthetic {i}", slug=f"mail-budget-{i}", status="active")
               for i in range(1 if same_tenant else 2)]
    db.add_all(tenants); db.flush()
    properties = [FieldNestProperty(tenant_id=t.id, name="Synthetic property", address="Synthetic address")
                  for t in tenants]
    db.add_all(properties)
    db.add_all([TenantMembership(tenant_id=t.id, user_id=owner.id, role="owner", is_active=True)
                for t in tenants])
    db.flush()
    targets = [(t.id, prop.id) for t, prop in zip(tenants, properties)]
    db.commit()
    return targets if len(targets) == 2 else targets * 2


@pytest.mark.parametrize("budget", [
    "receipt_hour", "receipt_day", "recipient_hour", "recipient_day",
    "tenant_hour", "tenant_day", "platform_hour", "platform_day",
])
def test_parallel_dispatchers_cannot_both_claim_last_send(raw_client, db_session, monkeypatch, budget):
    engine = db_session.get_bind()
    assert engine.dialect.name == "postgresql"
    targets = setup_businesses(db_session, same_tenant=budget.startswith("tenant"))
    same_recipient = budget.startswith(("receipt", "recipient"))
    for index, (tenant_id, property_id) in enumerate(targets):
        order = FieldNestWorkOrder(tenant_id=tenant_id, property_id=property_id, title="Synthetic concurrent report")
        db_session.add(order); db_session.flush()
        db_session.add(FieldNestNotification(
            tenant_id=tenant_id, work_order_id=order.id, kind="receipt",
            receipt_email=f"recipient-{0 if same_recipient else index}@example.test",
            event_key=sha256(str(uuid4()).encode()).hexdigest(),
        ))
    db_session.commit()
    monkeypatch.setattr(email_limits, "EMAIL_LIMITS", replace(email_limits.EMAIL_LIMITS, **{budget: 1}))
    barrier = Barrier(2)
    original_lock = email_limits.lock_email_delivery

    def synchronized_lock(db):
        db.execute(text("SET LOCAL lock_timeout = '5s'"))
        db.execute(text("SET LOCAL statement_timeout = '10s'"))
        barrier.wait(timeout=5)
        original_lock(db)

    monkeypatch.setattr(email_limits, "lock_email_delivery", synchronized_lock)
    calls = []
    sender_lock = Lock()

    def sender(message, config):
        with sender_lock:
            calls.append(message["Message-ID"])

    factory = sessionmaker(bind=engine)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: deliver_one(factory, sender, lambda: {"from_email": "test@example.test"}), range(2)))
    assert results == [True, True]
    assert len(calls) == 1
    assert sorted(db_session.scalars(select(FieldNestNotification.status)).all()) == ["sent", "suppressed"]
    assert db_session.scalar(select(func.count()).select_from(FieldNestEmailAttempt)) == 1


def test_pending_queue_limit_does_not_deadlock_fk_inserts_or_lose_reports(raw_client, db_session, monkeypatch):
    engine = db_session.get_bind()
    assert engine.dialect.name == "postgresql"
    targets = setup_businesses(db_session, same_tenant=True)
    monkeypatch.setattr(email_limits, "EMAIL_LIMITS", replace(email_limits.EMAIL_LIMITS, tenant_pending=1))
    barrier = Barrier(2)

    def report(target):
        with Session(engine) as db:
            db.execute(text("SET LOCAL lock_timeout = '5s'"))
            db.execute(text("SET LOCAL statement_timeout = '10s'"))
            order = FieldNestWorkOrder(tenant_id=target[0], property_id=target[1], title="Synthetic pending-slot report")
            db.add(order); db.flush()  # Both FK KEY SHARE locks precede queue admission.
            barrier.wait(timeout=5)
            queue_request_notifications(db, order)
            db.commit()

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(report, targets))
    assert sorted(db_session.scalars(select(FieldNestNotification.status)).all()) == ["pending", "suppressed"]
    assert db_session.scalar(select(func.count()).select_from(FieldNestWorkOrder)) == 2
