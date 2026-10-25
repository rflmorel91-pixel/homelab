# PréstamoDesk live-data readiness gates

This checklist is a launch gate for borrower records and payment operations.
A code change or a green container health check does not by itself pass it.
Record the release commit, operator, date, evidence location, measured result,
and unresolved exceptions for every gate.

## Public intake

The Nginx routes for public PréstamoDesk quotes and applications must apply
`jobflow_public_request` rate limiting. After deployment, verify both paths
through the public hostname and confirm the configured limit returns HTTP 429
when exceeded. Confirm Nginx access logs identify the actual client address
used for the limit. Do not use production borrower data in this check.

## API process identity

The API image must run as UID/GID `10001:10001`. Confirm the running process
identity and verify that the process can write only to the private-document
volume and its configured temporary filesystem. The database and migration
containers have separate user and permission requirements; do not infer their
identity from the API container.

Before the first non-root deployment, review the target volume and take a
verified backup. Build the image, then stop the current API so it cannot create
more root-owned files during the ownership change. Run the one-time ownership
repair, then start the API with the new image:

```sh
docker-compose build jobflow-api
docker-compose stop jobflow-api
docker-compose run --rm --no-deps --user 0:0 --entrypoint sh jobflow-api \
  -ec 'chown -R 10001:10001 /var/lib/jobflow-private/prestamodesk'
docker-compose up -d jobflow-api
```

This changes ownership inside the mounted document volume. Do not proceed if
the volume name or mount path differs from the production Compose configuration.

## Storage encryption

Verify that both the PostgreSQL data volume and private-document volume reside
on storage encrypted at rest. Docker named volumes do not provide encryption;
the host storage layer must supply it. Use `docker volume inspect` to identify
each volume mount point, then `findmnt -T <mount-point>` to identify its backing
filesystem. For a LUKS-backed filesystem, verify the active mapping with
`cryptsetup status <mapper-name>` and document how the key is recovered after a
host outage.

If either volume is on unencrypted storage, do not enable encryption in place
or remove the existing data. Plan an offline migration: take and verify a
backup, create encrypted storage, restore or copy while services are stopped,
verify ownership and contents, run the application against the new storage in
isolation, and retain the original until the new copy is verified and rollback
is possible. Require a second operator or documented recovery procedure for
the encryption key; a lost key makes the data unrecoverable.

## Backup and restore evidence

Restore a recent backup into an isolated environment with no public route and
no customer email delivery. Record backup age at restore start, elapsed restore
time, database migration head, table and row-count checks, and a sample of
financial totals reconciled against the source ledger. Protect any restored
personal data with production-equivalent access controls and delete the drill
copy under the retention policy.

The October 19, 2026 pilot plan proposes RPO of at most 24 hours and RTO of at
most 8 hours. These remain targets until a restore drill measures them. The
operator and customer owner must agree to stricter limits if losing a day of
payment records is unacceptable. Do not advertise a target as an achieved SLA.

## Go/no-go

Do not enter real borrower records or record live customer payments until all
of the following are evidenced:

- Public quote/application rate limits work through the actual public route.
- The API runs as non-root and private-document access still works.
- Database and document storage encryption and key recovery are verified.
- A recent backup restores successfully, and measured RPO/RTO meet the agreed
  limits.
- The exact release passes tenant, role, payment, export, and recovery checks.
- The customer owner approves access, data fields, retention, support, and exit
  terms; resolve local privacy requirements before live data.

## Current recovery evidence

On October 25, 2026, isolated restore validation passed for
`jobflow-20261024-200315.dump`: 40 table counts matched and the temporary
container was removed. This validated the local backup selected by the
off-site success record; it did not retrieve or decrypt a new B2 object.
Off-site recovery remains open until that separate drill is completed on the
authorized recovery machine.
