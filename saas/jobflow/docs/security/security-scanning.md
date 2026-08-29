# Security scanning

The SaaS platform release gate scans pinned Python dependencies,
tracked source, relevant Git history, and the API and web container
images. The required GitHub Actions job is named `Security Scanning`.

A verified release requires the authoritative workflow for the exact
commit to finish successfully. Therefore, a failed security scan blocks
release verification.

## Repeatable command

From a clean, full-history checkout at the commit being evaluated, run:

    saas/jobflow/scripts/run-security-scans.sh

Requirements:

- Docker
- Git with complete repository history
- Python 3
- access to the public scanner and package registries

The script records the commit and pinned scanner versions in its
output. Temporary reports and caches are removed when it finishes.

## Scanning scope

### Python dependencies

`pip-audit` scans `backend/requirements.txt`. Every active requirement
must use an exact `==` pin. The command does not print environment
variables or application credentials.

### Secrets

Gitleaks scans:

1. a `git archive` snapshot of tracked files at the evaluated commit;
2. the repository's complete Git history.

Ignored operational files, including `.env`, private keys, runtime
state and credential directories, are intentionally excluded from the
tracked snapshot. They are protected operational secrets, not source
artifacts. Gitleaks output uses redaction and must never publish a
secret value.

There are no secret-scanner false-positive exceptions at initial
adoption. A future exception must identify only a stable rule and file
location, never the detected value, and must include an owner,
rationale and review date.

### Container images

The command builds the API and web images from the evaluated commit,
pulling current base-image metadata. Trivy scans both images for HIGH
and CRITICAL vulnerabilities.

The API build applies available Debian security upgrades and removes
pip after dependency installation. The web image derives from Nginx
Alpine and applies available Alpine security upgrades.

## Blocking policy

A HIGH or CRITICAL container finding blocks the scan when:

- a fixed version is available;
- no reviewed exception matches its image, CVE and package;
- its exception has expired;
- an exception is duplicated; or
- an exception remains after its finding disappears.

Exceptions are stored in:

`security/container-vulnerability-exceptions.json`

The validator prints only the image label, vulnerability identifier,
package name, disposition and expiry. It does not print vulnerability
descriptions, environment variables, request data or secret values.

## Initial reviewed exceptions

The initial API exceptions cover 13 unique upstream-unfixed Debian
CVEs represented by 16 package findings. Review established that:

- Perl, gzip and several ncurses packages are Debian essential
  components and cannot be safely removed.
- SQLite and ncurses libraries are linked into Python runtime modules.
- The application does not expose the affected Perl, archive,
  terminal, SQLite FTS5, gzip LZH or ACL mutation surfaces.
- Debian 13 did not provide fixed package versions at acceptance time.

These exceptions expire on 2026-09-29. They cease to authorize a
finding immediately when Trivy reports a fixed version, even before
the expiry date.

## Exception approval

A new or renewed exception requires:

1. the exact image label, CVE and package;
2. confirmation that no fixed version is available;
3. documented runtime reachability and compensating controls;
4. a named owner;
5. an acceptance date;
6. an expiry no more than 31 days later; and
7. review through a pull request.

Do not accept a finding merely to make CI pass. Fixable findings must
be remediated.

## Ownership and cadence

The repository owner is responsible for scanner versions, base-image
refreshes and exception review.

Scanning runs on every applicable pull request and every push to
`main`. In addition:

- review scanner versions monthly;
- rebuild against current base images at least monthly;
- review exceptions before their expiry;
- respond immediately to a newly fixable CRITICAL finding; and
- remove stale exceptions in the same pull request that removes the
  associated finding.

Scanner failures and possible secret findings must be investigated in
private. If a real secret is detected, rotate or revoke it before
removing it from source and history.
