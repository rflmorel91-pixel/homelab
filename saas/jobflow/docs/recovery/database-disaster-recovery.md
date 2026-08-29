# JobFlow Database Disaster Recovery

## Purpose

This runbook documents the controlled recovery procedure for restoring the production JobFlow PostgreSQL database from a verified backup.

This procedure is intended for actual database recovery events, such as:

* Database corruption
* Accidental data loss
* Failed database replacement
* Storage failure
* Recovery to a known-good backup

The safe restore-validation script should be used for routine backup testing. This runbook is for restoring the live `jobflow` database.

## Recovery Principles

Before restoring production data:

* Confirm that recovery is necessary.
* Identify the backup that should be restored.
* Stop application write traffic before replacing the database.
* Preserve the current database state when possible before destructive actions.
* Verify the backup archive before restoring it.
* Restore the database in a controlled order.
* Run migrations after restoration.
* Validate application health and public access before declaring recovery complete.

## Recovery Sequence

The production recovery sequence is:

1. Identify the verified backup to restore.
2. Stop `jobflow-web` and `jobflow-api` to prevent application access and writes.
3. Create an emergency backup of the current production database when possible.
4. Verify the selected backup archive with `pg_restore --list`.
5. Drop and recreate the production `jobflow` database.
6. Restore the selected backup into the production database.
7. Run Alembic migrations to ensure the restored database is at the current schema revision.
8. Start the JobFlow API and web services.
9. Verify Docker healthchecks.
10. Verify the public frontend and `/api/v1/health`.
11. Sign in and validate representative application data.
12. Confirm Uptime Kuma monitors return to Up.

The database container should remain running during the restore procedure unless the failure specifically requires PostgreSQL container or storage recovery.

## Production Restore Commands

> **Warning:** The following procedure replaces the live `jobflow` database. Use it only during an actual recovery event after confirming the correct backup.

From the JobFlow project directory:

```bash
cd ~/homelab/saas/jobflow
```

Select the backup to restore:

```bash
RESTORE_FILE="backups/jobflow-YYYYMMDD-HHMMSS.dump"
```

Stop application access while keeping PostgreSQL running:

```bash
docker-compose stop jobflow-web jobflow-api
```

When the current database is still readable, create an emergency pre-restore backup:

```bash
EMERGENCY_BACKUP="backups/jobflow-pre-restore-$(date '+%Y%m%d-%H%M%S').dump"

docker exec jobflow-db pg_dump \
  -U jobflow \
  -d jobflow \
  -Fc \
  > "$EMERGENCY_BACKUP"
```

Verify the selected recovery archive before making destructive database changes:

```bash
docker exec -i jobflow-db pg_restore \
  --list \
  < "$RESTORE_FILE" \
  > /dev/null
```

Terminate any remaining connections to the production database:

```bash
docker exec jobflow-db psql -U jobflow -d postgres -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'jobflow'
  AND pid <> pg_backend_pid();
"
```

Drop and recreate the production database:

```bash
docker exec jobflow-db psql -U jobflow -d postgres \
  -c "DROP DATABASE jobflow;"

docker exec jobflow-db psql -U jobflow -d postgres \
  -c "CREATE DATABASE jobflow OWNER jobflow;"
```

Restore the selected backup:

```bash
docker exec -i jobflow-db pg_restore \
  -U jobflow \
  -d jobflow \
  < "$RESTORE_FILE"
```

Run the current database migrations:

```bash
docker-compose run --rm jobflow-migrate
```

Start the API and frontend:

```bash
docker-compose start jobflow-api jobflow-web
```

## Post-Recovery Validation

After the API and frontend have been started, verify the container state:

```bash
docker-compose ps -a
```

Expected steady state:

```text
jobflow-db       healthy
jobflow-api      healthy
jobflow-web      healthy
```

The one-shot migration command must have completed successfully before the API is started. When `docker-compose run --rm jobflow-migrate` is used, its temporary container is removed after completion and may not appear in `docker-compose ps -a`.

Verify the public frontend:

```bash
curl -I https://jobflow.fieldlookers.com/
```

Expected result:

