import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "readiness_monitor", Path(__file__).resolve().parents[1] / "check-platform-readiness.py")
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)


class MonitorTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.project = Path(self.directory.name)
        (self.project / "runtime").mkdir()
        self.output = io.StringIO()
        self.enterContext(contextlib.redirect_stdout(self.output))
        self.enterContext(contextlib.redirect_stderr(self.output))

    def response(self, body=None, status=b"200", code=0):
        if body is None:
            body = json.dumps(monitor.EXPECTED).encode()
        return subprocess.CompletedProcess([], code, body + b"\n" + status, b"PRIVATE_RESPONSE")

    def test_valid_response_uses_bounded_https_without_curlrc_or_redirects(self):
        with patch.object(monitor.subprocess, "run", return_value=self.response()) as run:
            monitor.probe()
        command = run.call_args.args[0]
        self.assertEqual(command[:2], ["curl", "-q"])
        self.assertNotIn("--location", command)
        self.assertNotIn("--insecure", command)
        self.assertEqual(command[-1], monitor.PUBLIC_URL)
        self.assertEqual(run.call_args.kwargs["timeout"], 15)

    def test_http_failures_and_redirects_rejected(self):
        for status, code in ((b"503", 22), (b"302", 0), (b"401", 22), (b"200", 28)):
            with patch.object(monitor.subprocess, "run", return_value=self.response(status=status, code=code)):
                with self.assertRaises((RuntimeError, ValueError)):
                    monitor.probe()

    def test_wrong_json_and_partial_checks_rejected(self):
        variants = [{}, {"status": "ready"}, {"status": "healthy"}]
        for key in monitor.EXPECTED["checks"]:
            value = copy.deepcopy(monitor.EXPECTED)
            value["checks"][key] = "failed"
            variants.append(value)
        for value in variants:
            with patch.object(monitor.subprocess, "run", return_value=self.response(json.dumps(value).encode())):
                with self.assertRaises(ValueError):
                    monitor.probe()

    def test_html_invalid_json_and_oversized_body_rejected(self):
        for body in (b"<html>login</html>", b"invalid", b"x" * 4097):
            with patch.object(monitor.subprocess, "run", return_value=self.response(body)):
                with self.assertRaises(ValueError):
                    monitor.probe()

    def test_success_sends_only_success_and_writes_private_evidence(self):
        with patch.object(monitor, "probe"), patch.object(monitor, "notify") as notify:
            self.assertEqual(monitor.run_once(self.project), 0)
        notify.assert_called_once_with(self.project, "success")
        path = self.project / "runtime/last-readiness-monitor.json"
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(json.loads(path.read_text())["status"], "verified")
        monitor.check(self.project)

    def test_probe_failure_sends_failure_and_no_success(self):
        with patch.object(monitor, "probe", side_effect=RuntimeError("PRIVATE_CUSTOMER")), \
             patch.object(monitor, "notify") as notify:
            self.assertEqual(monitor.run_once(self.project), 1)
        notify.assert_called_once_with(self.project, "failure")
        self.assertNotIn("PRIVATE_CUSTOMER", self.output.getvalue())
        with self.assertRaises(ValueError):
            monitor.check(self.project)

    def test_timeout_reports_failure(self):
        with patch.object(monitor.subprocess, "run", side_effect=subprocess.TimeoutExpired("curl", 15)), \
             patch.object(monitor, "notify") as notify:
            self.assertEqual(monitor.run_once(self.project), 1)
        notify.assert_called_once_with(self.project, "failure")

    def test_heartbeat_failure_is_nonzero_and_sanitized(self):
        with patch.object(monitor, "probe"), \
             patch.object(monitor, "notify", side_effect=RuntimeError("SECRET_PING_URL")):
            self.assertEqual(monitor.run_once(self.project), 1)
        self.assertNotIn("SECRET_PING_URL", self.output.getvalue())
        with self.assertRaises(ValueError):
            monitor.check(self.project)

    def test_write_failure_does_not_report_successful_exit(self):
        with patch.object(monitor, "probe"), patch.object(monitor, "notify") as notify, \
             patch.object(monitor, "write_status", side_effect=OSError("PRIVATE_PATH")):
            self.assertEqual(monitor.run_once(self.project), 1)
        self.assertEqual([c.args[1] for c in notify.call_args_list], ["success", "failure"])
        self.assertNotIn("PRIVATE_PATH", self.output.getvalue())

    def test_stale_future_nan_and_failed_status_rejected(self):
        valid = {"status": "verified", "heartbeat": "accepted", "checked_at": time.time()}
        variants = [{**valid, "checked_at": t} for t in (time.time()-181, time.time()+30, float("nan"))]
        variants += [{**valid, "status": "failed"}, {**valid, "heartbeat": "failed"}]
        for record in variants:
            monitor.write_status(self.project, record)
            with self.assertRaises(ValueError):
                monitor.check(self.project)

    def test_status_file_with_unsafe_permissions_rejected(self):
        monitor.write_status(self.project, {"status": "verified", "heartbeat": "accepted", "checked_at": time.time()})
        (self.project / "runtime/last-readiness-monitor.json").chmod(0o644)
        with self.assertRaises(ValueError):
            monitor.check(self.project)

    def test_local_check_does_not_ping(self):
        monitor.write_status(self.project, {"status": "verified", "heartbeat": "accepted", "checked_at": time.time()})
        with patch.object(monitor, "notify") as notify, patch.object(monitor, "probe") as probe:
            self.assertEqual(monitor.main(["--project-dir", str(self.project), "--check"]), 0)
        notify.assert_not_called()
        probe.assert_not_called()

    def test_reporter_receives_separate_readiness_secret_path(self):
        with patch.object(monitor.importlib.util, "spec_from_file_location") as spec, \
             patch.object(monitor.importlib.util, "module_from_spec") as factory:
            monitor.notify(self.project, "failure")
        self.assertEqual(spec.call_args.args[1], self.project / "scripts/report-backup-health.py")
        factory.return_value.send.assert_called_once_with(
            "failure", Path.home() / ".config/fieldlookers/healthchecks-readiness-ping-url")


if __name__ == "__main__":
    unittest.main()
