from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.models import AdminAuditLog, TenantMembership
from app.products.prestamodesk.models import Installment, LateFeePolicy, Loan, Payment, PaymentPromise, PromisePaymentAllocation
from tests.test_prestamodesk_payments import create_borrower, create_tenant, create_two_installment_loan, get_product

BASE = "/api/v1/products/prestamodesk"
REASON = "Incorrect payment entry"


def setup(client, db):
    tenant = create_tenant(db, get_product(db), "Correction Test", "correction-test")
    tenant.client_number = 901
    db.commit()
    borrower = create_borrower(db, tenant, "Synthetic Borrower")
    loan = create_two_installment_loan(client, tenant, borrower)
    headers = client.owner_headers(tenant)
    return tenant, loan, headers


def pay(client, loan, headers, amount="1000.00", index=0):
    response = client.post(BASE + "/payments", headers=headers,
                           json={"installment_id": loan["installments"][index]["id"], "amount": amount})
    assert response.status_code == 201, response.text
    return response.json()


def void(client, payment, headers, reason=REASON):
    return client.post(BASE + f"/payments/{payment['id']}/void", headers=headers, json={"reason": reason})


def test_void_restores_balances_preserves_receipt_and_allows_correct_payment(authenticated_client, db_session):
    client = authenticated_client
    tenant, loan, headers = setup(client, db_session)
    payment = pay(client, loan, headers)
    original_id = payment["id"]
    response = void(client, payment, headers)
    assert response.status_code == 200, response.text
    assert response.json()["amount"] == payment["amount"]
    assert response.json()["void_reason"] == REASON
    installment = db_session.get(Installment, loan["installments"][0]["id"])
    db_session.refresh(installment)
    assert installment.paid_amount == 0
    assert installment.interest_paid == 0
    assert installment.principal_paid == 0
    assert installment.status == "pending"
    replacement = pay(client, loan, headers, "500.00")
    assert replacement["id"] != original_id
    assert Decimal(replacement["installment_paid"]) == Decimal("500.00")
    history = client.get(BASE + f"/payments/loan/{loan['id']}", headers=headers).json()
    assert len(history) == 2
    assert next(row for row in history if row["id"] == original_id)["voided_at"]
    audit = db_session.scalar(select(AdminAuditLog).where(AdminAuditLog.action == "payments.voided"))
    assert audit.tenant_id == tenant.id
    assert audit.after_data["reason"] == REASON


def test_same_void_is_idempotent_and_reason_is_immutable(authenticated_client, db_session):
    client = authenticated_client
    _, loan, headers = setup(client, db_session)
    payment = pay(client, loan, headers)
    first = void(client, payment, headers)
    repeated = void(client, payment, headers)
    assert first.status_code == repeated.status_code == 200
    assert first.json()["voided_at"] == repeated.json()["voided_at"]
    assert void(client, payment, headers, "Different correction reason").status_code == 409
    assert db_session.scalar(select(func.count(AdminAuditLog.id)).where(AdminAuditLog.action == "payments.voided")) == 1


def test_latest_payment_rule_and_sequential_voids(authenticated_client, db_session):
    client = authenticated_client
    _, loan, headers = setup(client, db_session)
    first = pay(client, loan, headers)
    second = pay(client, loan, headers, "500.00", index=1)
    assert void(client, first, headers).status_code == 409
    assert void(client, second, headers).status_code == 200
    assert void(client, first, headers).status_code == 200


def test_fully_paid_loan_reopens(authenticated_client, db_session):
    client = authenticated_client
    _, loan, headers = setup(client, db_session)
    pay(client, loan, headers, "5500.00")
    final = pay(client, loan, headers, "5500.00", index=1)
    assert final["loan_status"] == "paid"
    assert void(client, final, headers).status_code == 200
    stored = db_session.get(Loan, loan["id"])
    db_session.refresh(stored)
    assert stored.status == "active"


@pytest.mark.parametrize("role", ["member", "cashier", "collector", "supervisor"])
def test_operational_roles_cannot_void(authenticated_client, db_session, role):
    client = authenticated_client
    tenant, loan, headers = setup(client, db_session)
    payment = pay(client, loan, headers)
    membership = db_session.scalar(select(TenantMembership).where(TenantMembership.tenant_id == tenant.id,
                                                                   TenantMembership.user_id == client.auth_user.id))
    membership.role = role
    db_session.commit()
    assert void(client, payment, headers).status_code == 403
    stored = db_session.get(Payment, payment["id"])
    db_session.refresh(stored)
    assert stored.voided_at is None


