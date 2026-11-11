"""API/transaction checks with actual ORM persistence, isolated from live data.

Run directly with unittest for SQLite checks. The platform suite additionally
runs these under its usual PostgreSQL-backed application environment.
"""
import os
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET", "maintenance-tests-only-secret-at-least-32-bytes")

import unittest
from datetime import date
from types import SimpleNamespace
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.auth_context import get_current_user_id
from app.tenant_context import get_current_tenant, get_current_tenant_membership
from app.models import Product, Tenant, User
from app.products.fieldnest import maintenance as m
from app.products.fieldnest.api import router as workspace_router
from app.products.fieldnest.models import FieldNestProperty, FieldNestVendor, FieldNestWorkOrder


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        @event.listens_for(self.engine, "connect")
        def foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
        names = ["products", "tenants", "users", "fieldnest_properties", "fieldnest_vendors", "fieldnest_residents", "fieldnest_work_orders", "fieldnest_maintenance_plans", "fieldnest_maintenance_occurrences"]
        Base.metadata.create_all(self.engine, tables=[Base.metadata.tables[n] for n in names])
        with Session(self.engine) as db:
            db.add(Product(id=1, name="FieldNest", slug="fieldnest", status="active", workspace_key="fieldnest")); db.flush()
            db.add_all([Tenant(id=i, product_id=1, name=f"Company {i}", slug=f"company-{i}") for i in (1,2)])
            db.add(User(id=1, email="sample@example.test", display_name="Sample")); db.flush()
            db.add_all([FieldNestProperty(id=i, tenant_id=i, name=f"Property {i}", address="Sample address") for i in (1,2)])
            db.add_all([FieldNestVendor(id=i, tenant_id=i, name=f"Vendor {i}", trade="Maintenance") for i in (1,2)])
            db.commit()
        self.tenant = 1
        app = FastAPI(); app.include_router(m.router); app.include_router(workspace_router)
        def session():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_db] = session
        app.dependency_overrides[get_current_tenant] = lambda: SimpleNamespace(id=self.tenant)
        app.dependency_overrides[get_current_user_id] = lambda: 1
        app.dependency_overrides[get_current_tenant_membership] = lambda: SimpleNamespace(role="owner")
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close(); self.engine.dispose()

    def plan(self, **changes):
        data = dict(property_id=1, vendor_id=1, title="Filter", interval_months=1, next_due="2024-01-31")
        response = self.client.post("/maintenance-plans", json={**data, **changes})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def generate(self, p):
        return self.client.post(f'/maintenance-plans/{p["id"]}/generate', json={"scheduled_date":p["next_due"]})

    def test_month_end_and_leap_year_keep_anchor(self):
        self.assertEqual(m.next_due_date(date(2024,1,31),1,31), date(2024,2,29))
        self.assertEqual(m.next_due_date(date(2024,2,29),1,31), date(2024,3,31))
        self.assertEqual(m.next_due_date(date(2024,2,29),12,29), date(2025,2,28))

    def test_generate_retry_completion_and_history(self):
        p=self.plan(); first=self.generate(p); self.assertEqual(first.status_code,200,first.text)
        order=first.json(); self.assertEqual(order["vendor_id"],1)
        self.assertEqual(self.generate(p).json()["id"],order["id"])
        path=f'/work-orders/{order["id"]}'
        for _ in range(2):
            response=self.client.patch(path,json={"status":"completed"});self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(self.client.get('/maintenance-plans').json()[0]['next_due'],'2024-02-29')
        history=self.client.get('/maintenance-occurrences').json()
        self.assertEqual(len(history),1);self.assertIsNotNone(history[0]['completed_at'])
        self.assertEqual(self.generate(p).json()['id'],order['id'])
        self.assertEqual(self.client.patch(path,json={"status":"open"}).status_code,409)
        self.assertEqual(self.client.delete(path).status_code,409)
        # Advance the next overdue occurrence, without silently skipping backlog.
        second=self.generate(self.client.get('/maintenance-plans').json()[0]).json()
        self.client.patch(f'/work-orders/{second["id"]}',json={"status":"completed"})
        self.assertEqual(self.client.get('/maintenance-plans').json()[0]['next_due'],'2024-03-31')

    def test_pause_resume_and_future_due(self):
        p=self.plan();path=f'/maintenance-plans/{p["id"]}'
        self.assertEqual(self.client.patch(path,json={"paused":True}).status_code,200)
        self.assertEqual(self.generate(p).status_code,409)
        self.client.patch(path,json={"paused":False})
        self.assertEqual(self.generate(p).status_code,200)
        self.assertEqual(self.generate(self.plan(next_due='2090-01-01')).status_code,409)

    def test_cross_company_ids_and_lists_are_isolated(self):
        for field in ['property_id','vendor_id']:
            r=self.client.post('/maintenance-plans',json={"title":"Task","property_id":1,"next_due":"2024-01-31",field:2})
            self.assertEqual(r.status_code,404)
        p=self.plan(); order=self.generate(p).json();self.tenant=2
        self.assertEqual(self.client.get('/maintenance-plans').json(),[])
        self.assertEqual(self.client.get('/maintenance-occurrences').json(),[])
        self.assertEqual(self.generate(p).status_code,404)
        self.assertEqual(self.client.patch(f'/maintenance-plans/{p["id"]}',json={"paused":True}).status_code,404)
        self.assertEqual(self.client.patch(f'/work-orders/{order["id"]}',json={"status":"completed"}).status_code,404)

    def test_stale_date_and_invalid_input(self):
        p=self.plan()
        self.assertEqual(self.client.post(f'/maintenance-plans/{p["id"]}/generate',json={"scheduled_date":"2024-02-01"}).status_code,409)
        for changes in [{"title":"   "},{"interval_months":2},{"next_due":"bad"},{"paused":True}]:
            self.assertEqual(self.client.post('/maintenance-plans',json={"property_id":1,"title":"Task","next_due":"2024-01-31",**changes}).status_code,422)

    def test_completion_failure_rolls_back_history(self):
        p=self.plan(); order=self.generate(p).json()
        r=self.client.patch(f'/work-orders/{order["id"]}',json={"status":"completed","vendor_id":2})
        self.assertEqual(r.status_code,404)
        self.assertEqual(self.client.get('/maintenance-plans').json()[0]['next_due'],p['next_due'])
        self.assertIsNone(self.client.get('/maintenance-occurrences').json()[0]['completed_at'])

    def test_migration_matches_models_and_preserves_existing_orders(self):
        import importlib.util
        from pathlib import Path
        from alembic.migration import MigrationContext
        from alembic.operations import Operations
        from alembic.autogenerate import compare_metadata
        path = Path(__file__).resolve().parents[1] / 'app/products/fieldnest/migrations/versions/c8e0a2b4d637_add_maintenance_plans.py'
        spec = importlib.util.spec_from_file_location('maintenance_migration', path)
        migration = importlib.util.module_from_spec(spec); spec.loader.exec_module(migration)
        names = {'fieldnest_maintenance_occurrences', 'fieldnest_maintenance_plans'}
        m.Occurrence.__table__.drop(self.engine); m.Plan.__table__.drop(self.engine)
        with self.engine.begin() as connection:
            context = MigrationContext.configure(connection)
            with Operations.context(context):
                migration.upgrade()
            def include_object(obj, name, kind, reflected, compare_to):
                return name in names if kind == 'table' else True
            drift = MigrationContext.configure(connection, opts={'include_object': include_object})
            self.assertEqual(compare_metadata(drift, Base.metadata), [])
            with Operations.context(context):
                migration.downgrade()
                migration.upgrade()
        p = self.plan(); order = self.generate(p).json()
        with self.engine.begin() as connection:
            with Operations.context(MigrationContext.configure(connection)):
                with self.assertRaisesRegex(RuntimeError, 'Maintenance plans exist'):
                    migration.downgrade()
        self.assertEqual(self.client.get('/work-orders').json()[0]['id'], order['id'])

    def test_cancellation_is_explicitly_blocked(self):
        order=self.generate(self.plan()).json()
        self.assertEqual(self.client.patch(f'/work-orders/{order["id"]}',json={"status":"cancelled"}).status_code,409)


