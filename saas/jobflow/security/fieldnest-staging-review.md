# FieldNest staging security review ? 2026-11-03

Status: CI and local staging verification passed. PR #154 remains draft pending review.

## Verified in existing staging
- API and migration containers run as UID/GID 10001.
- Read-only root filesystem, restricted /tmp, all capabilities dropped.
- No-new-privileges enabled; API capability sets zero; seccomp active.
- Database, migration and product readiness passed.
- Synthetic work-order creation and completion passed.

## Alpine replacement candidate
- Multi-stage Python 3.14 Alpine image with compiled psycopg 3.3.4.
- API imports and password hashing passed under restricted execution.
- Migrations and API readiness passed against a disposable PostgreSQL database.
- Full backend suite: 1005 passed, 1 deprecation warning.
- Tests used an LF-preserving source snapshot.
- Trivy 0.74.0 and 0.76.1 reported zero HIGH/CRITICAL findings.
- Removed 40 obsolete Debian API image exceptions; none remain.
- Test configuration accepts an explicit TEST_DATABASE_URL.

## CI and local staging verification
- All six CI checks passed for commit 483caf2, including Security Scanning.
- Local staging now runs Alpine 3.24.3; database, migrations and product readiness passed.
- Owner sign-in and existing portfolio data verified.
- Synthetic work-order creation, vendor assignment, completion and persistence after refresh verified.
- No production deployment or risk exception approval is recorded.
