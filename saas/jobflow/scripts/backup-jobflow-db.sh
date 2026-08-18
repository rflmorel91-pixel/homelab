#!/usr/bin/env bash

set -euo pipefail
umask 077

PROJECT_DIR="$HOME/homelab/saas/jobflow"
BACKUP_DIR="$PROJECT_DIR/backups"
TIMESTAMP="$(date '+%Y%m%d-%H%M%S')"
BACKUP_FILE="$BACKUP_DIR/jobflow-$TIMESTAMP.dump"
STATUS_FILE="$PROJECT_DIR/runtime/last-backup-success"

mkdir -p "$BACKUP_DIR"

docker exec jobflow-db pg_dump \
  -U jobflow \
  -d jobflow \
  -Fc \
  > "$BACKUP_FILE"

docker exec -i jobflow-db pg_restore \
  --list \
  < "$BACKUP_FILE" \
  > /dev/null

find "$BACKUP_DIR" \
  -type f \
  -name 'jobflow-*.dump' \
  -mtime +7 \
  -delete

date --iso-8601=seconds > "$STATUS_FILE"
if [[ -n "${UPTIME_KUMA_PUSH_URL:-}" ]]; then
  curl -fsS --retry 3 --max-time 10 "$UPTIME_KUMA_PUSH_URL" > /dev/null
fi

echo "Backup created and verified: $BACKUP_FILE"
