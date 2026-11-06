"""Synthetic SMTP only; standalone SQLite checks and normal CI collection."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import os
from pathlib import Path
import secrets
import sys
import unittest
from unittest.mock import Mock, patch

if __name__ == "__main__":
    os.environ["DATABASE_URL"] = "sqlite://"
    os.environ.setdefault("JWT_SECRET", "synthetic-fieldnest-budget-tests-32-bytes")
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, func, select
from sqlalchemy.orm import sessionmaker

from app.products.fieldnest import email_limits
from app.products.fieldnest.models import FieldNestEmailAttempt, FieldNestNotification, FieldNestWorkOrder
from app.products.fieldnest.notifications import deliver_one, notification_counts
from tests import test_fieldnest_notifications as mail_fixture


class FieldNestEmailLimits(unittest.TestCase):
    setUp = mail_fixture.FieldNestEmailNotifications.setUp
    tearDown = mail_fixture.FieldNestEmailNotifications.tearDown
    report = mail_fixture.FieldNestEmailNotifications.report
    dispatch = mail_fixture.FieldNestEmailNotifications.dispatch
    rows = mail_fixture.FieldNestEmailNotifications.rows

    def limits(self, **changes):
        replacement = patch.object(email_limits, "EMAIL_LIMITS", replace(email_limits.EMAIL_LIMITS, **changes))
        replacement.start(); self.addCleanup(replacement.stop)

    def history(self, count, *, email="victim@example.test", tenant_id=None, kind="receipt", hours_ago=0):
        when = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
        self.db.add_all([FieldNestEmailAttempt(
            tenant_id=tenant_id or self.fx.tenant.id, notification_id=999,
            recipient_hash=sha256(email.casefold().encode()).hexdigest(), kind=kind, attempted_at=when,
        ) for _ in range(count)])
        self.db.commit()

    def receipt(self, email="victim@example.test", *, other_tenant=False):
        tenant = self.fx.other if other_tenant else self.fx.tenant
        prop = self.fx.other_prop if other_tenant else self.fx.prop
        order = FieldNestWorkOrder(tenant_id=tenant.id, property_id=prop.id, title="Synthetic email test")
        self.db.add(order); self.db.flush()
        row = FieldNestNotification(tenant_id=tenant.id, work_order_id=order.id,
                                   kind="receipt", receipt_email=email, event_key=secrets.token_hex(32))
        self.db.add(row); self.db.commit()
        return row.id

    def attempt_count(self):
        return self.db.scalar(select(func.count()).select_from(FieldNestEmailAttempt))

    def drain(self):
        for _ in range(100):
            if not self.dispatch():
                return
        self.fail("Synthetic queue did not drain")

    def test_distinct_reports_share_receipt_budget_but_remain_saved(self):
        for email in ("Victim@example.test", "victim@EXAMPLE.test", "VICTIM@example.test", "victim@example.test"):
            self.report(email)
        self.drain()
        receipts = [r for r in self.rows() if r.kind == "receipt"]
        self.assertEqual([r.status for r in receipts], ["sent", "sent", "sent", "suppressed"])
        self.assertEqual(receipts[-1].last_error, "ReceiptRecipientHourLimit")
        self.assertEqual(self.db.scalar(select(func.count()).select_from(FieldNestWorkOrder)), 4)
        self.assertEqual(self.sender.call_count, 7)  # Four owner alerts, three receipts.

    def test_receipt_day_budget_survives_restart_and_tenant_change(self):
        self.history(10, hours_ago=2)
        self.receipt(other_tenant=True)
        deliver_one(sessionmaker(bind=self.fx.engine), self.sender, self.config)
        self.sender.assert_not_called()
        self.assertEqual(self.rows()[0].last_error, "ReceiptRecipientDayLimit")

    def test_combined_recipient_budget_counts_owner_and_receipt_attempts(self):
        self.history(30, kind="owner")
        self.receipt()
        self.dispatch()
        self.assertEqual(self.rows()[0].last_error, "RecipientHourLimit")
        self.sender.assert_not_called()

    def test_owner_budget_uses_resolved_current_address(self):
        self.history(30, email="changed@example.test", kind="owner")
        self.report()
        self.owner.email = "CHANGED@example.test"; self.db.commit()
        self.dispatch()
        self.assertEqual(self.rows()[0].last_error, "RecipientHourLimit")
        self.sender.assert_not_called()

    def test_tenant_hour_limit_counts_distinct_recipients_and_kinds(self):
        self.history(100, email="different@example.test", kind="owner")
        self.report("victim@example.test"); self.drain()
        self.assertEqual([r.last_error for r in self.rows()], ["TenantHourLimit"] * 2)
        self.sender.assert_not_called()

    def test_tenant_day_limit_survives_hour_rollover(self):
        self.history(500, hours_ago=2)
        self.receipt("new@example.test"); self.dispatch()
        self.assertEqual(self.rows()[0].last_error, "TenantDayLimit")
        self.sender.assert_not_called()

    def test_platform_hour_limit_spans_tenants(self):
        self.history(300, tenant_id=self.fx.other.id)
        self.receipt("new@example.test"); self.dispatch()
        self.assertEqual(self.rows()[0].last_error, "PlatformHourLimit")
        self.sender.assert_not_called()

    def test_platform_day_limit_survives_hour_rollover(self):
        self.history(1500, tenant_id=self.fx.other.id, hours_ago=2)
        self.receipt("new@example.test"); self.dispatch()
        self.assertEqual(self.rows()[0].last_error, "PlatformDayLimit")
        self.sender.assert_not_called()

    def test_pending_limit_suppresses_mail_without_losing_report_or_tracking(self):
        self.limits(tenant_pending=2)
        self.report("one@example.test")
        token = self.fx.link()
        payload = self.fx.issue(token)
        payload.update(receipt_email="two@example.test", tracking_secret=secrets.token_urlsafe(32))
        response = self.fx.client.post("/api/v1/products/fieldnest/public/maintenance", json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertIn("tracking_path", response.json())
        self.assertEqual([r.status for r in self.rows()], ["pending", "pending", "suppressed", "suppressed"])
        self.assertEqual(notification_counts(self.db)["suppressed"], 2)
        self.assertEqual(self.db.scalar(select(func.count()).select_from(FieldNestWorkOrder)), 2)

    def test_smtp_failures_consume_budget_and_cannot_retry_around_it(self):
        self.receipt()
        failing_sender = Mock(side_effect=RuntimeError("synthetic SMTP failure"))
        for _ in range(4):
            row = self.rows()[0]
            row.available_at = datetime.now(timezone.utc); self.db.commit()
            self.dispatch(sender=failing_sender)
        self.assertEqual(failing_sender.call_count, 3)
        self.assertEqual(self.attempt_count(), 3)
        self.assertEqual((self.rows()[0].status, self.rows()[0].last_error),
                         ("suppressed", "ReceiptRecipientHourLimit"))
        self.assertFalse(self.dispatch())

    def test_deleting_reports_and_outbox_does_not_reset_send_budget(self):
        for _ in range(3):
            self.receipt(); self.dispatch()
        self.db.execute(delete(FieldNestNotification))
        self.db.execute(delete(FieldNestWorkOrder)); self.db.commit()
        self.receipt(); self.dispatch()
        self.assertEqual(self.sender.call_count, 3)
        self.assertEqual(self.attempt_count(), 3)
        self.assertEqual(self.rows()[0].status, "suppressed")

    def test_hour_rollover_allows_new_mail_and_old_history_is_pruned(self):
        self.history(30, email="owner@example.test", kind="owner", hours_ago=2)
        self.history(5, hours_ago=49)
        self.report(); self.dispatch()
        self.assertEqual(self.rows()[0].status, "sent")
        self.assertEqual(self.attempt_count(), 31)

    def test_day_rollover_releases_daily_budget(self):
        self.history(10, hours_ago=25)
        self.receipt(); self.dispatch()
        self.assertEqual(self.rows()[0].status, "sent")
        self.sender.assert_called_once()

    def test_budget_failure_never_calls_smtp(self):
        self.receipt()
        with patch.object(email_limits, "reserve_email_attempt", side_effect=RuntimeError("synthetic budget failure")):
            self.dispatch()
        self.sender.assert_not_called()
        self.assertEqual(self.rows()[0].status, "pending")
        self.assertEqual(self.attempt_count(), 0)

    def test_attempt_history_does_not_store_raw_address_or_report_text(self):
        self.receipt(); self.dispatch()
        attempt = self.db.scalar(select(FieldNestEmailAttempt))
        self.assertEqual(attempt.recipient_hash, sha256(b"victim@example.test").hexdigest())
        self.assertEqual(set(FieldNestEmailAttempt.__table__.columns.keys()),
                         {"id", "tenant_id", "notification_id", "recipient_hash", "kind", "attempted_at"})


if __name__ == "__main__":
    unittest.main()
