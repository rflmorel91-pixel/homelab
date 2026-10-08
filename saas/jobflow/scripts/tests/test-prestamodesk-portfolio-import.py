"""Isolated API/SQLite regression scenarios; does not contact a real database."""
import csv
import io
import os
import sys
import unittest
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "isolated-import-tests-secret-with-at-least-32-bytes"
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, func, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.models import Product, Tenant, TenantMembership, User, AdminAuditLog
from app.auth_context import get_current_user_id
from app.products.prestamodesk.models import Borrower, Installment, Loan, Payment
from app.products.prestamodesk.models.portfolio_import import PortfolioImport, ImportedLoan
from app.products.prestamodesk.portfolio_import_api import router, COLUMNS
from app.products.prestamodesk.payments_api import router as payments_router
from app.products.prestamodesk.payment_corrections_api import router as corrections_router

URL = "/administration/imports"


def payload(**changes):
    common = {"referencia": "TEST-001", "nombre": "Ana Ejemplo", "tipo_documento": "cedula", "documento": "TEST-001",
        "telefono": "", "tipo_prestamo": "personal", "fecha_inicio": "2026-09-01", "primera_cuota": "2026-10-01",
        "frecuencia": "monthly", "capital_original": "10000.00", "interes_porcentaje": "10", "numero_cuotas": "2",
        "capital_cuota": "5000.00", "interes_cuota": "500.00", "mora_pendiente": "0.00"}
    rows = [{**common, "cuota": "1", "vencimiento": "2026-10-01", "capital_pagado": "1000.00", "interes_pagado": "100.00", "saldo_pendiente": "4400.00"},
            {**common, "cuota": "2", "vencimiento": "2026-11-01", "capital_pagado": "0.00", "interes_pagado": "0.00", "saldo_pendiente": "5500.00"}]
    for row in rows:
        row.update(changes)
    stream = io.StringIO(); writer = csv.DictWriter(stream, COLUMNS); writer.writeheader(); writer.writerows(rows)
    return {"csv_text": stream.getvalue(), "cutoff_date": "2026-10-08"}


