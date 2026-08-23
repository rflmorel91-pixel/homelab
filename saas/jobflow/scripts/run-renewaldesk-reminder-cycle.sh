#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.."
  pwd
)"

RUNTIME_DIR="${PROJECT_DIR}/runtime"
LOCK_FILE="${RUNTIME_DIR}/renewaldesk-reminders.lock"
SUCCESS_FILE="${RUNTIME_DIR}/last-reminder-success"
FAILURE_FILE="${RUNTIME_DIR}/last-reminder-failure"
RESULT_FILE="${RUNTIME_DIR}/last-reminder-cycle.json"

mkdir -p "${RUNTIME_DIR}"

exec 9>"${LOCK_FILE}"

if ! flock -n 9; then
  printf '%s\n'     '{"status":"skipped","reason":"already_running"}'
  exit 0
fi

worker_arguments=()

if [[ "${1:-}" == "--dry-run" ]]; then
  worker_arguments+=("--dry-run")
  shift
fi

if [[ "$#" -ne 0 ]]; then
  printf 'Unsupported argument: %s\n'     "$1"     >&2
  exit 2
fi

if output="$(
  docker exec     jobflow-api     python     scripts/run_renewaldesk_reminders.py     "${worker_arguments[@]}"     2>&1
)"; then
  completed_at="$(
    date -u +%Y-%m-%dT%H:%M:%SZ
  )"

  printf '%s\n' "${output}"

  printf '%s\n' "${completed_at}"     > "${SUCCESS_FILE}.tmp"
  mv     "${SUCCESS_FILE}.tmp"     "${SUCCESS_FILE}"

  printf '%s\n' "${output}"     > "${RESULT_FILE}.tmp"
  mv     "${RESULT_FILE}.tmp"     "${RESULT_FILE}"

  rm -f "${FAILURE_FILE}"

  exit 0
else
  status=$?
  failed_at="$(
    date -u +%Y-%m-%dT%H:%M:%SZ
  )"

  printf '%s\n' "${output}" >&2

  printf '%s exit=%s\n'     "${failed_at}"     "${status}"     > "${FAILURE_FILE}.tmp"
  mv     "${FAILURE_FILE}.tmp"     "${FAILURE_FILE}"

  exit "${status}"
fi
