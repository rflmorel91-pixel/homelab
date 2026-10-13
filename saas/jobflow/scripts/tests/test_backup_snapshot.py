import hashlib
import io
import importlib.util
import json
from pathlib import Path
import selectors
import subprocess
import sys
import tempfile
import tarfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "create-jobflow-backup.py"
spec = importlib.util.spec_from_file_location("backup_snapshot", SCRIPT)
snapshot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot)
TABLES = sorted(snapshot.CORE_TABLES | {"renewaldesk_renewal_items"})
IMAGE = "sha256:" + "a" * 64


class Session:
    active = False
    def __enter__(self):
        self.active = True
        return self
    def __exit__(self, *args):
        self.active = False
    def query(self, sql):
        if "pg_export_snapshot" in sql:
            return {"snapshot": "00000003-000000C9-1", "revisions": ["b9c3e5f7d124"], "tables": TABLES}
        return 3


class PrivateSession(Session):
    def query(self, sql):
        if "pg_export_snapshot" in sql:
            return {"snapshot": "00000003-000000C9-1", "revisions": ["b9c3e5f7d124"],
                    "tables": TABLES + ["prestamodesk_application_review_documents"]}
        if "SELECT COALESCE(json_agg" in sql:
            return [{"file_key": "1/2/11111111-1111-4111-8111-111111111111.png",
                     "byte_size": 4, "sha256": hashlib.sha256(b"data").hexdigest()}]
        return 3


