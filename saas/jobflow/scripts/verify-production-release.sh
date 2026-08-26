#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  verify-production-release.sh \
    --deployed-commit SHA \
    --rollback-commit SHA \
    --cookie-file PATH

Options:
  --base-url URL       Public platform URL.
  --allow-dirty        Development-only verification of uncommitted work.
  --help               Show this help.

Required environment:
  POSTGRES_PASSWORD

The cookie file must be created with:
  scripts/create-release-smoke-session.py
EOF
}

BASE_URL="https://jobflow.fieldlookers.com"
DEPLOYED_COMMIT=""
ROLLBACK_COMMIT=""
COOKIE_FILE=""
ALLOW_DIRTY="false"

while test "$#" -gt 0
do
  case "$1" in
    --base-url)
      test "$#" -ge 2 || {
        printf 'Missing value for --base-url\n' >&2
        exit 2
      }
      BASE_URL="${2%/}"
      shift 2
      ;;
    --deployed-commit)
      test "$#" -ge 2 || {
        printf 'Missing value for --deployed-commit\n' >&2
        exit 2
      }
      DEPLOYED_COMMIT="$2"
      shift 2
      ;;
    --rollback-commit)
      test "$#" -ge 2 || {
        printf 'Missing value for --rollback-commit\n' >&2
        exit 2
      }
      ROLLBACK_COMMIT="$2"
      shift 2
      ;;
    --cookie-file)
      test "$#" -ge 2 || {
        printf 'Missing value for --cookie-file\n' >&2
        exit 2
      }
      COOKIE_FILE="$2"
      shift 2
      ;;
    --allow-dirty)
      ALLOW_DIRTY="true"
      shift
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

test -n "${POSTGRES_PASSWORD:-}" || {
  printf 'POSTGRES_PASSWORD is required\n' >&2
  exit 2
}

test -n "$DEPLOYED_COMMIT" || {
  printf -- '--deployed-commit is required\n' >&2
  exit 2
}

test -n "$ROLLBACK_COMMIT" || {
  printf -- '--rollback-commit is required\n' >&2
  exit 2
}

test -n "$COOKIE_FILE" || {
  printf -- '--cookie-file is required\n' >&2
  exit 2
}

for command in \
  curl \
  docker \
  gh \
  git \
  python3
do
  command -v "$command" >/dev/null || {
    printf 'Required command not found: %s\n' "$command" >&2
    exit 2
  }
done

SCRIPT_DIR="$(
  cd "$(
    dirname "${BASH_SOURCE[0]}"
  )"
  pwd
)"

JOBFLOW_ROOT="$(
  cd "$SCRIPT_DIR/.."
  pwd
)"

REPOSITORY_ROOT="$(
  git -C "$JOBFLOW_ROOT" rev-parse --show-toplevel
)"

BACKEND_ROOT="$JOBFLOW_ROOT/backend"
PYTHON="$BACKEND_ROOT/.venv/bin/python"
COOKIE_FILE="$(
  python3 -c '
from pathlib import Path
import sys
print(Path(sys.argv[1]).expanduser().resolve())
' "$COOKIE_FILE"
)"

test -x "$PYTHON" || {
  printf 'Backend virtual environment is unavailable: %s\n' \
    "$PYTHON" >&2
  exit 2
}

test -f "$COOKIE_FILE" || {
  printf 'Cookie file does not exist: %s\n' "$COOKIE_FILE" >&2
  exit 2
}

cookie_mode="$(
  stat -c '%a' "$COOKIE_FILE"
)"

case "$cookie_mode" in
  600|400)
    ;;
  *)
    printf \
      'Cookie file must have mode 600 or 400; found %s\n' \
      "$cookie_mode" \
      >&2
    exit 2
    ;;
esac

CURRENT_COMMIT="$(
  git -C "$REPOSITORY_ROOT" rev-parse HEAD
)"

DEPLOYED_COMMIT="$(
  git -C "$REPOSITORY_ROOT" rev-parse "$DEPLOYED_COMMIT^{commit}"
)"

