#!/bin/sh
set -eu

PIP_AUDIT_VERSION="2.10.1"
GITLEAKS_IMAGE="zricethezav/gitleaks:v8.30.0"
TRIVY_IMAGE="aquasec/trivy:0.74.0"

SCRIPT_DIRECTORY=$(
  CDPATH= cd -- "$(dirname -- "$0")" && pwd
)
JOBFLOW_ROOT=$(
  CDPATH= cd -- "$SCRIPT_DIRECTORY/.." && pwd
)
REPOSITORY_ROOT=$(
  git -C "$JOBFLOW_ROOT" rev-parse --show-toplevel
)

test -z "$(
  git -C "$REPOSITORY_ROOT" status --porcelain
)" || {
  printf '%s\n' \
    "Repository must be clean for security scanning." >&2
  exit 1
}

test "$(
  git -C "$REPOSITORY_ROOT" \
    rev-parse --is-shallow-repository
)" = "false" || {
  printf '%s\n' \
    "Full Git history is required for secret scanning." >&2
  exit 1
}

command -v docker >/dev/null
command -v git >/dev/null
command -v python3 >/dev/null

CURRENT_COMMIT=$(
  git -C "$REPOSITORY_ROOT" rev-parse HEAD
)
SHORT_COMMIT=$(
  git -C "$REPOSITORY_ROOT" rev-parse --short=12 HEAD
)

API_IMAGE="fieldlookers-security-api:$SHORT_COMMIT"
WEB_IMAGE="fieldlookers-security-web:$SHORT_COMMIT"

TEMPORARY_ROOT=$(mktemp -d)
SNAPSHOT_ROOT="$TEMPORARY_ROOT/tracked-tree"
REPORT_ROOT="$TEMPORARY_ROOT/reports"
TRIVY_CACHE="$TEMPORARY_ROOT/trivy-cache"

mkdir -p \
  "$SNAPSHOT_ROOT" \
  "$REPORT_ROOT" \
  "$TRIVY_CACHE"

chmod 700 \
  "$TEMPORARY_ROOT" \
  "$SNAPSHOT_ROOT" \
  "$REPORT_ROOT" \
  "$TRIVY_CACHE"

cleanup() {
  rm -rf "$TEMPORARY_ROOT"
}
trap cleanup EXIT HUP INT TERM

printf '\n===== SECURITY SCAN IDENTITY =====\n'
printf 'Repository: %s\n' "$REPOSITORY_ROOT"
printf 'Commit: %s\n' "$CURRENT_COMMIT"
printf 'pip-audit: %s\n' "$PIP_AUDIT_VERSION"
printf 'Gitleaks: %s\n' "$GITLEAKS_IMAGE"
printf 'Trivy: %s\n' "$TRIVY_IMAGE"

printf '\n===== PINNED PYTHON DEPENDENCIES =====\n'
python3 - "$JOBFLOW_ROOT/backend/requirements.txt" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
requirements = []

for number, raw_line in enumerate(
    path.read_text().splitlines(),
    start=1,
):
    line = raw_line.strip()

    if not line or line.startswith("#"):
        continue

    if "==" not in line:
        raise SystemExit(
            f"{path}:{number}: dependency is not pinned with =="
        )

    name, version = line.split("==", 1)

    if not name.strip() or not version.strip():
        raise SystemExit(
            f"{path}:{number}: invalid dependency pin"
        )

    if not re.fullmatch(
        r"[A-Za-z0-9_.-]+(?:\[[A-Za-z0-9_,.-]+\])?",
        name.strip(),
    ):
        raise SystemExit(
            f"{path}:{number}: unsupported requirement name"
        )

    requirements.append(line)

if not requirements:
    raise SystemExit("No pinned dependencies found")

print(f"Validated {len(requirements)} pinned dependencies.")
PY

printf '\n===== DEPENDENCY VULNERABILITY SCAN =====\n'
docker run \
  --rm \
  --volume \
    "$JOBFLOW_ROOT/backend/requirements.txt:/scan/requirements.txt:ro" \
  python:3.14-slim \
  sh -ceu '
    python -m pip install \
      --disable-pip-version-check \
      --no-cache-dir \
      "pip-audit=='"$PIP_AUDIT_VERSION"'" \
      >/dev/null

    python -m pip_audit \
      --no-deps \
      --disable-pip \
      --strict \
      --requirement /scan/requirements.txt
  '

printf '\n===== TRACKED SOURCE SNAPSHOT =====\n'
git -C "$REPOSITORY_ROOT" \
  archive \
  --format=tar \
  HEAD |
tar -xf - -C "$SNAPSHOT_ROOT"

printf 'Tracked commit snapshot created.\n'

printf '\n===== TRACKED SOURCE SECRET SCAN =====\n'
docker run \
  --rm \
  --volume "$SNAPSHOT_ROOT:/snapshot:ro" \
  "$GITLEAKS_IMAGE" \
  dir \
  /snapshot \
  --redact \
  --no-banner \
  --exit-code 1

printf '\n===== GIT HISTORY SECRET SCAN =====\n'
docker run \
  --rm \
  --volume "$REPOSITORY_ROOT:/repo:ro" \
  "$GITLEAKS_IMAGE" \
  git \
  /repo \
  --redact \
  --no-banner \
  --exit-code 1

printf '\n===== BUILD API SCAN IMAGE =====\n'
docker build \
  --pull \
  --tag "$API_IMAGE" \
  "$JOBFLOW_ROOT/backend"

printf '\n===== BUILD WEB SCAN IMAGE =====\n'
docker build \
  --pull \
  --tag "$WEB_IMAGE" \
  "$JOBFLOW_ROOT/nginx"

USER_ID_GROUP_ID="$(id -u):$(id -g)"
DOCKER_GROUP_ID=$(
  stat -c %g /var/run/docker.sock
)

scan_image() {
  image_label=$1
  image_name=$2
  report_name=$3

  printf '\n===== SCAN %s IMAGE =====\n' "$image_label"

  docker run \
    --rm \
    --user "$USER_ID_GROUP_ID" \
    --group-add "$DOCKER_GROUP_ID" \
    --volume \
      /var/run/docker.sock:/var/run/docker.sock \
    --volume "$TRIVY_CACHE:/cache" \
    --volume "$REPORT_ROOT:/reports" \
    "$TRIVY_IMAGE" \
    image \
    --cache-dir /cache \
    --scanners vuln \
    --severity HIGH,CRITICAL \
    --no-progress \
    --format json \
    --output "/reports/$report_name" \
    "$image_name"
}

scan_image API "$API_IMAGE" api.json
scan_image WEB "$WEB_IMAGE" web.json

printf '\n===== CONTAINER FINDING POLICY =====\n'
python3 \
  "$SCRIPT_DIRECTORY/validate-container-security-findings.py" \
  --exceptions \
  "$JOBFLOW_ROOT/security/container-vulnerability-exceptions.json" \
  --report "api=$REPORT_ROOT/api.json" \
  --report "web=$REPORT_ROOT/web.json"

printf '\nSECURITY SCANS PASSED\n'
printf 'Commit: %s\n' "$CURRENT_COMMIT"
