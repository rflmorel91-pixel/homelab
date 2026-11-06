# FieldNest notification abuse limits

Maintenance reports remain saved and trackable when a notification is limited.
Email is a convenience; the manager workspace remains the record of requests.

## Policy

| Scope | Rolling hour | Rolling 24 hours |
| --- | ---: | ---: |
| Receipts to one normalized address, across businesses | 3 | 10 |
| All FieldNest mail to one normalized address | 30 | 100 |
| One business, across recipients | 100 | 500 |
| All FieldNest businesses combined | 300 | 1,500 |

Each business may additionally have at most 200 pending notifications. Limits
are declared in `EmailLimits` in `email_limits.py`; changing them requires a
reviewed release. These limits count SMTP attempts, including retries/failures,
not only successful deliveries. Configuration failures before SMTP do not use
the send budget but remain subject to the existing five dispatch-attempt limit.

Pending admission serializes on the tenant row. Every notification beyond the
pending allowance is recorded as `suppressed` with `TenantPendingLimit` while
the report and its private tracking link are still created. At dispatch,
budgets are checked again immediately before SMTP. A rate-limited notification
is terminally `suppressed` with a fixed reason such as `ReceiptRecipientHourLimit`;
it is not automatically replayed when the window expires. This avoids a later
burst of old receipts. Manager follow-up uses the saved request/workspace.

FieldNest's global ceiling does not include RenewalDesk reminders, invitations
or password-reset emails; those workflows are unchanged.

## Persistence and concurrency

Migration `b7d9f1a3c526`, after `a6c8e0f2b415`, creates
`fieldnest_email_attempts`. The dispatcher locks the existing FieldNest product
row with PostgreSQL NO KEY UPDATE before checking usage and retains that lock
through SMTP and commit. Separate dispatchers cannot each spend the last budget
slot. Intake does not acquire the dispatch lock and does not wait for SMTP.

Queue admission also uses NO KEY UPDATE, which is compatible with foreign-key
KEY SHARE locks acquired while inserting reports. It avoids an upgrade deadlock
between simultaneous report inserts and serializes pending-count decisions.

The attempt history records tenant/notification IDs, notification kind, UTC
attempt time and a hash of the normalized actual destination address. It does
not store raw mailbox addresses, subjects, bodies, credentials or report text.
Hashes of email addresses are pseudonymous, not secret or anonymous.

History intentionally has no cascading foreign keys. Deleting a work order or
outbox row cannot reset a mailbox/business/global sending allowance. Entries
older than 48 hours are pruned during dispatch; this is not an automatic TTL
when the dispatcher is idle. Old outbox records retain their existing lifecycle.

Existing sent messages are not backfilled at initial migration. New accounting
starts at rollout; pending messages are immediately subject to the new limits.

## Boundaries

- A property intake link does not prove mailbox ownership. This change bounds
  abuse; it does not turn a supplied receipt address into a verified identity.
- Address matching strips surrounding whitespace and case-folds. Provider-specific
  aliases, plus tags and dot variants are not merged. Business/global budgets
  still apply when aliases or recipients are varied.
- Pending and suppressed outbox rows grow with report history. These controls
  are not report-storage quotas or distributed denial-of-service protection.
- SMTP remains at-least-once. A crash or ambiguous database commit after SMTP
  can leave the existing delivery/commit uncertainty window. Stable Message-ID
  helps identify retries but does not guarantee inbox deduplication. Stop mail
  delivery during database incidents rather than assuming exact counters.
- Owner access, active business/product and current owner address are rechecked
  after obtaining the dispatch lock. In-flight messages can still complete
  while access changes, as with any external send.

## Validation and rollout

Run standalone synthetic SMTP checks without a PostgreSQL server:

```bash
python -B tests/test_fieldnest_notifications.py
python -B tests/test_fieldnest_email_limits.py
```

The normal PostgreSQL test suite includes nine concurrency checks in
`test_fieldnest_email_limits_postgres.py`: eight competing dispatch budgets and
pending admission after simultaneous foreign-key inserts. SQLite tests cannot
prove PostgreSQL lock behavior. Require the normal full CI and migration check.

Unlike the two preceding fixes, this release **requires a database migration**.
Keep email disabled during the schema/API transition; apply the additive
migration with the new migration image, replace all old API workers together,
check readiness and queue counts, then enable the new dispatcher. An old worker
does not enforce these limits. Do not recreate the new API against the old schema.

Take and restore-validate a pre-release backup. Validate the new migration
against an isolated restored copy before production; after release, create and
verify a new backup and encrypted configuration snapshot. The new table also
becomes part of the normal backup inventory. Do not downgrade/drop attempt
history to roll back application code. Retain the additive table during an
application rollback and keep email disabled until the intended sender is ready.

Use controlled synthetic recipients and a fake/captured SMTP transport for
abuse tests. Do not send hundreds of real messages or flood production forms.
For live acceptance, one authorized report and expected receipt/owner alert
are sufficient; rate-limit boundaries are exercised in isolation.

Review `notification_counts()` for `pending`, `failed` and `suppressed`, and
aggregate fixed `last_error` suppression reasons. Never print recipient addresses,
message bodies or private tracking links into monitoring logs.
