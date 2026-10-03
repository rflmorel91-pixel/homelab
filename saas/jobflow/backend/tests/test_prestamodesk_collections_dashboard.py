from datetime import date, datetime, timezone
from decimal import Decimal

from app.products.prestamodesk.models import (
    CollectionActivity,
    LoanCollectorAssignment,
    PaymentPromise,
)
from tests.test_prestamodesk_collections import (
    BASE_URL,
    add_collector,
    create_loan,
    create_tenant,
    role_headers,
)


def test_owner_sees_actionable_collections_dashboard(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        client_number=880,
        slug="collections-actionable-dashboard",
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
        email="ana.dashboard@example.test",
        display_name="Ana Dashboard",
    )
    second_collector = add_collector(
        db_session,
        tenant=tenant,
        email="bruno.dashboard@example.test",
        display_name="Bruno Dashboard",
    )

    _, loan_1_30, _ = create_loan(
        db_session,
        tenant=tenant,
        suffix=880,
        due_date=date(2026, 9, 22),
    )
    _, loan_31_60, _ = create_loan(
        db_session,
        tenant=tenant,
        suffix=881,
        due_date=date(2026, 8, 23),
        paid_amount=Decimal("100.00"),
    )
    _, loan_61_90, _ = create_loan(
        db_session,
        tenant=tenant,
        suffix=882,
        due_date=date(2026, 7, 24),
        paid_amount=Decimal("200.00"),
    )
    _, loan_91_plus, _ = create_loan(
        db_session,
        tenant=tenant,
        suffix=883,
        due_date=date(2026, 6, 24),
        paid_amount=Decimal("300.00"),
    )

    db_session.add_all(
        [
            LoanCollectorAssignment(
                tenant_id=tenant.id,
                loan_id=loan_1_30.id,
                collector_user_id=first_collector.id,
                assigned_by_user_id=(
                    authenticated_client.auth_user.id
                ),
                assigned_at=datetime(
                    2026,
                    9,
                    20,
                    12,
                    0,
                    tzinfo=timezone.utc,
                ),
            ),
            LoanCollectorAssignment(
                tenant_id=tenant.id,
                loan_id=loan_61_90.id,
                collector_user_id=first_collector.id,
                assigned_by_user_id=(
                    authenticated_client.auth_user.id
                ),
                assigned_at=datetime(
                    2026,
                    9,
                    20,
                    12,
                    0,
                    tzinfo=timezone.utc,
                ),
            ),
        ]
    )

    db_session.add_all(
        [
            CollectionActivity(
                tenant_id=tenant.id,
                loan_id=loan_1_30.id,
                recorded_by_user_id=first_collector.id,
                channel="phone",
                outcome="Seguimiento vencido",
                contacted_at=datetime(
                    2026,
                    9,
                    30,
                    12,
                    0,
                    tzinfo=timezone.utc,
                ),
                next_follow_up_at=datetime(
                    2026,
                    10,
                    1,
                    12,
                    0,
                    tzinfo=timezone.utc,
                ),
            ),
            CollectionActivity(
                tenant_id=tenant.id,
                loan_id=loan_61_90.id,
                recorded_by_user_id=first_collector.id,
                channel="whatsapp",
                outcome="Seguimiento para hoy",
                contacted_at=datetime(
                    2026,
                    10,
                    1,
                    12,
                    0,
                    tzinfo=timezone.utc,
                ),
                next_follow_up_at=datetime(
                    2026,
                    10,
                    2,
                    15,
                    0,
                    tzinfo=timezone.utc,
                ),
            ),
            CollectionActivity(
                tenant_id=tenant.id,
                loan_id=loan_31_60.id,
                recorded_by_user_id=second_collector.id,
                channel="visit",
                outcome="Seguimiento futuro",
                contacted_at=datetime(
                    2026,
                    10,
                    1,
                    13,
                    0,
                    tzinfo=timezone.utc,
                ),
                next_follow_up_at=datetime(
                    2026,
                    10,
                    3,
                    12,
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
                loan_id=loan_1_30.id,
                created_by_user_id=first_collector.id,
                promised_amount=Decimal("150.00"),
                fulfilled_amount=Decimal("0.00"),
                due_date=date(2026, 10, 2),
                status="pending",
            ),
            PaymentPromise(
                tenant_id=tenant.id,
                loan_id=loan_61_90.id,
                created_by_user_id=first_collector.id,
                promised_amount=Decimal("200.00"),
                fulfilled_amount=Decimal("50.00"),
                due_date=date(2026, 10, 2),
                status="partial",
            ),
            PaymentPromise(
                tenant_id=tenant.id,
                loan_id=loan_31_60.id,
                created_by_user_id=second_collector.id,
                promised_amount=Decimal("100.00"),
                fulfilled_amount=Decimal("100.00"),
                due_date=date(2026, 10, 2),
                status="fulfilled",
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
    dashboard = response.json()

    assert dashboard["overdue_loan_count"] == 4
    assert dashboard["overdue_balance"] == "3400.00"

    assert dashboard["assigned_overdue_loan_count"] == 2
    assert dashboard["assigned_overdue_balance"] == "1800.00"
    assert dashboard["unassigned_overdue_loan_count"] == 2
    assert dashboard["unassigned_overdue_balance"] == "1600.00"

    assert dashboard["promises_due_today_count"] == 2
    assert dashboard["follow_ups_due_today_count"] == 1
    assert dashboard["overdue_follow_up_count"] == 1

    assert dashboard["aging_buckets"] == [
        {
            "key": "days_1_30",
            "label": "1–30 días",
            "minimum_days": 1,
            "maximum_days": 30,
            "loan_count": 1,
            "balance": "1000.00",
        },
        {
            "key": "days_31_60",
            "label": "31–60 días",
            "minimum_days": 31,
            "maximum_days": 60,
            "loan_count": 1,
            "balance": "900.00",
        },
        {
            "key": "days_61_90",
            "label": "61–90 días",
            "minimum_days": 61,
            "maximum_days": 90,
            "loan_count": 1,
            "balance": "800.00",
        },
        {
            "key": "days_91_plus",
            "label": "91 días o más",
            "minimum_days": 91,
            "maximum_days": None,
            "loan_count": 1,
            "balance": "700.00",
        },
    ]

    collectors = {
        collector["display_name"]: collector
        for collector in dashboard["collectors"]
    }

    first = collectors["Ana Dashboard"]
    assert first["active_overdue_loan_count"] == 2
    assert first["active_overdue_balance"] == "1800.00"

    second = collectors["Bruno Dashboard"]
    assert second["active_overdue_loan_count"] == 0
    assert second["active_overdue_balance"] == "0.00"


def test_empty_actionable_dashboard_uses_zero_values(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        client_number=881,
        slug="collections-actionable-dashboard-empty",
    )
    owner_headers = role_headers(
        authenticated_client,
        db_session,
        tenant,
        "owner",
    )

    response = authenticated_client.get(
        f"{BASE_URL}/collections/supervision",
        params={"as_of": "2026-10-02"},
        headers=owner_headers,
    )

    assert response.status_code == 200
    dashboard = response.json()

    assert dashboard["assigned_overdue_loan_count"] == 0
    assert dashboard["assigned_overdue_balance"] == "0.00"
    assert dashboard["unassigned_overdue_loan_count"] == 0
    assert dashboard["unassigned_overdue_balance"] == "0.00"
    assert dashboard["promises_due_today_count"] == 0
    assert dashboard["follow_ups_due_today_count"] == 0
    assert dashboard["overdue_follow_up_count"] == 0

    assert [
        (bucket["loan_count"], bucket["balance"])
        for bucket in dashboard["aging_buckets"]
    ] == [
        (0, "0.00"),
        (0, "0.00"),
        (0, "0.00"),
        (0, "0.00"),
    ]
