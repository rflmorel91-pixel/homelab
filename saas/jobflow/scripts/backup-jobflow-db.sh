#!/usr/bin/env bash

set -euo pipefail
umask 077

PROJECT_DIR="$HOME/homelab/saas/jobflow"
BACKUP_DIR="$PROJECT_DIR/backups"
TIMESTAMP="$(date '+%Y%m%d-%H%M%S')"
BACKUP_FILE="$BACKUP_DIR/jobflow-$TIMESTAMP.dump"

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

echo "Backup created and verified: $BACKUP_FILE"
