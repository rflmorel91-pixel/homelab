from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from app.models import (
    Product,
    Tenant,
    TenantMembership,
    User,
)
from app.products.prestamodesk.models import (
    Borrower,
    CollectionActivity,
    Installment,
    Loan,
    LoanCollectorAssignment,
    Payment,
    PaymentPromise,
    PromisePaymentAllocation,
)


BASE_URL = "/api/v1/products/prestamodesk"


def role_headers(
    authenticated_client,
    db_session,
    tenant,
    role,
):
    headers = authenticated_client.auth_headers(
        tenant
    )

    membership = db_session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant.id,
            TenantMembership.user_id
            == authenticated_client.auth_user.id,
        )
    )
    assert membership is not None

    membership.role = role
    db_session.commit()

    return headers


def create_tenant(
    db_session,
    *,
    client_number,
    slug,
):
    product = db_session.scalar(
        select(Product).where(
            Product.slug == "prestamodesk"
        )
    )
    assert product is not None

    tenant = Tenant(
        product_id=product.id,
        client_number=client_number,
        name=f"Collections Tenant {client_number}",
        slug=slug,
        status="active",
    )
    db_session.add(tenant)
    db_session.flush()

    return tenant


def create_loan(
    db_session,
    *,
    tenant,
    suffix,
    due_date=date(2026, 9, 1),
    total_due=Decimal("1000.00"),
    paid_amount=Decimal("0.00"),
):
    borrower = Borrower(
        tenant_id=tenant.id,
        full_name=f"Cliente Cobros {suffix}",
        document_type="cedula",
        document_number=(
            f"000-0000{suffix:03d}-0"
        ),
        phone=f"809-555-{suffix:04d}",
        email=f"cliente{suffix}@example.test",
        status="active",
    )
    db_session.add(borrower)
    db_session.flush()

    loan = Loan(
        tenant_id=tenant.id,
        borrower_id=borrower.id,
        principal_amount=Decimal("900.00"),
        flat_interest_rate_percent=Decimal(
            "11.1111"
        ),
        total_interest=Decimal("100.00"),
        total_due=total_due,
        installment_count=1,
        payment_frequency="monthly",
        start_date=date(2026, 8, 1),
        first_payment_date=due_date,
        currency="DOP",
        status="active",
        loan_type="personal",
        late_fee_enabled=False,
    )
    db_session.add(loan)
    db_session.flush()

    principal_paid = min(
        paid_amount,
        Decimal("900.00"),
    )
    interest_paid = max(
        Decimal("0.00"),
        paid_amount - principal_paid,
    )

    installment = Installment(
        tenant_id=tenant.id,
        loan_id=loan.id,
        sequence_number=1,
        due_date=due_date,
        principal_due=Decimal("900.00"),
        interest_due=Decimal("100.00"),
        total_due=total_due,
        paid_amount=paid_amount,
        principal_paid=principal_paid,
        interest_paid=interest_paid,
        late_fee_accrued=Decimal("0.00"),
        late_fee_paid=Decimal("0.00"),
        status=(
            "paid"
            if paid_amount >= total_due
            else "pending"
        ),
    )
    db_session.add(installment)
    db_session.commit()

    return borrower, loan, installment


def test_collector_sees_only_assigned_overdue_portfolio(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        client_number=810,
        slug="collections-portfolio",
    )
    _, first_loan, _ = create_loan(
        db_session,
        tenant=tenant,
        suffix=810,
        due_date=date(2026, 8, 15),
    )
    _, second_loan, _ = create_loan(
        db_session,
        tenant=tenant,
        suffix=811,
        due_date=date(2026, 9, 15),
        paid_amount=Decimal("250.00"),
    )
    _, future_loan, _ = create_loan(
        db_session,
        tenant=tenant,
        suffix=812,
        due_date=date(2026, 11, 15),
    )

    other_tenant = create_tenant(
        db_session,
        client_number=811,
        slug="collections-other-tenant",
    )
    _, other_loan, _ = create_loan(
        db_session,
        tenant=other_tenant,
        suffix=813,
        due_date=date(2026, 7, 1),
    )

    headers = role_headers(
        authenticated_client,
        db_session,
        tenant,
        "collector",
    )

    db_session.add(
        LoanCollectorAssignment(
            tenant_id=tenant.id,
            loan_id=first_loan.id,
            collector_user_id=(
                authenticated_client.auth_user.id
            ),
            assigned_by_user_id=(
                authenticated_client.auth_user.id
            ),
        )
    )
    db_session.commit()

    response = authenticated_client.get(
        f"{BASE_URL}/collections/portfolio",
        params={"as_of": "2026-10-02"},
        headers=headers,
    )

    assert response.status_code == 200
    portfolio = response.json()

    assert {
        item["loan_id"]
        for item in portfolio
    } == {
        first_loan.id,
    }
    assert second_loan.id not in {
        item["loan_id"]
        for item in portfolio
    }
    assert future_loan.id not in {
        item["loan_id"]
        for item in portfolio
    }
    assert other_loan.id not in {
        item["loan_id"]
        for item in portfolio
    }

    first = next(
        item
        for item in portfolio
        if item["loan_id"] == first_loan.id
    )
    assert first["days_overdue"] == 48
    assert first["overdue_installment_count"] == 1
    assert first["total_balance_due"] == "1000.00"

    assert first["assigned_collector_user_id"] == (
        authenticated_client.auth_user.id
    )
    assert (
        first["assigned_collector_display_name"]
        == authenticated_client.auth_user.display_name
    )


