# PréstamoDesk private-document capacity

Private review documents now have four server-side limits:

| Scope | Maximum |
| --- | --- |
| File | 8 MiB (existing application limit; proxy limits may be lower) |
| Business | 256 MiB of recorded document bytes and 1,000 documents |
| Application | 20 documents across all document types |
| Document type within an application | 5 retained versions |

Every successful upload creates a retained version. Re-uploading identical bytes
also consumes capacity. Exact byte capacity is allowed; the next upload is
rejected. New uploads are blocked with HTTP 413 for byte capacity or 409 for
document/version counts and a Spanish message directing the operator to support.

Existing evidence is not removed, replaced or hidden. Tenants already above
a limit can still read authorized existing documents, but cannot upload more.
Any later evidence cleanup must preserve approved/signed review references and
follow a separately reviewed retention procedure. Do not delete production
evidence just to make a quota test pass.

## Consistency and failure handling

The upload body is bounded and read before taking row locks. Then the tenant
row is locked, recorded usage is measured, and the application is locked and
refreshed to recheck review status. No async body reads occur while these
synchronous locks are held. The tenant lock is retained through file writing
and the database commit/rollback; separate workers cannot each claim the same
remaining allocation under PostgreSQL's default READ COMMITTED isolation.

All application documents, including rejected/converted application evidence,
count toward the business allocation. Count checks also bound growth from tiny
uploads. Different tenants have separate allocation decisions.

If recording metadata, the audit event or the transaction commit fails, the
database work is rolled back and the newly stored file is removed. The existing
storage helper removes incomplete temporary uploads if writing fails.

No database migration, deployment environment setting or dependency change is
required. Limits are defined together in `DocumentStorageLimits` in the product's
`document_capacity.py`; raising them requires an explicit code review/release.

## Verification

Offline endpoint regression checks with synthetic SQLite data:

```bash
python -B tests/test_document_storage_limits.py
```

The normal PostgreSQL `pytest -q` suite also runs
`tests/test_document_capacity_postgres.py`, including simultaneous transactions
competing for the last byte/count/version allocation. SQLite endpoint tests do
not establish row-lock behavior; retain the PostgreSQL checks as a release gate.

## Operational boundaries

Quotas measure committed metadata. Existing orphan files, process termination
between file creation and commit, an ambiguous database commit outcome, and a
failed filesystem cleanup still require reconciliation and free-space alerts.
Do not infer that all on-disk bytes are represented by the quota query.

These are per-business limits, not a global disk-reserve mechanism. Provisioning
many businesses can still exhaust a shared filesystem. Monitor space/inodes and
backup sizes, set a safe tenant onboarding capacity, and consider filesystem
quotas or isolated storage. This change does not scan document contents for
malware or add a new upload request-rate limit.

No live disk-filling tests are needed. After the normal release checks and
backup, use a synthetic tenant for one upload/download acceptance check.