```text
HTTP/2 200
Content-Type: text/html
```

Verify the public API health endpoint:

```bash
curl -i https://jobflow.fieldlookers.com/api/v1/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "jobflow-api"
}
```

Then sign in through the browser and verify representative production data, including:

* Customers
* Jobs
* Schedules
* Estimates
* Invoices
* Payments

Confirm that the Uptime Kuma monitors for the JobFlow frontend and API return to `Up`.

If any of these checks fail, recovery should not be considered complete.

## Recovery Completion Criteria

Production recovery is complete only when:

* PostgreSQL is healthy.
* The restored database is accessible.
* Current migrations have completed successfully.
* JobFlow API is healthy.
* JobFlow frontend is healthy.
* Public HTTPS frontend access returns HTTP 200.
* Public API health returns HTTP 200.
* Authentication succeeds.
* Representative application data is present.
* Monitoring has returned to normal.

---
# OpenMediaVault Off-Host Backup Recovery

## Backup Architecture

JobFlow database backups are stored in two locations:

```text
PostgreSQL
    |
    v
Local JobFlow backup
/home/rflmorel/homelab/saas/jobflow/backups
    |
    v
OpenMediaVault off-host copy
/srv/dev-disk-by-uuid-b3f81412-c245-4670-9fc1-1d0c80c74fe5/Data/jobflow-backups
```

The OpenMediaVault copy is transferred using a dedicated SSH key:

```text
~/.ssh/jobflow_omv_backup
```

The backup process uses key-only SSH authentication with password fallback disabled.

Both local and OpenMediaVault backups use a 7-day retention policy.

## Recover a Backup from OpenMediaVault

If the local JobFlow backup directory is unavailable, identify the available backups on OpenMediaVault:

```bash
ssh -i ~/.ssh/jobflow_omv_backup \
  -o IdentitiesOnly=yes \
  -o BatchMode=yes \
  Rafael@192.168.1.137 \
  'ls -1lht /srv/dev-disk-by-uuid-b3f81412-c245-4670-9fc1-1d0c80c74fe5/Data/jobflow-backups/'
```

Select the backup to recover and copy it back to the JobFlow server:

```bash
scp \
  -i ~/.ssh/jobflow_omv_backup \
  -o IdentitiesOnly=yes \
  -o BatchMode=yes \
  Rafael@192.168.1.137:/srv/dev-disk-by-uuid-b3f81412-c245-4670-9fc1-1d0c80c74fe5/Data/jobflow-backups/jobflow-YYYYMMDD-HHMMSS.dump \
  ~/homelab/saas/jobflow/backups/
```

Verify that the recovered file exists locally:

```bash
ls -lh ~/homelab/saas/jobflow/backups/
```

Before restoring the recovered backup, validate the archive:

```bash
docker exec -i jobflow-db pg_restore \
  --list \
  < ~/homelab/saas/jobflow/backups/jobflow-YYYYMMDD-HHMMSS.dump \
  > /dev/null
```

The recovered backup can then be used with the normal JobFlow restore-validation or production disaster-recovery procedure.

## Backup Integrity Validation

A local JobFlow backup and its corresponding OpenMediaVault copy were compared using SHA-256.

The checksums matched exactly, confirming that the off-host transfer preserved the backup file byte-for-byte.

## Recovery Principle

OpenMediaVault provides a second copy of JobFlow database backups outside the Ubuntu Server VM.

This protects against loss of the local JobFlow backup directory or failure of the Ubuntu VM storage.

OpenMediaVault is still part of the same physical homelab environment, so it should be treated as off-host backup protection rather than full geographic off-site disaster recovery.

## Canonical migration ownership during recovery

The authoritative migration graph is assembled by
`backend/scripts/platform_alembic.py`. Shared and historical platform
revisions live under
`backend/app/platform/migrations/versions/`, while active products own
their revisions under
`backend/app/products/<product>/migrations/versions/`.

Do not restore or recreate the removed `backend/migrations/` duplicate
tree. Do not rename, copy or rewrite an applied revision. After a
database restore, use the platform wrapper to compare `current` and
`heads`, then run its migration drift check.
