# SaaS Platform Versioning and Release Policy

Version: 1.0
Status: Active internal policy
Last updated: 2026-08-21

---

## 1. Purpose

This policy governs versioning, compatibility, validation, packaging,
release approval, and rollback for `jobflow-saas-platform`.

It applies to the shared platform runtime and developer tooling.

Individual products use independent product versions.

---

## 2. Version Boundaries

The system has three independent version boundaries:

### Platform Package Version

The version in `backend/pyproject.toml` identifies a release of the
shared platform runtime and developer tools.

Current platform package version:

`0.1.0`

### Platform Contract Version

`PLATFORM_CONTRACT_VERSION` identifies the product integration
contract.

Current contract version:

`1`

The contract version is not derived from the platform package version.

### Product Version

Each `ProductDefinition` declares its own product version.

Product versions describe product behavior and do not change the
platform package or contract version automatically.

---

## 3. Source of Truth

The authoritative platform package version is:

`backend/pyproject.toml`

The authoritative contract version is:

`backend/app/platform/products.py`

The authoritative product version is each product's
`ProductDefinition`.

Release tags, artifacts, documentation, and deployment records must
match these sources.

---

## 4. Platform Versioning

The platform follows semantic versioning.

### Patch Version

Increment the patch version for compatible fixes, including:

- Defect corrections
- Security fixes that preserve supported interfaces
- Documentation corrections
- Test and CI improvements
- Packaging corrections
- Compatible operational hardening

### Minor Version

Increment the minor version for compatible platform capabilities,
including:

- New optional Contract v1 fields with safe defaults
- New developer tools
- New validation checks for existing requirements
- New platform-owned services
- Compatible administration or lifecycle capabilities

### Major Version

Increment the major version for a substantial platform distribution or
runtime change.

A major package version does not automatically require a new contract
version, and a new contract version does not require the same numeric
package version.

---

## 5. Pre-1.0 Rule

Although the package is currently below `1.0.0`, Platform Contract v1
is treated as an explicit compatibility commitment.

A platform `0.x` release may change undocumented internals.

It may not silently break a valid Contract v1 product.

A Contract v1 breaking change requires the deliberate contract-version
process defined in `platform-contract-v1.md`.

---

## 6. Product Versioning

Products version independently from the platform.

A product version should change when its own behavior, data model,
workflow, or supported interface changes.

Examples:

- RenewalDesk `0.1.0` may move to `0.2.0` without changing the platform
- JobFlow `1.0.0` may receive a patch without changing Contract v1
- A platform patch may ship without changing any product version

Product changes must still pass the platform validator and migration
checks.

---

## 7. Compatibility Policy

Every platform release must declare which contract versions it
supports.

The current supported contract set is:

- Platform Contract v1

A release claiming Contract v1 compatibility must:

- Discover valid Contract v1 products
- Compose their routers
- Enforce product and tenant boundaries
- Discover product models
- Discover product migrations
- Preserve supported developer tooling
- Pass product validation
- Pass representative product tests

Breaking changes must follow the deprecation and compatibility rules in
`platform-contract-v1.md`.

---

## 8. Release Identifiers

Repository tags for platform releases should use:

`saas-platform-v<version>`

Example:

`saas-platform-v0.1.0`

Release candidates should use:

`saas-platform-v<version>-rc.<number>`

Example:

`saas-platform-v0.2.0-rc.1`

Do not create a release tag unless the commit has passed all release
gates.

---

## 9. Release Gates

A platform release candidate must pass:

- Product Contract Validation
- Generated product round-trip validation
- Installed standalone-plugin validation
- Platform wheel build and clean installation
- Full backend test suite
- PostgreSQL migration upgrade
- Alembic migration-drift check
- Git diff whitespace validation
- Clean source-control state
- Review of security-sensitive changes

The authoritative automated gate is:

`SaaS Platform CI`

A failed required job blocks release approval.

