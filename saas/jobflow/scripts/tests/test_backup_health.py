import contextlib
import importlib.util
import io
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

SCRIPTS = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "backup_health", SCRIPTS / "report-backup-health.py"
)
health = importlib.util.module_from_spec(spec)
spec.loader.exec_module(health)

class HealthTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "url"
        self.path.write_text(
            "https://hc-ping.com/00000000-0000-0000-0000-000000000000\n"
        )
        self.path.chmod(0o600)
        self.opener = MagicMock()
        self.opener.open.return_value.__enter__.return_value.status = 200

    def test_success_and_failure_send_status_only(self):
        for action in ("success", "failure"):
            with patch.object(
                health.urllib.request, "build_opener",
                return_value=self.opener,
            ):
                health.send(action, self.path)
            request = self.opener.open.call_args.args[0]
            self.assertEqual(request.data, b"")
            self.assertEqual(request.get_method(), "POST")
            self.assertEqual(
                request.full_url.endswith("/fail"), action == "failure"
            )

    def test_unsafe_permissions_rejected(self):
        self.path.chmod(0o644)
        with self.assertRaises(ValueError):
            health.send("success", self.path)

    def test_invalid_host_rejected(self):
        self.path.write_text("https://example.invalid/test")
        with self.assertRaises(ValueError):
            health.send("success", self.path)

    def test_rejected_response_fails(self):
        self.opener.open.return_value.__enter__.return_value.status = 500
        with patch.object(
            health.urllib.request, "build_opener",
            return_value=self.opener,
        ):
            with self.assertRaises(RuntimeError):
                health.send("success", self.path)

    def test_errors_do_not_expose_details(self):
        output = io.StringIO()
        with patch.object(sys, "argv", ["reporter", "success"]), \
             patch.object(health, "send", side_effect=RuntimeError("PRIVATE_TEST_VALUE")), \
             contextlib.redirect_stderr(output):
            self.assertEqual(health.main(), 1)
        self.assertNotIn("PRIVATE_TEST_VALUE", output.getvalue())

    def test_exit_hook_preserves_failure(self):
        source = (SCRIPTS / "backup-jobflow-db.sh").read_text()
        match = re.search(
            r"report_backup_exit\(\) \{.*?^trap report_backup_exit EXIT",
            source, re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(match)
        for backup_exit, reporter_exit, expected, signal in (
            (0, 0, 0, "success"),
            (7, 0, 7, "failure"),
            (7, 9, 7, "failure"),
            (0, 9, 1, "success"),
        ):
            stub = (
                'set -e\nPROJECT_DIR=/unused\n'
                'python3() { printf "%s\\n" "${@: -1}"; return '
                + str(reporter_exit) + '; }\n'
            )
            result = subprocess.run(
                ["bash"], input=stub + match.group(0)
                + "\nexit " + str(backup_exit) + "\n",
                text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, expected)
            self.assertEqual(result.stdout.strip(), signal)

if __name__ == "__main__":
    unittest.main()
