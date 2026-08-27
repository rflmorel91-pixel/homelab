#!/usr/bin/env python3
"""Probe public readiness and send a status-only external heartbeat."""
import argparse
import fcntl
import importlib.util
import json
import math
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time

PUBLIC_URL = "https://jobflow.fieldlookers.com/api/v1/ready"
EXPECTED = {
    "status": "ready", "service": "jobflow-api",
    "checks": {"database": "passed", "migrations": "passed", "products": "passed"},
}
MAX_BODY = 4096
MAX_AGE = 180


def probe():
    # -q must be first: ignore ~/.curlrc (including redirects or TLS overrides).
    # Neither the public URL nor this command contains credentials.
    result = subprocess.run(
        ["curl", "-q", "--silent", "--show-error", "--fail",
         "--proto", "=https", "--connect-timeout", "3", "--max-time", "10",
         "--max-filesize", str(MAX_BODY), "--max-redirs", "0",
         "--header", "Cache-Control: no-cache",
         "--write-out", "\n%{http_code}", PUBLIC_URL],
        capture_output=True, timeout=15, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("Public request failed")
    body, separator, status = result.stdout.rpartition(b"\n")
    if not separator or status != b"200" or len(body) > MAX_BODY:
        raise ValueError("Unexpected HTTP response")
    if json.loads(body) != EXPECTED:
        raise ValueError("Readiness did not pass")


def notify(project, action):
    spec = importlib.util.spec_from_file_location(
        "readiness_heartbeat", project / "scripts/report-backup-health.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.send(action, Path.home() / ".config/fieldlookers/healthchecks-readiness-ping-url")


def write_status(project, record):
    runtime = project / "runtime"
    fd, temporary = tempfile.mkstemp(prefix=".readiness-monitor-", dir=runtime)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(record, stream, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, runtime / "last-readiness-monitor.json")
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def run_once(project):
    stage = "public-readiness"
    try:
        probe()
        checked_at = time.time()
        stage = "heartbeat-delivery"
        notify(project, "success")
        stage = "status-publication"
        write_status(project, {
            "format_version": 1, "status": "verified", "checked_at": checked_at,
            "completed_at": time.time(), "heartbeat": "accepted",
        })
        print("Public readiness and external heartbeat: passed")
        return 0
    except Exception as error:
        record = {
            "format_version": 1, "status": "failed", "completed_at": time.time(),
            "stage": stage, "error_type": type(error).__name__,
        }
        try:
            write_status(project, record)
        except Exception:
            print("Readiness failure status could not be saved.", file=sys.stderr)
        try:
            notify(project, "failure")
        except Exception:
            print("Readiness failure heartbeat could not be delivered.", file=sys.stderr)
        print("Readiness monitor failed at " + stage + ": " + type(error).__name__, file=sys.stderr)
        return 1


def check(project):
    path = project / "runtime/last-readiness-monitor.json"
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o600 or info.st_size > 4096):
            raise ValueError("Unsafe status file")
        record = json.load(stream)
    checked = record.get("checked_at")
    if (record.get("status") != "verified" or record.get("heartbeat") != "accepted"
            or type(checked) not in (int, float) or not math.isfinite(checked)
            or not -5 <= time.time() - checked <= MAX_AGE):
        raise ValueError("Readiness monitor stale or failed")
    print("Readiness monitor freshness: passed")


def main(argv=None):
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--check", action="store_true", help="Check local evidence only; do not ping")
    args = parser.parse_args(argv)
    project = args.project_dir.resolve()
    try:
        runtime = project / "runtime"
        runtime.mkdir(parents=True, exist_ok=True, mode=0o700)
        if runtime.is_symlink():
            raise ValueError("Unexpected runtime directory")
        if args.check:
            check(project)
            return 0
        fd = os.open(runtime / "readiness-monitor.lock",
                     os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return run_once(project)
    except Exception as error:
        # Setup/lock failures do not report success; the external missing-ping
        # deadline still applies, even when the host or its filesystem is down.
        print("Readiness monitor operation failed: " + type(error).__name__, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
