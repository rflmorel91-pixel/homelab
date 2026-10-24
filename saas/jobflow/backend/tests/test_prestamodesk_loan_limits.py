from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest

from fastapi import HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models import Tenant, TenantMembership, TenantResourceLimit
from app.products.prestamodesk.loan_limits import ACTIVE_LOAN_RESOURCE
from app.products.prestamodesk.models import Borrower, Loan, LoanApplication
from app.products.prestamodesk.schemas import LoanCreate
from tests.test_prestamodesk_loans import (
    LOANS_URL, create_borrower, create_tenant, get_product, loan_payload,
)
from tests.test_prestamodesk_application_management import (
    APPLICATIONS_URL, create_application,
)


def setup(client, db):
    tenant = create_tenant(
        db, get_product(db, "prestamodesk"), "Limit Tenant", "limit-tenant",
    )
    borrower = create_borrower(db, tenant)
    return tenant, borrower, client.owner_headers(tenant)


def assign_limit(db, tenant, maximum):
    record = db.get(TenantResourceLimit, (tenant.id, ACTIVE_LOAN_RESOURCE))
    if record is None:
        record = TenantResourceLimit(
            tenant_id=tenant.id,
            resource_key=ACTIVE_LOAN_RESOURCE,
            maximum_count=maximum,
        )
        db.add(record)
    else:
        record.maximum_count = maximum
    db.commit()


def post_loan(client, borrower, headers, **changes):
    return client.post(
        LOANS_URL, headers=headers,
        json={**loan_payload(borrower.id), **changes},
    )


def test_unassigned_tenant_remains_unlimited(authenticated_client, db_session):
    client = authenticated_client
    tenant, borrower, headers = setup(client, db_session)
    assert db_session.get(
        TenantResourceLimit, (tenant.id, ACTIVE_LOAN_RESOURCE),
    ) is None
    for _ in range(3):
        assert post_loan(client, borrower, headers).status_code == 201


def test_zero_limit_blocks_creation_but_not_preview(
    authenticated_client, db_session,
):
    client = authenticated_client
    tenant, borrower, headers = setup(client, db_session)
    assign_limit(db_session, tenant, 0)
    assert post_loan(client, borrower, headers).status_code == 409
    preview = client.post(
        f"{LOANS_URL}/preview",
        headers=headers, json=loan_payload(borrower.id),
    )
    assert preview.status_code == 200
    assert db_session.scalar(select(func.count(Loan.id))) == 0


def test_limit_preserves_retry_reads_and_payments(
    authenticated_client, db_session,
):
    client = authenticated_client
    tenant, borrower, headers = setup(client, db_session)
    assign_limit(db_session, tenant, 1)
    key = str(uuid4())
    payload = {"installment_count": 2, "idempotency_key": key}
    first = post_loan(client, borrower, headers, **payload)
    assert first.status_code == 201
    detail = first.json()

    retry = post_loan(client, borrower, headers, **payload)
    assert retry.status_code == 201
    assert retry.json() == detail
    assert post_loan(client, borrower, headers).status_code == 409
    assert client.get(
        f"{LOANS_URL}/{detail['id']}", headers=headers,
    ).status_code == 200

    for installment in detail["installments"]:
        paid = client.post(
            "/api/v1/products/prestamodesk/payments",
            headers=headers,
            json={
                "installment_id": installment["id"],
                "amount": installment["total_due"],
                "idempotency_key": str(uuid4()),
            },
        )
        assert paid.status_code == 201, paid.text
    assert paid.json()["loan_status"] == "paid"
    assert post_loan(client, borrower, headers).status_code == 201


def test_limit_is_scoped_to_tenant(authenticated_client, db_session):
    client = authenticated_client
    tenant, borrower, headers = setup(client, db_session)
    assign_limit(db_session, tenant, 0)
    other = create_tenant(
        db_session, get_product(db_session, "prestamodesk"),
        "Other Limit Tenant", "other-limit-tenant",
    )
    other_borrower = create_borrower(db_session, other)
    other_headers = client.owner_headers(other)
    assert post_loan(client, borrower, headers).status_code == 409
    assert post_loan(client, other_borrower, other_headers).status_code == 201


def test_conversion_obeys_limit_without_partial_writes(
    authenticated_client, db_session,
):
    client = authenticated_client
    tenant, _, headers = setup(client, db_session)
    application = create_application(db_session, tenant, status="approved")
    application_id = application.id
    assign_limit(db_session, tenant, 0)
    before = db_session.scalar(select(func.count(Borrower.id)))

    blocked = client.post(
        f"{APPLICATIONS_URL}/{application_id}/convert", headers=headers,
    )
    assert blocked.status_code == 409
    db_session.expire_all()
    assert db_session.get(LoanApplication, application_id).status == "approved"
    assert db_session.scalar(select(func.count(Borrower.id))) == before
    assert db_session.scalar(select(func.count(Loan.id))) == 0

    assign_limit(db_session, tenant, 1)
    converted = client.post(
        f"{APPLICATIONS_URL}/{application_id}/convert", headers=headers,
    )
    assert converted.status_code == 201, converted.text
    assert db_session.scalar(select(func.count(Loan.id))) == 1


@pytest.mark.parametrize("competing_conversion", [False, True])
def test_concurrent_creations_cannot_exceed_last_slot(
    authenticated_client, db_session, competing_conversion,
):
    from app.products.prestamodesk.loans_api import create_loan
    from app.products.prestamodesk.applications_api import convert_application

    client = authenticated_client
    tenant, borrower, _ = setup(client, db_session)
    assign_limit(db_session, tenant, 1)
    tenant_id, user_id = tenant.id, client.auth_user.id
    payloads = [
        LoanCreate.model_validate({
            **loan_payload(borrower.id), "idempotency_key": str(uuid4()),
        })
        for _ in range(2)
    ]
    application_id = None
    if competing_conversion:
        application = create_application(
            db_session, tenant, status="approved",
        )
        application_id = application.id
        payloads[1] = None

    engine = db_session.get_bind()
    db_session.rollback()
    barrier = Barrier(2)

    def submit(payload):
        with Session(engine) as db:
            db.execute(text("SET LOCAL statement_timeout = '15s'"))
            current_tenant = db.get(Tenant, tenant_id)
            actor = db.scalar(select(TenantMembership).where(
                TenantMembership.tenant_id == tenant_id,
                TenantMembership.user_id == user_id,
            ))
            barrier.wait(timeout=10)
            try:
                if payload is None:
                    convert_application(
                        application_id=application_id,
                        db=db, tenant=current_tenant,
                    )
                else:
                    create_loan(
                        payload=payload, db=db,
                        tenant=current_tenant, membership=actor,
                    )
                return 201
            except HTTPException as error:
                db.rollback()
                return error.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(submit, payload) for payload in payloads]
        results = [future.result(timeout=25) for future in futures]
    assert sorted(results) == [201, 409]
    db_session.expire_all()
    assert db_session.scalar(select(func.count(Loan.id)).where(
        Loan.tenant_id == tenant_id, Loan.status == "active",
    )) == 1
