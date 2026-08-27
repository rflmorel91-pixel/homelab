#!/usr/bin/env python3
"""Create a dump and count manifest from one read-only PostgreSQL snapshot."""
import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import subprocess
import sys
import tempfile
import time

CORE_TABLES = {"alembic_version", "users", "tenants", "tenant_memberships", "products"}
MAX_DUMP_BYTES = 256 * 1024 * 1024
PSQL = ["docker", "exec", "-i", "-e",
        "PGOPTIONS=-c statement_timeout=60000 -c lock_timeout=5000 -c idle_in_transaction_session_timeout=600000",
        "jobflow-db", "psql", "-X", "-qAt", "-v", "ON_ERROR_STOP=1",
        "-U", "jobflow", "-d", "jobflow"]
SNAPSHOT_SQL = """SELECT json_build_object(
  'snapshot', pg_export_snapshot(),
  'revisions', (SELECT json_agg(version_num ORDER BY version_num) FROM public.alembic_version),
  'tables', (SELECT json_agg(tablename ORDER BY tablename) FROM pg_tables WHERE schemaname='public')
);"""


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def quote_identifier(value):
    require(isinstance(value, str) and value and "\x00" not in value, "invalid-identifier")
    return '"' + value.replace('"', '""') + '"'


def validate_snapshot(value):
    require(isinstance(value, dict), "snapshot-object")
    require(re.fullmatch(r"[0-9A-Fa-f]+-[0-9A-Fa-f]+-\d+", value.get("snapshot", "")),
            "snapshot-id")
    revisions = value.get("revisions")
    require(isinstance(revisions, list) and bool(revisions), "migration-revisions")
    require(all(isinstance(item, str) and re.fullmatch(r"[A-Za-z0-9_]+", item)
                for item in revisions), "migration-revision-format")
    tables = value.get("tables")
    require(isinstance(tables, list) and bool(tables), "table-list")
    require(all(isinstance(item, str) and item and "\x00" not in item for item in tables),
            "table-names")
    require(len(tables) == len(set(tables)), "duplicate-tables")
    require(CORE_TABLES.issubset(tables), "missing-core-tables")
    return value


class SnapshotSession:
    def __enter__(self):
        self.process = subprocess.Popen(PSQL, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                        bufsize=0)
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        self.pending = bytearray()
        try:
            self.write("BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;")
            return self
        except BaseException:
            self.close()
            raise

    def write(self, sql):
        self.process.stdin.write((sql + "\n").encode())
        self.process.stdin.flush()

    def query(self, sql, timeout=65):
        self.write(sql)
        deadline = time.monotonic() + timeout
        while b"\n" not in self.pending:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not self.selector.select(remaining):
                raise TimeoutError("snapshot-query-timeout")
            chunk = os.read(self.process.stdout.fileno(), 65536)
            require(bool(chunk), "snapshot-session-ended")
            self.pending.extend(chunk)
            require(len(self.pending) <= 1024 * 1024, "snapshot-response-limit")
        line, _, rest = self.pending.partition(b"\n")
        self.pending = bytearray(rest)
        return json.loads(line)

    def close(self):
        # EOF ends psql and rolls back its read-only transaction.
        try:
            self.process.stdin.close()
        except (BrokenPipeError, OSError):
            pass
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=10)
        self.selector.close()
        self.process.stdout.close()

    def __exit__(self, kind, value, traceback):
        self.close()


def capture(output, project, session_factory=SnapshotSession):
    backup_dir = project / "backups"
    require(output.parent.resolve() == backup_dir.resolve(), "output-directory")
    require(re.fullmatch(r"jobflow-\d{8}-\d{6}\.dump", output.name), "output-name")
    require(backup_dir.is_dir(), "backup-directory-missing")
    manifest_path = output.with_name(output.name + ".manifest.json")
    require(not output.exists() and not output.is_symlink(), "dump-already-exists")
    require(not manifest_path.exists() and not manifest_path.is_symlink(), "manifest-already-exists")
    image = subprocess.run(["docker", "inspect", "jobflow-db", "--format", "{{.Image}}"],
                           check=True, capture_output=True, text=True, timeout=30).stdout.strip()
    require(re.fullmatch(r"sha256:[0-9a-f]{64}", image), "postgres-image-id")
    started = time.time()
    with tempfile.TemporaryDirectory(prefix=".snapshot-", dir=backup_dir) as directory:
        temporary_dump = Path(directory) / "backup.dump"
        temporary_manifest = Path(directory) / "manifest.json"
        with session_factory() as session:
            snapshot = validate_snapshot(session.query(SNAPSHOT_SQL))
            counts = {}
            for table in snapshot["tables"]:
                count = session.query("SELECT to_json(count(*)) FROM public." + quote_identifier(table) + ";")
                require(type(count) is int and count >= 0, "invalid-count")
                counts[table] = count
            with temporary_dump.open("xb") as stream:
                subprocess.run([
                    "docker", "exec", "jobflow-db", "pg_dump", "-w", "-U", "jobflow",
                    "-d", "jobflow", "-Fc", "--lock-wait-timeout=5s",
                    "--snapshot=" + snapshot["snapshot"],
                ], stdout=stream, stderr=subprocess.DEVNULL, check=True, timeout=300)
                stream.flush()
                os.fsync(stream.fileno())
        require(0 < temporary_dump.stat().st_size <= MAX_DUMP_BYTES, "dump-size-limit")
        with temporary_dump.open("rb") as stream:
            require(stream.read(5) == b"PGDMP", "dump-format")
            stream.seek(0)
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
            stream.seek(0)
            subprocess.run(["docker", "exec", "-i", "jobflow-db", "pg_restore", "--list"],
                           stdin=stream, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           check=True, timeout=60)
        manifest = {
            "format_version": 1, "source": output.name, "sha256": digest,
            "bytes": temporary_dump.stat().st_size,
            "snapshot_started_at": started, "capture_completed_at": time.time(),
            "postgres_image_id": image, "migration_revisions": sorted(snapshot["revisions"]),
            "schema": "public", "table_counts": counts,
            "count_basis": "same-exported-snapshot-as-pg-dump",
        }
        with temporary_manifest.open("x") as stream:
            json.dump(manifest, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary_dump.chmod(0o600)
        temporary_manifest.chmod(0o600)
        # Hard links publish without replacing a pre-existing destination.
        os.link(temporary_dump, output)
        try:
            os.link(temporary_manifest, manifest_path)
        except BaseException:
            output.unlink()
            raise
    return manifest


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        runtime = args.project_dir / "runtime"
        runtime.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (runtime / "backup-snapshot.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            manifest = capture(args.output, args.project_dir)
        print("Snapshot dump and manifest: created")
        print("Backup:", manifest["source"])
        print("Tables captured:", len(manifest["table_counts"]))
        print("Migration revisions:", ", ".join(manifest["migration_revisions"]))
        return 0
    except Exception as error:
        print("Snapshot capture failed: " + type(error).__name__, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
