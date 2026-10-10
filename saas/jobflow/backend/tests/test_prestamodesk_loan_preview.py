from decimal import Decimal
from sqlalchemy import select, func
from app.products.prestamodesk.models import Loan, Installment
from tests.test_prestamodesk_payment_corrections import setup
from tests.test_prestamodesk_loan_creation_safety import request

URL = "/api/v1/products/prestamodesk/loans"

def test_preview_is_read_only_and_matches_created_schedule(authenticated_client, db_session):
    _, loan, headers = setup(authenticated_client, db_session)
    payload = request(loan) | {"principal_amount": "1000.01", "installment_count": 3, "first_payment_date": "2027-01-31"}
    before = (db_session.scalar(select(func.count(Loan.id))), db_session.scalar(select(func.count(Installment.id))))
    response = authenticated_client.post(URL + "/preview", headers=headers, json=payload)
    assert response.status_code == 200, response.text
    assert response.headers["Cache-Control"] == "no-store"
    preview = response.json()
    assert (db_session.scalar(select(func.count(Loan.id))), db_session.scalar(select(func.count(Installment.id)))) == before
    assert [i["due_date"] for i in preview["installments"]] == ["2027-01-31", "2027-02-28", "2027-03-31"]
    created = authenticated_client.post(URL, headers=headers, json=payload)
    assert created.status_code == 201, created.text
    for field in ["principal_amount", "total_interest", "total_due"]:
        assert Decimal(preview[field]) == Decimal(created.json()[field])
    for actual, expected in zip(created.json()["installments"], preview["installments"]):
        for field in expected:
            assert actual[field] == expected[field]

def test_preview_permissions_and_foreign_borrower(authenticated_client, db_session):
    tenant, loan, headers = setup(authenticated_client, db_session)
    payload = request(loan)
    assert authenticated_client.post(URL + "/preview", headers=authenticated_client.auth_headers(tenant), json=payload).status_code == 403
    headers = authenticated_client.owner_headers(tenant)
    assert authenticated_client.post(URL + "/preview", headers=headers, json=payload | {"borrower_id": 999999}).status_code == 404
