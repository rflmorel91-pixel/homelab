#!/usr/bin/env python3
"""Encrypt and verify B2 backup copies. Not scheduled until explicitly integrated."""
import argparse
import base64
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

BUCKET = "1e54c09a4c6e4437ab030215"
PREFIX = "platform/"
MAX_AGE = 36 * 3600
MAX_BYTES = 256 * 1024 * 1024
CAPABILITIES = {
    "listBuckets", "listFiles", "readFiles", "writeFiles",
    "readFileRetentions", "writeFileRetentions",
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def plan(source, backup_dir, now):
    require(not source.is_symlink(), "symlink-source")
    require(source.resolve().parent == backup_dir.resolve(), "source-directory")
    require(re.fullmatch(r"jobflow-\d{8}-\d{6}\.dump", source.name), "source-name")
    info = source.stat()
    require(0 < info.st_size <= MAX_BYTES, "source-size")
    require(0 <= now - info.st_mtime <= MAX_AGE, "source-freshness")
    stamp = dt.datetime.fromtimestamp(info.st_mtime, dt.timezone.utc)
    tiers = [("daily", 7)]
    if stamp.weekday() == 6:
        tiers.append(("weekly", 35))
    if stamp.day == 1:
        tiers.append(("monthly", 365))
    return [{"tier": tier, "days": days, "date": stamp.date().isoformat(),
             "retain_until_ms": int((info.st_mtime + days * 86400) * 1000)}
            for tier, days in tiers]


def safe_url(url):
    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname or ""
    require(parsed.scheme == "https" and not parsed.username and not parsed.password,
            "unsafe-url")
    require(parsed.port in (None, 443), "unsafe-port")
    require(host.endswith((".backblazeb2.com", ".backblaze.com")), "unsafe-host")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class B2:
    def __init__(self, path):
        require(not path.is_symlink(), "credential-symlink")
        info = path.stat()
        require(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o600,
                "credential-permissions")
        self.opener = urllib.request.build_opener(NoRedirect())
        credentials = json.loads(path.read_text())
        pair = f"{credentials['keyId']}:{credentials['applicationKey']}"
        basic = base64.b64encode(pair.encode()).decode()
        with self.open("https://api.backblazeb2.com/b2api/v4/b2_authorize_account",
                       {"Authorization": "Basic " + basic}) as response:
            auth = json.load(response)
        self.api = auth["apiInfo"]["storageApi"]
        self.token = auth["authorizationToken"]
        allowed = self.api["allowed"]
        require(set(allowed["capabilities"]) == CAPABILITIES, "credential-capabilities")
        require(allowed["namePrefix"] == PREFIX, "credential-prefix")
        require({b["id"] for b in allowed["buckets"]} == {BUCKET}, "credential-bucket")

    def open(self, url, headers, data=None):
        safe_url(url)
        return self.opener.open(urllib.request.Request(url, headers=headers, data=data),
                                timeout=90)

    def call(self, method, body):
        with self.open(self.api["apiUrl"] + "/b2api/v4/" + method,
                       {"Authorization": self.token, "Content-Type": "application/json"},
                       json.dumps(body).encode()) as response:
            return json.load(response)

    def ensure_copy(self, name, data, until):
        files = self.call("b2_list_file_names", {
            "bucketId": BUCKET, "prefix": name, "maxFileCount": 1,
        })["files"]
        existing = next((item for item in files if item["fileName"] == name), None)
        if existing is None:
            target = self.call("b2_get_upload_url", {"bucketId": BUCKET})
            with self.open(target["uploadUrl"], {
                "Authorization": target["authorizationToken"],
                "Content-Type": "application/octet-stream",
                "X-Bz-File-Name": urllib.parse.quote(name, safe="/"),
                "X-Bz-Content-Sha1": hashlib.sha1(data).hexdigest(),
                "X-Bz-File-Retention-Mode": "governance",
                "X-Bz-File-Retention-Retain-Until-Timestamp": str(until),
                "X-Bz-Server-Side-Encryption": "AES256",
            }, data) as response:
                existing = json.load(response)
        query = urllib.parse.urlencode({"fileId": existing["fileId"]})
        with self.open(self.api["downloadUrl"] + "/b2api/v4/b2_download_file_by_id?" + query,
                       {"Authorization": self.token}) as response:
            downloaded = response.read(len(data) + 1)
            require(downloaded == data, "remote-bytes")
            require(response.headers.get("X-Bz-File-Retention-Mode") == "governance",
                    "remote-retention-mode")
            retained = int(response.headers["X-Bz-File-Retention-Retain-Until-Timestamp"])
            require(retained >= until, "remote-retention-duration")
            require(response.headers.get("X-Bz-Server-Side-Encryption") == "AES256",
                    "remote-server-encryption")
        return {"name": name, "file_id": existing["fileId"], "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(), "retain_until_ms": retained}


def atomic_json(path, value):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".offsite-")
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def encrypted_copy(source, spool, recipient):
    data = source.read_bytes()
    require(0 < len(data) <= MAX_BYTES, "source-size")
    require(data.startswith(b"PGDMP"), "postgres-archive-magic")
    digest = hashlib.sha256(data).hexdigest()
    target = spool / (source.name + "." + digest + ".age")
    if not target.exists():
        with tempfile.TemporaryDirectory(dir=spool) as temporary:
            output = Path(temporary) / "encrypted.age"
            subprocess.run(["age", "-R", str(recipient), "-o", str(output)],
                           input=data, check=True, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=300)
            os.replace(output, target)
    require(not target.is_symlink(), "spool-symlink")
    ciphertext = target.read_bytes()
    require(ciphertext.startswith(b"age-encryption.org/v1\n"), "age-format")
    return ciphertext, digest


def replicate(source, project, config, now):
    tiers = plan(source, project / "backups", now)
    spool = project / "runtime/b2-spool"
    spool.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(spool, 0o700)
    data, source_hash = encrypted_copy(source, spool, config / "backup-recipient.txt")
    b2 = B2(config / "b2-upload.json")
    suffix = hashlib.sha256(data).hexdigest()
    copies = []
    for tier in tiers:
        name = f"{PREFIX}{tier['tier']}/{tier['date']}/{source.name}.{suffix}.age"
        item = b2.ensure_copy(name, data, tier["retain_until_ms"])
        item["tier"] = tier["tier"]
        copies.append(item)
    result = {"status": "verified", "completed_at": time.time(),
              "source_mtime": source.stat().st_mtime, "source": source.name,
              "source_sha256": source_hash, "objects": copies}
    atomic_json(project / "runtime/last-offsite-success.json", result)
    atomic_json(project / "runtime/last-offsite-attempt.json", result)
    # Cache only: remote lifecycle cleanup must be configured separately.
    for cached in spool.glob("jobflow-*.dump.*.age"):
        if not cached.is_symlink() and now - cached.stat().st_mtime > 8 * 86400:
            cached.unlink()
    return result


def check_freshness(runtime, now):
    success = json.loads((runtime / "last-offsite-success.json").read_text())
    attempt = json.loads((runtime / "last-offsite-attempt.json").read_text())
    require(success["status"] == "verified" and attempt["status"] == "verified",
            "replication-failed")
    require(0 <= now - success["source_mtime"] <= MAX_AGE, "replication-stale")
    require(bool(success["objects"]), "missing-objects")


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--config-dir", type=Path, default=Path.home() / ".config/fieldlookers")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", type=Path, metavar="DUMP")
    mode.add_argument("--upload", type=Path, metavar="DUMP")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.plan:
            print(json.dumps(plan(args.plan, args.project_dir / "backups", time.time()), indent=2))
        elif args.check:
            check_freshness(args.project_dir / "runtime", time.time())
            print("Off-site freshness: passed")
        else:
            with (args.config_dir / "replication.lock").open("a") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                try:
                    result = replicate(args.upload, args.project_dir, args.config_dir, time.time())
                except Exception as error:
                    failure = {"status": "failed", "attempted_at": time.time(),
                               "error_type": type(error).__name__}
                    if isinstance(error, urllib.error.HTTPError):
                        failure["http_status"] = error.code
                    atomic_json(args.project_dir / "runtime/last-offsite-attempt.json", failure)
                    raise
                print("Off-site replication verified: " + ", ".join(o["tier"] for o in result["objects"]))
    except Exception as error:
        print("Off-site operation failed: " + type(error).__name__)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
