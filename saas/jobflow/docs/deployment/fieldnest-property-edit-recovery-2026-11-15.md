# FieldNest property-edit release and image recovery — November 15, 2026

## Evidence and scope

This record summarizes operator-provided terminal output and staging/browser acceptance from the release session. Commands were run by the operator; the assistant did not directly access the production host. Source release: PR #179, merged as `37e18447a83db9f7e2a08e9cc2abe547a0657339`.

Property editing updates name, address, unit count and type in place. No schema migration was introduced. The candidate was derived from the existing private billing API image, replacing only FieldNest api.py and schemas.py.

## Deployed artifacts

| Artifact | Verified value |
| --- | --- |
| Previous API image | `sha256:d4bb686a5b24531aef5ceb209bfb1c176350e5bd54a228c5a13fd3c830931d78` |
| Property-edit API image | `sha256:319c6a6d967112ac01dd40c887280a25530178e77a3d59eff9072b9f1c5c4bb6` |
| Candidate image tag | `fieldlookers-api:property-edit-37e1844` |
| Production workspace script | `assets/fieldnest-workspace-dfb9d8983636.js` |
| API Compose override | `/home/linuxuser/.config/jobflow/property-edit-37e1844.json` |
| API rollback receipt | `/home/linuxuser/.config/jobflow/recovery/fieldnest-property-edit-20261115T182611Z/api-release.json` |

The existing billing module hash was checked unchanged, and the generated API schema exposed the property PATCH endpoint plus billing, checkout, portal and webhook routes. Route presence does not establish successful payment processing.

Six isolated API tests passed in both staging and production candidate images, covering partial edits, identity/link retention, tenant boundaries, invalid input, empty patches and commit failure. The frontend candidate passed syntax and editor regression tests. The operator reported staging passed, then approved production activation and reported completion after receiving the production browser acceptance steps.

API activation was followed by successful internal and public readiness responses with database, migrations and products passed. Initial connection refusals occurred while the API started; subsequent checks succeeded. Nginx configuration validation and reload succeeded.

The web redeploy script was updated to include the property-edit override; its configuration-only check passed. The script still applies only the web service. Its backup is `/home/linuxuser/.config/jobflow/redeploy-web.sh.before-property-edit-20261115T183128Z`. Other deployment commands must explicitly retain the API override; this change does not modify every deployment entry point.

## Post-release database and frontend backup

The November 15 run finished at **18:30:15 UTC (1:30:15 PM America/New_York)**:

- Database dump: `jobflow-20261115-182952.dump`.
- Daily and weekly off-site replication verified.
- Isolated database restore passed with matching counts for all 50 tables.
- Migration revision remained `c8e0a2b4d637`.
- Temporary restore container removal passed.
- Frontend off-site backup verified 118 files.
- Service result, main status and frontend post-hook all reported success; monitoring success was accepted.

## API image recovery verification

The API image was exported separately because the routine database/frontend backup does not establish Docker image recoverability.

| Check | SHA256 |
| --- | --- |
| Compressed Docker image archive | `fba9d357801cec3c803fa7bcc8dd10279f6fd8c9a3a18321177e6c57e7c0ce75` |
| Plaintext tar recovery bundle | `9e3fee0d354202f7daafdcce003d1483a17f1c7525250bd8aa27348f4c97471b` |

The tar bundle contains exactly `release/jobflow-api.tar.gz` and `release/image-receipt.json`. It was age-encrypted, replicated to B2 with a requested retention deadline at least 35 days from upload, and freshly downloaded by object file ID. Download length and encrypted SHA256 matched the off-site receipt.

The backup helper rejected an initial gzip input because its archive magic guard accepts PostgreSQL dumps or uncompressed tar. Wrapping the verified gzip image in a tar bundle preserved that guard. A root-run upload was rejected by the credential ownership check; the successful upload ran as linuxuser using a private user-owned copy, without changing credentials.

On Windows, the fresh B2 copy was decrypted using the existing recovery identity. The plaintext bundle hash, allowed regular-file entries, image receipt, archive byte count and image archive hash all passed. Docker loaded the recovered archive and inspection confirmed the exact production image ID above.

Local recovery folder: `C:\Users\rafae\.ssh\fieldlookers-recovery\property-edit-drill-20261115-173251`.

Server upload/download receipt: `/home/linuxuser/fieldlookers-property-edit-offsite/offsite-receipt.json`.

## Limits and follow-up

This image recovery check loaded and inspected the image. It did **not** start the recovered API against a restored database, perform a new full-stack restore, or change production containers during the recovery check. The earlier November 14 full-stack drill remains separate evidence for its earlier release.

Routine backups and this separate image receipt do not prove that the newly added Compose override and edited redeploy script have been incorporated into an updated off-site configuration archive. Include those files in the next configuration recovery checkpoint. Keep recovery identities private and outside the public repository.
