#!/usr/bin/env python3
"""Restore a snapshot-verified local backup in a disposable isolated container."""
import argparse
import contextlib
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import tempfile
import tarfile
import time
import uuid

NAME = "fieldlookers-restore-validation"
OWNER = "fieldlookers.restore-owner"
PROJECT = "fieldlookers.restore-project"
OWNER_VALUE = "snapshot-validator-v1"
MAX_BYTES = 256 * 1024 * 1024
MAX_PRIVATE_ARCHIVE_BYTES = 256 * 1024 * 1024
MAX_MANIFEST_BYTES = 16 * 1024 * 1024
MAX_SOURCE_AGE = 36 * 3600
MAX_CHECK_AGE = 8 * 86400
CORE = {"alembic_version", "users", "tenants", "tenant_memberships", "products"}


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def run(argv, **kwargs):
    return subprocess.run(argv, check=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=kwargs.pop("timeout", 60),
                          text=True, **kwargs).stdout.strip()


def timestamp(value):
    return type(value) in (int, float) and math.isfinite(value)


def read_json(path):
    with open_private(path) as stream:
        require(os.fstat(stream.fileno()).st_size <= MAX_MANIFEST_BYTES, "json-size")
        return json.load(stream)


def open_private(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                and stat.S_IMODE(info.st_mode) == 0o600, "private-file-required")
        return os.fdopen(fd, "rb")
    except BaseException:
        os.close(fd)
        raise


