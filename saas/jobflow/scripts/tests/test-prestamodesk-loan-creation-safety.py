"""Synthetic API and migration checks without network or production databases."""
from pathlib import Path
import os,sys,unittest,importlib.util
from uuid import uuid4
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'backend'))
os.environ['DATABASE_URL']='sqlite://';os.environ['JWT_SECRET']='synthetic-tests-at-least-32-characters'
from fastapi import FastAPI,Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine,select,func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base,get_db
from app.models import User,Tenant,Product,TenantMembership
from app.products.prestamodesk.models import Borrower,Loan,Installment
from app.products.prestamodesk.loans_api import router
from app.products.prestamodesk.authorization import require_prestamodesk_operations_member,require_prestamodesk_manager,require_roles,OPERATIONS_ROLES,ADMINISTRATION_ROLES
from app.tenant_context import get_current_tenant

class Scenarios(unittest.TestCase):
 def setUp(self):
  self.engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool);Base.metadata.create_all(self.engine);self.sessions=sessionmaker(bind=self.engine)
  with self.sessions() as db:
   p=Product(name='Synthetic',slug='prestamodesk',status='active',workspace_key='prestamodesk');db.add(p);db.flush()
   u=User(email='synthetic@example.test',is_active=True,display_name='Synthetic');v=User(email='second@example.test',is_active=True,display_name='Second');db.add_all([u,v]);db.flush()
   t=Tenant(product_id=p.id,name='Synthetic',slug='synthetic',client_number=1);db.add(t);db.flush()
   b=Borrower(tenant_id=t.id,full_name='Synthetic',status='active',document_type='other');db.add(b)
   m=TenantMembership(tenant_id=t.id,user_id=u.id,role='owner');n=TenantMembership(tenant_id=t.id,user_id=v.id,role='administrator');db.add_all([m,n]);db.commit()
   self.tid=t.id;self.bid=b.id;self.mid=m.id;self.other_mid=n.id
  def get_session():
   with self.sessions() as db:yield db
  def tenant(db=Depends(get_db)):return db.get(Tenant,self.tid)
  def member(db=Depends(get_db)):return db.get(TenantMembership,self.mid)
  def operations(db=Depends(get_db)):return require_roles(member(db),OPERATIONS_ROLES)
  def manager(db=Depends(get_db)):return require_roles(member(db),ADMINISTRATION_ROLES)
  app=FastAPI();app.include_router(router);app.dependency_overrides.update({get_db:get_session,get_current_tenant:tenant,require_prestamodesk_operations_member:operations,require_prestamodesk_manager:manager});self.client=TestClient(app)
 def tearDown(self):self.client.close();self.engine.dispose()
 def payload(self):return dict(borrower_id=self.bid,principal_amount='1000.00',flat_interest_rate_percent='10.0000',installment_count=2,payment_frequency='monthly',start_date='2026-10-10',first_payment_date='2026-11-10',idempotency_key=str(uuid4()))
 def counts(self):
  with self.sessions() as db:return (db.scalar(select(func.count(Loan.id))),db.scalar(select(func.count(Installment.id))))
 def test_retry_snapshot_normalization_and_conflict(self):
  p=self.payload();a=self.client.post('/loans',json=p);self.assertEqual(a.status_code,201,a.text)
  with self.sessions() as db:
   db.get(Borrower,self.bid).status='inactive';db.get(Loan,a.json()['id']).status='cancelled';db.commit()
  b=self.client.post('/loans',json=p|{'principal_amount':'1000','flat_interest_rate_percent':'10'});self.assertEqual(b.json(),a.json());self.assertEqual(self.counts(),(1,2))
  self.assertEqual(self.client.post('/loans',json=p|{'notes':'different'}).status_code,409);self.mid=self.other_mid;self.assertEqual(self.client.post('/loans',json=p).status_code,409)
 def test_validation_and_legacy(self):
  p=self.payload();self.assertEqual(self.client.post('/loans',json=p|{'first_payment_date':'2026-09-01'}).status_code,422);self.assertEqual(self.counts(),(0,0));self.assertEqual(self.client.post('/loans',json=p).status_code,201)
  del p['idempotency_key'];self.assertEqual(self.client.post('/loans',json=p).status_code,201);self.assertEqual(self.counts(),(2,4))
 def test_transaction_failure_rolls_back_loan_and_schedule(self):
  from unittest.mock import patch
  from sqlalchemy.orm import Session
  p=self.payload()
  with patch.object(Session,'commit',side_effect=RuntimeError('Synthetic commit failure')):
   with self.assertRaises(RuntimeError):self.client.post('/loans',json=p)
  self.assertEqual(self.counts(),(0,0));self.assertEqual(self.client.post('/loans',json=p).status_code,201);self.assertEqual(self.counts(),(1,2))
 def test_roles_and_tenant(self):
  p=self.payload()
  for role in ['member','cashier','collector','supervisor']:
   with self.sessions() as db:db.get(TenantMembership,self.mid).role=role;db.commit()
   self.assertEqual(self.client.post('/loans',json=p).status_code,403)
  with self.sessions() as db:db.get(TenantMembership,self.mid).role='administrator';db.commit()
  self.assertEqual(self.client.post('/loans',json=p|{'borrower_id':999}).status_code,404);self.assertEqual(self.client.post('/loans',json=p).status_code,201)
 def test_migration_round_trip_and_guard(self):
  from alembic.migration import MigrationContext
  from alembic.operations import Operations
  path=Path(__file__).resolve().parents[2]/'backend/app/products/prestamodesk/migrations/versions/c2d4e6f8a0b2_loan_request_keys.py';spec=importlib.util.spec_from_file_location('request_migration',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  with self.engine.begin() as conn:
   module.op=Operations(MigrationContext.configure(conn));module.downgrade();module.upgrade()
  self.assertEqual(self.client.post('/loans',json=self.payload()).status_code,201)
  with self.engine.begin() as conn:
   module.op=Operations(MigrationContext.configure(conn))
   with self.assertRaises(RuntimeError):module.downgrade()

if __name__=='__main__':unittest.main(verbosity=2)
