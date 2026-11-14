#!/usr/bin/env python3
"""Back up the active web bind mount through the existing age/B2 pipeline."""
import argparse
import datetime as dt
import fcntl
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import tarfile
import tempfile
import time

MAX_FILES = 10000
MAX_BYTES = 128 * 1024 * 1024


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def mounted_frontend(container):
    result = subprocess.run(["docker", "inspect", container], check=True,
                            capture_output=True, text=True, timeout=30)
    records = json.loads(result.stdout)
    require(len(records) == 1, "container-count")
    mounts = [m for m in records[0]["Mounts"]
              if m["Destination"] == "/usr/share/nginx/html"]
    require(len(mounts) == 1 and mounts[0]["Type"] == "bind"
            and mounts[0].get("RW") is False, "frontend-readonly-bind")
    source = Path(mounts[0]["Source"])
    require(source.is_absolute() and source.is_dir() and not source.is_symlink(),
            "frontend-source")
    return source


def inventory(source):
    files = {}
    total = 0
    for path in sorted(source.rglob("*")):
        info = path.lstat()
        require(not stat.S_ISLNK(info.st_mode), "frontend-symlink")
        if stat.S_ISDIR(info.st_mode):
            continue
        require(stat.S_ISREG(info.st_mode), "frontend-special-file")
        name = path.relative_to(source).as_posix()
        require(not any(part.startswith(".") for part in Path(name).parts)
                and path.suffix.lower() not in {".key", ".pem", ".p12", ".pfx"},
                "frontend-private-file")
        total += info.st_size
        require(total <= MAX_BYTES and len(files) < MAX_FILES, "frontend-size-limit")
        data = path.read_bytes()
        require(len(data) == info.st_size, "frontend-changed")
        files[name] = data
    require("fieldnest-workspace.html" in files and bool(files), "frontend-workspace-missing")
    return files


def build_archive(source):
    files = inventory(source)
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    manifest = {"format_version": 1, "kind": "frontend", "files": hashes}
    entries = {"manifest.json": json.dumps(manifest, sort_keys=True).encode(),
               **{"app/" + name: data for name, data in files.items()}}
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for name, data in entries.items():
            info = tarfile.TarInfo("frontend/" + name)
            info.size, info.mode, info.mtime = len(data), 0o644, 0
            archive.addfile(info, io.BytesIO(data))
    require(inventory(source) == files, "frontend-changed")
    return output.getvalue(), hashes


def run_backup(project, config, container, helper, now):
    source = mounted_frontend(container)
    archive, hashes = build_archive(source)
    digest = hashlib.sha256(archive).hexdigest()
    spool = project / "runtime/b2-spool"
    require(not spool.is_symlink(), "spool-symlink")
    spool.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(spool, 0o700)
    with tempfile.TemporaryDirectory(dir=spool) as temporary:
        path = Path(temporary) / ("fieldnest-web-" + digest + ".tar")
        path.write_bytes(archive)
        path.chmod(0o600)
        encrypted, source_hash = helper.encrypted_copy(path, spool, config / "backup-recipient.txt")
    require(source_hash == digest, "encrypted-source-mismatch")
    # Check the mount again to detect a release switch during the snapshot.
    require(mounted_frontend(container) == source, "frontend-mount-changed")
    day = dt.datetime.fromtimestamp(now, dt.timezone.utc).date()
    until = int((dt.datetime.combine(day, dt.time(), dt.timezone.utc).timestamp()
                 + 36 * 86400) * 1000)
    name = (helper.PREFIX + "frontend/daily/" + day.isoformat() + "/fieldnest-web-"
            + digest + "." + hashlib.sha256(encrypted).hexdigest() + ".age")
    result = helper.B2(config / "b2-upload.json").ensure_copy(name, encrypted, until)
    receipt = {"status": "verified", "completed_at": time.time(), "source": str(source),
               "source_sha256": digest, "files": len(hashes), "object": result}
    helper.atomic_json(project / "runtime/last-frontend-offsite-success.json", receipt)
    helper.atomic_json(project / "runtime/last-frontend-offsite-attempt.json", receipt)
    # Local cache cleanup only; B2 lifecycle retention remains separately managed.
    for cached in spool.glob("fieldnest-web-*.tar.*.age"):
        if not cached.is_symlink() and now - cached.stat().st_mtime > 40 * 86400:
            cached.unlink()
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--config-dir", type=Path, default=Path.home() / ".config/fieldlookers")
    parser.add_argument("--container", default="jobflow-web")
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location(
        "frontend_replication", args.project_dir / "scripts/replicate-jobflow-backup.py")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    try:
        with (args.config_dir / "replication.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            result = run_backup(args.project_dir, args.config_dir, args.container, helper, time.time())
        print("Frontend off-site backup verified:", result["files"], "files")
    except Exception as error:
        helper.atomic_json(args.project_dir / "runtime/last-frontend-offsite-attempt.json",
                           {"status": "failed", "completed_at": time.time(),
                            "error_type": type(error).__name__})
        raise SystemExit("Frontend backup failed: " + type(error).__name__) from None


if __name__ == "__main__":
    main()
