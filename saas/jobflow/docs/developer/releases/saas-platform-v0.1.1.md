# SaaS Platform 0.1.1 Internal Release Record

Status: Approved internal validation release
Release date: 2026-08-21
Distribution: Internal validation only
Platform package: `jobflow-saas-platform`
Platform version: `0.1.1`
Supported contract: Platform Contract v1

---

## 1. Release Decision

Platform version `0.1.1` is approved as an internal patch release.

This release improves migration-tool configuration behavior and keeps
generated standalone-product dependencies synchronized with the
platform package version.

This is not a public package release.

No PyPI publication, public announcement, production wheel rollout, or
Git tag is approved.

---

## 2. Version Classification

Previous internal version:

`0.1.0`

Current internal version:

`0.1.1`

Classification:

`Patch`

Rationale:

- Supported Contract v1 interfaces remain compatible
- No database schema change is introduced
- No product API is removed
- Migration CLI behavior is corrected
- Generator version synchronization is corrected
- Existing valid products require no changes

---

## 3. Approved Source

Approved Git commit:

`b4eac4d2f7a8201b64ab01c989fa26434f9d94f5`

Commit description:

`Prepare platform 0.1.1 migration tooling`

Repository:

`rflmorel91-pixel/homelab`

Platform source:

`saas/jobflow/backend`

This release record is documentation created after the approved
artifact commit.

---

## 4. Included Changes

### Migration CLI Help

`saas-alembic --help` now succeeds without application configuration.

The help output documents:

- heads
- current
- history
- upgrade
- downgrade
- revision
- check

### Database Configuration

Migration commands now fail clearly with exit code `2` when
`DATABASE_URL` is absent.

The failure does not produce an application-import traceback.

### Authentication Configuration

Migration tooling no longer requires a production `JWT_SECRET`.

Migration commands use isolated tooling configuration for imports while
continuing to require an explicit database URL.

### Generator Version Synchronization

Standalone products now derive their platform dependency from the
current source or installed platform package version.

Generated `0.1.1` products declare:

`jobflow-saas-platform==0.1.1`

This removes the previous hardcoded `0.1.0` dependency.

---

## 5. Compatibility

Supported contract:

`Platform Contract v1`

Contract version:

`1`

Compatibility decision:

`Compatible`

All five bundled products validate without changes:

- AssetTrack `0.1.0`
- JobFlow `1.0.0`
- PermitPulse `0.1.0`
- ProofVault `0.1.0`
- RenewalDesk `0.1.0`

No multi-version contract support is claimed.

---

## 6. Migration State

Approved migration head:

`385d6260b08a`

Migration change in this release:

`None`

Migration validation:

- Existing global head preserved
- Clean-database upgrade passed in CI
- Alembic drift check passed
- No new upgrade operations detected
- Product migration discovery passed
- Real PostgreSQL head inspection passed without `JWT_SECRET`

JobFlow retains historical schema revisions in the shared migration
tree.

---

## 7. Test Evidence

Local full-suite result:

`315 passed`

Focused migration and generator result:

`25 passed`

Verified behaviors include:

- Migration help without `DATABASE_URL`
- Clear missing-database error
- Migration operation without `JWT_SECRET`
- Dynamic standalone dependency version
- Product discovery and validation
- Authentication and authorization
- Tenant isolation
- Product lifecycle
- Administration
- Commercialization
- Reminder processing and SMTP behavior
- Migration graph integrity

---

## 8. CI Evidence

Workflow:

`SaaS Platform CI`

Successful run:

`32535941983`

Run URL:

https://github.com/rflmorel91-pixel/homelab/actions/runs/32535941983

Run commit:

`b4eac4d2f7a8201b64ab01c989fa26434f9d94f5`

Conclusion:

`success`

Successful jobs:

- Product Contract Validation
- Backend Tests and Migration Check

Successful release gates:

- Installed product validation
- Generated product round trip
- Installed standalone-plugin validation
- Platform release-wheel validation
- PostgreSQL initialization
- Migration upgrade
- Full backend test suite
- Migration-drift check

---

## 9. Artifact Evidence

Validated wheel:

`jobflow_saas_platform-0.1.1-py3-none-any.whl`

SHA-256:

`d2cdcebdac1ab84973cf618e1df4cfd1c4cac94ed3beb94eb1cac72de475dbb6`

Clean-install validation confirmed:

- Platform dependencies installed
- Migration CLI installed
- Migration help worked without application configuration
- Product validator installed
- Five bundled products discovered
- Product models discovered
- Product migrations discovered
- Contract v1 validation succeeded

The wheel was a temporary validation artifact and is not retained as a
public or production distribution artifact.

---

## 10. Security and Operations

Security-relevant decisions:

- No production database credential is embedded
- No production JWT secret is embedded
- Migration operations still require an explicit database URL
- The migration-only JWT fallback is process-local tooling
  configuration
- GitHub Actions retains read-only repository permissions
- CI uses isolated test database and JWT values
- No customer or production data was used

---

## 11. Known Limitations

Current limitations include:

- Python `3.14` or newer is required
- Only Platform Contract v1 is supported
- Public package distribution is not configured
- No durable artifact repository is configured
- No package-signing or provenance policy is implemented
- No automated release-tag workflow exists
- No external developer has completed the documented journey
- The package retains its legacy JobFlow-derived name
- Bundled reference products remain in the platform wheel
- JobFlow migrations remain in the historical shared migration tree
- Production wheel deployment and rollback remain untested

---

## 12. Distribution and Tag Decision

Distribution decision:

`Do not publish`

Tag decision:

`Do not tag`

Reasons:

- No validated public distribution need
- External developer demonstration remains incomplete
- Package naming and ownership are not final
- Licensing review is incomplete
- Artifact retention and signing are undefined
- Support expectations are not ready

The future reserved tag is:

`saas-platform-v0.1.1`

It must not be created unless this internal release is promoted to a
retained deployable artifact.

---

## 13. Rollback Position

This release introduces no schema change.

No production wheel deployment occurred.

If later deployed, application rollback to `0.1.0` is expected to be
schema-compatible because migration head `385d6260b08a` is unchanged.

That expectation must still be verified in the target environment
before rollback.

---

## 14. Roadmap Position

Current platform position:

Build → Document → **Demonstrate** → Customer Validation → Package → Sell

The `0.1.1` patch removes a developer-demonstration blocker.

It does not advance the platform to public packaging or selling.

---

## 15. Single Next Milestone

Complete and exercise the platform developer demonstration runbook.

The runbook must show that a developer can:

- Inspect the supported commands
- Generate a standalone product
- Install the product
- Validate Contract v1
- Configure a database explicitly
- Inspect migration heads
- Run the platform application
- Verify automatic product discovery
- Record positive and negative developer feedback

Further speculative platform features remain premature until this
developer journey is exercised.
