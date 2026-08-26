# FieldLookers Production Release Verification

Version: 1.0
Status: Active operating procedure
Last updated: 2026-08-26
Owner: FieldLookers LLC

## 1. Purpose

This procedure verifies that a specific FieldLookers commit:

- Passes the complete backend test suite
- Has no migration drift
- Contains valid installed products
- Has successful CI evidence for the exact commit
- Matches the commit represented as deployed
- Has healthy production containers
- Uses the current production migration head
- Passes public, protected, and authenticated smoke checks
- Has a documented rollback commit

A release must not be represented as verified unless the complete gate succeeds.

## 2. Supported Environment

Run the gate from the production host with:

- A clean `main` branch synchronized with `origin/main`
- The supported backend virtual environment
- The dedicated `jobflow_test` database
- Running production containers
- GitHub CLI authentication
- A temporary authenticated cookie jar
- `POSTGRES_PASSWORD` loaded into the shell

The production image intentionally excludes tests. Tests run through the host virtual environment against `jobflow_test`.

## 3. Safety Boundaries

The gate:

- Never runs tests against the production database
- Never prints `POSTGRES_PASSWORD`
- Never records credentials or authentication cookies
- Never records customer data
- Never changes the production schema
- Applies migrations only to `jobflow_test`
- Writes evidence only beneath ignored `runtime/`

Do not point the test database URL at `jobflow`.

## 4. Pre-Deployment Requirements

Confirm:

- [ ] Intended commit reviewed
- [ ] Rollback commit selected
- [ ] Database-impacting changes reviewed
- [ ] Backup and recovery plan current
- [ ] Repository clean and pushed
- [ ] CI succeeded for the exact commit

Deploy only from the intended commit.

## 5. Create a Temporary Smoke Session

From `saas/jobflow`, create a protected temporary file:

    cookie_file="$(mktemp)"
    chmod 600 "$cookie_file"

Create the session:

    scripts/create-release-smoke-session.py \
      --output "$cookie_file"

The helper prompts for the platform-administrator email and password without printing the password.

Delete the cookie file immediately after verification.

## 6. Load Runtime Configuration

Load the application environment without printing it:

    set -a
    . ./.env
    set +a
    test -n "$POSTGRES_PASSWORD"

## 7. Run the Complete Gate

Run:

    scripts/verify-production-release.sh \
      --deployed-commit "$(git rev-parse HEAD)" \
      --rollback-commit "[APPROVED PREVIOUS COMMIT]" \
      --cookie-file "$cookie_file"

The rollback commit must be a different ancestor of the deployed commit.

The gate stops when any required check fails.

## 8. Required Checks

The gate verifies:

1. Required tools and environment
2. Clean synchronized source
3. Tested and deployed commit identity
4. Valid rollback ancestry
5. Git whitespace validation
6. Dedicated test-database existence
7. Test migration to head
8. Full backend test suite
9. Migration drift
10. Installed-product validation
11. Successful authoritative CI
12. Database, API, and web container health
13. Production migration at head
14. Public critical routes
15. Unauthenticated administration rejection
16. Authenticated administration access
17. Non-sensitive evidence creation

## 9. Evidence

Successful verification creates:

- `runtime/release-verifications/`
- `runtime/last-release-verification.json`

Evidence records:

- Verification time and status
- Tested commit
- Deployed commit
- Rollback commit
- CI run and URL
- Migration head
- Check outcomes

Runtime evidence is excluded from source control.

Never edit a failed or incomplete record to represent success.

## 10. Cleanup

Immediately afterward:

    rm -f "$cookie_file"
    unset POSTGRES_PASSWORD
    test ! -e "$cookie_file"

## 11. Failure Procedure

If any check fails:

1. Do not describe the release as verified.
2. Stop further rollout.
3. Preserve non-sensitive failure evidence.
4. Determine whether production is affected.
5. Roll back only when schema compatibility permits.
6. Use database recovery for incompatible schema changes.
7. Correct the issue in a new commit.
8. Run CI and the complete gate again.
9. Record the final decision.

A partial pass is not release verification.

## 12. Development Mode

`--allow-dirty` exists only while developing the verification script.

Dirty-worktree evidence must not authorize a production release.

## 13. Release Record Integration

The release record must reference:

- Verified commit
- CI run
- Verification timestamp
- Migration head
- Rollback commit
- Deployment result
- Known limitations
- Security-relevant changes

A tag, healthy container, or successful CI run alone is not a complete release record.