ROLLBACK_COMMIT="$(
  git -C "$REPOSITORY_ROOT" rev-parse "$ROLLBACK_COMMIT^{commit}"
)"

test "$DEPLOYED_COMMIT" = "$CURRENT_COMMIT" || {
  printf \
    'Deployed commit %s does not match current HEAD %s\n' \
    "$DEPLOYED_COMMIT" \
    "$CURRENT_COMMIT" \
    >&2
  exit 1
}

test "$ROLLBACK_COMMIT" != "$DEPLOYED_COMMIT" || {
  printf 'Rollback commit must differ from deployed commit\n' >&2
  exit 1
}

git -C "$REPOSITORY_ROOT" \
  merge-base \
  --is-ancestor \
  "$ROLLBACK_COMMIT" \
  "$DEPLOYED_COMMIT" \
  || {
    printf \
      'Rollback commit is not an ancestor of deployed commit\n' \
      >&2
    exit 1
  }

if test "$ALLOW_DIRTY" != "true"
then
  test -z "$(
    git -C "$REPOSITORY_ROOT" status --porcelain
  )" || {
    printf 'Repository must be clean for release verification\n' >&2
    exit 1
  }

  git -C "$REPOSITORY_ROOT" fetch origin main --quiet

  ORIGIN_COMMIT="$(
    git -C "$REPOSITORY_ROOT" rev-parse origin/main
  )"

  test "$CURRENT_COMMIT" = "$ORIGIN_COMMIT" || {
    printf \
      'Current HEAD does not match origin/main\n' \
      >&2
    exit 1
  }
fi

printf '\n===== RELEASE IDENTITY =====\n'
printf 'Repository: %s\n' "$REPOSITORY_ROOT"
printf 'Tested commit: %s\n' "$CURRENT_COMMIT"
printf 'Deployed commit: %s\n' "$DEPLOYED_COMMIT"
printf 'Rollback commit: %s\n' "$ROLLBACK_COMMIT"
printf 'Base URL: %s\n' "$BASE_URL"

printf '\n===== SOURCE VALIDATION =====\n'
git -C "$REPOSITORY_ROOT" diff --check

test_database_exists="$(
  docker exec jobflow-db \
    psql -U jobflow -d postgres -tAc \
    "SELECT 1 FROM pg_database WHERE datname = 'jobflow_test';"
)"

test "$test_database_exists" = "1" || {
  printf 'Dedicated jobflow_test database does not exist\n' >&2
  exit 1
}

TEST_DATABASE_URL="postgresql+psycopg://jobflow:${POSTGRES_PASSWORD}@127.0.0.1:5433/jobflow_test"
TEST_JWT_SECRET="jobflow-release-verification-secret-at-least-32-bytes"

printf '\n===== TEST DATABASE MIGRATION =====\n'
(
  cd "$BACKEND_ROOT"

  POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
  DATABASE_URL="$TEST_DATABASE_URL" \
  JWT_SECRET="$TEST_JWT_SECRET" \
  "$PYTHON" \
    scripts/platform_alembic.py \
    upgrade \
    head
)

printf '\n===== FULL BACKEND TEST SUITE =====\n'
(
  cd "$BACKEND_ROOT"

  POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
  DATABASE_URL="$TEST_DATABASE_URL" \
  JWT_SECRET="$TEST_JWT_SECRET" \
  "$PYTHON" \
    -m pytest \
    -q
)

printf '\n===== MIGRATION DRIFT CHECK =====\n'
(
  cd "$BACKEND_ROOT"

  POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
  DATABASE_URL="$TEST_DATABASE_URL" \
  JWT_SECRET="$TEST_JWT_SECRET" \
  "$PYTHON" \
    scripts/platform_alembic.py \
    check
)

printf '\n===== INSTALLED PRODUCT VALIDATION =====\n'
(
  cd "$BACKEND_ROOT"

  POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
  DATABASE_URL="$TEST_DATABASE_URL" \
  JWT_SECRET="$TEST_JWT_SECRET" \
  "$PYTHON" \
    scripts/validate_product.py
)

