"""Isolated synthetic API/SQLite checks; no production database or network."""
from pathlib import Path
import os
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'backend'))
os.environ['DATABASE_URL'] = 'sqlite://'
os.environ['JWT_SECRET'] = 'synthetic-contact-tests-not-real-at-least32'
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.models import Product, Tenant
from app.tenant_context import get_current_tenant
from app.products.prestamodesk.authorization import require_prestamodesk_operations_member, require_prestamodesk_manager, require_roles, OPERATIONS_ROLES, ADMINISTRATION_ROLES
from app.products.prestamodesk.borrowers_api import router

URL = '/borrowers'


class ContactScenarios(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        with self.sessions() as db:
            product = Product(name='Synthetic PréstamoDesk', slug='prestamodesk', status='active', workspace_key='prestamodesk')
            db.add(product); db.flush()
            self.tenant = Tenant(product_id=product.id, name='Synthetic First', slug='contact-first', client_number=1)
            self.other = Tenant(product_id=product.id, name='Synthetic Second', slug='contact-second', client_number=2)
            db.add_all([self.tenant, self.other]); db.commit(); db.refresh(self.tenant); db.refresh(self.other); db.expunge_all()
        self.current = self.tenant
        self.membership = SimpleNamespace(role='owner', is_active=True)
        def db():
            with self.sessions() as session:
                yield session
        app = FastAPI(); app.include_router(router)
        app.dependency_overrides[get_db] = db
        app.dependency_overrides[get_current_tenant] = lambda: self.current
        app.dependency_overrides[require_prestamodesk_operations_member] = lambda: require_roles(self.membership, OPERATIONS_ROLES)
        app.dependency_overrides[require_prestamodesk_manager] = lambda: require_roles(self.membership, ADMINISTRATION_ROLES)
        self.client = TestClient(app)
        response = self.client.post(URL, json={'full_name':'SYNTHETIC Ana', 'document_type':'other', 'document_number':'SYN-CONTACT-001', 'status':'inactive', 'phone':'809-555-0101'})
        self.assertEqual(response.status_code, 201)
        self.record = response.json()
        self.url = f"{URL}/{self.record['id']}/contact"

    def tearDown(self):
        self.client.close(); self.engine.dispose()

    def payload(self, record=None):
        record = record or self.record
        return {key:record[key] for key in ['phone','email','address','municipality','province','notes']} | {'expected_updated_at':record['updated_at']}

    def test_preserve_identity_trim_clear_and_stale_retry(self):
        for role in ('owner','administrator'):
            self.membership.role = role
            data = self.payload() | {'phone':' 809-555-0102 ', 'email':' synthetic@example.test ', 'notes':' '}
            response = self.client.patch(self.url, json=data)
            self.assertEqual(response.status_code,200)
            saved = response.json()
            self.assertEqual(saved['phone'],'809-555-0102'); self.assertIsNone(saved['notes'])
            for key in ('id','full_name','document_type','document_number','status','created_at'):
                self.assertEqual(saved[key],self.record[key])
            self.assertEqual(self.client.patch(self.url,json=data).status_code,409)
            self.assertEqual(self.client.get(f"{URL}/{saved['id']}").json(),saved)
            cleared = self.client.patch(self.url,json=self.payload(saved)|{'phone':None,'email':None})
            self.assertEqual(cleared.status_code,200); self.assertIsNone(cleared.json()['phone'])
            self.record = cleared.json()

    def test_full_update_invalidates_snapshot(self):
        data = {key:value for key,value in self.record.items() if key not in ('id','created_at','updated_at')}
        data['full_name'] = 'SYNTHETIC Changed'
        self.assertEqual(self.client.put(f"{URL}/{self.record['id']}",json=data).status_code,200)
        self.assertEqual(self.client.patch(self.url,json=self.payload()).status_code,409)

    def test_validation_writes_nothing(self):
        for extra in ({'email':'bad'},{'phone':'x'*41},{'province':'x'*121},{'address':'x'*2001},{'notes':'x'*5001},{'full_name':'Changed'},{'status':'active'},{'expected_updated_at':'bad'}):
            with self.subTest(extra=next(iter(extra))):
                self.assertEqual(self.client.patch(self.url,json=self.payload()|extra).status_code,422)
                self.assertEqual(self.client.get(f"{URL}/{self.record['id']}").json(),self.record)
        missing = self.payload(); del missing['expected_updated_at']
        self.assertEqual(self.client.patch(self.url,json=missing).status_code,422)

    def test_other_roles_and_suspended_members_denied(self):
        for role in ('member','cashier','supervisor','collector'):
            self.membership.role=role
            self.assertEqual(self.client.patch(self.url,json=self.payload()).status_code,403)
        self.membership.role='owner'; self.membership.is_active=False
        self.assertEqual(self.client.patch(self.url,json=self.payload()).status_code,403)

    def test_foreign_and_missing_borrowers_hidden(self):
        self.current=self.other
        self.assertEqual(self.client.patch(self.url,json=self.payload()).status_code,404)
        self.assertEqual(self.client.patch('/borrowers/999/contact',json=self.payload()).status_code,404)


if __name__ == '__main__':
    unittest.main(verbosity=2)
