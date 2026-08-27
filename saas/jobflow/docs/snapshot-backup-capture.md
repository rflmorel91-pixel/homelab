# Snapshot-consistent backup capture

Installed and integrated into the daily backup service on 2026-08-27.
A manually started backup service completed successfully, including snapshot
capture, manifest copying to OMV, and encrypted dump replication to B2.

## Purpose

Create a PostgreSQL custom-format dump and a private JSON manifest from the
same exported, read-only transaction snapshot. The exporting session stays open
while pg_dump imports that snapshot. Production changes after export therefore
do not cause mismatched baseline counts. No production records are changed.

The manifest records every public table's exact count, migration revision(s),
the dump hash and size, capture timestamps, and the PostgreSQL image ID.
It is intended as the expected baseline for the isolated restore validator.
It is not itself evidence that a database restore succeeded.

## Manual capture and tests

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts/tests -p 'test_backup_snapshot.py' -v
python3 scripts/create-jobflow-backup.py --project-dir /home/rflmorel/homelab/saas/jobflow --output /home/rflmorel/homelab/saas/jobflow/backups/jobflow-YYYYMMDD-HHMMSS.dump
```

The output name must be unique. Existing dumps/manifests are not overwritten.
The backup directory must already exist. PostgreSQL 16 tools are used inside
the existing jobflow-db container, with local socket authentication. No API
container, production password export, or extra Python package is required.

The helper validates the archive listing and publishes dump and manifest with
mode 600 only after successful capture. A failed capture returns nonzero and
does not publish a completed pair. A host crash between the two publications
can leave a dump without a manifest; consumers must require both files and a
matching SHA256. Raw database/tool errors are not printed to public logs.

Each count statement has a 60-second timeout and 5-second lock timeout; pg_dump
has a 300-second process timeout. An idle exporting transaction is limited to
10 minutes by a session-local PostgreSQL setting. Locks are read-only and can
delay concurrent DDL, so avoid running migrations during capture. Dump size is
checked against 256 MiB after capture, matching the current uploader limit.

The helper does not copy files to OMV, encrypt/upload them, update overall
backup-success markers, send alerts, or delete existing backups. Those remain
the existing backup workflow's responsibility. The manifest is retained beside the local dump and copied to OMV.
The backup workflow applies its existing seven-day cleanup rule to both dumps
and manifests. B2 receives the encrypted dump only, not the manifest.
Existing B2 dump format is unchanged.

The isolated restore timer is enabled and active for Sunday 03:30 UTC.
Its separate external failure and recovery emails were confirmed.
The first automatic run is pending, scheduled for 2026-08-30 03:30 UTC.
The age private recovery key remains off the production host.

## Verification status

The included tests exercise snapshot use during dump, baseline counts/hashes,
private file modes, non-overwrite behavior, failure cleanup, manifest validation,
identifier quoting, and the interactive session's fragmented-response handling.
Docker/PostgreSQL behavior is mocked in the unit tests. Live capture and
isolated restore were also verified on dellpc: all 22 public table counts and
snapshot migration revisions matched. The combined backup test suite passed
50 tests. See isolated-restore-validation.md for deployment evidence.
