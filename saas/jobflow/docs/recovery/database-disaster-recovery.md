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