printf '\n===== AUTHORITATIVE CI =====\n'
CI_RECORD="$(
  gh run list \
    --repo rflmorel91-pixel/homelab \
    --workflow "SaaS Platform CI" \
    --commit "$CURRENT_COMMIT" \
    --limit 1 \
    --json databaseId,headSha,status,conclusion,url \
    --jq '.[0] // empty'
)"

test -n "$CI_RECORD" || {
  printf 'No SaaS Platform CI run found for current commit\n' >&2
  exit 1
}

CI_STATUS="$(
  python3 -c '
import json
import sys
print(json.load(sys.stdin)["status"])
' <<<"$CI_RECORD"
)"

CI_CONCLUSION="$(
  python3 -c '
import json
import sys
print(json.load(sys.stdin)["conclusion"])
' <<<"$CI_RECORD"
)"

CI_HEAD_SHA="$(
  python3 -c '
import json
import sys
print(json.load(sys.stdin)["headSha"])
' <<<"$CI_RECORD"
)"

CI_RUN_ID="$(
  python3 -c '
import json
import sys
print(json.load(sys.stdin)["databaseId"])
' <<<"$CI_RECORD"
)"

CI_URL="$(
  python3 -c '
import json
import sys
print(json.load(sys.stdin)["url"])
' <<<"$CI_RECORD"
)"

test "$CI_STATUS" = "completed" || {
  printf 'CI is not complete\n' >&2
  exit 1
}

test "$CI_CONCLUSION" = "success" || {
  printf 'CI did not succeed\n' >&2
  exit 1
}

test "$CI_HEAD_SHA" = "$CURRENT_COMMIT" || {
  printf 'CI commit does not match current commit\n' >&2
  exit 1
}

printf 'CI run: %s\n' "$CI_RUN_ID"
printf 'CI URL: %s\n' "$CI_URL"
printf 'CI conclusion: %s\n' "$CI_CONCLUSION"

printf '\n===== CONTAINER HEALTH =====\n'
for container in \
  jobflow-db \
  jobflow-api \
  jobflow-web
do
  health="$(
    docker inspect \
      --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' \
      "$container"
  )"

  printf '%s: %s\n' "$container" "$health"

  test "$health" = "healthy" || {
    printf 'Container is not healthy: %s\n' "$container" >&2
    exit 1
  }
done

printf '\n===== PRODUCTION MIGRATION =====\n'
PRODUCTION_CURRENT="$(
  docker exec jobflow-api \
    python scripts/platform_alembic.py current
)"

PRODUCTION_HEADS="$(
  docker exec jobflow-api \
    python scripts/platform_alembic.py heads
)"

printf 'Current: %s\n' "$PRODUCTION_CURRENT"
printf 'Heads: %s\n' "$PRODUCTION_HEADS"

test "$PRODUCTION_CURRENT" = "$PRODUCTION_HEADS" || {
  printf 'Production migration is not at the supported head\n' >&2
  exit 1
}

smoke_status() {
  expected_status="$1"
  url="$2"
  description="$3"
  shift 3

  actual_status="$(
    curl \
      --silent \
      --show-error \
      --output /dev/null \
      --write-out '%{http_code}' \
      --max-time 20 \
      "$@" \
      "$url"
  )"

  printf '%s: %s\n' "$description" "$actual_status"

  test "$actual_status" = "$expected_status" || {
    printf \
      'Smoke check failed for %s: expected %s, received %s\n' \
      "$description" \
      "$expected_status" \
      "$actual_status" \
      >&2
    exit 1
  }
}

printf '\n===== PUBLIC SMOKE CHECKS =====\n'
smoke_status 200 "$BASE_URL/" "Platform landing"
smoke_status 200 "$BASE_URL/renewaldesk" "RenewalDesk landing"
smoke_status 200 "$BASE_URL/workflow-automation" "Workflow Automation landing"
smoke_status 200 "$BASE_URL/admin" "Administration page"
smoke_status 200 "$BASE_URL/api/v1/health" "API health"

