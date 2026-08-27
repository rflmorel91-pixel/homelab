import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "restore_validator", Path(__file__).resolve().parents[1] / "validate-jobflow-backup.py")
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.project = Path(self.directory.name)
        (self.project / "runtime").mkdir()
        (self.project / "backups").mkdir()
        self.source = self.project / "backups/jobflow-20260827-153240.dump"
        self.source.write_bytes(b"PGDMP-test-snapshot")
        self.source.chmod(0o600)
        self.manifest = {
            "format_version": 1, "source": self.source.name,
            "schema": "public", "count_basis": "same-exported-snapshot-as-pg-dump",
            "sha256": hashlib.sha256(self.source.read_bytes()).hexdigest(),
            "bytes": self.source.stat().st_size,
            "snapshot_started_at": time.time() - 10, "capture_completed_at": time.time() - 1,
            "migration_revisions": ["test_revision"], "postgres_image_id": "sha256:" + "a" * 64,
            "table_counts": {name: 1 for name in sorted(v.CORE)},
        }
        self.write_manifest()
        self.write("last-offsite-success.json", {
            "status": "verified", "source": self.source.name,
            "source_sha256": self.manifest["sha256"],
        })
        self.output = io.StringIO()
        self.enterContext(contextlib.redirect_stdout(self.output))
        self.enterContext(contextlib.redirect_stderr(self.output))

    def write(self, name, data):
        v.atomic_json(self.project / "runtime" / name, data)

    def read(self, name):
        return json.loads((self.project / "runtime" / name).read_text())

    def write_manifest(self):
        path = self.source.with_name(self.source.name + ".manifest.json")
        path.write_text(json.dumps(self.manifest))
        path.chmod(0o600)

    def info(self):
        return {
            "Id": "b" * 64, "Name": "/" + v.NAME,
            "Image": self.manifest["postgres_image_id"],
            "Config": {"Labels": {v.OWNER: v.OWNER_VALUE, v.PROJECT: v.project_id(self.project)}},
            "HostConfig": {
                "NetworkMode": "none", "Privileged": False, "Binds": None,
                "VolumesFrom": None, "PortBindings": {}, "IpcMode": "private", "PidMode": "",
                "Memory": 512 * 1024 * 1024, "NanoCpus": 1000000000, "PidsLimit": 128,
                "Tmpfs": {"/var/lib/postgresql/data": "rw,nosuid,size=256m"},
            },
            "Mounts": [{"Type": "tmpfs", "Destination": "/var/lib/postgresql/data"}],
        }

    def test_success_marker_is_private_and_has_no_counts(self):
        with patch.object(v, "restore") as restore, patch.object(v, "notify") as notify:
            self.assertEqual(v.perform(self.project, send_alert=True), 0)
        restore.assert_called_once()
        notify.assert_called_once_with(self.project, "success")
        success = self.read("last-restore-success.json")
        self.assertEqual(success["source_sha256"], self.manifest["sha256"])
        self.assertEqual(success["tables_verified"], len(v.CORE))
        self.assertEqual(success["cleanup"], "passed")
        self.assertNotIn("table_counts", success)
        self.assertEqual((self.project / "runtime/last-restore-success.json").stat().st_mode & 0o777, 0o600)
        v.check(self.project)

    def test_restore_failure_preserves_success_and_notifies(self):
        previous = {"status": "verified", "sentinel": "previous-success"}
        self.write("last-restore-success.json", previous)
        with patch.object(v, "restore", side_effect=RuntimeError("PRIVATE_DATABASE_VALUE")), \
             patch.object(v, "notify") as notify:
            self.assertEqual(v.perform(self.project, send_alert=True), 1)
        self.assertEqual(self.read("last-restore-success.json"), previous)
        self.assertEqual(self.read("last-restore-attempt.json")["status"], "failed")
        notify.assert_called_once_with(self.project, "failure")
        self.assertNotIn("PRIVATE_DATABASE_VALUE", self.output.getvalue())

    def test_notification_failure_does_not_publish_success(self):
        with patch.object(v, "restore"), patch.object(v, "notify", side_effect=RuntimeError("SECRET_URL")):
            self.assertEqual(v.perform(self.project, send_alert=True), 1)
        self.assertFalse((self.project / "runtime/last-restore-success.json").exists())
        self.assertNotIn("SECRET_URL", self.output.getvalue())

    def test_in_place_dump_change_prevents_success(self):
        def change(*args):
            self.source.write_bytes(b"PGDMP-altered-after-hash")
        with patch.object(v, "restore", side_effect=change):
            self.assertEqual(v.perform(self.project), 1)
        self.assertFalse((self.project / "runtime/last-restore-success.json").exists())

    def test_bad_source_never_reaches_docker(self):
        for mutation in ("hash", "empty", "permissions", "symlink", "directory"):
            with self.subTest(mutation=mutation):
                original = self.source.read_bytes()
                if mutation == "hash":
                    self.source.write_bytes(b"PGDMP-invalid-hash!")
                elif mutation == "empty":
                    self.source.write_bytes(b"")
                elif mutation == "permissions":
                    self.source.chmod(0o644)
                elif mutation == "symlink":
                    replacement = self.source.with_suffix(".real")
                    self.source.rename(replacement)
                    self.source.symlink_to(replacement)
                selected = self.source if mutation != "directory" else self.project / self.source.name
                with patch.object(v, "restore") as restore:
                    self.assertEqual(v.perform(self.project, selected=selected), 1)
                    restore.assert_not_called()
                if mutation == "symlink":
                    self.source.unlink()
                    replacement.rename(self.source)
                self.source.write_bytes(original)
                self.source.chmod(0o600)

    def test_manifest_contract_rejects_missing_core_and_invalid_counts(self):
        variants = []
        for field, value in (("format_version", 2), ("schema", "private"),
                             ("count_basis", "live-database"), ("migration_revisions", []),
                             ("postgres_image_id", "postgres:16"), ("bytes", True)):
            variant = copy.deepcopy(self.manifest)
            variant[field] = value
            variants.append(variant)
        for counts in ({"users": 1}, {**self.manifest["table_counts"], "users": -1},
                       {**self.manifest["table_counts"], "users": True}):
            variant = copy.deepcopy(self.manifest)
            variant["table_counts"] = counts
            variants.append(variant)
        for variant in variants:
            with self.assertRaises(ValueError):
                v.validate_manifest(variant, self.source, time.time(), False)

    def test_stale_and_future_snapshots_rejected(self):
        for value in (time.time() - v.MAX_SOURCE_AGE - 100, time.time() + 600, float("nan")):
            variant = copy.deepcopy(self.manifest)
            variant["snapshot_started_at"] = value
            variant["capture_completed_at"] = value
            with self.assertRaises(ValueError):
                v.validate_manifest(variant, self.source, time.time(), False)

    def test_old_manual_drill_cannot_satisfy_freshness(self):
        self.manifest["snapshot_started_at"] = time.time() - 10 * 86400
        self.manifest["capture_completed_at"] = time.time() - 10 * 86400 + 1
        self.write_manifest()
        with patch.object(v, "restore"):
            self.assertEqual(v.perform(self.project, self.source, allow_old=True), 0)
        with self.assertRaises(ValueError):
            v.check(self.project)

    def test_offsite_hash_must_match(self):
        self.write("last-offsite-success.json", {"status": "verified", "source": self.source.name,
                                               "source_sha256": "0" * 64})
        with patch.object(v, "restore") as restore:
            self.assertEqual(v.perform(self.project), 1)
            restore.assert_not_called()

    def test_freshness_rejects_failed_running_old_future_or_different_attempt(self):
        with patch.object(v, "restore"):
            self.assertEqual(v.perform(self.project), 0)
        success = self.read("last-restore-success.json")
        attempt = self.read("last-restore-attempt.json")
        for field, value in (("status", "failed"), ("status", "running"), ("attempt_id", "different")):
            self.write("last-restore-attempt.json", {**attempt, field: value})
            with self.assertRaises(ValueError):
                v.check(self.project)
        self.write("last-restore-attempt.json", attempt)
        for stamp in (time.time() - v.MAX_CHECK_AGE - 1, time.time() + 600, float("nan")):
            self.write("last-restore-success.json", {**success, "completed_at": stamp})
            with self.assertRaises(ValueError):
                v.check(self.project)

    def test_lock_prevents_concurrent_validator(self):
        with v.locked(self.project):
            with self.assertRaises(BlockingIOError):
                with v.locked(self.project):
                    self.fail("second validator entered")

    def test_cleanup_refuses_unowned_container(self):
        for mutation in ("owner", "project", "name"):
            info = self.info()
            if mutation == "name":
                info["Name"] = "/jobflow-db"
            else:
                info["Config"]["Labels"][v.OWNER if mutation == "owner" else v.PROJECT] = "wrong"
            with patch.object(v, "run", side_effect=[info["Id"], json.dumps([info])]) as run:
                with self.assertRaises(ValueError):
                    v.cleanup(self.project)
            self.assertEqual(run.call_count, 2)

    def test_cleanup_removes_only_owned_id_and_verifies_absence(self):
        info = self.info()
        with patch.object(v, "run", side_effect=[info["Id"], json.dumps([info]), "", ""]) as run:
            v.cleanup(self.project)
        self.assertEqual(run.call_args_list[2].args[0],
                         ["docker", "container", "rm", "--force", "--volumes", info["Id"]])

    def test_cleanup_fails_if_resource_remains(self):
        with patch.object(v, "owned_container", return_value=self.info()), patch.object(v, "run"):
            with self.assertRaises(ValueError):
                v.cleanup(self.project)

    def test_isolation_rejects_network_volumes_privilege_or_limits(self):
        for key, value in (("NetworkMode", "host"), ("Binds", ["/prod:/prod"]),
                           ("Privileged", True), ("Memory", 0), ("PortBindings", {"5432/tcp": [{}]}),
                           ("VolumesFrom", ["jobflow-db"]), ("PidMode", "host")):
            info = self.info()
            info["HostConfig"][key] = value
            with self.assertRaises(ValueError):
                v.verify_isolation(info, self.manifest["postgres_image_id"])

    def fake_docker(self, failure=None):
        def command(argv, **kwargs):
            if argv[:2] == ["docker", "create"]:
                return "b" * 64
            if "pg_restore" in argv:
                if failure == "restore":
                    raise subprocess.CalledProcessError(1, argv, stderr="PRIVATE_ROW")
                return ""
            if "psql" in argv:
                sql = argv[-1]
                if "json_agg(version_num" in sql:
                    return json.dumps(["wrong"] if failure == "revision" else self.manifest["migration_revisions"])
                if "json_agg(tablename" in sql:
                    return json.dumps([] if failure == "inventory" else sorted(self.manifest["table_counts"]))
                return "2" if failure == "count" else "1"
            return ""
        return command

    def test_restore_commands_target_only_isolated_container(self):
        with patch.object(v, "cleanup") as cleanup, \
             patch.object(v, "owned_container", return_value=self.info()), \
             patch.object(v, "run", side_effect=self.fake_docker()) as run:
            with self.source.open("rb") as stream:
                v.restore(self.project, self.source, self.manifest, stream, lambda phase: None)
        self.assertEqual(cleanup.call_count, 2)
        commands = [call.args[0] for call in run.call_args_list]
        restore = next(cmd for cmd in commands if "pg_restore" in cmd)
        self.assertIn("--exit-on-error", restore)
        self.assertIn("--single-transaction", restore)
        self.assertEqual(restore[3], "b" * 64)
        for command in commands:
            self.assertNotIn("jobflow-db", command)
        self.assertEqual(sum("psql" in cmd for cmd in commands), len(v.CORE) + 2)

    def test_restore_errors_always_cleanup(self):
        for failure in ("restore", "revision", "inventory", "count"):
            with self.subTest(failure=failure), patch.object(v, "cleanup") as cleanup, \
                 patch.object(v, "owned_container", return_value=self.info()), \
                 patch.object(v, "run", side_effect=self.fake_docker(failure)):
                with self.source.open("rb") as stream:
                    with self.assertRaises((ValueError, subprocess.CalledProcessError)):
                        v.restore(self.project, self.source, self.manifest, stream, lambda phase: None)
                self.assertEqual(cleanup.call_count, 2)

    def test_create_timeout_still_attempts_owned_cleanup(self):
        def command(argv, **kwargs):
            if "create" in argv:
                raise subprocess.TimeoutExpired(argv, 60)
            return ""
        with patch.object(v, "cleanup") as cleanup, patch.object(v, "run", side_effect=command):
            with self.source.open("rb") as stream:
                with self.assertRaises(subprocess.TimeoutExpired):
                    v.restore(self.project, self.source, self.manifest, stream, lambda phase: None)
        self.assertEqual(cleanup.call_count, 2)

    def test_cleanup_failure_prevents_success(self):
        with patch.object(v, "cleanup", side_effect=[None, RuntimeError("CLEANUP_PRIVATE")]), \
             patch.object(v, "owned_container", return_value=self.info()), \
             patch.object(v, "run", side_effect=self.fake_docker()):
            self.assertEqual(v.perform(self.project), 1)
        self.assertFalse((self.project / "runtime/last-restore-success.json").exists())
        self.assertNotIn("CLEANUP_PRIVATE", self.output.getvalue())

    def test_readiness_uses_tcp_and_failure_cleans_up(self):
        base = self.fake_docker()
        def command(argv, **kwargs):
            if "pg_isready" in argv:
                self.assertIn("127.0.0.1", argv)
                raise subprocess.CalledProcessError(1, argv)
            return base(argv, **kwargs)
        with patch.object(v, "cleanup") as cleanup, \
             patch.object(v, "owned_container", return_value=self.info()), \
             patch.object(v, "run", side_effect=command), \
             patch.object(v.time, "monotonic", side_effect=[0, 61]):
            with self.source.open("rb") as stream:
                with self.assertRaises(TimeoutError):
                    v.restore(self.project, self.source, self.manifest, stream, lambda phase: None)
        self.assertEqual(cleanup.call_count, 2)

    def test_stop_post_reports_service_failure(self):
        with patch.object(v, "cleanup") as cleanup, patch.object(v, "notify") as notify, \
             patch.dict(os.environ, {"SERVICE_RESULT": "timeout"}):
            self.assertEqual(v.main(["--project-dir", str(self.project), "--cleanup", "--notify"]), 0)
        cleanup.assert_called_once_with(self.project)
        notify.assert_called_once_with(self.project, "failure")

    def test_old_backup_cannot_send_scheduled_success(self):
        with self.assertRaises(SystemExit) as result:
            v.main(["--backup", str(self.source), "--allow-old", "--notify"])
        self.assertEqual(result.exception.code, 2)

    def test_identifier_quote(self):
        self.assertEqual(v.quote_identifier('table"name'), '"table""name"')


if __name__ == "__main__":
    unittest.main()