def test_administrator_can_void(authenticated_client, db_session):
    client = authenticated_client
    tenant, loan, headers = setup(client, db_session)
    payment = pay(client, loan, headers)
    membership = db_session.scalar(select(TenantMembership).where(TenantMembership.tenant_id == tenant.id,
                                                                   TenantMembership.user_id == client.auth_user.id))
    membership.role = "administrator"
    db_session.commit()
    assert void(client, payment, headers).status_code == 200


@pytest.mark.parametrize("reason", ["", "    ", "abc", "a" * 1001])
def test_reason_validation(authenticated_client, db_session, reason):
    client = authenticated_client
    _, loan, headers = setup(client, db_session)
    payment = pay(client, loan, headers)
    assert void(client, payment, headers, reason).status_code == 422


def test_other_tenant_cannot_void(authenticated_client, db_session):
    client = authenticated_client
    _, loan, headers = setup(client, db_session)
    payment = pay(client, loan, headers)
    other = create_tenant(db_session, get_product(db_session), "Other", "correction-other")
    assert void(client, payment, client.owner_headers(other)).status_code == 404


def test_legacy_and_changed_installments_are_blocked(authenticated_client, db_session):
    client = authenticated_client
    _, loan, headers = setup(client, db_session)
    payment = pay(client, loan, headers)
    stored = db_session.get(Payment, payment["id"])
    snapshot = stored.correction_snapshot
    stored.correction_snapshot = None
    db_session.commit()
    assert void(client, payment, headers).status_code == 409
    stored.correction_snapshot = snapshot
    installment = db_session.get(Installment, payment["installment_id"])
    installment.principal_paid += Decimal("1.00")
    db_session.commit()
    assert void(client, payment, headers).status_code == 409


def test_closed_payment_is_blocked(authenticated_client, db_session):
    client = authenticated_client
    tenant, loan, _ = setup(client, db_session)
    headers = client.auth_headers(tenant)
    payment = pay(client, loan, headers)
    response = client.post(BASE + "/cashier/closings", headers=headers, json={"cash_counted": "1000.00"})
    assert response.status_code == 201, response.text
    assert void(client, payment, client.owner_headers(tenant)).status_code == 409


def test_voided_payment_excluded_from_cash_preview_and_recovery_total(authenticated_client, db_session):
    client = authenticated_client
    tenant, loan, _ = setup(client, db_session)
    payment = pay(client, loan, client.auth_headers(tenant))
    headers = client.owner_headers(tenant)
    assert void(client, payment, headers).status_code == 200
    dashboard = client.get(BASE + "/collections/supervision", headers=headers)
    assert dashboard.status_code == 200, dashboard.text
    assert Decimal(dashboard.json()["total_recovered"]) == 0
    preview = client.get(BASE + "/cashier/closing-preview", headers=client.auth_headers(tenant))
    assert preview.status_code == 200
    assert preview.json()["payment_count"] == 0
    assert Decimal(preview.json()["total_collected"]) == 0


@pytest.mark.parametrize("cancelled", [False, True])
def test_promise_allocations_reversed_without_deleting_history(authenticated_client, db_session, cancelled):
    client = authenticated_client
    tenant, loan, headers = setup(client, db_session)
    promise = PaymentPromise(tenant_id=tenant.id, loan_id=loan["id"], created_by_user_id=client.auth_user.id,
                             promised_amount=Decimal("1000.00"), due_date=date(2026, 10, 10), status="pending")
    db_session.add(promise)
    db_session.commit()
    payment = pay(client, loan, headers)
    db_session.refresh(promise)
    assert promise.status == "fulfilled"
    if cancelled:
        promise.status = "cancelled"
        db_session.commit()
    assert void(client, payment, headers).status_code == 200
    db_session.refresh(promise)
    assert promise.fulfilled_amount == 0
    assert promise.status == ("cancelled" if cancelled else "pending")
    assert promise.fulfilled_at is None
    allocation = db_session.scalar(select(PromisePaymentAllocation).where(PromisePaymentAllocation.payment_id == payment["id"]))
    assert allocation.reversed_at is not None
    assert allocation.amount == Decimal("1000.00")
    history = client.get(BASE + f"/collections/promises/{promise.id}/allocations", headers=headers)
    assert history.status_code == 200
    assert history.json()[0]["reversed_at"]