class Tests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name)
        (self.project / "backups").mkdir()
        self.output = self.project / "backups/jobflow-20260827-160000.dump"
        self.session = Session()
        self.calls = []

    def run_fake(self, args, **kwargs):
        self.calls.append(args)
        if args[:3] == ["docker", "inspect", "jobflow-api"]:
            return subprocess.CompletedProcess(args, 0, '[{"Type":"volume","Name":"jobflow_private","Destination":"/var/lib/jobflow-private/prestamodesk"}]', "")
        if "inspect" in args:
            return subprocess.CompletedProcess(args, 0, IMAGE + "\n", "")
        if "pg_dump" in args:
            self.assertTrue(self.session.active)
            self.assertIn("--snapshot=00000003-000000C9-1", args)
            kwargs["stdout"].write(b"PGDMP-test-archive")
        return subprocess.CompletedProcess(args, 0, "", "")

    def test_snapshot_counts_hash_and_private_publication(self):
        with patch.object(snapshot.subprocess, "run", side_effect=self.run_fake):
            result = snapshot.capture(self.output, self.project, lambda: self.session)
        manifest = self.output.with_name(self.output.name + ".manifest.json")
        self.assertEqual(json.loads(manifest.read_text()), result)
        self.assertEqual(result["table_counts"], dict.fromkeys(TABLES, 3))
        self.assertEqual(result["sha256"], hashlib.sha256(self.output.read_bytes()).hexdigest())
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o600)
        self.assertEqual(manifest.stat().st_mode & 0o777, 0o600)
        self.assertFalse(self.session.active)

    def test_private_archive_is_published_as_part_of_snapshot(self):
        session = PrivateSession()
        self.session = session
        def archive(path, records, image):
            self.assertTrue(session.active)
            self.assertEqual(records[0]["file_key"],
                             "1/2/11111111-1111-4111-8111-111111111111.png")
            path.write_bytes(b"private-tar-content")
        with patch.object(snapshot.subprocess, "run", side_effect=self.run_fake), \
             patch.object(snapshot, "create_private_archive", side_effect=archive):
            result = snapshot.capture(self.output, self.project, lambda: session)
        sidecar = self.output.with_name(self.output.name + ".private.tar")
        self.assertEqual(sidecar.read_bytes(), b"private-tar-content")
        self.assertEqual(sidecar.stat().st_mode & 0o777, 0o600)
        self.assertEqual(result["private_documents"]["archive"], sidecar.name)
        self.assertEqual(result["private_documents"]["sha256"],
                         hashlib.sha256(sidecar.read_bytes()).hexdigest())

    def test_private_archive_failure_publishes_nothing(self):
        session = PrivateSession()
        self.session = session
        with patch.object(snapshot.subprocess, "run", side_effect=self.run_fake), \
             patch.object(snapshot, "create_private_archive", side_effect=RuntimeError("archive failed")):
            with self.assertRaises(RuntimeError):
                snapshot.capture(self.output, self.project, lambda: session)
        self.assertEqual(list((self.project / "backups").iterdir()), [])

    def test_private_archive_captures_read_only_volume_and_checks_content(self):
        payload = b"private document fixture"
        records = [{"file_key": "1/2/11111111-1111-4111-8111-111111111111.pdf",
                    "byte_size": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}]
        calls = []
        def docker(args, **kwargs):
            calls.append(args)
            if args[:3] == ["docker", "inspect", "jobflow-api"]:
                return subprocess.CompletedProcess(args, 0,
                    '[{"Type":"volume","Name":"jobflow_private","Destination":"/var/lib/jobflow-private/prestamodesk"}]', "")
            with tarfile.open(fileobj=kwargs["stdout"], mode="w") as archive:
                for name in ("1", "1/2"):
                    directory = tarfile.TarInfo(name)
                    directory.type = tarfile.DIRTYPE
                    archive.addfile(directory)
                file = tarfile.TarInfo(records[0]["file_key"])
                file.size = len(payload)
                archive.addfile(file, io.BytesIO(payload))
            return subprocess.CompletedProcess(args, 0, "", "")
        target = self.project / "backups/private.tar"
        with patch.object(snapshot.subprocess, "run", side_effect=docker):
            snapshot.create_private_archive(target, records, IMAGE)
        self.assertEqual(len(calls), 2)
        self.assertIn("--network", calls[1])
        self.assertIn("none", calls[1])
        self.assertIn("readonly", calls[1][calls[1].index("--mount") + 1])

    def test_existing_dump_not_overwritten(self):
        self.output.write_bytes(b"existing")
        with self.assertRaises(ValueError):
            snapshot.capture(self.output, self.project, lambda: self.session)
        self.assertEqual(self.output.read_bytes(), b"existing")

    def test_wrong_directory_rejected(self):
        with self.assertRaises(ValueError):
            snapshot.capture(self.project / self.output.name, self.project, lambda: self.session)

    def test_dump_failure_does_not_publish(self):
        def fail(args, **kwargs):
            if "pg_dump" in args:
                raise subprocess.CalledProcessError(1, args)
            return self.run_fake(args, **kwargs)
        with patch.object(snapshot.subprocess, "run", side_effect=fail):
            with self.assertRaises(subprocess.CalledProcessError):
                snapshot.capture(self.output, self.project, lambda: self.session)
        self.assertFalse(self.output.exists())
        self.assertEqual(list((self.project / "backups").iterdir()), [])
        self.assertFalse(self.session.active)

    def test_manifest_publish_failure_removes_new_dump(self):
        real_link = snapshot.os.link
        def link(source, destination):
            if str(destination).endswith(".json"):
                raise OSError("simulated disk error")
            real_link(source, destination)
        with patch.object(snapshot.subprocess, "run", side_effect=self.run_fake), patch.object(snapshot.os, "link", side_effect=link):
            with self.assertRaises(OSError):
                snapshot.capture(self.output, self.project, lambda: self.session)
        self.assertFalse(self.output.exists())

    def test_snapshot_contract(self):
        good = {"snapshot": "00000003-000000C9-1", "revisions": ["b9c3e5f7d124"], "tables": TABLES}
        snapshot.validate_snapshot(good)
        for change in ({"snapshot": "bad"}, {"revisions": []}, {"tables": []}, {"tables": TABLES + TABLES}):
            with self.assertRaises(ValueError):
                snapshot.validate_snapshot({**good, **change})

    def test_identifiers_are_quoted(self):
        self.assertEqual(snapshot.quote_identifier('a"b'), '"a""b"')
        with self.assertRaises(ValueError):
            snapshot.quote_identifier("bad\x00name")

    def test_session_handles_fragmented_response_and_eof_cleanup(self):
        real_popen = subprocess.Popen
        program = ('import sys,time\n'
                   'for line in sys.stdin:\n'
                   ' if line.startswith("BEGIN"): continue\n'
                   ' sys.stdout.write("{\\\"value\\\":");sys.stdout.flush()\n'
                   ' time.sleep(0.01)\n'
                   ' sys.stdout.write("1}\\n");sys.stdout.flush()\n')
        def process(args, **kwargs):
            return real_popen([sys.executable, "-u", "-c", program], **kwargs)
        with patch.object(snapshot.subprocess, "Popen", side_effect=process):
            with snapshot.SnapshotSession() as session:
                self.assertEqual(session.query("SELECT test;"), {"value": 1})
                child = session.process
            self.assertIsNotNone(child.poll())


if __name__ == "__main__":
    unittest.main()
