# Release recovery drill — 2026-11-14

This record summarizes operator-reported command output from an isolated Windows Docker Desktop recovery drill. It records observed results, not an automated certification or a complete disaster-recovery procedure.

## Selected artifacts

Release identifier: `20261114T203806Z`. The deployed frontend included the work-order attention change merged at `b549653115bb7cf83320fa63a20127b646e09a5b`, plus existing billing customizations. Its active workspace asset was `fieldnest-workspace-1956c601f4b2.js`. The production checkout alone did not represent all deployed files.

| Artifact | Identity |
| --- | --- |
| API image | `sha256:d4bb686a5b24531aef5ceb209bfb1c176350e5bd54a228c5a13fd3c830931d78` |
| Web image | `sha256:3898835b1adbb6c73b2c8fd46a280fa56ecbae99e6d57c4616ac9dc51e649c8d` |
| Database snapshot | `jobflow-20261114-203428.dump` |
| Migration revision | `c8e0a2b4d637` |
| Frontend inventory | 106 files |
| Release tar SHA256 | `73a921ba975fe2171bf9b6b5c2f30f840bdf58b72119ba84b9611e457064d0d7` |
| Configuration tar SHA256 | `d4b35dacea19a826ac38c743c8893de7dd2a0f9c93bbdddec91d716cd92e83b6` |
| Database dump SHA256 | `a15c2179ef4e89bd204ccb09413307bcead55068e16cc9c1343e2ce91e2302c5` |

The release tar contained its manifest, frontend files, two compressed Docker image archives and their receipt. A separate encrypted configuration archive contained six Compose files, nginx configuration and the runtime environment file. The database snapshot, private-document archive and database manifest were separate backup artifacts. These captures had different timestamps; this was not an atomic snapshot of every component.

## Observed results

| Check | Result |
| --- | --- |
| Fresh B2 downloads | Ciphertext sizes and hashes matched receipts |
| Local age decryption | Original plaintext archive hashes matched |
| Frontend and image archive inventories | 106 frontend files and two image archives verified |
| Docker image loading | Both image IDs matched; archives had no repository tags |
| PostgreSQL 16 restore | Exact public-table inventory and row counts matched: 50 tables, before API startup |
| Private-document archive | Zero documents; one safe directory entry allowed |
| Restored API readiness | Database, migrations and products passed |
| Recovery web gateway | Reached restored API; readiness passed through proxy |
| Workspace and static delivery | Workspace route and all 106 frontend files matched release hashes over HTTP |
| Isolation | All three containers used only an internal network; no published ports |
| Cleanup | Temporary web, API, database and network removed successfully |

The API used fresh recovery credentials and a fresh signing secret. Production environment files and production volumes were not mounted. Email notifications were disabled and Stripe secrets were empty. The database used temporary memory-backed storage.

The gateway used a minimal recovery-only HTTP nginx configuration. This did not validate the recovered production nginx configuration or TLS.

## Repeat-drill sequence

1. Select a release manifest and database snapshot deliberately. Obtain encrypted artifacts using existing backup receipts; do not replace routine backup-success markers.
2. Verify downloaded ciphertext against receipts, decrypt on the recovery workstation with its separately held identity, and verify plaintext hashes.
3. Inspect archive members before extraction. Reject absolute paths, traversal, links and unsupported member types; permit safe directory entries. Verify expected file inventories and hashes. Keep decrypted configuration private.
4. Load image archives and compare exact image IDs. Check tags first to avoid overwriting unrelated local tags.
5. Create a uniquely named internal Docker network and disposable PostgreSQL instance with no published ports or production volumes. Restore with errors treated as failures. Compare table inventory and counts to the snapshot manifest before starting the API.
6. Start the exact restored API image using recovery-only credentials, writable temporary directories as needed and disabled external integrations. Check readiness.
7. Start the restored web image with the verified frontend and a recovery-only gateway configuration. Verify proxy readiness, workspace delivery and every frontend file hash.
8. Stop and remove only the uniquely named recovery containers and network. Retain recovery evidence and artifacts according to the operator's protected-storage policy.

Never publish decrypted configuration, database contents, credentials or recovery identities in the repository. Do not connect the drill to production services.

## Limits and follow-up

- Login, authorization and business workflows were not exercised in the recovered stack.
- Production TLS, DNS, Cloudflare routing and external integrations were not tested.
- Configuration decryption and whole-archive integrity passed; the recovered production configuration was not applied.
- No recovery-time objective was measured.
- Zero private documents means this drill did not exercise recovery of nonempty document storage.
- Manual release/image/configuration bundles are separate from the automatic frontend backup. Their creation is not yet a recurring release process.
- Preserve deployed billing customizations and exact images when preparing future releases; a checkout of main alone is insufficient to reproduce this deployment.

At this checkpoint, the scheduled database backup and isolated restore service also ran successfully, and its frontend hook verified 106 files. The timer was scheduled for 02:30 UTC. Existing database tiers were daily/weekly/monthly; frontend backups retained at least 35 days. The one-time release and configuration uploads requested at least 35 days of retention. These historical results do not prove current backup freshness or indefinite artifact availability.

Production and staging containers were untouched by the Windows drill. Downloaded recovery files and loaded images remained on the workstation after temporary-container cleanup.
