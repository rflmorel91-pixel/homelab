# Staging verification — 2026-08-28

Base commit: 734ed742cefa5c75f19820ef911f8dea8479a519
Branch: infrastructure/isolated-staging

Evidence is based on user-supplied terminal output and browser confirmations.
This records the staging candidate, not a production release.

## Infrastructure verified

- Dedicated staging API image built successfully.
- Separate staging database initialized; migrations exited successfully.
- API readiness passed database, migration and product checks.
- Only the web gateway joins the ingress network.
- API, database and Mailpit remain on the internal staging network.
- Gateway ports 18443 and 18025 are published on host loopback only.
- HTTPS certificate verification passed; Windows user trust was explicitly approved.
- Platform email was captured by Mailpit using synthetic recipient data.
- Production containers remained healthy during the reported checks.

## Corrections verified

- Added gateway ingress networking to enable localhost port publication.
- Proxied the inbox through the gateway; Mailpit remains internal-only.
- Changed staging's binary client-IP fallback to textual remote_addr.
  This resolved the malformed upstream login request.

## Browser flows confirmed under staging CSP enforcement

- Administrator sign-in; enforced CSP and staging response header present.
- Administration, Commercialization and Prospecting pages loaded.
- Synthetic RenewalDesk public intake created lead #1.
- Lead transitioned New -> Contacted -> Qualified.
- Invitation creation and owner activation succeeded.
- Provisioning converted the lead to staging Client #1.
- Synthetic owner signed in to RenewalDesk.
- Renewal creation and editing persisted after refresh.
- Password-reset email arrived in Mailpit.
- Reset succeeded; owner signed in with the new password.
- Reusing the reset link was rejected.
- The password from the successful reset still worked afterward.
- No JavaScript or CSP errors were reported for the confirmed checks.

## Limitations and pending work

- Network configuration and membership were checked; active egress probes
  have not established comprehensive outbound isolation.
- The gateway has ordinary bridge egress; this is not a hardened sandbox
  against a compromised gateway.
- Prospecting mutations, campaign execution, team-management actions,
  reminder delivery and other unlisted workflows remain unverified.
- Private staging does not reproduce Cloudflare-injected browser behavior.
- Full repository CI for this staging branch has not yet been confirmed.
- Path checks excluded runtime files; no complete secret scan is claimed.
- Certificates expire and require renewal; trust removal remains an
  operator responsibility when staging is retired.
- Production remains Report-Only. JobFlow remains unchanged.
- Issue #19 remains open; this does not authorize production enforcement.

No passwords, session cookies, activation/reset tokens or private keys
are included in this record.