def atomic_json(path, value):
    fd, temporary = tempfile.mkstemp(prefix=".restore-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextlib.contextmanager
def locked(project):
    runtime = project / "runtime"
    runtime.mkdir(parents=True, exist_ok=True, mode=0o700)
    require(not runtime.is_symlink(), "runtime-symlink")
    fd = os.open(runtime / "restore-validation.lock",
                 os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def project_id(project):
    return hashlib.sha256(str(project.resolve()).encode()).hexdigest()


def owned_container(project):
    ids = run(["docker", "container", "ls", "--all", "--no-trunc",
               "--filter", "name=^/" + NAME + "$", "--format", "{{.ID}}"])
    if not ids:
        return None
    require(re.fullmatch(r"[0-9a-f]{64}", ids), "container-selection")
    info = json.loads(run(["docker", "container", "inspect", ids]))[0]
    labels = info["Config"].get("Labels") or {}
    require(info["Id"] == ids and info["Name"] == "/" + NAME
            and labels.get(OWNER) == OWNER_VALUE
            and labels.get(PROJECT) == project_id(project), "container-ownership")
    return info


def cleanup(project):
    info = owned_container(project)
    if info is not None:
        run(["docker", "container", "rm", "--force", "--volumes", info["Id"]])
    require(owned_container(project) is None, "container-cleanup")


def verify_isolation(info, image):
    host = info["HostConfig"]
    mounts = info.get("Mounts", [])
    require(info["Image"] == image and host["NetworkMode"] == "none"
            and not host.get("Privileged") and not host.get("Binds")
            and not host.get("VolumesFrom") and not host.get("PortBindings")
            and not host.get("CapAdd")
            and host.get("PidMode", "") == ""
            and host.get("IpcMode") == "private"
            and host["Memory"] == 512 * 1024 * 1024
            and host["NanoCpus"] == 1000000000 and host["PidsLimit"] == 128
            and host.get("Tmpfs") == {
                "/var/lib/postgresql/data": "rw,nosuid,size=256m",
                "/restore-documents": "rw,nosuid,size=256m"}
            and all(m["Type"] == "tmpfs" for m in mounts), "isolation-contract")


def validate_private_documents(metadata, source):
    if metadata is None:
        return None
    require(isinstance(metadata, dict)
            and metadata.get("archive") == source.name + ".private.tar",
            "private-archive-name")
    require(type(metadata.get("bytes")) is int and
            0 < metadata["bytes"] <= MAX_PRIVATE_ARCHIVE_BYTES, "private-archive-size")
    require(re.fullmatch(r"[0-9a-f]{64}", metadata.get("sha256", "")),
            "private-archive-digest")
    records = metadata.get("documents")
    require(isinstance(records, list) and len(records) <= 100000,
            "private-document-records")
    keys = set()
    for record in records:
        require(isinstance(record, dict), "private-document-record")
        key = record.get("file_key", "")
        require(re.fullmatch(
            r"[1-9][0-9]*/[1-9][0-9]*/"
            r"[0-9a-fA-F-]{36}\.(?:pdf|jpg|png)", key
        ) is not None, "private-document-key")
        identifier = key.split("/")[-1].rsplit(".", 1)[0]
        require(str(uuid.UUID(identifier)) == identifier.lower(), "private-document-uuid")
        require(type(record.get("byte_size")) is int and 0 < record["byte_size"] <= 8 * 1024 * 1024,
                "private-document-size")
        require(re.fullmatch(r"[0-9a-f]{64}", record.get("sha256", "")),
                "private-document-hash")
        require(key not in keys, "duplicate-private-document-key")
        keys.add(key)
    return records


def validate_private_archive(stream, metadata):
    stream.seek(0)
    require(os.fstat(stream.fileno()).st_size == metadata["bytes"], "private-archive-size-mismatch")
    require(hashlib.file_digest(stream, "sha256").hexdigest() == metadata["sha256"],
            "private-archive-hash-mismatch")
    stream.seek(0)
    expected = {item["file_key"]: item for item in metadata["documents"]}
    actual = set()
    with tarfile.open(fileobj=stream, mode="r|") as archive:
        for member in archive:
            name = member.name
            require(not name.startswith("/"), "private-archive-absolute-path")
            while name.startswith("./"):
                name = name[2:]
            name = name.rstrip("/")
            require(name in ("", ".") or all(part not in ("", ".", "..")
                    for part in name.split("/")), "private-archive-path")
            if member.isdir():
                # Safe directory entries may remain after document cleanup.
                # Every non-directory entry must still match the manifest.
                continue
            require(member.isfile() and name in expected and name not in actual,
                    "private-archive-entry")
            content = archive.extractfile(member)
            require(content is not None and member.size == expected[name]["byte_size"],
                    "private-archive-size")
            require(hashlib.file_digest(content, "sha256").hexdigest() == expected[name]["sha256"],
                    "private-archive-document-hash")
            actual.add(name)
    require(actual == set(expected), "private-archive-inventory")
    stream.seek(0)


def quote_identifier(name):
    require(isinstance(name, str) and name and "\x00" not in name, "identifier")
    return '"' + name.replace('"', '""') + '"'


def validate_manifest(manifest, source, now, allow_old):
    require(manifest.get("format_version") == 1 and manifest.get("source") == source.name
            and manifest.get("schema") == "public"
            and manifest.get("count_basis") == "same-exported-snapshot-as-pg-dump",
            "manifest-contract")
    require(re.fullmatch(r"sha256:[0-9a-f]{64}", manifest.get("postgres_image_id", "")), "image-id")
    require(re.fullmatch(r"[0-9a-f]{64}", manifest.get("sha256", "")), "dump-digest")
    require(type(manifest.get("bytes")) is int and 0 < manifest["bytes"] <= MAX_BYTES, "dump-size")
    start, end = manifest.get("snapshot_started_at"), manifest.get("capture_completed_at")
    require(timestamp(start) and timestamp(end) and 0 < start <= end <= now + 300, "capture-time")
    require(allow_old or now - start <= MAX_SOURCE_AGE, "stale-backup")
    revisions = manifest.get("migration_revisions")
    require(isinstance(revisions, list) and revisions
            and all(isinstance(r, str) and re.fullmatch(r"[A-Za-z0-9_]+", r) for r in revisions)
            and len(revisions) == len(set(revisions)), "migration-revisions")
    counts = manifest.get("table_counts")
    require(isinstance(counts, dict) and CORE.issubset(counts) and len(counts) <= 1000, "core-tables")
    for table, count in counts.items():
        quote_identifier(table)
        require(type(count) is int and count >= 0, "row-count")
    validate_private_documents(manifest.get("private_documents"), source)


def restore(project, source, manifest, stream, phase, private_stream=None):
    phase("stale-resource-cleanup")
    cleanup(project)
    image = manifest["postgres_image_id"]
    phase("image-verification")
    run(["docker", "image", "inspect", image])
    try:
        phase("container-creation")
        created = run([
            "docker", "create", "--pull", "never", "--name", NAME,
            "--label", OWNER + "=" + OWNER_VALUE,
            "--label", PROJECT + "=" + project_id(project),
            "--network", "none", "--ipc", "private", "--restart", "no",
            "--memory", "512m", "--cpus", "1", "--pids-limit", "128",
            "--tmpfs", "/var/lib/postgresql/data:rw,nosuid,size=256m",
            "--tmpfs", "/restore-documents:rw,nosuid,size=256m",
            "--env", "POSTGRES_HOST_AUTH_METHOD=trust",
            "--env", "POSTGRES_USER=jobflow", "--env", "POSTGRES_DB=restore_validation",
            image,
        ])
        info = owned_container(project)
        require(info is not None and info["Id"] == created, "created-container")
        verify_isolation(info, image)
        run(["docker", "start", created])
        phase("database-readiness")
        deadline = time.monotonic() + 60
        while True:
            try:
                run(["docker", "exec", created, "pg_isready", "-h", "127.0.0.1",
                     "-U", "jobflow", "-d", "restore_validation"], timeout=5)
                break
            except subprocess.CalledProcessError:
                if time.monotonic() >= deadline:
                    raise TimeoutError("readiness")
                time.sleep(1)
        phase("database-restore")
        run(["docker", "exec", "-i", created, "pg_restore", "--exit-on-error",
             "--single-transaction", "--no-owner", "--no-privileges",
             "-h", "127.0.0.1", "-U", "jobflow",
             "-d", "restore_validation"], stdin=stream, timeout=300)
        private_metadata = manifest.get("private_documents")
        if private_metadata is not None:
            require(private_stream is not None, "private-archive-stream")
            phase("private-document-extraction")
            private_stream.seek(0)
            run(["docker", "exec", "-i", created, "tar", "--no-same-owner",
                 "--no-same-permissions", "-xpf", "-", "-C", "/restore-documents"],
                stdin=private_stream, timeout=300)

        def query(sql):
            return json.loads(run([
                "docker", "exec", "-e", "PGOPTIONS=-c statement_timeout=30000", created,
                "psql", "-X", "-qAt", "-v", "ON_ERROR_STOP=1", "-h", "127.0.0.1",
                "-U", "jobflow", "-d", "restore_validation", "-c", sql,
            ]))

        phase("migration-comparison")
        revisions = query("SELECT json_agg(version_num ORDER BY version_num) FROM public.alembic_version")
        require(revisions == sorted(manifest["migration_revisions"]), "migration-mismatch")
        phase("table-inventory-comparison")
        tables = query("SELECT json_agg(tablename ORDER BY tablename) FROM pg_tables WHERE schemaname='public'")
        require(tables == sorted(manifest["table_counts"]), "table-inventory-mismatch")
        phase("snapshot-count-comparison")
        for table, expected in sorted(manifest["table_counts"].items()):
            actual = query("SELECT to_json(count(*)) FROM public." + quote_identifier(table))
            require(type(actual) is int and actual == expected, "row-count-mismatch")
        if private_metadata is not None:
            phase("private-document-comparison")
            expected_documents = sorted(private_metadata["documents"], key=lambda item: item["file_key"])
            actual_documents = query("SELECT COALESCE(json_agg(json_build_object("
                "'file_key',file_key,'byte_size',byte_size,'sha256',sha256) ORDER BY file_key),"
                "'[]'::json) FROM public.prestamodesk_application_review_documents")
            require(actual_documents == expected_documents, "private-document-database-mismatch")
            for record in expected_documents:
                path = "/restore-documents/" + record["file_key"]
                digest = run(["docker", "exec", created, "sha256sum", path]).split()[0]
                size = run(["docker", "exec", created, "stat", "-c", "%s", path])
                require(digest == record["sha256"] and size == str(record["byte_size"]),
                        "private-document-restored-file-mismatch")
    finally:
        # Also handles create/start timeouts where Docker created the resource
        # but its ID never reached this process. Ownership must still match.
        try:
            cleanup(project)
        except Exception:
            phase("container-cleanup")
            raise


def notify(project, action):
    spec = importlib.util.spec_from_file_location(
        "restore_health", project / "scripts/report-backup-health.py")
    health = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(health)
    health.send(action, Path.home() / ".config/fieldlookers/healthchecks-restore-ping-url")


def perform(project, selected=None, allow_old=False, send_alert=False):
    runtime = project / "runtime"
    attempt = {"format_version": 1, "attempt_id": uuid.uuid4().hex,
               "status": "running", "started_at": time.time(), "stage": "selection"}

    def phase(name):
        attempt["stage"] = name

    try:
        atomic_json(runtime / "last-restore-attempt.json", attempt)
        evidence = None
        if selected is None:
            evidence = read_json(runtime / "last-offsite-success.json")
            require(evidence.get("status") == "verified", "offsite-status")
            selected = project / "backups" / evidence["source"]
        require(selected.parent.resolve() == (project / "backups").resolve()
                and re.fullmatch(r"jobflow-\d{8}-\d{6}\.dump", selected.name), "source-path")
        phase("manifest-verification")
        manifest_path = selected.with_name(selected.name + ".manifest.json")
        with open_private(manifest_path) as metadata:
            require(os.fstat(metadata.fileno()).st_size <= MAX_MANIFEST_BYTES, "manifest-size")
            raw = metadata.read()
        manifest = json.loads(raw)
        validate_manifest(manifest, selected, time.time(), allow_old)
        private_metadata = manifest.get("private_documents")
        private_stream = None
        private_path = selected.with_name(selected.name + ".private.tar")
        if private_metadata is not None:
            private_stream = open_private(private_path)
            validate_private_archive(private_stream, private_metadata)
        with open_private(selected) as stream:
            require(os.fstat(stream.fileno()).st_size == manifest["bytes"], "size-mismatch")
            require(stream.read(5) == b"PGDMP", "dump-format")
            stream.seek(0)
            require(hashlib.file_digest(stream, "sha256").hexdigest() == manifest["sha256"], "hash-mismatch")
            if evidence is not None:
                require(evidence.get("source_sha256") == manifest["sha256"], "offsite-source-mismatch")
                if private_metadata is not None:
                    artifacts = evidence.get("artifacts", [])
                    match = next((item for item in artifacts
                                  if item.get("source") == private_metadata["archive"]), None)
                    require(match is not None and match.get("source_sha256") == private_metadata["sha256"],
                            "offsite-private-archive-mismatch")
            stream.seek(0)
            try:
                restore(project, selected, manifest, stream, phase, private_stream)
            finally:
                if private_stream is not None:
                    private_stream.close()
            # Reject an in-place change while the same open file was restored.
            stream.seek(0)
            require(hashlib.file_digest(stream, "sha256").hexdigest() == manifest["sha256"], "source-changed")
        if private_metadata is not None:
            with open_private(private_path) as verify_stream:
                require(os.fstat(verify_stream.fileno()).st_size == private_metadata["bytes"]
                        and hashlib.file_digest(verify_stream, "sha256").hexdigest()
                        == private_metadata["sha256"], "private-archive-changed")
        if send_alert:
            phase("success-notification")
            notify(project, "success")
        phase("success-publication")
        success = {
            "format_version": 1, "status": "verified", "attempt_id": attempt["attempt_id"],
            "completed_at": time.time(), "source": selected.name,
            "source_sha256": manifest["sha256"],
            "manifest_sha256": hashlib.sha256(raw).hexdigest(),
            "snapshot_started_at": manifest["snapshot_started_at"],
            "migration_revisions": sorted(manifest["migration_revisions"]),
            "tables_verified": len(manifest["table_counts"]), "cleanup": "passed",
            "source_kind": "local-snapshot-dump",
            "offsite_source_matched": evidence is not None,
            "scheduled_eligible": not allow_old,
            "notification": "accepted" if send_alert else "not-requested",
        }
        atomic_json(runtime / "last-restore-success.json", success)
        attempt.update(status="verified", completed_at=success["completed_at"], stage="complete")
        atomic_json(runtime / "last-restore-attempt.json", attempt)
        print("Isolated restore validation: passed")
        print("Tested backup:", selected.name)
        print("Snapshot table counts matched:", success["tables_verified"])
        print("Temporary container removed: passed")
        return 0
    except Exception as error:
        attempt.update(status="failed", completed_at=time.time(), error_type=type(error).__name__)
        try:
            atomic_json(runtime / "last-restore-attempt.json", attempt)
        except Exception:
            print("Restore failure marker could not be saved.", file=sys.stderr)
        if send_alert:
            try:
                notify(project, "failure")
            except Exception:
                print("Restore failure notification could not be delivered.", file=sys.stderr)
        print("Restore validation failed at " + attempt["stage"] + ": " + type(error).__name__, file=sys.stderr)
        return 1


def check(project):
    success = read_json(project / "runtime/last-restore-success.json")
    attempt = read_json(project / "runtime/last-restore-attempt.json")
    completed = success.get("completed_at")
    require(success.get("status") == attempt.get("status") == "verified"
            and success.get("attempt_id") == attempt.get("attempt_id")
            and timestamp(completed) and -300 <= time.time() - completed <= MAX_CHECK_AGE
            and success.get("cleanup") == "passed" and success.get("scheduled_eligible") is True
            and type(success.get("tables_verified")) is int and success["tables_verified"] >= len(CORE),
            "restore-stale-or-failed")
    print("Restore freshness: passed")


def terminated(signum, frame):
    raise RuntimeError("termination-requested")


def main(argv=None):
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path(__file__).resolve().parent.parent)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--latest", action="store_true")
    actions.add_argument("--backup", type=Path)
    actions.add_argument("--check", action="store_true")
    actions.add_argument("--cleanup", action="store_true")
    parser.add_argument("--notify", action="store_true")
    parser.add_argument("--allow-old", action="store_true")
    args = parser.parse_args(argv)
    if args.allow_old and (args.backup is None or args.notify):
        parser.error("--allow-old requires --backup and cannot send scheduled notifications")
    project = args.project_dir.resolve()
    previous = {sig: signal.signal(sig, terminated) for sig in (signal.SIGTERM, signal.SIGINT)}
    try:
        with locked(project):
            if args.check:
                check(project)
                return 0
            if args.cleanup:
                try:
                    cleanup(project)
                except Exception:
                    if args.notify:
                        notify(project, "failure")
                    raise
                if args.notify and os.environ.get("SERVICE_RESULT", "success") != "success":
                    notify(project, "failure")
                print("Restore container cleanup: passed")
                return 0
            return perform(project, args.backup, args.allow_old, args.notify)
    except Exception as error:
        print("Restore operation failed: " + type(error).__name__, file=sys.stderr)
        return 1
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


if __name__ == "__main__":
    raise SystemExit(main())
