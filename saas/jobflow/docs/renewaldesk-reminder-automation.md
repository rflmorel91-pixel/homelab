# RenewalDesk Reminder Automation

## Scope

The scheduled worker processes active commercial
RenewalDesk Clients only.

It excludes RenewalDesk validation workspaces and all other
FieldLookers Tenant/Products.

The internal database model uses the `tenants` table for
both Clients and validation workspaces. The worker identifies
Clients by requiring a non-null `client_number`.

## Schedule

The systemd timer runs every five minutes using:

    *-*-* *:0/5:00

Each cycle evaluates reminder eligibility using the Client's
configured IANA timezone. Reminders are scheduled for 9:00 AM
in the Client's local time and stored as UTC.

## Components

- Wrapper: `scripts/run-renewaldesk-reminder-cycle.sh`
- Service: `systemd/fieldlookers-renewaldesk-reminders.service`
- Timer: `systemd/fieldlookers-renewaldesk-reminders.timer`
- Worker: `backend/scripts/run_renewaldesk_reminders.py`

The wrapper uses `flock` to prevent overlapping cycles.

## Runtime Markers

Runtime state is written under `runtime/`:

- `last-reminder-success`
- `last-reminder-failure`
- `last-reminder-cycle.json`
- `renewaldesk-reminders.lock`

A successful cycle atomically updates the success and result
files and clears a previous failure marker.

A failed cycle records its timestamp and exit status and
returns the worker's nonzero status to systemd.

## Safe Manual Check

Run a read-only candidate inspection:

    ./scripts/run-renewaldesk-reminder-cycle.sh --dry-run

A dry run must not create, process, retry, or send deliveries.

## Installation

Copy the repository-managed units:

    sudo install -m 0644       systemd/fieldlookers-renewaldesk-reminders.service       /etc/systemd/system/

    sudo install -m 0644       systemd/fieldlookers-renewaldesk-reminders.timer       /etc/systemd/system/

    sudo systemctl daemon-reload

Verify the installed units:

    systemd-analyze verify       /etc/systemd/system/fieldlookers-renewaldesk-reminders.service       /etc/systemd/system/fieldlookers-renewaldesk-reminders.timer

## Supervised Production Cycle

Run one supervised cycle before enabling automation:

    sudo systemctl start       fieldlookers-renewaldesk-reminders.service

    sudo systemctl status       fieldlookers-renewaldesk-reminders.service       --no-pager

Only after the supervised cycle succeeds:

    sudo systemctl enable --now       fieldlookers-renewaldesk-reminders.timer

## Monitoring

Inspect the timer:

    systemctl list-timers       fieldlookers-renewaldesk-reminders.timer       --all

Inspect service executions:

    journalctl       -u fieldlookers-renewaldesk-reminders.service       --since today       --no-pager

Inspect the latest result:

    cat runtime/last-reminder-success
    cat runtime/last-reminder-cycle.json

A present `runtime/last-reminder-failure` means the latest
attempt failed without a later successful recovery.

## Disable Automation

Disable future executions:

    sudo systemctl disable --now       fieldlookers-renewaldesk-reminders.timer
