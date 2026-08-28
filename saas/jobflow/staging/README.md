# FieldLookers isolated staging — candidate, not yet runtime-verified

This directory is a standalone Compose project. Never combine it with production docker-compose.yml, source production .env, copy a production database, or use real customer records.

Production remains unchanged at its verified commit. Unfinished JobFlow source is not modified. Staging alone receives the scoped CSP tested previously with inert fixtures; real application compatibility remains unverified.

## Boundaries

- Dedicated infrastructure/isolated-staging worktree and fieldlookers-staging project.
- Dedicated fieldlookers_staging database and project-owned data volume; no database port is published.
- Fresh database password and JWT secret generated locally in ignored .runtime/.
- Backend and mail services attached only to a Docker internal network; no OpenAI key, SMTP relay or forwarding is configured.
- Both platform and RenewalDesk SMTP go to staging-mail:1025. SMTP TLS is disabled only for this private captured-mail connection, not for browser login.
- Only staging-web joins a second, non-internal ingress network. It publishes browser HTTPS on host loopback 18443 and proxies the email UI on host loopback 18025. Mailpit has no published ports. Backend, database, migration and mail containers remain internal-only. No public DNS, Cloudflare tunnel or production network attachment.
- The gateway has ordinary bridge egress; it is not a general forward proxy and its upstreams are fixed staging service names. This is a testing boundary, not a hardened sandbox against a compromised gateway.
- CPU/memory limits and restart: no. Start manually and stop when finished. Image building can use additional resources and requires package downloads.
- Backend builds from this worktree, not a production container. Nginx/Postgres use exact local production image IDs; Mailpit uses the exact locally pulled image ID recorded at initialization.
- Existing secure session cookie behavior is unchanged. App URL is https://localhost:8443 through SSH forwarding.

## Review and launch sequence — do not run all steps blindly

1. Review/stage candidate files in the isolated worktree and run the supplied preflight before patching. Do not deploy this branch to production.
2. Pull the official axllent/mailpit:latest image explicitly when ready. Initialization itself never pulls it; the resolved image ID is pinned in the local runtime file. Official documentation: https://mailpit.axllent.org/docs/install/docker/
3. From saas/jobflow/staging: python3 staging.py init. This generates local secrets and a 30-day CA plus a 14-day localhost certificate. It creates no containers and installs no trust. Initialization refuses to overwrite existing .runtime; do not delete that directory once a database exists, as this would lose the matching credentials.
4. Run python3 staging.py validate. It captures Compose's interpolated configuration privately and checks isolation without printing secrets. Never paste raw docker-compose config or docker inspect environment output.
5. Review validation before python3 staging.py build; then python3 staging.py start. Start forbids automatic pulls/builds. Check python3 staging.py status and validate actual network memberships, limits, mounts and published ports before browser testing.
6. A separate, explicit Windows trust step is REQUIRED: verify the displayed CA fingerprint and import only ca.crt into the intended user's trust store if approved. Never transfer ca.key, server.key or runtime.env. Do not bypass certificate warnings or weaken Secure cookies. Remove the staging CA from trust when no longer needed. Certificate renewal is not automated in this candidate.
7. Forward from Windows with ssh -N -L 8443:127.0.0.1:18443 -L 8025:127.0.0.1:18025 rflmorel@192.168.1.92. Use https://localhost:8443 for the app and http://localhost:8025 for captured email. Verify staging response headers and the certificate before entering staging credentials. Prefer a dedicated browser profile.
8. Run python3 staging.py seed-admin. It requires the staging flag, the exact staging DB target, an independently checked DB name and zero existing users. It creates operator@staging.example.test with a prompted, unique password. It cannot reset existing users. No other records are seeded; create synthetic test clients through the reviewed application workflow later.
9. Verify authentication, synthetic invitation/reset flows via captured mail, RenewalDesk edits and reminders, and operator actions with synthetic records. Confirm no external email or discovery request can leave backend/mail containers. Probe actual network isolation; configuration checks alone are not a proof of egress isolation. Do not use production credentials, tokens, links or backups.
10. Stop with python3 staging.py stop. This retains only the staging database volume; no destroy-volume command is supplied. Captured email is ephemeral and can disappear if its container is recreated. No reminder cron/worker is installed.

## Verification status

Before delivery: Python compilation, YAML parsing, offline isolation-validator tests and source-hash/patch checks passed. Full Docker Compose resolution, image build, migrations, TLS, runtime egress isolation, startup/readiness, synthetic admin creation and browser tests have NOT run in the assistant environment. The full repository is present only on dellpc. Candidate is not a verified staging environment yet.

HTTPS conversion of the previously tested scoped Nginx configuration needs a fresh nginx -t in staging. Cloudflare-injected behavior is not reproduced by this private environment, so production Report-Only observations remain relevant. Do not switch production CSP based on this scaffold.
