# FieldNest maintenance email notifications

Resident reports queue notifications in the same transaction as the work order.
Active company owners receive an alert. Residents receive a receipt only when
they explicitly fill the optional receipt email field. General contact information
does not automatically opt someone into email.

Only new resident reports queue these notifications. Existing work orders are not
backfilled. Vendor assignments, status changes and manager-created work orders
do not send email in this version.

## Delivery

The API lifespan starts a dispatcher when FIELDNEST_EMAIL_NOTIFICATIONS_ENABLED=1.
Delivery uses the existing platform SMTP configuration. Default behavior outside
the staging overlay is disabled; reports can still queue while delivery is disabled.
Staging enables delivery and retains its existing Mailpit SMTP destination.
No external SMTP credentials or production configuration are changed by this patch.

The dispatcher polls every five seconds while idle and drains one message at a time.
PostgreSQL row locking with SKIP LOCKED prevents API workers from simultaneously
processing the same outbox row. SQLite tests cannot validate PostgreSQL lock behavior.
SMTP timeouts and temporary failures leave the work order intact, and retry
automatically after approximately one, two, four and eight minutes. After five
failed attempts, the message stays failed for operator review.
Only an error class name is saved; SMTP exception text and credentials are not logged.

SMTP delivery is at-least-once, not guaranteed exactly-once. If SMTP accepts a
message and the process crashes before recording success, a retry can deliver a
duplicate. Each logical message has a stable Message-ID and outbox event key.

Owner eligibility and active company/product status are rechecked before sending.
Removed owners and unavailable workspaces are skipped. Owner alerts include a
reference and property name, with a link to the authenticated workspace when
PLATFORM_PUBLIC_BASE_URL is valid. They do not include resident contact details,
the property request token or the issue description.

Resident receipts use fixed text and a reference; they do not repeat unverified
issue text or private workspace details. Receipt addresses are self-reported,
not verified account identities. Nginx's existing public intake limits still apply.
Receipts explain that receipt is not a scheduled repair or permission to enter.

## Observe and recover

Inside the configured API container:

    python -B scripts/send_fieldnest_notifications.py --status
    python -B scripts/send_fieldnest_notifications.py --once
    python -B scripts/send_fieldnest_notifications.py --retry-failed --tenant-id 1

The first command returns aggregate pending/sent/failed/skipped counts without
recipient addresses or report contents. Replace the tenant ID only after identifying
the affected company. Retry failures after fixing SMTP or recipient configuration.

Pending messages survive API restarts. Restoring a DB backup can restore older
pending records; review the queue before enabling delivery after a restore.
Turning the dispatcher off stops future polling but does not retract already sent
mail or interrupt an in-flight SMTP attempt.

Migration e4b6d8f0a213 follows f2a4c6e8b091 and adds an outbox table. Deleting a
work order also removes its outbox entries through a database cascade. Downgrade
drops the notification history; export it first if that history must be retained.

## Validation

Eleven focused email tests passed, plus the existing resident request/form checks.
Tests cover atomic enqueue, retry scheduling, retry limits, deduplication, opt-in,
recipient access changes, fixed receipt content and configured SMTP use.
PostgreSQL upgrade SQL and model definitions were reviewed; full migration drift,
CI and actual Mailpit delivery remain staging acceptance checks.
