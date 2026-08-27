import datetime as dt
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "replicate-jobflow-backup.py"
spec = importlib.util.spec_from_file_location("backup_replication", SCRIPT)
replication = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replication)


class Response(io.BytesIO):
    def __init__(self, data, headers=None):
        super().__init__(data)
        self.headers = headers or {}


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.backups = self.root / "backups"
        self.backups.mkdir()
        self.source = self.backups / "jobflow-20260827-141801.dump"
        self.source.write_bytes(b"PGDMP-example")
        self.now = dt.datetime(2026, 8, 27, 15, tzinfo=dt.timezone.utc).timestamp()
        os.utime(self.source, (self.now, self.now))

    def test_daily(self):
        result = replication.plan(self.source, self.backups, self.now)
        self.assertEqual([(x["tier"], x["days"]) for x in result], [("daily", 7)])
        self.assertEqual(result[0]["retain_until_ms"], int((self.now + 7 * 86400) * 1000))

    def test_sunday_first_gets_all_tiers(self):
        stamp = dt.datetime(2026, 11, 1, 2, 30, tzinfo=dt.timezone.utc).timestamp()
        os.utime(self.source, (stamp, stamp))
        self.assertEqual([(x["tier"], x["days"]) for x in replication.plan(self.source, self.backups, stamp)],
                         [("daily", 7), ("weekly", 35), ("monthly", 365)])

    def test_first_weekday_gets_monthly(self):
        stamp = dt.datetime(2026, 9, 1, 2, 30, tzinfo=dt.timezone.utc).timestamp()
        os.utime(self.source, (stamp, stamp))
        self.assertEqual([x["tier"] for x in replication.plan(self.source, self.backups, stamp)],
                         ["daily", "monthly"])

    def test_stale_future_empty_and_wrong_directory_rejected(self):
        for now in (self.now - 1, self.now + replication.MAX_AGE + 1):
            with self.assertRaises(ValueError):
                replication.plan(self.source, self.backups, now)
        with self.assertRaises(ValueError):
            replication.plan(self.source, self.root, self.now)
        self.source.write_bytes(b"")
        with self.assertRaises(ValueError):
            replication.plan(self.source, self.backups, self.now)

    def test_url_allowlist(self):
        for url in ("https://api005.backblazeb2.com/test", "https://pod-050-1048-06.backblaze.com/test"):
            replication.safe_url(url)
        for url in ("http://api005.backblazeb2.com", "https://backblaze.com.evil.test", "https://evilbackblaze.com", "https://x@api005.backblazeb2.com", "https://api005.backblazeb2.com:444"):
            with self.assertRaises(ValueError):
                replication.safe_url(url)

    def b2(self):
        b2 = object.__new__(replication.B2)
        b2.api = {"downloadUrl": "https://f005.backblazeb2.com"}
        b2.token = "FAKE_TEST_TOKEN"
        return b2

    def headers(self):
        return {"X-Bz-File-Retention-Mode": "governance",
                "X-Bz-File-Retention-Retain-Until-Timestamp": "10000",
                "X-Bz-Server-Side-Encryption": "AES256"}

    def test_existing_verified_copy_is_not_uploaded(self):
        b2 = self.b2()
        with patch.object(b2, "call", return_value={"files": [{"fileName": "platform/test", "fileId": "id"}]}) as call, patch.object(b2, "open", return_value=Response(b"ciphertext", self.headers())):
            result = b2.ensure_copy("platform/test", b"ciphertext", 10000)
        self.assertEqual(result["file_id"], "id")
        self.assertEqual(call.call_count, 1)

    def test_new_copy_uploads_with_retention_then_downloads(self):
        b2 = self.b2()
        with patch.object(b2, "call", side_effect=[{"files": []}, {"uploadUrl": "https://pod-050-1048-06.backblaze.com/upload", "authorizationToken": "FAKE_UPLOAD_TOKEN"}]), patch.object(b2, "open", side_effect=[Response(b'{"fileId":"new"}'), Response(b"ciphertext", self.headers())]) as opened:
            result = b2.ensure_copy("platform/test", b"ciphertext", 10000)
        self.assertEqual(result["file_id"], "new")
        self.assertEqual(opened.call_args_list[0].args[1]["X-Bz-File-Retention-Mode"], "governance")
        self.assertEqual(opened.call_count, 2)

    def test_bad_download_or_retention_fails(self):
        variants = [(b"wrong", self.headers()), (b"ciphertext", {**self.headers(), "X-Bz-File-Retention-Mode": ""}),
                    (b"ciphertext", {**self.headers(), "X-Bz-File-Retention-Retain-Until-Timestamp": "9999"})]
        for data, headers in variants:
            b2 = self.b2()
            with patch.object(b2, "call", return_value={"files": [{"fileName": "platform/test", "fileId": "id"}]}), patch.object(b2, "open", return_value=Response(data, headers)):
                with self.assertRaises(ValueError):
                    b2.ensure_copy("platform/test", b"ciphertext", 10000)

    def test_encryption_cache_reused(self):
        spool = self.root / "spool"
        spool.mkdir()
        def encrypt(args, **kwargs):
            Path(args[args.index("-o") + 1]).write_bytes(b"age-encryption.org/v1\nFAKE-CIPHERTEXT")
        with patch.object(replication.subprocess, "run", side_effect=encrypt) as run:
            first = replication.encrypted_copy(self.source, spool, self.root / "recipient")
            second = replication.encrypted_copy(self.source, spool, self.root / "recipient")
        self.assertEqual(first, second)
        self.assertEqual(run.call_count, 1)

    def test_failure_does_not_write_success(self):
        with patch.object(replication, "encrypted_copy", return_value=(b"ciphertext", "hash")), patch.object(replication, "B2") as client:
            client.return_value.ensure_copy.side_effect = RuntimeError("FAKE_SECRET_MUST_NOT_BE_LOGGED")
            with self.assertRaises(RuntimeError):
                replication.replicate(self.source, self.root, self.root, self.now)
        self.assertFalse((self.root / "runtime/last-offsite-success.json").exists())

    def test_encryption_failure_prevents_network(self):
        with patch.object(replication, "encrypted_copy", side_effect=RuntimeError("encryption failed")), patch.object(replication, "B2") as client:
            with self.assertRaises(RuntimeError):
                replication.replicate(self.source, self.root, self.root, self.now)
        client.assert_not_called()

    def test_main_failure_is_sanitized_and_keeps_previous_success(self):
        previous = {"status": "verified", "source_mtime": self.now, "objects": [{"file_id": "previous"}]}
        replication.atomic_json(self.root / "runtime/last-offsite-success.json", previous)
        output = io.StringIO()
        arguments = [str(SCRIPT), "--project-dir", str(self.root), "--config-dir", str(self.root), "--upload", str(self.source)]
        with patch.object(sys, "argv", arguments), patch.object(replication, "replicate", side_effect=RuntimeError("FAKE_SECRET_MUST_NOT_BE_LOGGED")), contextlib.redirect_stdout(output):
            self.assertEqual(replication.main(), 1)
        self.assertNotIn("FAKE_SECRET", output.getvalue())
        attempt = (self.root / "runtime/last-offsite-attempt.json").read_text()
        self.assertNotIn("FAKE_SECRET", attempt)
        self.assertEqual(json.loads(attempt)["status"], "failed")
        self.assertEqual(json.loads((self.root / "runtime/last-offsite-success.json").read_text()), previous)

    def test_freshness_rejects_old_or_failed_attempt(self):
        runtime = self.root / "runtime"
        success = {"status": "verified", "source_mtime": self.now, "objects": [{"file_id": "test"}]}
        replication.atomic_json(runtime / "last-offsite-success.json", success)
        replication.atomic_json(runtime / "last-offsite-attempt.json", success)
        replication.check_freshness(runtime, self.now)
        with self.assertRaises(ValueError):
            replication.check_freshness(runtime, self.now + replication.MAX_AGE + 1)
        replication.atomic_json(runtime / "last-offsite-attempt.json", {"status": "failed"})
        with self.assertRaises(ValueError):
            replication.check_freshness(runtime, self.now)


if __name__ == "__main__":
    unittest.main()
