import runpy
from pathlib import Path

def test_receipt_history_scenarios():
    suite = runpy.run_path(str(Path(__file__).resolve().parents[2] / "scripts/tests/test-prestamodesk-receipt-history.py"))["ReceiptScenarios"]
    import unittest
    result = unittest.TestResult()
    unittest.defaultTestLoader.loadTestsFromTestCase(suite).run(result)
    assert result.wasSuccessful(), str(result.errors + result.failures)


def test_authenticated_receipt_copy_and_void(authenticated_client, db_session):
    from uuid import uuid4
    from tests.test_prestamodesk_payment_corrections import setup, void
    from app.products.prestamodesk.models import Payment
    from app.models import TenantMembership
    from sqlalchemy import select
    tenant, loan, headers = setup(authenticated_client, db_session)
    response = authenticated_client.post('/api/v1/products/prestamodesk/payments', headers=headers,
        json={'installment_id': loan['installments'][0]['id'], 'amount': '10.00', 'idempotency_key': str(uuid4())})
    assert response.status_code == 201, response.text
    payment = response.json()
    url = f"/api/v1/products/prestamodesk/payments/{payment['id']}/receipt"
    copied = authenticated_client.get(url, headers=headers)
    assert copied.status_code == 200, copied.text
    assert copied.headers['Cache-Control'] == 'no-store'
    assert copied.json()['receipt'] == payment
    assert void(authenticated_client, payment, headers).status_code == 200
    copied = authenticated_client.get(url, headers=headers).json()
    assert copied['receipt']['voided_at']
    assert copied['receipt']['loan_balance'] == payment['loan_balance']
    db_session.expire_all()
    assert db_session.get(Payment, payment['id']).receipt_snapshot == payment
    membership = db_session.scalar(select(TenantMembership).where(
        TenantMembership.tenant_id == tenant.id,
        TenantMembership.user_id == authenticated_client.auth_user.id))
    membership.role = 'member'
    db_session.commit()
    assert authenticated_client.get(url, headers=headers).status_code == 403
