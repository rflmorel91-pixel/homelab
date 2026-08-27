# Public readiness heartbeat using existing Healthchecks

Owner: Rafael Morel. Issue: homelab #17.

## Status

Installed and verified on dellpc on 2026-08-27.

- API release ea24f6ed0559b486cfb6f18a9342063acfeee3d2 passed the full
  production release gate at 17:07:53 UTC, including 556 backend tests.
- Monitor unit tests: 13 passed; existing backup/restore tests: 50 passed.
- Installed monitor service returned Result=success and ExecMainStatus=0.
- Automatic timer runs at 17:24 and 17:25 UTC passed.
- Stopping only the monitor timer produced a hosted missing-heartbeat email
  while the public API remained ready.
- Timer and service were restarted; freshness and recovery email confirmed.
- Uptime Kuma readiness monitor reports Up with notifications enabled.
- CI now includes the monitor tests; follow-up commit CI remains pending.

HTTP failure responses and notification error handling are covered by mocked
tests. Live notification tests verified direct failure signaling and missing
heartbeats; no production database outage was induced. Uptime Kuma's own
notification delivery has not been separately demonstrated.

The API release evidence remains associated with ea24f6e; these host-monitor
changes do not imply that a different API image was deployed.

## Architecture and limitation

No new monitoring platform is added. A systemd job on dellpc fetches the public
`https://jobflow.fieldlookers.com/api/v1/ready` endpoint every minute and sends a
status-only heartbeat to the existing hosted Healthchecks account. Local Uptime
Kuma should also monitor the readiness endpoint, with liveness kept separately.

This is external heartbeat supervision of a local HTTP probe, **not an
independent off-host HTTP probe**. Hosted Healthchecks can detect missing
reports after a host, site or Internet failure, but the HTTP request originates
inside the homelab. It cannot prove that every outside client or geography can
reach the service. Local Uptime Kuma shares the homelab failure domain.

## Passing conditions


- Public HTTPS request with certificate verification and no redirect following.
- Exact HTTP 200, not 3xx, authentication challenges, 4xx or 5xx.
- JSON must exactly match the published readiness contract: ready status,
  jobflow-api service, and passed database/migrations/products checks.
- A success heartbeat must be accepted by Healthchecks.
- The local status marker must be written successfully.

The curl command ignores `.curlrc`, limits its body to 4096 bytes, has a
three-second connection timeout and ten-second transfer timeout, and runs
under a fifteen-second subprocess timeout. The systemd service has a
45-second overall limit. Host scheduling, DNS and network failures can cause
false alarms; investigate failures rather than treating every alert as a
database outage.

No database credentials, cookies, response bodies or customer data are sent to
Healthchecks or printed in logs. The ping URL is read from the private mode-600
file `~/.config/fieldlookers/healthchecks-readiness-ping-url`. It must not be the
backup or restore check URL. The existing `report-backup-health.py` validates
that URL and sends the status-only POST. Keep secrets outside Git.

## Cadence and alerts

| Setting | Value |
| --- | --- |
| Unit | `fieldlookers-readiness-monitor.service` |
| Timer | `fieldlookers-readiness-monitor.timer` |
| Schedule | Every minute, calendar timer, persistent |
| Healthchecks name | FieldLookers Platform Readiness |
| Healthchecks period | 1 minute |
| Healthchecks grace | 2 minutes |
| Notification | Email enabled |

A detected failure sends `/fail` promptly and returns nonzero; grace does not
delay explicit failure signals. If the process/host cannot report at all, the
hosted check declares a missing heartbeat after roughly three minutes since
the last successful report, subject to provider processing. Failed checks
repeat on subsequent timer executions; there is no automatic API restart.
No Docker dependency is required: the monitor should still run and report
failure when Docker is unavailable. No production state is modified.

## Local evidence

`runtime/last-readiness-monitor.json` is an atomic mode-600 status file containing
only result, timestamps, heartbeat acceptance or a sanitized failure stage/type.
It is ignored runtime evidence, not a source-controlled artifact.

```bash
cd ~/homelab/saas/jobflow
python3 -B scripts/check-platform-readiness.py --check
```

`--check` only inspects local evidence. It sends no heartbeat and makes no
HTTP request. It rejects failed evidence or evidence older than 180 seconds.
An abrupt process failure may leave a previous passing record until it becomes
stale; hosted missing-heartbeat monitoring supplies the independent deadline.

## Installation and verification gates

1. Check the delivered archive SHA256 and expected members before extraction.
2. Run staged unit tests. Run the staged monitor with explicit `--project-dir`
   pointing to the real application; confirm public readiness plus heartbeat
   acceptance, local freshness and the recovery email. No timer is installed yet.
3. Install the five new files into the matching repository locations. Validate
   systemd syntax; install the units only after source tests pass.
4. Run the service manually and verify Result=success and ExecMainStatus=0.
5. Test synthetic HTTP failure through the monitor's error path without touching
   production. Clearly label it synthetic; confirm failure and recovery emails.
6. Enable the minute timer and verify at least two actual timer-driven runs.
7. Stop **only this monitor's timer**, let any in-flight service finish, and wait
   beyond the hosted period plus grace. Do not pause the hosted check. Confirm a
   missing-heartbeat email while the API remains healthy; restart the timer and
   confirm recovery. Never stop the database or backup/restore timers for this.
8. Add the public readiness URL to existing Uptime Kuma, accepting exactly 200,
   with a 60-second interval and a configured notification channel. Confirm Up.
9. Extend the existing script CI job with
   `python -B -m unittest discover -s scripts/tests -p 'test_readiness_monitor.py' -v`.
   Run both this suite and the existing 50 backup/restore tests on the host.
10. Update deployment evidence, commit, push and verify CI. Do not
    represent monitor installation or missing-heartbeat detection as complete
    until those results have been observed.

## Routine commands after installation

```bash
sudo systemctl start fieldlookers-readiness-monitor.service
systemctl show fieldlookers-readiness-monitor.service -p Result -p ExecMainStatus
systemctl list-timers fieldlookers-readiness-monitor.timer --all --no-pager
python3 -B scripts/check-platform-readiness.py --check
```

Do not paste the Healthchecks ping URL, `.env` contents, or cookie files into
issues or chat. During approved maintenance, deliberately pause/resume the
dedicated hosted readiness check as needed; never silently leave it paused.

References: https://healthchecks.io/docs/configuring_checks/ and
https://curl.se/docs/manpage.html.
