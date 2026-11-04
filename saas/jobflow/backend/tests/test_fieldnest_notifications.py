import importlib.util
import os
from pathlib import Path
import sys
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

if __name__ == "__main__":
    os.environ["DATABASE_URL"] = "sqlite://"
    os.environ.setdefault("JWT_SECRET", "synthetic-fieldnest-mail-tests-32-bytes")
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select, func
from sqlalchemy.orm import sessionmaker
from app.models import User, TenantMembership
from app.products.fieldnest.models import FieldNestNotification, FieldNestWorkOrder
from app.products.fieldnest.notifications import deliver_one, send_message

spec = importlib.util.spec_from_file_location("_resident_mail_fixture", Path(__file__).with_name("test_fieldnest_resident_requests.py"))
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


class FieldNestEmailNotifications(unittest.TestCase):
    def setUp(self):
        self.fx = fixture.ResidentRequests()
        self.fx.setUp()
        self.db = self.fx.db
        self.factory = sessionmaker(bind=self.fx.engine)
        self.owner = User(email="owner@example.test", display_name="Owner", is_active=True)
        self.db.add(self.owner); self.db.flush()
        self.membership = TenantMembership(tenant_id=self.fx.tenant.id, user_id=self.owner.id, role="owner", is_active=True)
        self.db.add(self.membership); self.db.commit()
        self.sender = Mock()
        self.config = lambda: {"from_email": "staging@example.test"}

    def tearDown(self):
        self.fx.tearDown()

    def report(self, receipt=None):
        payload = self.fx.issue(self.fx.link())
        if receipt:
            payload["receipt_email"] = receipt
        response = self.fx.client.post(f"{fixture.PREFIX}/public/maintenance", json=payload)
        self.assertEqual(response.status_code, 201, response.text)
        return payload, response

    def dispatch(self, sender=None, config=None):
        return deliver_one(self.factory, sender or self.sender, config or self.config)

    def rows(self):
        self.db.expire_all()
        return self.db.scalars(select(FieldNestNotification).order_by(FieldNestNotification.id)).all()

    def test_smtp_uses_configured_transport(self):
        self.report()
        self.dispatch()
        message = self.sender.call_args.args[0]
        config = {"host": "staging-mail", "port": 1025, "use_tls": True,
                  "username": "synthetic-user", "password": "synthetic-password"}
        with patch("app.products.fieldnest.notifications.smtplib.SMTP") as smtp:
            send_message(message, config)
            smtp.assert_called_once_with("staging-mail", 1025, timeout=15)
            transport = smtp.return_value.__enter__.return_value
            transport.starttls.assert_called_once()
            transport.login.assert_called_once_with("synthetic-user", "synthetic-password")
            transport.send_message.assert_called_once_with(message)

    def test_report_queues_owner_and_opted_in_receipt_once(self):
        payload, first = self.report("resident@example.test")
        second = self.fx.client.post(f"{fixture.PREFIX}/public/maintenance", json=payload)
        self.assertEqual(first.json(), second.json())
        self.assertEqual([r.kind for r in self.rows()], ["owner", "receipt"])
        self.assertEqual(self.db.scalar(select(func.count()).select_from(FieldNestWorkOrder)), 1)

    def test_receipt_is_not_sent_to_general_contact_implicitly(self):
        self.report()
        self.assertEqual([r.kind for r in self.rows()], ["owner"])

    def test_successful_delivery_marks_sent_and_does_not_resend(self):
        self.report()
        with patch.dict(os.environ, {"PLATFORM_PUBLIC_BASE_URL": "https://localhost:18443"}):
            self.assertTrue(self.dispatch())
        self.assertEqual(self.rows()[0].status, "sent")
        self.assertIsNotNone(self.rows()[0].sent_at)
        message = self.sender.call_args.args[0]
        self.assertEqual(message["To"], "owner@example.test")
        self.assertIn("Maple Court", message.get_content())
        self.assertIn(f"?company={self.fx.tenant.id}#work-orders", message.get_content())
        self.assertFalse(self.dispatch())
        self.sender.assert_called_once()

    def test_receipt_contains_reference_but_no_private_report_details(self):
        self.report("receipt@example.test")
        self.dispatch(); self.dispatch()
        message = self.sender.call_args.args[0]
        self.assertEqual(message["To"], "receipt@example.test")
        self.assertIn("FN-", message.get_content())
        self.assertNotIn("Slow sink", message.get_content())
        self.assertNotIn("resident@example.test", message.get_content())
        self.assertNotIn("/fieldnest/report#", message.get_content())

    def test_smtp_failure_preserves_report_and_schedules_retry(self):
        self.report()
        self.dispatch(sender=Mock(side_effect=RuntimeError("private SMTP credential")))
        row = self.rows()[0]
        self.assertEqual((row.status, row.attempts, row.last_error), ("pending", 1, "RuntimeError"))
        self.assertEqual(self.db.scalar(select(func.count()).select_from(FieldNestWorkOrder)), 1)
        self.assertFalse(self.dispatch())
        row.available_at = datetime.now(timezone.utc); self.db.commit()
        self.dispatch()
        self.assertEqual((self.rows()[0].status, self.rows()[0].attempts), ("sent", 2))

    def test_repeated_configuration_failure_eventually_stops(self):
        self.report()
        config = Mock(side_effect=RuntimeError("missing config"))
        for attempt in range(5):
            row = self.rows()[0]
            row.available_at = datetime.now(timezone.utc); self.db.commit()
            self.dispatch(config=config)
        self.assertEqual((self.rows()[0].status, self.rows()[0].attempts), ("failed", 5))
        self.assertFalse(self.dispatch())

    def test_former_owner_does_not_receive_queued_alert(self):
        self.report()
        self.membership.is_active = False; self.db.commit()
        self.dispatch()
        self.sender.assert_not_called()
        self.assertEqual(self.rows()[0].status, "skipped")

    def test_suspended_company_does_not_send_queued_email(self):
        self.report()
        self.fx.tenant.status = "suspended"; self.db.commit()
        self.dispatch()
        self.sender.assert_not_called()
        self.assertEqual(self.rows()[0].status, "skipped")

    def test_invalid_receipt_email_rejected(self):
        payload = self.fx.issue(self.fx.link())
        for email in ["not an email", "a@example.test\nBcc: other@example.test"]:
            response = self.fx.client.post(f"{fixture.PREFIX}/public/maintenance", json={**payload, "receipt_email": email})
            self.assertEqual(response.status_code, 422)
        self.assertEqual(self.rows(), [])

    def test_queue_failure_does_not_commit_half_a_report(self):
        payload = self.fx.issue(self.fx.link())
        with patch("app.products.fieldnest.resident_requests.queue_request_notifications", side_effect=RuntimeError("queue unavailable")):
            with self.assertRaises(RuntimeError):
                self.fx.client.post(f"{fixture.PREFIX}/public/maintenance", json=payload)
        self.db.rollback()
        self.assertEqual(self.db.scalar(select(func.count()).select_from(FieldNestWorkOrder)), 0)
        self.assertEqual(self.rows(), [])


if __name__ == "__main__":
    unittest.main()
