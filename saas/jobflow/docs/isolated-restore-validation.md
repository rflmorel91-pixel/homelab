# Recurring isolated restore validation

Owner: Rafael Morel. Issue: homelab #16.

## Rollout status

Deployed and manually verified on dellpc on 2026-08-27.

- Combined backup test suite: 50 tests passed.
- Staged validator restored `jobflow-20260827-153240.dump`; all 22 public
  table counts and snapshot migration revisions matched.
- Installed systemd service: Result=success, ExecMainStatus=0.
- Temporary container removal and restore freshness checks passed.
- A deliberate count mismatch in a separate test copy returned nonzero,
  preserved the previous success marker, and caused freshness to fail.
- The failure test removed its temporary container, dump, and manifest.
- Restore failure and subsequent recovery emails were confirmed.
- Timer is enabled and active for Sunday 03:30 UTC.
- First automatic run remains pending: 2026-08-30 03:30 UTC.

Manual service execution proves the service works; it does not prove that
the timer has executed. CI verification for these changes is still pending.

## What it proves

`scripts/create-jobflow-backup.py` captures a PostgreSQL custom dump and a private
JSON manifest using one exported read-only snapshot. The manifest records exact
public table counts, migration revisions, dump SHA256/size, image ID, and times.
The backup shell now copies both files to OMV; B2 replication still uploads only
the encrypted dump. Keep the existing local and offsite backup jobs working.

`scripts/validate-jobflow-backup.py --latest` selects the local dump named in
`runtime/last-offsite-success.json`, checks that its SHA256 matches that evidence,
and requires the matching snapshot manifest. It does **not** download or decrypt
B2 data. Manifest and dump must be regular, owner-held, mode-600 files. Default
source freshness is 36 hours, based on snapshot time, not a filename or copied
file timestamp. Checksums detect changes; they do not defend against a host
administrator who can replace both the dump and its evidence.

It restores with `pg_restore --exit-on-error --single-transaction`, compares the
complete public table inventory, every exact snapshot count, and the complete
set of snapshot migration revisions. It does not compare with changing live
production counts or automatically migrate old backups to today's schema.
Application behavior, constraints outside the restored schema, external files,
and business-level data correctness still need separate recovery drills.

## Isolation and cleanup

- Fixed container name: `fieldlookers-restore-validation`.
- The image is the locally available immutable PostgreSQL image ID from the
  snapshot manifest. Automatic image downloads are disabled.
- No external networking, published ports, host bind mounts, production volumes,
  Docker socket mount, host PID namespace, or privileged mode.
- Restore database: `restore_validation` inside this new container only.
- Limits: 512 MiB RAM, one CPU, 128 PIDs, 256 MiB temporary PostgreSQL data mount.
- TCP readiness is checked on its internal loopback interface, avoiding the
  temporary Unix-socket-only initialization server.
- A local exclusive lock prevents overlapping validator/cleanup commands.
- Cleanup accepts only the exact name, full container ID, validator ownership
  label, and project identity label. An unrelated name collision is refused.
- Cleanup runs on restore errors and handled termination. The systemd
  `ExecStopPost` performs another cleanup pass after process failure/timeouts.
  A hard host/Docker failure can leave resources; the next run cleans up only
  matching owned resources. Do not use broad Docker prune commands.

Cleanup failure means validation failure. No passing marker is written for
failed verification or failed cleanup. Docker is a shared host service, so this
does not create a separate physical fault domain or guarantee zero production
resource contention. Tmpfs data may be paged to host swap; this is not a secure
erase mechanism. Source dumps remain private on disk under existing retention.

The source dump is limited to 256 MiB, but a smaller compressed dump can expand
beyond the temporary database capacity. Such a restore must fail and alert;
review limits as the database grows. Service runtime is capped at 15 minutes.

## Schedule and external alerts

Approved schedule: Sunday 03:30 UTC, following the daily 02:30 UTC backup.
The timer is persistent: missed runs can catch up after restart. Ordering after
the backup service waits for it if both are starting; it does not start a new
backup or require the daily backup to succeed.

Dedicated Healthchecks check:

| Setting | Value |
| --- | --- |
| Name | FieldLookers PostgreSQL Restore Validation |
| Cron | `30 3 * * 0` |
| Time zone | UTC |
| Grace | 30 minutes |
| Notification | Email enabled |
| Secret path | `~/.config/fieldlookers/healthchecks-restore-ping-url` (600) |

Both the initial notification test and the validator's deliberate
count-mismatch failure produced confirmed failure emails. A subsequent
successful service run produced a confirmed recovery email.
This check remains separate from the daily backup check.

`--notify` reuses `report-backup-health.py`'s URL validation and status-only POST
sender with the restore URL path. It sends no dump bytes, counts, exception
details, or logs. A success signal follows verified restoration and cleanup.
Failed notification delivery also returns nonzero. `ExecStopPost --notify`
sends failure on abnormal service exit, including systemd timeout. If the host
is off or no failure signal can be delivered, Healthchecks detects the missing
scheduled success after its grace period. It does not execute the restore.

## Evidence

