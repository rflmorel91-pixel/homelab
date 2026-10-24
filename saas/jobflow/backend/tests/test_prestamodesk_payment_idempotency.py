from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest

from sqlalchemy import func, select
from app.products.prestamodesk.models import Payment
from tests.test_prestamodesk_payment_corrections import setup, void

URL = '/api/v1/products/prestamodesk/payments'


def request(loan, amount='1000.00', key=None):
    return {'installment_id': loan['installments'][0]['id'], 'amount': amount,
            'idempotency_key': key or str(uuid4())}


def test_retry_returns_original_receipt_after_later_payment(authenticated_client, db_session):
    client = authenticated_client
    tenant, loan, headers = setup(client, db_session)
    payload = request(loan)
    first = client.post(URL, headers=headers, json=payload)
    assert first.status_code == 201, first.text
    assert client.post(URL, headers=headers, json=request(loan, '500.00')).status_code == 201
    retry = client.post(URL, headers=headers, json={**payload, 'amount': '1000'})
    assert retry.status_code == 201
    assert retry.json() == first.json()
    assert db_session.scalar(select(func.count(Payment.id))) == 2


def test_changed_details_conflict(authenticated_client, db_session):
    client = authenticated_client
    _, loan, headers = setup(client, db_session)
    payload = request(loan)
    assert client.post(URL, headers=headers, json=payload).status_code == 201
    assert client.post(URL, headers=headers, json={**payload, 'amount':'1001.00'}).status_code == 409
    assert db_session.scalar(select(func.count(Payment.id))) == 1


def test_concurrent_identical_requests_create_one_payment(authenticated_client, db_session):
    client = authenticated_client
    _, loan, headers = setup(client, db_session)
    payload = request(loan)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: client.post(URL, headers=headers, json=payload), range(2)))
    assert [r.status_code for r in results] == [201, 201]
    assert results[0].json() == results[1].json()
    assert db_session.scalar(select(func.count(Payment.id))) == 1


def test_voided_request_cannot_create_replacement(authenticated_client, db_session):
    client = authenticated_client
    _, loan, headers = setup(client, db_session)
    payload = request(loan)
    first = client.post(URL, headers=headers, json=payload)
    assert first.status_code == 201
    assert void(client, first.json(), headers).status_code == 200
    assert client.post(URL, headers=headers, json=payload).status_code == 409
    assert db_session.scalar(select(func.count(Payment.id))) == 1


def test_rejected_request_key_can_be_reused_with_valid_amount(authenticated_client, db_session):
    client = authenticated_client
    _, loan, headers = setup(client, db_session)
    payload = request(loan, '5500.01')
    assert client.post(URL, headers=headers, json=payload).status_code == 409
    assert client.post(URL, headers=headers, json={**payload, 'amount':'1000.00'}).status_code == 201
    assert db_session.scalar(select(func.count(Payment.id))) == 1


def test_completed_loan_replays_original_receipt(authenticated_client, db_session):
    client = authenticated_client
    _, loan, headers = setup(client, db_session)
    first = request(loan, '5500.00')
    assert client.post(URL, headers=headers, json=first).status_code == 201
    second = {**request(loan, '5500.00'), 'installment_id':loan['installments'][1]['id']}
    receipt = client.post(URL, headers=headers, json=second)
    assert receipt.status_code == 201
    assert receipt.json()['loan_status'] == 'paid'
    assert client.post(URL, headers=headers, json=second).json() == receipt.json()
    assert db_session.scalar(select(func.count(Payment.id))) == 2


def test_request_key_is_scoped_to_tenant(authenticated_client, db_session):
    from tests.test_prestamodesk_payments import create_tenant, create_borrower, create_two_installment_loan, get_product
    client = authenticated_client
    tenant, loan, headers = setup(client, db_session)
    payload = request(loan)
    assert client.post(URL, headers=headers, json=payload).status_code == 201
    other = create_tenant(db_session, get_product(db_session), 'Other Request Tenant', 'other-request-tenant')
    borrower = create_borrower(db_session, other, 'Synthetic Other')
    other_loan = create_two_installment_loan(client, other, borrower)
    response = client.post(URL, headers=client.owner_headers(other), json=request(other_loan, key=payload['idempotency_key']))
    assert response.status_code == 201, response.text
    assert db_session.scalar(select(func.count(Payment.id))) == 2


@pytest.mark.parametrize(
    "amount,accepted_count",
    [("4000.00", 1), ("2000.00", 2)],
)
def test_distinct_operators_compete_for_installment_balance(
    authenticated_client, db_session, amount, accepted_count,
):
    from decimal import Decimal
    from threading import Barrier
    from fastapi import HTTPException
    from sqlalchemy import text
    from sqlalchemy.orm import Session
    from app.models import Tenant, TenantMembership, User
    from app.products.prestamodesk.models import Installment
    from app.products.prestamodesk.payments_api import record_payment
    from app.products.prestamodesk.schemas import PaymentCreate

    client = authenticated_client
    tenant, loan, _ = setup(client, db_session)
    tenant_id = tenant.id
    first_user_id = client.auth_user.id
    installment_id = loan["installments"][0]["id"]
    assert Decimal(loan["installments"][0]["total_due"]) == Decimal("5500.00")

    second = User(
        email="competing-cashier@example.test",
        display_name="Synthetic competing cashier",
        is_active=True,
    )
    db_session.add(second)
    db_session.flush()
    db_session.add(TenantMembership(
        tenant_id=tenant_id, user_id=second.id,
        role="cashier", is_active=True,
    ))
    db_session.commit()
    second_user_id = second.id
    engine = db_session.get_bind()
    assert engine.dialect.name == "postgresql"
    db_session.rollback()

    barrier = Barrier(2)
    keys = [str(uuid4()), str(uuid4())]

    def submit(index):
        user_id = [first_user_id, second_user_id][index]
        with Session(engine) as db:
            db.execute(text("SET LOCAL statement_timeout = '15s'"))
            actor = db.scalar(select(TenantMembership).where(
                TenantMembership.tenant_id == tenant_id,
                TenantMembership.user_id == user_id,
            ))
            current_tenant = db.get(Tenant, tenant_id)
            payload = PaymentCreate(
                installment_id=installment_id,
                amount=Decimal(amount),
                idempotency_key=keys[index],
            )
            barrier.wait(timeout=10)
            try:
                receipt = record_payment(
                    payload=payload, db=db,
                    tenant=current_tenant, membership=actor,
                )
                return 201, receipt
            except HTTPException as error:
                db.rollback()
                return error.status_code, None

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(submit, index) for index in range(2)]
        results = [future.result(timeout=25) for future in futures]

    expected_statuses = [201, 409] if accepted_count == 1 else [201, 201]
    assert sorted(status for status, _ in results) == expected_statuses

    db_session.expire_all()
    payments = db_session.scalars(select(Payment).where(
        Payment.tenant_id == tenant_id,
        Payment.installment_id == installment_id,
    )).all()
    assert len(payments) == accepted_count
    assert len({item.idempotency_key for item in payments}) == accepted_count

    paid = Decimal(amount) * accepted_count
    assert sum((item.amount for item in payments), Decimal("0.00")) == paid

    installment = db_session.get(Installment, installment_id)
    assert installment.paid_amount == paid
    assert installment.principal_paid + installment.interest_paid == paid
    assert installment.total_due - installment.paid_amount == Decimal("1500.00")
    assert installment.status == "partial"
