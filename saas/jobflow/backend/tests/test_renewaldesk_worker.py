from datetime import date
import os
from pathlib import Path
import subprocess
import sys

from sqlalchemy import select

from app.models import Product, Tenant
from app.products.renewaldesk.models import (
    RenewalItem,
    RenewalReminderDelivery,
)
from app.products.renewaldesk.reminder_worker import (
    run_reminder_cycle,
)


def create_product(
    db_session,
    *,
    name,
    slug,
    status="active",
):
    product = Product(
        name=name,
        slug=slug,
        status=status,
        workspace_key=slug,
    )

    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    return product


def create_tenant(
    db_session,
    product,
    *,
    name,
    slug,
    status="active",
    client_number=1,
):
    tenant = Tenant(
        product_id=product.id,
        name=name,
        slug=slug,
        status=status,
        client_number=client_number,
    )

    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    return tenant


def create_due_item(
    db_session,
    tenant,
):
    item = RenewalItem(
        tenant_id=tenant.id,
        name="Worker Insurance",
        renewal_date=date.today(),
        status="active",
        owner_name="Worker Owner",
        owner_email="worker-owner@example.test",
        reminder_days=30,
    )

    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    return item


def test_worker_dry_run_does_not_write_or_send(
    db_session,
    monkeypatch,
):
    from app.products.renewaldesk import reminders_api

    product = create_product(
        db_session,
        name="RenewalDesk",
        slug="renewaldesk",
    )

    tenant = create_tenant(
        db_session,
        product,
        name="Dry Run Tenant",
        slug="dry-run-tenant",
    )

    create_due_item(
        db_session,
        tenant,
    )

    delivered = []

    monkeypatch.setattr(
        reminders_api,
        "deliver_reminder",
        lambda delivery, item: delivered.append(
            delivery.id
        ),
    )

    summary = run_reminder_cycle(
        db_session,
        dry_run=True,
    )

    assert summary.dry_run is True
    assert summary.client_count == 1
    assert summary.candidate_count == 1
    assert summary.tracked_delivery_count == 0
    assert summary.processed_count == 0
    assert summary.sent_count == 0
    assert delivered == []

    assert db_session.scalar(
        select(RenewalReminderDelivery)
    ) is None


def test_worker_cycle_queues_and_sends_due_item(
    db_session,
    monkeypatch,
):
    from app.products.renewaldesk import reminders_api

    product = create_product(
        db_session,
        name="RenewalDesk",
        slug="renewaldesk",
    )

    tenant = create_tenant(
        db_session,
        product,
        name="Worker Tenant",
        slug="worker-tenant",
    )

    item = create_due_item(
        db_session,
        tenant,
    )

    delivered = []

    monkeypatch.setattr(
        reminders_api,
        "deliver_reminder",
        lambda delivery, queued_item: (
            delivered.append(
                (
                    delivery.id,
                    queued_item.id,
                )
            )
        ),
    )

    summary = run_reminder_cycle(
        db_session,
    )

    assert summary.dry_run is False
    assert summary.client_count == 1
    assert summary.candidate_count == 1
    assert summary.tracked_delivery_count == 1
    assert summary.processed_count == 1
    assert summary.sent_count == 1
    assert summary.retry_scheduled_count == 0
    assert summary.failed_count == 0

    delivery = db_session.scalar(
        select(RenewalReminderDelivery)
    )

    assert delivery is not None
    assert delivery.tenant_id == tenant.id
    assert delivery.renewal_item_id == item.id
    assert delivery.recipient_email == (
        "worker-owner@example.test"
    )
    assert delivery.status == "sent"
    assert delivery.attempt_count == 1
    assert delivery.sent_at is not None
    assert delivered == [
        (
            delivery.id,
            item.id,
        )
    ]


def test_worker_summary_reports_scheduled_retry(
    db_session,
    monkeypatch,
):
    from app.products.renewaldesk import reminders_api

    product = create_product(
        db_session,
        name="RenewalDesk",
        slug="renewaldesk",
    )

    tenant = create_tenant(
        db_session,
        product,
        name="Retry Summary Tenant",
        slug="retry-summary-tenant",
    )

    create_due_item(
        db_session,
        tenant,
    )

    def fail_delivery(delivery, item):
        raise RuntimeError("Provider unavailable")

    monkeypatch.setattr(
        reminders_api,
        "deliver_reminder",
        fail_delivery,
    )

    summary = run_reminder_cycle(
        db_session,
    )

    assert summary.client_count == 1
    assert summary.candidate_count == 1
    assert summary.tracked_delivery_count == 1
    assert summary.processed_count == 1
    assert summary.sent_count == 0
    assert summary.retry_scheduled_count == 1
    assert summary.failed_count == 0

    delivery = db_session.scalar(
        select(RenewalReminderDelivery)
    )

    assert delivery is not None
    assert delivery.status == "retry_scheduled"
    assert delivery.attempt_count == 1
    assert delivery.next_attempt_at is not None
    assert delivery.last_error == (
        "RuntimeError: Provider unavailable"
    )


def test_worker_cli_help_needs_no_database():
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_renewaldesk_reminders.py"
    )

    environment = os.environ.copy()
    environment.pop("DATABASE_URL", None)

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--help",
        ],
        capture_output=True,
        text=True,
        env=environment,
        check=False,
    )

    assert result.returncode == 0
    assert "--dry-run" in result.stdout
    assert result.stderr == ""


def test_worker_ignores_validation_workspace(
    db_session,
    monkeypatch,
):
    from app.products.renewaldesk import reminders_api

    product = create_product(
        db_session,
        name="RenewalDesk",
        slug="renewaldesk",
    )

    workspace = create_tenant(
        db_session,
        product,
        name="Validation Workspace",
        slug="validation-workspace",
        client_number=None,
    )

    create_due_item(
        db_session,
        workspace,
    )

    delivered = []

    monkeypatch.setattr(
        reminders_api,
        "deliver_reminder",
        lambda delivery, item: delivered.append(
            delivery.id
        ),
    )

    summary = run_reminder_cycle(
        db_session,
    )

    assert summary.client_count == 0
    assert summary.candidate_count == 0
    assert summary.tracked_delivery_count == 0
    assert summary.processed_count == 0
    assert delivered == []

    assert db_session.scalars(
        select(RenewalReminderDelivery)
    ).all() == []


def test_worker_ignores_inactive_and_wrong_product_tenants(
    db_session,
    monkeypatch,
):
    from app.products.renewaldesk import reminders_api

    renewaldesk = create_product(
        db_session,
        name="RenewalDesk",
        slug="renewaldesk",
    )

    jobflow = db_session.scalar(
        select(Product).where(
            Product.slug == "jobflow"
        )
    )
    assert jobflow is not None

    suspended = create_tenant(
        db_session,
        renewaldesk,
        name="Suspended RenewalDesk",
        slug="suspended-renewaldesk",
        status="suspended",
    )

    wrong_product = create_tenant(
        db_session,
        jobflow,
        name="Wrong Product",
        slug="wrong-product-worker",
    )

    create_due_item(
        db_session,
        suspended,
    )
    create_due_item(
        db_session,
        wrong_product,
    )

    delivered = []

    monkeypatch.setattr(
        reminders_api,
        "deliver_reminder",
        lambda delivery, item: delivered.append(
            delivery.id
        ),
    )

    summary = run_reminder_cycle(
        db_session,
    )

    assert summary.client_count == 0
    assert summary.candidate_count == 0
    assert summary.processed_count == 0
    assert delivered == []

    assert db_session.scalars(
        select(RenewalReminderDelivery)
    ).all() == []