def test_late_fee_assessment_restores_before_payment_snapshot(authenticated_client, db_session):
    client = authenticated_client
    tenant, loan, headers = setup(client, db_session)
    stored = db_session.get(Loan, loan["id"])
    stored.late_fee_enabled = True
    installment = db_session.get(Installment, loan["installments"][0]["id"])
    installment.due_date = date(2026, 9, 1)
    db_session.add(LateFeePolicy(tenant_id=tenant.id, enabled=True, daily_rate_percent=Decimal("0.1000"),
                                grace_days=0, cap_percent=Decimal("25.0000"), effective_date=date(2026, 9, 1)))
    db_session.commit()
    payment = pay(client, loan, headers)
    db_session.refresh(installment)
    assert installment.late_fee_accrued > 0
    assert installment.late_fee_assessed_through is not None
    assert void(client, payment, headers).status_code == 200
    db_session.refresh(installment)
    assert installment.late_fee_accrued == 0
    assert installment.late_fee_paid == 0
    assert installment.late_fee_assessed_through is None


def test_postgresql_concurrent_void_requests_apply_once(authenticated_client, db_session):
    if db_session.get_bind().dialect.name != "postgresql":
        pytest.skip("Requires PostgreSQL row locks")
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from sqlalchemy.orm import Session
    from app.models import Tenant
    from app.products.prestamodesk.payment_corrections_api import void_payment
    from app.products.prestamodesk.schemas import PaymentVoidCreate

    client = authenticated_client
    tenant, loan, headers = setup(client, db_session)
    payment = pay(client, loan, headers)
    tenant_id, user_id = tenant.id, client.auth_user.id
    engine = db_session.get_bind()
    barrier = Barrier(2)

    def run():
        with Session(engine) as db:
            actor = db.scalar(select(TenantMembership).where(TenantMembership.tenant_id == tenant_id,
                                                             TenantMembership.user_id == user_id))
            current_tenant = db.get(Tenant, tenant_id)
            barrier.wait(timeout=10)
            return void_payment(payment["id"], PaymentVoidCreate(reason=REASON), db, current_tenant, actor)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: run(), range(2)))
    assert all(result.voided_at is not None for result in results)
    db_session.expire_all()
    assert db_session.get(Installment, payment["installment_id"]).paid_amount == 0
    assert db_session.scalar(select(func.count(AdminAuditLog.id)).where(AdminAuditLog.action == "payments.voided")) == 1


def test_postgresql_void_and_cash_closing_remain_consistent(authenticated_client, db_session):
    if db_session.get_bind().dialect.name != "postgresql":
        pytest.skip("Requires PostgreSQL row locks")
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from fastapi import HTTPException
    from sqlalchemy.orm import Session
    from app.models import Tenant, User
    from app.products.prestamodesk.cash_closings_api import close_cashier_register
    from app.products.prestamodesk.cash_closing_schemas import CashClosingCreate
    from app.products.prestamodesk.payment_corrections_api import void_payment
    from app.products.prestamodesk.schemas import PaymentVoidCreate

    client = authenticated_client
    tenant, loan, _ = setup(client, db_session)
    payment = pay(client, loan, client.auth_headers(tenant))
    manager = User(email="correction-manager@example.test", display_name="Correction Manager", is_active=True)
    db_session.add(manager)
    db_session.flush()
    db_session.add(TenantMembership(tenant_id=tenant.id, user_id=manager.id, role="administrator"))
    db_session.commit()
    tenant_id, cashier_id, manager_id = tenant.id, client.auth_user.id, manager.id
    engine = db_session.get_bind()
    barrier = Barrier(2)

    def run(operation):
        with Session(engine) as db:
            user_id = manager_id if operation == "void" else cashier_id
            actor = db.scalar(select(TenantMembership).where(TenantMembership.tenant_id == tenant_id,
                                                             TenantMembership.user_id == user_id))
            current_tenant = db.get(Tenant, tenant_id)
            barrier.wait(timeout=10)
            if operation == "close":
                return close_cashier_register(CashClosingCreate(cash_counted=Decimal("1000.00")), db, current_tenant, actor)
            try:
                return void_payment(payment["id"], PaymentVoidCreate(reason=REASON), db, current_tenant, actor)
            except HTTPException as error:
                assert error.status_code == 409
                return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        void_future = pool.submit(run, "void")
        close_future = pool.submit(run, "close")
        void_result = void_future.result(timeout=20)
        closing = close_future.result(timeout=20)
    db_session.expire_all()
    stored = db_session.get(Payment, payment["id"])
    if void_result is not None:
        assert stored.voided_at is not None
        assert stored.cash_closing_id is None
        assert closing.payment_count == 0
        assert closing.total_collected == 0
    else:
        assert stored.voided_at is None
        assert stored.cash_closing_id == closing.id
        assert closing.payment_count == 1
        assert closing.total_collected == Decimal("1000.00")