- `runtime/last-restore-success.json`: backup filename/SHA256, manifest SHA256,
  snapshot and completion time, migration revisions, number of verified tables,
  cleanup result and notification status; no actual table row counts.
- `runtime/last-restore-attempt.json`: running/verified/failed, attempt ID,
  stage and sanitized error type. A failed attempt preserves the prior passing
  marker unless a later publication error happened after that marker was written;
  the attempt marker still makes `--check` fail.
- Files are atomic mode-600 replacements. A crash can leave mismatched success
  and attempt IDs; `--check` rejects that state.
- `--check` verifies local evidence: last attempt and success must match, pass
  cleanup, and be no older than eight days. This is not a live database or B2
  check. External Sunday monitoring has the stricter calendar deadline.

Keep runtime files, manifests, URLs, credentials and dumps out of Git. The marker
is deliberately non-sensitive in content, but private by file permissions.

## Deployment gates (Ubuntu)

1. Verify the delivered archive SHA256; extract only the five expected files
   into a staging directory. Run the new unit tests there.
2. Run the staged validator with `--project-dir "$HOME/homelab/saas/jobflow"
   --latest --notify`. Confirm counts, cleanup, the freshness command and the
   restore check's recovery email. This performs real temporary database work
   and writes private runtime evidence, but does not install or enable a timer.
3. Install only the new files in the matching repository paths, preserving
   existing scripts. Run all `test_backup*.py` tests and `git diff --check`.
4. Validate unit syntax on the host, then install both new unit files under
   `/etc/systemd/system/`. Reload systemd and manually start the restore service.
   Confirm `Result=success`, `ExecMainStatus=0`, passing evidence and cleanup.
5. Exercise a controlled failure against a private copy of the dump/manifest,
   never the only real backup. Confirm nonzero exit, preserved previous success,
   cleanup, failure email and a later successful service recovery. A mismatched
   expected count tests restore failure after container creation.
6. Only after those gates: enable/start `jobflow-restore-validation.timer` and
   confirm its next Sunday 03:30 UTC run. Record first automatic-run evidence
   separately; a manually started service does not prove timer execution.
7. Update rollout status, documentation and issue evidence; commit, push and
   verify CI. Do not close #16 before acceptance evidence is complete.

## Manual operations after installation

```bash
cd ~/homelab/saas/jobflow
python3 scripts/validate-jobflow-backup.py --latest --notify
python3 scripts/validate-jobflow-backup.py --check
sudo systemctl start jobflow-restore-validation.service
systemctl show jobflow-restore-validation.service -p Result -p ExecMainStatus
systemctl list-timers jobflow-restore-validation.timer --all --no-pager
```

To validate a specifically selected local dump and its matching manifest:

```bash
python3 scripts/validate-jobflow-backup.py \
  --backup "$HOME/homelab/saas/jobflow/backups/jobflow-YYYYMMDD-HHMMSS.dump"
```

An older manual drill may add `--allow-old`; this cannot use `--notify`, and its
marker deliberately does not satisfy scheduled freshness. Run a fresh scheduled
validation afterward. Use the exact original manifest; do not fabricate a
baseline from current production counts.

For a stalled run, stop only `jobflow-restore-validation.service` and inspect
its result. The targeted cleanup command is:

```bash
python3 scripts/validate-jobflow-backup.py --cleanup
```

If Docker is unavailable or ownership checks fail, investigate instead of
deleting unrelated containers. Never direct `pg_restore` to `jobflow-db`.
The legacy `validate-jobflow-restore.sh` restores a temporary database inside
production's PostgreSQL container and compares live counts; it remains unchanged
but is not used by this scheduled validator.

## Full offsite recovery remains separate

The private age key remains on the Windows recovery machine and in an independent
password manager. Do not place it on production for scheduled validation.
The earlier B2 download/decrypt SHA256 match proved an encrypted byte roundtrip;
scheduled local restores add database validation but not a fresh offsite drill.
To prove offsite database recovery, retrieve/decrypt a retained B2 object on an
authorized recovery machine, retain its matching private manifest from a trusted
source, and restore in an isolated PostgreSQL environment. B2 currently lacks
these sidecar manifests, so total-site loss would require a separately available
manifest for exact original count comparison. Keep that limitation explicit.

## References

- PostgreSQL pg_restore: https://www.postgresql.org/docs/16/app-pgrestore.html
- Docker network isolation: https://docs.docker.com/engine/network/drivers/none/
- Docker tmpfs caveats: https://docs.docker.com/engine/storage/tmpfs/
- systemd service cleanup: https://www.freedesktop.org/software/systemd/man/systemd.service.html
- Healthchecks scheduling: https://healthchecks.io/docs/configuring_checks/

## Canonical migration verification

Restore validation compares the restored database revision against the
single migration graph assembled by
`backend/scripts/platform_alembic.py`. Platform revisions are loaded
from `backend/app/platform/migrations/versions/`, and product revisions
are loaded from their product-owned migration directories.

The legacy `backend/migrations/` tree must not exist. Do not recreate it
during recovery and do not rewrite an applied revision identifier.
