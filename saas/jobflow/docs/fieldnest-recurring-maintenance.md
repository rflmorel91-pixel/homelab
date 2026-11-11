# FieldNest recurring maintenance

Implementation candidate — November 10, 2026. Not deployed to production.

Owners and existing authorized FieldNest workspace members can create plans for
properties and optional vendors in their own company. Plans repeat every 1, 3,
6, or 12 months. The due day remains anchored to the initial schedule, with
month-end clamping (January 31 → February 28/29 → March 31).

The Planned maintenance workspace page explicitly generates due work orders.
There is no unattended scheduler or reminder delivery in this release. Due
checks use the current UTC date. Generation retries reuse the same work order
for the submitted scheduled date. PostgreSQL row locks serialize generation and
completion; a unique plan/date constraint provides an additional invariant.

Complete generated orders through the ordinary work-order details workflow.
Completion and advancement are committed together. Retries do not advance the
plan twice. Overdue backlog advances one occurrence at a time. Pausing blocks
new generation; existing orders remain available and can still be completed.
Completed recurring orders cannot be reopened, and recurring orders cannot be
cancelled or deleted, preserving schedule/history consistency. Other work orders
retain existing behavior. Plan title, property, interval, and initial assignment
are fixed in this first version; work-order vendor assignment can still change.

## Validation and release

Run the platform backend test/migration-drift workflow and workspace race checks.
The standalone maintenance tests exercise real SQLite ORM/API transactions; they
are not evidence of PostgreSQL locking behavior. The platform pytest suite includes concurrent generation/completion checks
against PostgreSQL. Local PostgreSQL execution was blocked because this runtime
disallows socket creation; those checks and migration drift require CI.

Before deployment: back up the shared database, apply migration c8e0a2b4d637 in
isolated staging, confirm readiness, and verify plan creation, generation,
assignment, completion, refresh persistence, and another-company rejection.
The migration adds tables; it does not rewrite existing work orders. Downgrade
refuses to discard stored maintenance plans. Preserve history and agree on a
recovery plan rather than blindly restoring a shared database with newer writes.
