"""Synthetic loan preview checks; no network or production database."""
import importlib.util
from pathlib import Path
import unittest
from decimal import Decimal
path = Path(__file__).with_name("test-prestamodesk-loan-creation-safety.py")
spec = importlib.util.spec_from_file_location("creation_fixtures", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class PreviewScenarios(unittest.TestCase):
    setUp = module.Scenarios.setUp
    tearDown = module.Scenarios.tearDown
    payload = module.Scenarios.payload
    counts = module.Scenarios.counts

    def test_rounding_dates_and_creation_match(self):
        payload = self.payload() | {"principal_amount": "1000.01", "installment_count": 3, "first_payment_date": "2027-01-31"}
        for _ in range(2):
            response = self.client.post("/loans/preview", json=payload)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.headers["Cache-Control"], "no-store")
            self.assertEqual(self.counts(), (0, 0))
        preview = response.json()
        self.assertEqual([i["due_date"] for i in preview["installments"]], ["2027-01-31", "2027-02-28", "2027-03-31"])
        self.assertEqual(sum(Decimal(i["total_due"]) for i in preview["installments"]), Decimal(preview["total_due"]))
        created = self.client.post("/loans", json=payload)
        self.assertEqual(created.status_code, 201, created.text)
        for field in ["principal_amount", "total_interest", "total_due"]:
            self.assertEqual(preview[field], created.json()[field])
        for actual, expected in zip(created.json()["installments"], preview["installments"]):
            for field in expected:
                self.assertEqual(actual[field], expected[field])

    def test_invalid_inactive_missing_and_late_fee_write_nothing(self):
        payload = self.payload()
        for changes, status in [({"first_payment_date":"2026-01-01"},422), ({"principal_amount":"0"},422), ({"late_fee_enabled":True},409), ({"borrower_id":9999},404)]:
            self.assertEqual(self.client.post("/loans/preview", json=payload | changes).status_code,status)
        with self.sessions() as db:
            db.get(module.Borrower,self.bid).status="inactive";db.commit()
        self.assertEqual(self.client.post("/loans/preview",json=payload).status_code,409)
        self.assertEqual(self.counts(),(0,0))

    def test_roles_and_foreign_tenant(self):
        for role in ["member","cashier","collector","supervisor"]:
            with self.sessions() as db:
                db.get(module.TenantMembership,self.mid).role=role;db.commit()
            self.assertEqual(self.client.post("/loans/preview",json=self.payload()).status_code,403)
        with self.sessions() as db:
            db.get(module.TenantMembership,self.mid).role="administrator"
            second=module.Tenant(product_id=db.get(module.Tenant,self.tid).product_id,name="Second",slug="second",client_number=2);db.add(second);db.flush()
            borrower=module.Borrower(tenant_id=second.id,full_name="Other tenant",status="active",document_type="other");db.add(borrower);db.commit();bid=borrower.id
        self.assertEqual(self.client.post("/loans/preview",json=self.payload() | {"borrower_id":bid}).status_code,404)
        self.assertEqual(self.client.post("/loans/preview",json=self.payload()).status_code,200)
        self.assertEqual(self.counts(),(0,0))

    def test_frequencies_and_vehicle(self):
        for frequency, dates in [("daily",["2026-11-10","2026-11-11"]),("weekly",["2026-11-10","2026-11-17"]),("biweekly",["2026-11-10","2026-11-24"])]:
            response=self.client.post("/loans/preview",json=self.payload() | {"payment_frequency":frequency})
            self.assertEqual([i["due_date"] for i in response.json()["installments"]],dates)
        payload=self.payload() | {"loan_type":"vehicle","vehicle_cash_price":"1500","vehicle_down_payment":"500","vehicle_make":"Toyota","vehicle_model":"Corolla","vehicle_year":2022}
        self.assertEqual(self.client.post("/loans/preview",json=payload).status_code,200)
        self.assertEqual(self.client.post("/loans/preview",json=payload | {"vehicle_down_payment":"600"}).status_code,422)
        self.assertEqual(self.counts(),(0,0))

if __name__ == "__main__": unittest.main(verbosity=2)
