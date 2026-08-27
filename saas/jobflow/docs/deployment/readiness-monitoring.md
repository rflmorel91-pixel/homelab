# Database-aware platform readiness

Issue #17. Owner: Rafael Morel.

## Rollout status

Source implementation and host testing completed on 2026-08-27:

- 17 standalone readiness tests passed on dellpc.
- 20 focused health/readiness tests passed against jobflow_test.
- Full backend suite: 556 tests passed.
- Migration drift check: no new upgrade operations detected.
- Docker healthcheck source now targets /api/v1/ready with a four-second
  HTTP timeout inside the existing five-second Docker timeout.
- Release verification checks both liveness and readiness.
- Release script shell syntax and Git whitespace checks passed.

Production deployment, exact-commit CI, Docker readiness verification,
external monitoring, and the complete production release gate remain pending.
No production database outage was induced during testing.

## Endpoints

| Endpoint | Purpose | Passing response | Failure |
| --- | --- | --- | --- |
| `/api/v1/health` | Existing lightweight process liveness | 200, `healthy` | Process/network failure |
| `/api/v1/ready` | Startup, database, migrations and product readiness | 200, `ready` | 503, `not_ready` |

Readiness is unauthenticated and exposes only `status`, `service`, and generic
database/migrations/products check results. It returns no revision IDs, product
names, customer data, connection strings or raw exception details. HTTP responses
use `Cache-Control: no-store`. Do not cache this route at the reverse proxy/CDN.

## Startup and dependency checks

The existing discovery and synchronization behavior is preserved. Readiness
state is published only after startup synchronization completes and cleared on
shutdown. Startup failures still abort startup; a running server without
completed readiness initialization returns 503.

Expected migration heads come from `scripts.platform_alembic.build_config()` and
Alembic `ScriptDirectory.get_heads()`, including bundled, workspace and installed
product migrations. No revision is hardcoded and readiness never runs migration
commands. The database must contain exactly that head set; empty, old, unknown
or duplicate revisions fail.

Every request checks the current in-memory product slug/workspace registry
against its startup baseline. The database must also contain matching records
for every initialized product. Historical extra database product rows are
allowed. Active/inactive product status remains an operator decision and is
not treated as infrastructure failure. This is registry/synchronization health,
not a full functional test of every product or external integration.

Database probing uses a separate async psycopg connection, leaving the main
SQLAlchemy pool unchanged. The application pool itself is not tested. The
connection is read-only, with a two-second connect timeout and one-second
statement timeout; the overall probe/lock wait has a three-second async deadline.
Deadline behavior still depends on event-loop and driver responsiveness.
One probe runs at a time per API worker, with a one-second success/failure cache.
After a failure, a subsequent request can retry once that short cache expires.
This can briefly delay detection/recovery by up to the cache duration.

The check reads `SELECT 1`, the migration version table, and product metadata.
It does not inspect customer records or write to the database. Matching migration
versions is not a comprehensive schema-drift audit: stamped revisions with
manually damaged application tables require other controls/tests.

## Failure interpretation

- `products=failed` with other checks `not_checked`: startup readiness state or
  the in-memory registry is unavailable/inconsistent, or an unexpected probe error.
- `database=failed`: connection or basic query failure, or probe deadline expiry.
- `migrations=failed`: missing/inaccessible version table, query failure,
  unacceptable applied revisions or deadline expiry during that query.
- `products=failed` after database/migrations passed: initialized product metadata
  is missing/inconsistent or its query failed.
- `not_checked` means no passing evidence was obtained for that dependency.

Liveness can remain 200 while readiness returns 503. That distinction is expected.

## Remaining deployment steps

1. Run staged standalone tests without touching production. Apply integration
   only after review. Extend the existing `test_health.py` tests and run the full
   backend suite against the dedicated test database using the existing workflow.
2. Deploy using the established release verification gate. Verify public liveness
   is unchanged and public readiness passes. Never stop production PostgreSQL or
   modify its migration table to manufacture a test failure.
3. Change only the API Docker healthcheck URL to `/api/v1/ready`, adding an HTTP
   client timeout of four seconds inside Docker's existing five-second timeout.
   Recreate the API through the normal deployment workflow and confirm it is healthy.
4. Configure an existing Uptime Kuma HTTP monitor for the public readiness URL,
   expecting exactly HTTP 200. Keep liveness as a separate diagnostic signal.
   Confirm the monitor and its notification channel. No new monitoring platform
   is required. External failure signaling must be tested without a production outage.
5. Record CI, deployed commit, Docker and external-monitor evidence. Update this
   rollout status before marking the issue complete.

Readiness being unhealthy does not automatically restart a Docker container or
stop Nginx from forwarding traffic. It supplies a health/monitoring signal; do not
assume Kubernetes-style traffic removal or restart semantics.

## References

- https://alembic.sqlalchemy.org/en/latest/cookbook.html#test-current-database-revision-is-at-head-s
- https://www.psycopg.org/psycopg3/docs/api/connections.html
- https://docs.python.org/3/library/asyncio-task.html#asyncio.timeout
