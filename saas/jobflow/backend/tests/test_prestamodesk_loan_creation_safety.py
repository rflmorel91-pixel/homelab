from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from sqlalchemy import select,func
from app.products.prestamodesk.models import Loan,Installment,Borrower
from tests.test_prestamodesk_payment_corrections import setup

URL='/api/v1/products/prestamodesk/loans'
def request(loan):
 return dict(borrower_id=loan['borrower_id'],principal_amount='1000.00',flat_interest_rate_percent='10.0000',installment_count=2,payment_frequency='monthly',start_date='2026-10-10',first_payment_date='2026-11-10',idempotency_key=str(uuid4()))

def test_concurrent_requests_create_one_loan_and_schedule(authenticated_client,db_session):
 _,loan,headers=setup(authenticated_client,db_session);payload=request(loan)
 with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:authenticated_client.post(URL,headers=headers,json=payload),range(2)))
 assert [r.status_code for r in results]==[201,201]
 assert results[0].json()==results[1].json()
 assert db_session.scalar(select(func.count(Loan.id)))==2
 assert db_session.scalar(select(func.count(Installment.id)))==4

def test_retry_original_snapshot_conflict_and_validation(authenticated_client,db_session):
 _,loan,headers=setup(authenticated_client,db_session);payload=request(loan)
 assert authenticated_client.post(URL,headers=headers,json=payload|{'first_payment_date':'2026-01-01'}).status_code==422
 first=authenticated_client.post(URL,headers=headers,json=payload);assert first.status_code==201,first.text
 db_session.get(Loan,first.json()['id']).status='cancelled';db_session.get(Borrower,loan['borrower_id']).status='inactive';db_session.commit()
 retry=authenticated_client.post(URL,headers=headers,json=payload|{'principal_amount':'1000','flat_interest_rate_percent':'10'})
 assert retry.status_code==201 and retry.json()==first.json()
 assert authenticated_client.post(URL,headers=headers,json=payload|{'notes':'different'}).status_code==409
 assert db_session.scalar(select(func.count(Loan.id)))==2


def test_same_key_is_scoped_to_tenant(authenticated_client,db_session):
 from tests.test_prestamodesk_payments import create_tenant,create_borrower,get_product
 _,loan,headers=setup(authenticated_client,db_session);payload=request(loan)
 first=authenticated_client.post(URL,headers=headers,json=payload);assert first.status_code==201
 tenant=create_tenant(db_session,get_product(db_session),'Second request tenant','second-request-tenant');borrower=create_borrower(db_session,tenant,'Synthetic second borrower')
 second=authenticated_client.post(URL,headers=authenticated_client.owner_headers(tenant),json=payload|{'borrower_id':borrower.id});assert second.status_code==201
 assert first.json()['id']!=second.json()['id']
 assert authenticated_client.post(URL,headers=headers,json=payload|{'borrower_id':borrower.id,'idempotency_key':str(uuid4())}).status_code==404


def test_replay_requires_current_manager_access(authenticated_client,db_session):
 tenant,loan,headers=setup(authenticated_client,db_session);payload=request(loan)
 assert authenticated_client.post(URL,headers=headers,json=payload).status_code==201
 member_headers=authenticated_client.auth_headers(tenant)
 assert authenticated_client.post(URL,headers=member_headers,json=payload).status_code==403
 assert db_session.scalar(select(func.count(Loan.id)))==2
