# Encrypted off-site PostgreSQL backups

Updated: 2026-08-27
Owner: Rafael Morel
Tracking: homelab#15

## Workflow

The existing jobflow-backup.service now performs:

1. Create a PostgreSQL custom-format dump.
2. Check its archive listing and copy it to OpenMediaVault.
3. Apply the existing local and OMV cleanup.
4. Encrypt and replicate the dump to Backblaze B2.
5. Download each due remote copy and verify bytes, retention, and encryption.
6. Record success and send the existing Uptime Kuma notification.
7. Report the overall exit status to hosted Healthchecks.io.

The timer remains enabled at 02:30 UTC daily. Local and OMV copies remain
in place. A B2 failure prevents the overall success marker/notification.

## Destination and retention

Private bucket: fieldlookers-production-backups
Endpoint: s3.us-east-005.backblazeb2.com

| Prefix | Copy schedule, UTC | Object Lock duration | Hide after upload | Delete after hiding |
| --- | --- | ---: | ---: | ---: |
| platform/daily/ | Every backup | 7 days | 7 days | 1 day |
| platform/weekly/ | Sunday backups | 35 days | 35 days | 1 day |
| platform/monthly/ | First-of-month backups | 365 days | 365 days | 1 day |

Object Lock deadlines are calculated from the source dump modification
timestamp. Lifecycle hiding is calculated from upload time. Cleanup occurs
after retention and is not instantaneous.

Lifecycle values were confirmed by the operator in the Backblaze UI;
actual age-based deletion has not yet been observed.

Governance mode protects retained versions from this uploader. An
administrator with governance-bypass authority can override that protection.
The uploader cannot delete versions, bypass governance, or administer buckets.
It can create new versions or hide markers; recovery should use retained file
versions, not assume the visible latest version is the only copy.

Weekly/monthly classification uses UTC source timestamps. Missed dates are
not automatically backfilled. Check missed schedules promptly.

The manual test objects under platform/verification/ are outside these
cleanup rules and require separate administrative cleanup.

## Credentials and recovery ownership

Server configuration, outside Git:
- ~/.config/fieldlookers/b2-upload.json: restricted credential, mode 600.
- ~/.config/fieldlookers/backup-recipient.txt: public age recipient.
- ~/.config/fieldlookers/healthchecks-ping-url: private ping URL, mode 600.

The B2 master credential and private age recovery identity remain off the
production server. Rafael maintains recovery access in an independent
password manager. Do not publish credentials, ping URLs, or dump contents.

For recovery, use runtime/last-offsite-success.json when available. It records
remote file IDs, encrypted hashes, source hash, and retention deadlines.
If the host and its evidence are lost, use the private bucket's dated
daily/weekly/monthly prefixes and inspect retained versions.

Download the selected encrypted object, verify the recorded encrypted hash
when available, and decrypt on a separate recovery computer with the private
age identity. Restore into an isolated database and validate its contents.
Do not compare an older snapshot's counts to changing live production data.

## Monitoring

Hosted Healthchecks.io expects cron schedule 30 2 * * *, UTC, with 30 minutes
of grace and email notifications enabled. Missing completion is expected to
alert after 03:00 UTC. This is backup monitoring, not immediate outage detection.

The EXIT hook reports explicit failure while preserving the backup exit code.
Failure to deliver a success heartbeat makes the service fail. If the host
cannot send anything, external missed-heartbeat detection remains available.
Only empty status requests are sent; no database contents or logs are attached.

Local freshness check:
    python3 scripts/replicate-jobflow-backup.py --check

This checks local evidence and a 36-hour source-age limit; it does not contact
B2. The previous success record is preserved when a later upload attempt fails.
The local check does not replace the external scheduled heartbeat.

## Implementation limits

The uploader accepts completed custom-format dumps no older than 36 hours,
with a 256 MiB maximum size. Larger backups require a streaming/multipart
implementation before use. The encrypted retry cache is runtime/b2-spool/.
Cached ciphertext enables repeat uploads to reuse the same remote file IDs.
Cache files older than eight days are cleaned after successful replication.
Losing the cache can create an additional retained copy on retry.

## Verification completed

- Private B2 access and restricted server credential capabilities verified.
- Real production dump encrypted, uploaded, downloaded, and decrypted on Windows.
- Decrypted SHA256 matched the original dump exactly.
- Remote governance retention verified.
- Repeat scripted upload reused remote file IDs and checksums.
- Integrated backup service completed successfully; freshness check passed.
- External failure email and recovery email received; check returned Up.
- 19 automated tests passed, including isolated exit-hook failure cases.
- Bash syntax and git diff whitespace checks passed.

The first timer-triggered run, future weekly/monthly production copies, and
actual lifecycle deletion remain to be observed. Full database restore
validation remains separate work; byte integrity is not a restore test.

Run tests:
    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts/tests -p 'test_backup*.py' -v