printf '\n===== ACCESS-CONTROL SMOKE CHECK =====\n'
smoke_status \
  401 \
  "$BASE_URL/api/v1/admin/overview" \
  "Unauthenticated administration API"

printf '\n===== AUTHENTICATED SMOKE CHECK =====\n'
smoke_status \
  200 \
  "$BASE_URL/api/v1/admin/overview" \
  "Authenticated administration API" \
  --cookie "$COOKIE_FILE"

if test "$ALLOW_DIRTY" = "true"
then
  printf '\nDEVELOPMENT VERIFICATION PASSED\n'
  printf '%s\n' \
    'No production release evidence was created because --allow-dirty was used.'
  exit 0
fi

printf '\n===== RELEASE EVIDENCE =====\n'
VERIFIED_AT="$(
  date -u +'%Y-%m-%dT%H:%M:%SZ'
)"

MIGRATION_HEAD="$(
  printf '%s\n' "$PRODUCTION_HEADS" \
    | awk '{print $1}'
)"

EVIDENCE_DIRECTORY="$JOBFLOW_ROOT/runtime/release-verifications"
EVIDENCE_NAME="$(
  date -u +'%Y%m%dT%H%M%SZ'
)-$(
  git -C "$REPOSITORY_ROOT" rev-parse --short=12 HEAD
).json"

mkdir -p "$EVIDENCE_DIRECTORY"

CURRENT_COMMIT="$CURRENT_COMMIT" \
DEPLOYED_COMMIT="$DEPLOYED_COMMIT" \
ROLLBACK_COMMIT="$ROLLBACK_COMMIT" \
VERIFIED_AT="$VERIFIED_AT" \
BASE_URL="$BASE_URL" \
CI_RUN_ID="$CI_RUN_ID" \
CI_URL="$CI_URL" \
MIGRATION_HEAD="$MIGRATION_HEAD" \
EVIDENCE_PATH="$EVIDENCE_DIRECTORY/$EVIDENCE_NAME" \
python3 - <<'PY'
import json
import os
from pathlib import Path

evidence = {
    "status": "verified",
    "verified_at": os.environ["VERIFIED_AT"],
    "repository": "rflmorel91-pixel/homelab",
    "tested_commit": os.environ["CURRENT_COMMIT"],
    "deployed_commit": os.environ["DEPLOYED_COMMIT"],
    "rollback_commit": os.environ["ROLLBACK_COMMIT"],
    "base_url": os.environ["BASE_URL"],
    "ci": {
        "run_id": int(os.environ["CI_RUN_ID"]),
        "url": os.environ["CI_URL"],
        "conclusion": "success",
    },
    "migration_head": os.environ["MIGRATION_HEAD"],
    "checks": {
        "source_clean": True,
        "full_backend_tests": "passed",
        "migration_drift": "passed",
        "product_validation": "passed",
        "containers": "healthy",
        "public_smoke": "passed",
        "access_control_smoke": "passed",
        "authenticated_smoke": "passed",
    },
}

path = Path(os.environ["EVIDENCE_PATH"])
temporary = path.with_suffix(".tmp")

temporary.write_text(
    json.dumps(
        evidence,
        indent=2,
        sort_keys=True,
    )
    + "\n"
)

temporary.replace(path)

latest = path.parent.parent / "last-release-verification.json"
latest_temporary = latest.with_suffix(".tmp")
latest_temporary.write_text(path.read_text())
latest_temporary.replace(latest)

print(path)
print(latest)
PY

printf '\nRELEASE VERIFIED\n'
printf 'Tested commit: %s\n' "$CURRENT_COMMIT"
printf 'Deployed commit: %s\n' "$DEPLOYED_COMMIT"
printf 'Rollback commit: %s\n' "$ROLLBACK_COMMIT"
printf 'Verified at: %s\n' "$VERIFIED_AT"
