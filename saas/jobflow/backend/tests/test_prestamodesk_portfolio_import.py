"""Run isolated scenarios plus imports against the suite's PostgreSQL database."""
import subprocess
import sys
from pathlib import Path
from decimal import Decimal
from sqlalchemy import select, func
from app.models import Product, Tenant
from app.products.prestamodesk.models import Borrower, Installment, Loan, Payment
from app.products.prestamodesk.models.portfolio_import import PortfolioImport

BASE = "/api/v1/products/prestamodesk/administration/imports"


def test_isolated_import_and_payment_regressions():
    script = Path(__file__).resolve().parents[2] / "scripts/tests/test-prestamodesk-portfolio-import.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr


def setup_import(client, db):
    product = db.scalar(select(Product).where(Product.slug == "prestamodesk"))
    tenant = Tenant(product_id=product.id, name="Import TEST", slug="portfolio-import-test")
    db.add(tenant); db.commit(); db.refresh(tenant)
    headers = client.owner_headers(tenant)
    response = client.get(BASE + "/template", headers=headers)
    assert response.status_code == 200
    data = {"csv_text": response.content.decode("utf-8-sig"), "cutoff_date": "2026-10-08"}
    return tenant, headers, data


def test_postgres_opening_balances_and_replay(authenticated_client, db_session):
    client, db = authenticated_client, db_session
    tenant, headers, data = setup_import(client, db)
    preview = client.post(BASE + "/preview", headers=headers, json=data)
    assert preview.status_code == 200 and preview.json()["valid"]
    request = {**data, "fingerprint": preview.json()["fingerprint"], "confirm_balances": True}
    response = client.post(BASE, headers=headers, json=request)
    assert response.status_code == 201, response.text
    assert response.json()["opening_balance"] == "9900.00"
    replay = client.post(BASE, headers=headers, json=request)
    assert replay.status_code == 200 and replay.json()["replayed"]
    assert db.scalar(select(func.count(PortfolioImport.id)).where(PortfolioImport.tenant_id == tenant.id)) == 1
    assert db.scalar(select(func.count(Loan.id)).where(Loan.tenant_id == tenant.id)) == 1
    assert db.scalar(select(func.count(Payment.id)).where(Payment.tenant_id == tenant.id)) == 0
    installment = db.scalar(select(Installment).where(Installment.tenant_id == tenant.id, Installment.sequence_number == 1))
    assert installment.principal_paid == Decimal("1000.00")
    assert installment.interest_paid == Decimal("100.00")
    assert client.get(f'{BASE}/{response.json()["import_id"]}', headers=headers).status_code == 200


def test_postgres_invalid_import_is_atomic(authenticated_client, db_session):
    client, db = authenticated_client, db_session
    tenant, headers, data = setup_import(client, db)
    data["csv_text"] = data["csv_text"].replace("4400.00", "1.00")
    preview = client.post(BASE + "/preview", headers=headers, json=data)
    assert preview.status_code == 200 and not preview.json()["valid"]
    response = client.post(BASE, headers=headers, json={**data, "fingerprint": preview.json()["fingerprint"], "confirm_balances": True})
    assert response.status_code == 422
    assert db.scalar(select(func.count(Loan.id)).where(Loan.tenant_id == tenant.id)) == 0
    assert db.scalar(select(func.count(Borrower.id)).where(Borrower.tenant_id == tenant.id)) == 0
