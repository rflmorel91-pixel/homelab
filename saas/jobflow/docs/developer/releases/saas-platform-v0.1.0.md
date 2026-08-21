# SaaS Platform 0.1.0 Internal Release Record

Status: Approved internal validation release
Release date: 2026-08-21
Distribution: Internal validation only
Platform package: `jobflow-saas-platform`
Platform version: `0.1.0`
Supported contract: Platform Contract v1

---

## 1. Release Decision

Platform version `0.1.0` is approved as the first internal validation
release.

This approval confirms that the platform can be built, tested,
packaged, installed, and used to validate bundled and standalone
products.

This is not a public package release.

No PyPI publication, public release announcement, production package
rollout, or Git tag is approved by this record.

---

## 2. Approved Source

Approved Git commit:

`90fa9183d54e452ce1731617ebed8f6376584c2a`

Commit description:

`Document platform release policy`

Repository:

`rflmorel91-pixel/homelab`

Platform source location:

`saas/jobflow/backend`

The release record itself is documentation created after the approved
artifact commit.

---

## 3. Compatibility

Supported platform contract:

`1`

Contract source:

`backend/app/platform/products.py`

The approved release validates products declaring:

`platform_contract_version=1`

No support for multiple simultaneous contract versions is claimed.

---

## 4. Migration State

Approved migration head:

`385d6260b08a`

Migration graph status:

- One supported head
- Platform and product migrations discoverable
- Clean-database upgrade verified in CI
- Alembic drift check passed
- No new upgrade operations detected locally

JobFlow retains historical migrations in the legacy shared migration
tree. Its product-specific migration-location count is therefore `0`
in validator output, while its schema remains covered by the global
migration graph.

---

## 5. CI Evidence

GitHub Actions workflow:

`SaaS Platform CI`

Successful run:

`32534793511`

Run URL:

https://github.com/rflmorel91-pixel/homelab/actions/runs/32534793511

Run commit:

`90fa9183d54e452ce1731617ebed8f6376584c2a`

Run conclusion:

`success`

Validated jobs:

- Product Contract Validation
- Backend Tests and Migration Check

Validated platform capabilities:

- Five bundled product definitions
- Contract v1 compatibility
- Product route and API-prefix uniqueness
- Public and tenant router registration
- Product model discovery
- Product migration discovery
- Generated product round trip
- Standalone plugin wheel installation
- Platform release wheel installation
- PostgreSQL migration upgrade
- Full backend test suite
- Alembic migration-drift check

Backend test result:

`312 passed`

---

## 6. Artifact Evidence

Validated artifact:

`jobflow_saas_platform-0.1.0-py3-none-any.whl`

SHA-256:

`9548970fcbc541cceb2894b3339d22bb138072fbd47254ec583ea1a3d30445b4`

Artifact behavior verified:

- Built from the approved source commit
- Installed into a clean Python virtual environment
- Installed declared dependencies
- Exposed supported platform commands
- Discovered all five bundled products
- Discovered bundled product models
- Discovered bundled product migration locations
- Completed product validation successfully

The validation artifact was temporary and is not designated as a
durable distribution artifact.

A future distributed artifact must be rebuilt from an approved commit,
assigned its own checksum, retained securely, and recorded separately.

---

## 7. Bundled Product Evidence

Validated bundled products:

- AssetTrack `0.1.0`
- JobFlow `1.0.0`
- PermitPulse `0.1.0`
- ProofVault `0.1.0`
- RenewalDesk `0.1.0`

These product versions are independent from platform version `0.1.0`.

Their inclusion validates the shared platform runtime. It does not
claim commercial validation for any product.

---

## 8. Standalone Plugin Evidence

The platform CI generated, built, installed, discovered, and validated
an independent `saas_products.*` plugin.

The proof included:

- Standalone Python project generation
- Tenant-scoped resource model
- Public product router
- Tenant-scoped CRUD router
- Contract v1 declaration
- Wheel construction
- Wheel installation
- Model discovery
- Migration-location preservation
- Product validation outside the source workspace

This proves the packaging mechanism.

It does not constitute validation by an external developer.

---

## 9. Known Limitations

The following limitations remain:

- Python `3.14` or newer is required
- Only Platform Contract v1 is supported
- Public package distribution is not configured
- No package-signing policy is implemented
- No durable artifact repository is configured
- No automated release-tag workflow exists
- No public support or deprecation commitment exists beyond Contract v1
- No external developer has independently integrated a product
- The platform package retains the legacy JobFlow-derived package name
- Bundled reference products remain inside the platform distribution
- JobFlow migrations remain in the historical shared migration tree
- Production rollback of a wheel-based deployment has not been tested
- The validated wheel was not deployed to production

---

## 10. Security and Operations

The release uses:

- Pinned direct runtime dependencies
- CI installation in clean Python environments
- PostgreSQL-backed tests
- Authentication and tenant-isolation tests
- Migration validation
- Product lifecycle validation
- Read-only GitHub Actions workflow permissions

No production credentials are embedded in the release record or CI
workflow.

CI database and JWT values are isolated test-only configuration.

---

## 11. Distribution Decision

Decision:

`Do not publish`

Reasons:

- No validated external distribution need
- Package naming has not been finalized
- License and public-distribution review is incomplete
- Artifact signing and provenance are not defined
- Support expectations are not ready
- An external developer integration has not occurred

Allowed use:

- Internal platform development
- Internal wheel validation
- CI compatibility testing
- Controlled deployment experiments
- Reference-product development

---

## 12. Tag Decision

No repository tag is created for this validation record.

The reserved future tag format is:

`saas-platform-v0.1.0`

A tag should be created only if this internal validation state is
promoted to a retained, deployable release artifact.

Existing tags must never be moved or reused.

---

## 13. Rollback Position

No production deployment was performed from this wheel.

Therefore no production rollback action is required.

For a future wheel deployment:

- Preserve the previous approved artifact
- Verify database-schema compatibility
- Record the deployed migration head
- Validate API health and product discovery after deployment
- Restore the previous artifact only when schema-compatible
- Use the database recovery procedure for incompatible schema changes

---

## 14. Roadmap Position

Current platform roadmap position:

Build → **Document** → Demonstrate → Customer Validation → Package → Sell

This record documents package readiness without advancing the platform
to public packaging or selling.

Product commercial validation remains independent from platform
technical readiness.

---

## 15. Single Next Milestone

Exercise the documented platform release process on the next
intentional platform version change.

That change must:

- Select a semantic version increment
- Preserve or deliberately update Contract v1 compatibility
- Pass all SaaS Platform CI gates
- Produce a clean-install wheel
- Record the migration head and artifact checksum
- Produce a new internal release record
- Avoid public publication unless the distribution gate is satisfied