class ImportScenarios(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        @event.listens_for(self.engine, "connect")
        def foreign_keys(connection, record):
            connection.execute("PRAGMA foreign_keys=ON")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine, expire_on_commit=False)
        product = Product(name="PréstamoDesk", slug="prestamodesk", workspace_key="prestamodesk"); self.db.add(product); self.db.flush()
        self.user = User(email="test@example.test", display_name="Operator", is_active=True); self.db.add(self.user); self.db.flush()
        self.tenant = Tenant(product_id=product.id, name="TEST", slug="test"); self.db.add(self.tenant); self.db.flush()
        self.actor = TenantMembership(tenant_id=self.tenant.id, user_id=self.user.id, role="owner", is_active=True); self.db.add(self.actor); self.db.commit()
        self.app = FastAPI(); self.app.include_router(router); self.app.include_router(payments_router); self.app.include_router(corrections_router)
        self.app.dependency_overrides[get_db] = lambda: self.db
        self.app.dependency_overrides[get_current_user_id] = lambda: self.user.id
        self.client = TestClient(self.app, headers={"X-Tenant-ID": str(self.tenant.id)})

    def tearDown(self):
        self.client.close(); self.db.close(); self.engine.dispose()

    def preview(self, data=None):
        return self.client.post(URL + "/preview", json=data or payload())

    def commit(self, data=None):
        data = data or payload(); response = self.preview(data); self.assertEqual(response.status_code, 200, response.text)
        return self.client.post(URL, json={**data, "fingerprint": response.json()["fingerprint"], "confirm_balances": True})

    def count(self, model):
        return self.db.scalar(select(func.count()).select_from(model))

    def test_preview_writes_nothing_and_reconciles(self):
        result = self.preview(); self.assertEqual(result.status_code, 200, result.text)
        self.assertTrue(result.json()["valid"]); self.assertEqual(result.json()["opening_balance"], "9900.00")
        self.assertEqual(result.json()["historical_paid"], "1100.00")
        for model in (Borrower, Loan, Installment, PortfolioImport, Payment): self.assertEqual(self.count(model), 0)

    def test_commit_preserves_history_without_cash_and_safe_retry(self):
        data = payload(); review = self.preview(data).json(); request = {**data, "fingerprint": review["fingerprint"], "confirm_balances": True}
        result = self.client.post(URL, json=request); self.assertEqual(result.status_code, 201, result.text)
        self.assertEqual(self.count(Payment), 0); self.assertEqual(self.count(Loan), 1)
        first = self.db.scalar(select(Installment).where(Installment.sequence_number == 1))
        self.assertEqual(first.paid_amount, Decimal("1100.00")); self.assertEqual(first.principal_paid, Decimal("1000.00"))
        self.assertEqual(first.interest_paid, Decimal("100.00")); self.assertEqual(first.status, "partial")
        self.assertEqual(self.count(AdminAuditLog), 1)
        again = self.client.post(URL, json=request); self.assertEqual(again.status_code, 200, again.text)
        self.assertTrue(again.json()["replayed"]); self.assertEqual(self.count(Loan), 1)
        report = self.client.get(URL + "/" + str(result.json()["import_id"])); self.assertEqual(report.status_code, 200)
        self.assertEqual(report.json()["source"]["rows"][0]["capital_pagado"], "1000.00")

    def test_payment_and_void_restore_imported_baseline(self):
        imported = self.commit(); self.assertEqual(imported.status_code, 201, imported.text)
        installment = self.db.scalar(select(Installment).where(Installment.sequence_number == 1))
        payment = self.client.post("/payments", json={"installment_id": installment.id, "amount": "500.00"})
        self.assertEqual(payment.status_code, 201, payment.text)
        self.assertEqual(self.count(Payment), 1)
        voided = self.client.post(f'/payments/{payment.json()["id"]}/void', json={"reason": "Prueba de corrección"})
        self.assertEqual(voided.status_code, 200, voided.text)
        self.db.refresh(installment)
        self.assertEqual(installment.paid_amount, Decimal("1100.00")); self.assertEqual(installment.principal_paid, Decimal("1000.00"))
        self.assertEqual(installment.interest_paid, Decimal("100.00"))

    def test_invalid_balances_and_unsupported_data(self):
        for changes in ({"saldo_pendiente": "1.00"}, {"mora_pendiente": "1.00"}, {"capital_pagado": "9999.00"},
                        {"capital_cuota": "4999.00"}, {"tipo_prestamo": "vehicle"}, {"capital_original": "NaN"},
                        {"interes_porcentaje": "Infinity"}, {"numero_cuotas": "0"}):
            with self.subTest(changes=changes):
                result = self.preview(payload(**changes)); self.assertEqual(result.status_code, 200, result.text)
                self.assertFalse(result.json()["valid"])
        self.assertEqual(self.count(Loan), 0)

    def test_missing_duplicate_installments_and_dates(self):
        data = payload(); lines = data["csv_text"].splitlines()
        for text in ("\n".join(lines[:2]), "\n".join([*lines, lines[1]])):
            result = self.preview({**data, "csv_text": text}); self.assertFalse(result.json()["valid"])
        self.assertFalse(self.preview(payload(vencimiento="2026-10-02")).json()["valid"])
        self.assertEqual(self.preview({**data, "cutoff_date": "2099-01-01"}).status_code, 422)

    def test_stale_fingerprint_and_no_confirmation(self):
        data = payload(); review = self.preview(data).json()
        self.assertEqual(self.client.post(URL, json={**data, "fingerprint": review["fingerprint"]}).status_code, 422)
        changed = payload(nombre="Changed")
        result = self.client.post(URL, json={**changed, "fingerprint": review["fingerprint"], "confirm_balances": True})
        self.assertEqual(result.status_code, 409); self.assertEqual(self.count(Loan), 0)

    def test_existing_borrower_reused_and_mismatch_rejected(self):
        borrower = Borrower(tenant_id=self.tenant.id, full_name="Ana Ejemplo", document_type="cedula", document_number="TEST001", phone="existing", status="active")
        self.db.add(borrower); self.db.commit()
        self.assertTrue(self.preview().json()["valid"])
        self.assertFalse(self.preview(payload(nombre="Different Person")).json()["valid"])
        result = self.commit(); self.assertEqual(result.status_code, 201, result.text)
        self.assertEqual(self.count(Borrower), 1); self.assertEqual(borrower.phone, "existing")

    def test_duplicate_reference_rejected_after_changed_import(self):
        self.assertEqual(self.commit().status_code, 201)
        data = payload(telefono="new")
        preview = self.preview(data).json(); self.assertFalse(preview["valid"])
        result = self.client.post(URL, json={**data, "fingerprint": preview["fingerprint"], "confirm_balances": True})
        self.assertEqual(result.status_code, 422); self.assertEqual(self.count(Loan), 1)

    def test_role_and_suspension_enforcement(self):
        for role in ("member", "collector", "cashier", "supervisor"):
            self.actor.role = role; self.db.commit()
            for suffix, method in (("/preview", "POST"), ("/template", "GET"), ("/1", "GET")):
                response = self.client.request(method, URL + suffix, json=payload() if method == "POST" else None)
                self.assertEqual(response.status_code, 403, response.text)
        self.actor.role = "administrator"; self.db.commit(); self.assertEqual(self.preview().status_code, 200)
        self.tenant.status = "suspended"; self.db.commit(); self.assertEqual(self.preview().status_code, 403)

    def test_cross_tenant_report_and_membership(self):
        result = self.commit(); identifier = result.json()["import_id"]
        other = Tenant(product_id=self.tenant.product_id, name="OTHER", slug="other"); self.db.add(other); self.db.flush()
        actor = TenantMembership(tenant_id=other.id, user_id=self.user.id, role="owner", is_active=True); self.db.add(actor); self.db.commit()
        headers = {"X-Tenant-ID": str(other.id)}
        self.assertEqual(self.client.get(f"{URL}/{identifier}", headers=headers).status_code, 404)
        self.assertTrue(self.client.post(URL + "/preview", headers=headers, json=payload()).json()["valid"])
        actor.is_active = False; self.db.commit()
        self.assertEqual(self.client.post(URL + "/preview", headers=headers, json=payload()).status_code, 403)

    def test_transaction_rolls_back_every_record_on_failure(self):
        from unittest.mock import patch
        data = payload(); review = self.preview(data).json()
        with patch("app.products.prestamodesk.portfolio_import_api.add_admin_audit", side_effect=RuntimeError("injected failure")):
            with self.assertRaises(RuntimeError):
                self.client.post(URL, json={**data, "fingerprint": review["fingerprint"], "confirm_balances": True})
        for model in (Borrower, Loan, Installment, PortfolioImport, ImportedLoan, AdminAuditLog):
            self.assertEqual(self.count(model), 0)

    def test_multiple_loans_reuse_one_new_borrower(self):
        data = payload(); other = payload(referencia="TEST-002")
        data["csv_text"] += "\n".join(other["csv_text"].splitlines()[1:]) + "\n"
        result = self.commit(data); self.assertEqual(result.status_code, 201, result.text)
        self.assertEqual(self.count(Borrower), 1); self.assertEqual(self.count(Loan), 2)
        self.assertEqual(result.json()["opening_balance"], "19800.00")

    def test_invalid_second_loan_prevents_entire_import(self):
        data = payload(); invalid = payload(referencia="TEST-002", saldo_pendiente="1.00")
        data["csv_text"] += "\n".join(invalid["csv_text"].splitlines()[1:]) + "\n"
        result = self.commit(data); self.assertEqual(result.status_code, 422, result.text)
        self.assertEqual(self.count(Borrower), 0); self.assertEqual(self.count(Loan), 0)

    def test_additive_migration_and_history_preserving_downgrade(self):
        import importlib.util
        from alembic.migration import MigrationContext
        from alembic.operations import Operations
        from sqlalchemy import inspect
        path = Path(__file__).resolve().parents[2] / "backend/app/products/prestamodesk/migrations/versions/c2e4f6a8b0d3_portfolio_imports.py"
        spec = importlib.util.spec_from_file_location("test_import_migration", path)
        migration = importlib.util.module_from_spec(spec); spec.loader.exec_module(migration)
        with self.engine.begin() as connection:
            ImportedLoan.__table__.drop(connection); PortfolioImport.__table__.drop(connection)
            with Operations.context(MigrationContext.configure(connection)):
                migration.upgrade()
                self.assertIn("prestamodesk_portfolio_imports", inspect(connection).get_table_names())
                migration.downgrade()
                migration.upgrade()
        self.assertEqual(self.commit().status_code, 201)
        with self.engine.begin() as connection:
            with Operations.context(MigrationContext.configure(connection)):
                with self.assertRaises(RuntimeError): migration.downgrade()

    def test_limits_and_headers(self):
        data = payload(); self.assertEqual(self.preview({**data, "csv_text": "bad\n1"}).status_code, 422)
        lines = data["csv_text"].splitlines()
        self.assertEqual(self.preview({**data, "csv_text": "\n".join([lines[0]] + [lines[1]] * 501)}).status_code, 422)
        self.assertEqual(self.preview({**data, "csv_text": "x" * 1_000_001}).status_code, 422)
        self.assertEqual(self.preview().headers.get("cache-control"), "no-store")
        template = self.client.get(URL + "/template"); self.assertEqual(template.status_code, 200)
        self.assertEqual(self.preview({**data, "csv_text": template.content.decode("utf-8-sig")}).status_code, 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
