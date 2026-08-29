"""Tests for the container vulnerability policy gate."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = (
    ROOT / "scripts" /
    "validate-container-security-findings.py"
)


class ContainerSecurityPolicyTests(unittest.TestCase):
    def run_policy(
        self,
        findings,
        exceptions,
        today="2026-08-29",
    ):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / "report.json"
            exception_file = root / "exceptions.json"

            report.write_text(
                json.dumps(
                    {
                        "Results": [
                            {
                                "Vulnerabilities": findings,
                            }
                        ]
                    }
                )
            )
            exception_file.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "exceptions": exceptions,
                    }
                )
            )

            return subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--exceptions",
                    str(exception_file),
                    "--report",
                    f"api={report}",
                    "--today",
                    today,
                ],
                check=False,
                capture_output=True,
                text=True,
            )

    @staticmethod
    def finding(fixed=""):
        return {
            "VulnerabilityID": "CVE-TEST-0001",
            "PkgName": "example",
            "InstalledVersion": "1.0",
            "FixedVersion": fixed,
            "Severity": "HIGH",
        }

    @staticmethod
    def exception(expires_on="2026-09-29"):
        return {
            "image": "api",
            "vulnerability": "CVE-TEST-0001",
            "package": "example",
            "accepted_at": "2026-08-29",
            "expires_on": expires_on,
            "owner": "security-owner",
            "rationale": "Upstream has no fixed package.",
        }

    def test_active_exception_accepts_unfixed_finding(self):
        result = self.run_policy(
            [self.finding()],
            [self.exception()],
        )

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("POLICY PASSED", result.stdout)

    def test_fixable_finding_is_always_blocked(self):
        result = self.run_policy(
            [self.finding(fixed="1.1")],
            [self.exception()],
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("fixed version available", result.stdout)

    def test_unreviewed_finding_is_blocked(self):
        result = self.run_policy(
            [self.finding()],
            [],
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("no reviewed exception", result.stdout)

    def test_expired_exception_is_blocked(self):
        result = self.run_policy(
            [self.finding()],
            [self.exception(expires_on="2026-08-28")],
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("exception expired", result.stdout)

    def test_stale_exception_is_blocked(self):
        result = self.run_policy(
            [],
            [self.exception()],
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("stale exception", result.stdout)

    def test_duplicate_exception_is_policy_error(self):
        exception = self.exception()

        result = self.run_policy(
            [self.finding()],
            [exception, exception],
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("Duplicate exception", result.stderr)


if __name__ == "__main__":
    unittest.main()
