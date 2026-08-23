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

METRICS_WRITER="$(
  printf '%s' \
    "${PROJECT_DIR}/scripts/"\
"write-renewaldesk-reminder-metrics.py"
)"

METRICS_FILE="$(
  printf '%s' \
    "${FIELDLOOKERS_REMINDER_METRICS_FILE:-"\
"/home/rflmorel/homelab/docker/monitoring/"\
"node-exporter-textfiles/"\
"fieldlookers-renewaldesk-reminders.prom}"
)"

mkdir -p "${RUNTIME_DIR}"

publish_metrics() {
  local status="$1"
  local exit_status="$2"
  local attempt_timestamp

  attempt_timestamp="$(
    date -u +%s
  )"

  if ! python3 \
    "${METRICS_WRITER}" \
    --status "${status}" \
    --exit-status "${exit_status}" \
    --attempt-timestamp "${attempt_timestamp}" \
    --success-file "${SUCCESS_FILE}" \
    --failure-file "${FAILURE_FILE}" \
    --result-file "${RESULT_FILE}" \
    --output "${METRICS_FILE}"
  then
    printf '%s\n' \
      "Warning: reminder metrics could not be published." \
      >&2
  fi
}

exec 9>"${LOCK_FILE}"

if ! flock -n 9; then
  printf '%s\n' \
    '{"status":"skipped","reason":"already_running"}'
  exit 0
fi

worker_arguments=()
dry_run="false"

if [[ "${1:-}" == "--dry-run" ]]; then
  worker_arguments+=("--dry-run")
  dry_run="true"
  shift
fi

if [[ "$#" -ne 0 ]]; then
  printf 'Unsupported argument: %s\n' \
    "$1" \
    >&2
  exit 2
fi

if output="$(
  docker exec \
    jobflow-api \
    python \
    scripts/run_renewaldesk_reminders.py \
    "${worker_arguments[@]}" \
    2>&1
)"; then
  printf '%s\n' "${output}"

  if [[ "${dry_run}" == "true" ]]; then
    exit 0
  fi

  completed_at="$(
    date -u +%Y-%m-%dT%H:%M:%SZ
  )"

  printf '%s\n' "${completed_at}" \
    > "${SUCCESS_FILE}.tmp"
  mv \
    "${SUCCESS_FILE}.tmp" \
    "${SUCCESS_FILE}"

  printf '%s\n' "${output}" \
    > "${RESULT_FILE}.tmp"
  mv \
    "${RESULT_FILE}.tmp" \
    "${RESULT_FILE}"

  rm -f "${FAILURE_FILE}"

  publish_metrics "success" 0

  exit 0
else
  status=$?

  printf '%s\n' "${output}" >&2

  if [[ "${dry_run}" == "true" ]]; then
    exit "${status}"
  fi

  failed_at="$(
    date -u +%Y-%m-%dT%H:%M:%SZ
  )"

  printf '%s exit=%s\n' \
    "${failed_at}" \
    "${status}" \
    > "${FAILURE_FILE}.tmp"
  mv \
    "${FAILURE_FILE}.tmp" \
    "${FAILURE_FILE}"

  publish_metrics "failure" "${status}"

  exit "${status}"
fi
