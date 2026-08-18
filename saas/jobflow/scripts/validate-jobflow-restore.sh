#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$HOME/homelab/saas/jobflow"
BACKUP_DIR="$PROJECT_DIR/backups"
RESTORE_DB="jobflow_restore_test"
cleanup() {
  docker exec jobflow-db psql -U jobflow -d postgres \
    -c "DROP DATABASE IF EXISTS $RESTORE_DB;" \
    > /dev/null 2>&1 || true
}

trap cleanup EXIT

LATEST_BACKUP="$(ls -1t "$BACKUP_DIR"/jobflow-*.dump | head -1)"

echo "Validating restore from: $LATEST_BACKUP"

docker exec jobflow-db psql -U jobflow -d postgres \
  -c "DROP DATABASE IF EXISTS $RESTORE_DB;"

docker exec jobflow-db psql -U jobflow -d postgres \
  -c "CREATE DATABASE $RESTORE_DB OWNER jobflow;"

docker exec -i jobflow-db pg_restore \
  -U jobflow \
  -d "$RESTORE_DB" \
  --clean \
  --if-exists \
  < "$LATEST_BACKUP"

for table in \
  customers jobs estimates schedules invoices payments \
  users tenants tenant_memberships
do
  live_count="$(
    docker exec jobflow-db psql -U jobflow -d jobflow \
      -Atc "SELECT count(*) FROM $table;"
  )"

  restore_count="$(
    docker exec jobflow-db psql -U jobflow -d "$RESTORE_DB" \
      -Atc "SELECT count(*) FROM $table;"
  )"

  if [[ "$live_count" != "$restore_count" ]]; then
    echo "Mismatch in $table: live=$live_count restore=$restore_count" >&2
    exit 1
  fi

  echo "$table=$restore_count"
done

echo "Restore validation successful"
