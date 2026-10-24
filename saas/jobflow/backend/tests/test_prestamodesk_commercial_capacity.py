"""Functional portfolio baseline; not a production load certification."""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from time import perf_counter

from app.models import TenantMembership, User
from app.security import create_access_token
from tests.test_prestamodesk_loans import (
    LOANS_URL,
    create_borrower,
    create_tenant,
    get_product,
    loan_payload,
)


def test_100_active_loans_with_three_simultaneous_readers(
    authenticated_client, db_session,
):
    client = authenticated_client
    tenant = create_tenant(
        db_session,
        get_product(db_session, "prestamodesk"),
        "Synthetic Capacity Tenant",
        "synthetic-capacity-tenant",
    )
    borrower = create_borrower(db_session, tenant)
    owner_headers = client.owner_headers(tenant)
    loan_ids = []

    for _ in range(100):
        payload = {
            **loan_payload(borrower.id),
            "installment_count": 12,
            "payment_frequency": "monthly",
        }
        response = client.post(
            LOANS_URL, headers=owner_headers, json=payload,
        )
        assert response.status_code == 201, response.text
        loan_ids.append(response.json()["id"])

    reader_headers = [owner_headers]
    for index in range(2):
        user = User(
            email=f"capacity-reader-{index}@example.test",
            display_name=f"Synthetic Reader {index}",
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()
        db_session.add(TenantMembership(
            tenant_id=tenant.id,
            user_id=user.id,
            role="member",
            is_active=True,
        ))
        db_session.commit()
        reader_headers.append({
            "Authorization": (
                f"Bearer {create_access_token(user.id, user.session_version)}"
            ),
            "X-Tenant-ID": str(tenant.id),
        })

    tenant_id = tenant.id
    db_session.rollback()
    samples = []
    response_sizes = []

    with ThreadPoolExecutor(max_workers=3) as pool:
        for _ in range(5):
            barrier = Barrier(3)

            def read(headers):
                barrier.wait(timeout=15)
                started = perf_counter()
                response = client.get(
                    f"{LOANS_URL}/details", headers=headers,
                )
                elapsed = perf_counter() - started
                assert response.status_code == 200, response.text
                body = response.json()
                assert [item["id"] for item in body] == loan_ids
                assert len(body) == 100
                assert all(item["status"] == "active" for item in body)
                assert all(len(item["installments"]) == 12 for item in body)

                total = sum(
                    (
                        Decimal(installment["total_due"])
                        - Decimal(installment["paid_amount"])
                        for loan in body
                        for installment in loan["installments"]
                    ),
                    Decimal("0.00"),
                )
                assert total == Decimal("1100000.00")
                assert all(
                    installment["loan_id"] == loan["id"]
                    for loan in body
                    for installment in loan["installments"]
                )
                return elapsed, len(response.content)

            for elapsed, size in pool.map(read, reader_headers):
                samples.append(elapsed)
                response_sizes.append(size)

    assert len(samples) == 15
    print(
        f"\nFUNCTIONAL CAPACITY BASELINE PASSED: tenant={tenant_id}; "
        "100 active loans; 1,200 installments; "
        "3 readers; 15 successful complete responses."
    )
    print(
        f"Diagnostic ASGI timings: median={sorted(samples)[7]:.3f}s; "
        f"maximum={max(samples):.3f}s; "
        f"maximum response bytes={max(response_sizes)}."
    )
    print("These timings are not a production network benchmark.")
