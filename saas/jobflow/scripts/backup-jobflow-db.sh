#!/usr/bin/env bash

set -euo pipefail
umask 077

PROJECT_DIR="$HOME/homelab/saas/jobflow"
BACKUP_DIR="$PROJECT_DIR/backups"
TIMESTAMP="$(date '+%Y%m%d-%H%M%S')"
BACKUP_FILE="$BACKUP_DIR/jobflow-$TIMESTAMP.dump"
STATUS_FILE="$PROJECT_DIR/runtime/last-backup-success"
OMV_HOST="192.168.1.137"
OMV_USER="Rafael"
OMV_KEY="$HOME/.ssh/jobflow_omv_backup"
OMV_BACKUP_DIR="/srv/dev-disk-by-uuid-b3f81412-c245-4670-9fc1-1d0c80c74fe5/Data/jobflow-backups"

report_backup_exit() {
  local backup_exit_status=$?
  trap - EXIT

  if [ "$backup_exit_status" -eq 0 ]; then
    if ! python3 "$PROJECT_DIR/scripts/report-backup-health.py" success; then
      exit 1
    fi
  else
    python3 "$PROJECT_DIR/scripts/report-backup-health.py" failure || true
  fi

  exit "$backup_exit_status"
}

trap report_backup_exit EXIT

mkdir -p "$BACKUP_DIR"

python3 "$PROJECT_DIR/scripts/create-jobflow-backup.py" \
  --project-dir "$PROJECT_DIR" \
  --output "$BACKUP_FILE"

docker exec -i jobflow-db pg_restore \
  --list \
  < "$BACKUP_FILE" \
  > /dev/null
scp \
  -i "$OMV_KEY" \
  -o IdentitiesOnly=yes \
  -o BatchMode=yes \
  "$BACKUP_FILE" \
  "$BACKUP_FILE.manifest.json" \
  "$OMV_USER@$OMV_HOST:$OMV_BACKUP_DIR/"
ssh \
  -i "$OMV_KEY" \
  -o IdentitiesOnly=yes \
  -o BatchMode=yes \
  "$OMV_USER@$OMV_HOST" \
  "find '$OMV_BACKUP_DIR' -type f \( -name 'jobflow-*.dump' -o -name 'jobflow-*.dump.manifest.json' \) -mtime +7 -delete"

find "$BACKUP_DIR" \
  -type f \
  \( -name 'jobflow-*.dump' -o -name 'jobflow-*.dump.manifest.json' \) \
  -mtime +7 \
  -delete

python3 "$PROJECT_DIR/scripts/replicate-jobflow-backup.py" \
  --project-dir "$PROJECT_DIR" \
  --upload "$BACKUP_FILE"

date --iso-8601=seconds > "$STATUS_FILE"
if [[ -n "${UPTIME_KUMA_PUSH_URL:-}" ]]; then
  curl -fsS --retry 3 --max-time 10 "$UPTIME_KUMA_PUSH_URL" > /dev/null
fi

echo "Backup created and verified: $BACKUP_FILE"