---

## 10. Migration Gate

Before release:

- The global migration graph must have one supported head
- Revision identifiers must be unique
- Product migration locations must be discoverable
- Upgrade to head must succeed on a clean database
- Alembic check must report no new upgrade operations
- Production-impacting migrations must have backup and recovery plans

Application rollback is allowed only when the deployed database schema
remains compatible with the previous application version.

Destructive schema rollback should use an approved database recovery
procedure rather than an improvised downgrade.

---

## 11. Release Artifacts

The primary platform artifact is a Python wheel for:

`jobflow-saas-platform`

A release artifact must:

- Match the version in `backend/pyproject.toml`
- Install into a clean supported Python environment
- Include platform runtime packages
- Include supported developer commands
- Include required migration templates
- Discover bundled products correctly
- Support installed `saas_products.*` plugins

Artifact checksums should be retained with any distributed release.

---

## 12. Release Record

Each approved release should record:

- Platform version
- Git commit
- Repository tag
- Release date
- Supported contract versions
- Included migration head
- CI run
- Security-relevant changes
- Known limitations
- Rollback constraints
- Artifact checksum
- Deployment result

A Git tag alone is not a complete operational release record.

---

## 13. Release Procedure

1. Confirm the intended platform version.
2. Review changes since the previous platform release.
3. Classify the change as patch, minor, or major.
4. Confirm Contract v1 compatibility.
5. Update the package version.
6. Run the full local validation suite.
7. Commit and push the release candidate.
8. Confirm all SaaS Platform CI jobs pass.
9. Build the wheel from the approved commit.
10. Verify the wheel in a clean environment.
11. Record the release evidence.
12. Create the namespaced platform tag.
13. Deploy only from the approved commit or artifact.
14. Perform post-deployment health and migration verification.

---

## 14. Rollback Procedure

If a release fails after deployment:

1. Stop further rollout.
2. Record the observed failure.
3. Determine whether the database schema changed.
4. If schema-compatible, redeploy the previous approved artifact.
5. If schema-incompatible, follow the documented recovery plan.
6. Verify API health, product discovery, authentication, tenancy, and
   migrations.
7. Record the rollback result.
8. Fix forward in a new patch release.

Do not move or reuse an existing release tag.

---

## 15. Distribution Gate

Public package publication is not currently approved.

Do not publish to PyPI until:

- An external developer or deployment has a validated distribution need
- Package naming and ownership are confirmed
- License and commercial-distribution obligations are reviewed
- Release credentials and ownership are secured
- Artifact signing or provenance requirements are selected
- Support and deprecation expectations are ready

Until then, wheel building and installation remain internal validation
activities.

---

## 16. Premature Work Guardrail

Before a validated distribution need exists, avoid:

- Automated public publishing
- Multiple release channels
- Plugin marketplaces
- Complex compatibility matrices
- Long-term-support editions
- Automated downgrade systems
- Public stability claims beyond Contract v1
- Release infrastructure for hypothetical consumers

Allowed work includes:

- Compatibility enforcement
- CI release gates
- Reproducible wheel validation
- Internal release documentation
- Security and migration controls
- Evidence required for a real deployment

---

## 17. Current Release Position

Current platform package:

`0.1.1`

Current supported contract:

`1`

Current distribution status:

Internal source and wheel validation only.

Current internal release record:

`releases/saas-platform-v0.1.0.md`

Current release readiness:

- Contract validation automated
- Product generation validation automated
- Standalone plugin installation automated
- Platform wheel installation automated
- Full PostgreSQL-backed tests automated
- Migration upgrade and drift checks automated
- Public package publication not approved

---

## 18. Single Next Milestone

Create the first internal platform release record for version `0.1.0`
without publishing the package publicly.

The record must reference:

- The approved Git commit
- The successful CI run
- Contract v1 support
- Migration head
- Wheel verification
- Known limitations
- The decision not to publish publicly