if __name__ == '__main__':
    unittest.main()


def test_postgres_concurrent_generation_and_completion(db_session):
    """Run under platform pytest/real PostgreSQL; exercise cross-session locks."""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from app.products.fieldnest.api import update_work_order
    from app.products.fieldnest.schemas import WorkOrderUpdate
    if db_session.bind.dialect.name != 'postgresql':
        import pytest
        pytest.skip('PostgreSQL is required to validate row-lock concurrency')
    product=Product(name='Maintenance test',slug='maintenance-test',status='active',workspace_key='fieldnest')
    db_session.add(product);db_session.flush()
    tenant=Tenant(product_id=product.id,name='Maintenance company',slug='maintenance-concurrency')
    user=User(email='maintenance-concurrency@example.test',display_name='Sample')
    db_session.add_all([tenant,user]);db_session.flush()
    prop=FieldNestProperty(tenant_id=tenant.id,name='Sample property',address='Sample address')
    db_session.add(prop);db_session.flush()
    plan=m.Plan(tenant_id=tenant.id,property_id=prop.id,title='Monthly check',interval_months=1,anchor_day=31,next_due=date(2024,1,31))
    db_session.add(plan);db_session.commit()
    tenant_id,user_id,plan_id=tenant.id,user.id,plan.id
    engine=db_session.get_bind();gate=Barrier(4)
    def generate(_):
        with Session(engine) as session:
            gate.wait(timeout=15)
            return m.generate_order(plan_id,m.GenerateRequest(scheduled_date=date(2024,1,31)),session,SimpleNamespace(id=tenant_id),user_id).id
    with ThreadPoolExecutor(max_workers=4) as pool:
        ids=list(pool.map(generate,range(4)))
    assert len(set(ids))==1
    gate=Barrier(4)
    def complete(_):
        with Session(engine) as session:
            gate.wait(timeout=15)
            update_work_order(ids[0],WorkOrderUpdate(status='completed'),session,SimpleNamespace(id=tenant_id))
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(complete,range(4)))
    db_session.expire_all()
    assert db_session.get(m.Plan,plan_id).next_due==date(2024,2,29)
    assert len(db_session.scalars(select(m.Occurrence).where(m.Occurrence.plan_id==plan_id)).all())==1