def test_collections_require_owner_or_collector(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        client_number=820,
        slug="collections-roles",
    )
    create_loan(
        db_session,
        tenant=tenant,
        suffix=820,
    )

    member_headers = role_headers(
        authenticated_client,
        db_session,
        tenant,
        "member",
    )
    denied = authenticated_client.get(
        f"{BASE_URL}/collections/portfolio",
        params={"as_of": "2026-10-02"},
        headers=member_headers,
    )
    assert denied.status_code == 403

    owner_headers = role_headers(
        authenticated_client,
        db_session,
        tenant,
        "owner",
    )
    owner_response = authenticated_client.get(
        f"{BASE_URL}/collections/portfolio",
        params={"as_of": "2026-10-02"},
        headers=owner_headers,
    )
    assert owner_response.status_code == 200

    collector_headers = role_headers(
        authenticated_client,
        db_session,
        tenant,
        "collector",
    )
    collector_response = authenticated_client.get(
        f"{BASE_URL}/collections/portfolio",
        params={"as_of": "2026-10-02"},
        headers=collector_headers,
    )
    assert collector_response.status_code == 200


def test_collector_records_activity_and_cannot_cross_tenants(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        client_number=830,
        slug="collections-activities",
    )
    _, loan, _ = create_loan(
        db_session,
        tenant=tenant,
        suffix=830,
    )

    other_tenant = create_tenant(
        db_session,
        client_number=831,
        slug="collections-activities-other",
    )
    _, other_loan, _ = create_loan(
        db_session,
        tenant=other_tenant,
        suffix=831,
    )

    headers = role_headers(
        authenticated_client,
        db_session,
        tenant,
        "collector",
    )

    assign_current_collector(
        db_session,
        authenticated_client=authenticated_client,
        tenant=tenant,
        loan=loan,
    )

    created = authenticated_client.post(
        (
            f"{BASE_URL}/collections/loans/"
            f"{loan.id}/activities"
        ),
        headers=headers,
        json={
            "channel": "phone",
            "outcome": "Cliente contactado",
            "notes": "Prometió confirmar mañana.",
            "contacted_at": (
                "2026-10-02T14:00:00Z"
            ),
            "next_follow_up_at": (
                "2026-10-03T14:00:00Z"
            ),
        },
    )
    assert created.status_code == 201
    assert created.json()["loan_id"] == loan.id
    assert created.json()["recorded_by_user_id"] == (
        authenticated_client.auth_user.id
    )

    listed = authenticated_client.get(
        (
            f"{BASE_URL}/collections/loans/"
            f"{loan.id}/activities"
        ),
        headers=headers,
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["channel"] == "phone"

    activity = db_session.scalar(
        select(CollectionActivity).where(
            CollectionActivity.loan_id == loan.id
        )
    )
    assert activity is not None

    cross_tenant = authenticated_client.post(
        (
            f"{BASE_URL}/collections/loans/"
            f"{other_loan.id}/activities"
        ),
        headers=headers,
        json={
            "channel": "visit",
            "outcome": "No disponible",
            "contacted_at": (
                "2026-10-02T15:00:00Z"
            ),
        },
    )
    assert cross_tenant.status_code == 404


def test_payments_reconcile_oldest_promises_once(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        client_number=840,
        slug="collections-promises",
    )
    _, loan, installment = create_loan(
        db_session,
        tenant=tenant,
        suffix=840,
    )

    collector_headers = role_headers(
        authenticated_client,
        db_session,
        tenant,
        "collector",
    )

    assign_current_collector(
        db_session,
        authenticated_client=authenticated_client,
        tenant=tenant,
        loan=loan,
    )

    first_response = authenticated_client.post(
        (
            f"{BASE_URL}/collections/loans/"
            f"{loan.id}/promises"
        ),
        headers=collector_headers,
        json={
            "promised_amount": "100.00",
            "due_date": "2026-10-05",
            "notes": "Primera promesa",
        },
    )
    assert first_response.status_code == 201
    first_id = first_response.json()["id"]

    second_response = authenticated_client.post(
        (
            f"{BASE_URL}/collections/loans/"
            f"{loan.id}/promises"
        ),
        headers=collector_headers,
        json={
            "promised_amount": "50.00",
            "due_date": "2026-10-06",
            "notes": "Segunda promesa",
        },
    )
    assert second_response.status_code == 201
    second_id = second_response.json()["id"]

    collector_payment = authenticated_client.post(
        f"{BASE_URL}/payments",
        headers=collector_headers,
        json={
            "installment_id": installment.id,
            "amount": "10.00",
            "payment_method": "cash",
            "paid_at": "2026-10-02T16:00:00Z",
        },
    )
    assert collector_payment.status_code == 403

    cashier_headers = role_headers(
        authenticated_client,
        db_session,
        tenant,
        "member",
    )

    first_payment_response = authenticated_client.post(
        f"{BASE_URL}/payments",
        headers=cashier_headers,
        json={
            "installment_id": installment.id,
            "amount": "60.00",
            "payment_method": "cash",
            "reference": "COLLECTION-PAYMENT-1",
            "paid_at": "2026-10-02T16:05:00Z",
        },
    )
    assert first_payment_response.status_code == 201

    first_promise = db_session.get(
        PaymentPromise,
        first_id,
    )
    second_promise = db_session.get(
        PaymentPromise,
        second_id,
    )
    db_session.refresh(first_promise)
    db_session.refresh(second_promise)

    assert first_promise.status == "partial"
    assert first_promise.fulfilled_amount == Decimal(
        "60.00"
    )
    assert second_promise.status == "pending"
    assert second_promise.fulfilled_amount == Decimal(
        "0.00"
    )

    second_payment_response = (
        authenticated_client.post(
            f"{BASE_URL}/payments",
            headers=cashier_headers,
            json={
                "installment_id": installment.id,
                "amount": "90.00",
                "payment_method": "bank_transfer",
                "reference": "COLLECTION-PAYMENT-2",
                "paid_at": (
                    "2026-10-02T16:10:00Z"
                ),
            },
        )
    )
    assert second_payment_response.status_code == 201

    db_session.refresh(first_promise)
    db_session.refresh(second_promise)

    assert first_promise.status == "fulfilled"
    assert first_promise.fulfilled_amount == Decimal(
        "100.00"
    )
    assert first_promise.fulfilled_at is not None

    assert second_promise.status == "fulfilled"
    assert second_promise.fulfilled_amount == Decimal(
        "50.00"
    )
    assert second_promise.fulfilled_at is not None

    allocations = list(
        db_session.scalars(
            select(PromisePaymentAllocation)
            .where(
                PromisePaymentAllocation.tenant_id
                == tenant.id
            )
            .order_by(
                PromisePaymentAllocation.id
            )
        ).all()
    )
    assert [
        (
            allocation.promise_id,
            allocation.amount,
        )
        for allocation in allocations
    ] == [
        (first_id, Decimal("60.00")),
        (first_id, Decimal("40.00")),
        (second_id, Decimal("50.00")),
    ]

    payments = list(
        db_session.scalars(
            select(Payment)
            .where(Payment.tenant_id == tenant.id)
            .order_by(Payment.id)
        ).all()
    )
    assert len(payments) == 2

    allocation_count_before = len(allocations)

    from app.products.prestamodesk.promise_reconciliation import (
        reconcile_payment_promises,
    )

    reconcile_payment_promises(
        db=db_session,
        payment=payments[-1],
    )
    db_session.commit()

    allocation_count_after = len(
        db_session.scalars(
            select(PromisePaymentAllocation).where(
                PromisePaymentAllocation.tenant_id
                == tenant.id
            )
        ).all()
    )
    assert allocation_count_after == (
        allocation_count_before
    )


def test_promise_cancellation_and_overdue_filter(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        client_number=850,
        slug="collections-cancellation",
    )
    _, loan, _ = create_loan(
        db_session,
        tenant=tenant,
        suffix=850,
    )

    headers = role_headers(
        authenticated_client,
        db_session,
        tenant,
        "collector",
    )

    assign_current_collector(
        db_session,
        authenticated_client=authenticated_client,
        tenant=tenant,
        loan=loan,
    )

    created = authenticated_client.post(
        (
            f"{BASE_URL}/collections/loans/"
            f"{loan.id}/promises"
        ),
        headers=headers,
        json={
            "promised_amount": "200.00",
            "due_date": "2026-10-01",
        },
    )
    assert created.status_code == 201
    promise_id = created.json()["id"]

    overdue = authenticated_client.get(
        f"{BASE_URL}/collections/promises",
        params={
            "overdue_only": "true",
            "as_of": "2026-10-02",
        },
        headers=headers,
    )
    assert overdue.status_code == 200
    assert [
        item["id"]
        for item in overdue.json()
    ] == [promise_id]
    assert overdue.json()[0]["is_overdue"] is True

    cancelled = authenticated_client.post(
        (
            f"{BASE_URL}/collections/promises/"
            f"{promise_id}/cancel"
        ),
        headers=headers,
        json={"notes": "Cliente renegociará."},
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert cancelled.json()["cancelled_at"] is not None

    overdue_after = authenticated_client.get(
        f"{BASE_URL}/collections/promises",
        params={
            "overdue_only": "true",
            "as_of": "2026-10-02",
        },
        headers=headers,
    )
    assert overdue_after.status_code == 200
    assert overdue_after.json() == []



def test_collector_is_blocked_from_operational_workspaces(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        client_number=825,
        slug="collections-operational-boundary",
    )
    _, loan, _ = create_loan(
        db_session,
        tenant=tenant,
        suffix=825,
    )

    headers = role_headers(
        authenticated_client,
        db_session,
        tenant,
        "collector",
    )

    blocked_paths = (
        "/applications",
        "/borrowers",
        "/cashier/loans",
        "/cashier/closing-preview",
        "/late-fee-policy",
        "/loans",
        f"/payments/loan/{loan.id}",
        "/prospects",
    )

    for path_suffix in blocked_paths:
        response = authenticated_client.get(
            f"{BASE_URL}{path_suffix}",
            headers=headers,
        )

        assert response.status_code == 403, (
            path_suffix,
            response.status_code,
            response.text,
        )

    allowed = authenticated_client.get(
        f"{BASE_URL}/collections/portfolio",
        params={"as_of": "2026-10-02"},
        headers=headers,
    )
    assert allowed.status_code == 200



def add_collector(
    db_session,
    *,
    tenant,
    email,
    display_name,
    is_active=True,
):
    user = User(
        email=email,
        display_name=display_name,
        is_active=is_active,
    )
    db_session.add(user)
    db_session.flush()

    membership = TenantMembership(
        tenant_id=tenant.id,
        user_id=user.id,
        role="collector",
    )
    db_session.add(membership)
    db_session.flush()

    return user


def test_owner_sees_collections_supervision_metrics(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        client_number=860,
        slug="collections-supervision",
    )
    _, first_loan, first_installment = create_loan(
        db_session,
        tenant=tenant,
        suffix=860,
        due_date=date(2026, 8, 1),
    )
    _, second_loan, _ = create_loan(
        db_session,
        tenant=tenant,
        suffix=861,
        due_date=date(2026, 9, 1),
        paid_amount=Decimal("250.00"),
    )

    owner_headers = role_headers(
        authenticated_client,
        db_session,
        tenant,
        "owner",
    )

    first_collector = add_collector(
        db_session,
        tenant=tenant,
        email="alice.collector@example.test",
        display_name="Alice Collector",
    )
    second_collector = add_collector(
        db_session,
        tenant=tenant,
        email="bruno.collector@example.test",
        display_name="Bruno Collector",
    )
    add_collector(
        db_session,
        tenant=tenant,
        email="inactive.collector@example.test",
        display_name="Inactive Collector",
        is_active=False,
    )

    db_session.add_all(
        [
            CollectionActivity(
                tenant_id=tenant.id,
                loan_id=first_loan.id,
                recorded_by_user_id=first_collector.id,
                channel="phone",
                outcome="Contactado",
                contacted_at=datetime(
                    2026,
                    9,
                    20,
                    14,
                    0,
                    tzinfo=timezone.utc,
                ),
            ),
            CollectionActivity(
                tenant_id=tenant.id,
                loan_id=first_loan.id,
                recorded_by_user_id=first_collector.id,
                channel="whatsapp",
                outcome="Sin respuesta",
                contacted_at=datetime(
                    2026,
                    9,
                    21,
                    14,
                    0,
                    tzinfo=timezone.utc,
                ),
            ),
            CollectionActivity(
                tenant_id=tenant.id,
                loan_id=second_loan.id,
                recorded_by_user_id=second_collector.id,
                channel="visit",
                outcome="Contactado",
                contacted_at=datetime(
                    2026,
                    9,
                    22,
                    14,
                    0,
                    tzinfo=timezone.utc,
                ),
            ),
        ]
    )

    db_session.add_all(
        [
            PaymentPromise(
                tenant_id=tenant.id,
                loan_id=first_loan.id,
                created_by_user_id=first_collector.id,
                promised_amount=Decimal("100.00"),
                fulfilled_amount=Decimal("0.00"),
                due_date=date(2026, 9, 30),
                status="pending",
            ),
            PaymentPromise(
                tenant_id=tenant.id,
                loan_id=first_loan.id,
                created_by_user_id=first_collector.id,
                promised_amount=Decimal("200.00"),
                fulfilled_amount=Decimal("200.00"),
                due_date=date(2026, 10, 1),
                status="fulfilled",
                fulfilled_at=datetime(
                    2026,
                    10,
                    1,
                    15,
                    0,
                    tzinfo=timezone.utc,
                ),
            ),
            PaymentPromise(
                tenant_id=tenant.id,
                loan_id=second_loan.id,
                created_by_user_id=second_collector.id,
                promised_amount=Decimal("300.00"),
                fulfilled_amount=Decimal("75.00"),
                due_date=date(2026, 10, 10),
                status="partial",
            ),
            PaymentPromise(
                tenant_id=tenant.id,
                loan_id=second_loan.id,
                created_by_user_id=second_collector.id,
                promised_amount=Decimal("400.00"),
                fulfilled_amount=Decimal("0.00"),
                due_date=date(2026, 9, 25),
                status="cancelled",
                cancelled_at=datetime(
                    2026,
                    9,
                    26,
                    15,
                    0,
                    tzinfo=timezone.utc,
                ),
            ),
        ]
    )

    db_session.add(
        Payment(
            tenant_id=tenant.id,
            loan_id=first_loan.id,
            installment_id=first_installment.id,
            recorded_by_user_id=(
                authenticated_client.auth_user.id
            ),
            amount=Decimal("150.00"),
            principal_amount=Decimal("135.00"),
            interest_amount=Decimal("15.00"),
            late_fee_amount=Decimal("0.00"),
            payment_method="cash",
            reference="SUPERVISION-PAYMENT",
            paid_at=datetime(
                2026,
                10,
                1,
                16,
                0,
                tzinfo=timezone.utc,
            ),
        )
    )

    other_tenant = create_tenant(
        db_session,
        client_number=861,
        slug="collections-supervision-isolated",
    )
    _, other_loan, other_installment = create_loan(
        db_session,
        tenant=other_tenant,
        suffix=862,
        due_date=date(2026, 7, 1),
    )
    other_collector = add_collector(
        db_session,
        tenant=other_tenant,
        email="isolated.collector@example.test",
        display_name="Isolated Collector",
    )
    db_session.add_all(
        [
            CollectionActivity(
                tenant_id=other_tenant.id,
                loan_id=other_loan.id,
                recorded_by_user_id=other_collector.id,
                channel="phone",
                outcome="Aislado",
                contacted_at=datetime(
                    2026,
                    9,
                    1,
                    14,
                    0,
                    tzinfo=timezone.utc,
                ),
            ),
            PaymentPromise(
                tenant_id=other_tenant.id,
                loan_id=other_loan.id,
                created_by_user_id=other_collector.id,
                promised_amount=Decimal("9999.00"),
                fulfilled_amount=Decimal("9999.00"),
                due_date=date(2026, 9, 1),
                status="fulfilled",
            ),
            Payment(
                tenant_id=other_tenant.id,
                loan_id=other_loan.id,
                installment_id=other_installment.id,
                recorded_by_user_id=other_collector.id,
                amount=Decimal("9999.00"),
                principal_amount=Decimal("900.00"),
                interest_amount=Decimal("100.00"),
                late_fee_amount=Decimal("0.00"),
                payment_method="cash",
                reference="ISOLATED-PAYMENT",
                paid_at=datetime(
                    2026,
                    9,
                    1,
                    16,
                    0,
                    tzinfo=timezone.utc,
                ),
            ),
        ]
    )
    db_session.commit()

    response = authenticated_client.get(
        f"{BASE_URL}/collections/supervision",
        params={"as_of": "2026-10-02"},
        headers=owner_headers,
    )

    assert response.status_code == 200
    supervision = response.json()

    assert supervision["as_of"] == "2026-10-02"
    assert supervision["overdue_loan_count"] == 2
    assert supervision["overdue_balance"] == "1750.00"
    assert supervision["total_recovered"] == "150.00"
    assert supervision["activity_count"] == 3
    assert supervision["promise_count"] == 4
    assert supervision["pending_promise_count"] == 1
    assert supervision["partial_promise_count"] == 1
    assert supervision["fulfilled_promise_count"] == 1
    assert supervision["cancelled_promise_count"] == 1
    assert supervision["overdue_promise_count"] == 1
    assert supervision["promised_amount"] == "1000.00"
    assert supervision["fulfilled_amount"] == "275.00"
    assert (
        supervision[
            "promise_count_fulfillment_percent"
        ]
        == "25.00"
    )
    assert (
        supervision[
            "promise_amount_fulfillment_percent"
        ]
        == "27.50"
    )

    assert [
        collector["display_name"]
        for collector in supervision["collectors"]
    ] == [
        "Alice Collector",
        "Bruno Collector",
    ]

    first = supervision["collectors"][0]
    assert first["activity_count"] == 2
    assert first["promise_count"] == 2
    assert first["pending_promise_count"] == 1
    assert first["fulfilled_promise_count"] == 1
    assert first["overdue_promise_count"] == 1
    assert first["promised_amount"] == "300.00"
    assert first["fulfilled_amount"] == "200.00"
    assert (
        first["promise_count_fulfillment_percent"]
        == "50.00"
    )
    assert (
        first["promise_amount_fulfillment_percent"]
        == "66.67"
    )
    assert "total_recovered" not in first

    second = supervision["collectors"][1]
    assert second["activity_count"] == 1
    assert second["promise_count"] == 2
    assert second["partial_promise_count"] == 1
    assert second["cancelled_promise_count"] == 1
    assert second["overdue_promise_count"] == 0
    assert second["promised_amount"] == "700.00"
    assert second["fulfilled_amount"] == "75.00"
    assert (
        second["promise_count_fulfillment_percent"]
        == "0.00"
    )
    assert (
        second["promise_amount_fulfillment_percent"]
        == "10.71"
    )


def test_collections_supervision_is_owner_only(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        client_number=862,
        slug="collections-supervision-authorization",
    )

    for role in ("collector", "member"):
        headers = role_headers(
            authenticated_client,
            db_session,
            tenant,
            role,
        )
        response = authenticated_client.get(
            f"{BASE_URL}/collections/supervision",
            headers=headers,
        )
        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Owner role required"
        )


def test_empty_collections_supervision_uses_zero_metrics(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        client_number=863,
        slug="collections-supervision-empty",
    )
    headers = role_headers(
        authenticated_client,
        db_session,
        tenant,
        "owner",
    )

    response = authenticated_client.get(
        f"{BASE_URL}/collections/supervision",
        params={"as_of": "2026-10-02"},
        headers=headers,
    )

    assert response.status_code == 200
    supervision = response.json()

    assert supervision["overdue_loan_count"] == 0
    assert supervision["overdue_balance"] == "0.00"
    assert supervision["total_recovered"] == "0.00"
    assert supervision["activity_count"] == 0
    assert supervision["promise_count"] == 0
    assert supervision["promised_amount"] == "0.00"
    assert supervision["fulfilled_amount"] == "0.00"
    assert (
        supervision[
            "promise_count_fulfillment_percent"
        ]
        == "0.00"
    )
    assert (
        supervision[
            "promise_amount_fulfillment_percent"
        ]
        == "0.00"
    )
    assert supervision["collectors"] == []


def assign_current_collector(
    db_session,
    *,
    authenticated_client,
    tenant,
    loan,
):
    db_session.add(
        LoanCollectorAssignment(
            tenant_id=tenant.id,
            loan_id=loan.id,
            collector_user_id=(
                authenticated_client.auth_user.id
            ),
            assigned_by_user_id=(
                authenticated_client.auth_user.id
            ),
        )
    )
    db_session.commit()
