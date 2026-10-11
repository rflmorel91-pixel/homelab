"""Synthetic receipt retrieval; no network or production database."""
import importlib.util
from pathlib import Path
from datetime import datetime
import unittest
p=Path(__file__).with_name('test-prestamodesk-loan-creation-safety.py')
spec=importlib.util.spec_from_file_location('fixtures',p);f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
from app.products.prestamodesk.payments_api import router
from app.products.prestamodesk.models import Payment
from app.products.prestamodesk.schemas import PaymentRead
from app.products.prestamodesk.authorization import require_prestamodesk_payment_member, require_prestamodesk_manager
class ReceiptScenarios(unittest.TestCase):
 def setUp(self):
  f.Scenarios.setUp(self)
  self.client.app.include_router(router)
  self.client.app.dependency_overrides[require_prestamodesk_payment_member]=self.client.app.dependency_overrides[require_prestamodesk_manager]
  loan=self.client.post('/loans',json=f.Scenarios.payload(self)).json()
  with self.sessions() as db:
   payment=Payment(tenant_id=self.tid,loan_id=loan['id'],installment_id=loan['installments'][0]['id'],recorded_by_user_id=db.get(f.TenantMembership,self.mid).user_id,amount=10,principal_amount=0,interest_amount=10,late_fee_amount=0,payment_method='cash',paid_at=datetime(2026,10,11,12))
   db.add(payment);db.flush()
   payment.receipt_snapshot=PaymentRead.model_validate(payment).model_dump(mode='json')|dict(receipt_number=f'PM-{payment.id:08d}',installment_total='550',installment_paid='10',installment_balance='540',installment_ordinary_balance='540',installment_late_fee_accrued='0',installment_late_fee_paid='0',installment_late_fee_balance='0',installment_status='partial',loan_balance='1090',loan_status='active',currency='DOP')
   db.commit();self.pid=payment.id;self.lid=loan['id']
 def tearDown(self):f.Scenarios.tearDown(self)
 def read(self):return self.client.get(f'/payments/{self.pid}/receipt')
 def test_snapshot_keeps_recorded_balances_and_current_void_state(self):
  with self.sessions() as db:
   payment=db.get(Payment,self.pid);payment.voided_at=datetime(2026,10,12,12);payment.voided_by_user_id=payment.recorded_by_user_id;payment.void_reason='Synthetic error';db.get(f.Borrower,self.bid).full_name='Updated name';db.commit()
  result=self.read();self.assertEqual(result.status_code,200,result.text);data=result.json();self.assertTrue(data['snapshot_available']);self.assertEqual(data['receipt']['loan_balance'],'1090');self.assertEqual(data['receipt']['void_reason'],'Synthetic error');self.assertEqual(data['borrower_name'],'Updated name')
  with self.sessions() as db:self.assertEqual(db.get(Payment,self.pid).receipt_snapshot['voided_at'],None)
 def test_legacy_does_not_invent_balances(self):
  with self.sessions() as db:db.get(Payment,self.pid).receipt_snapshot=None;db.commit()
  result=self.read();self.assertEqual(result.status_code,200,result.text);self.assertFalse(result.json()['snapshot_available']);self.assertNotIn('loan_balance',result.json()['receipt']);self.assertEqual(result.json()['receipt']['amount'],'10.00')
 def test_hidden_foreign_and_missing_payments(self):
  self.assertEqual(self.client.get('/payments/999999/receipt').status_code,404)
  with self.sessions() as db:
   tenant=f.Tenant(product_id=db.get(f.Tenant,self.tid).product_id,name='Other',slug='other',client_number=2);db.add(tenant);db.flush();db.get(Payment,self.pid).tenant_id=tenant.id;db.commit()
  self.assertEqual(self.read().status_code,404)
 def test_roles_and_suspension(self):
  for role in ['member','cashier','collector','supervisor']:
   with self.sessions() as db:db.get(f.TenantMembership,self.mid).role=role;db.commit()
   self.assertEqual(self.read().status_code,403)
  with self.sessions() as db:db.get(f.TenantMembership,self.mid).role='administrator';db.commit()
  self.assertEqual(self.read().status_code,200)
  with self.sessions() as db:db.get(f.TenantMembership,self.mid).is_active=False;db.commit()
  self.assertEqual(self.read().status_code,403)
if __name__=='__main__':unittest.main(verbosity=2)
