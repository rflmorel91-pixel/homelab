# SaaS Platform Contract v1

## Purpose

Platform Contract v1 defines the supported integration boundary between
the SaaS platform and independently developed product packages.

A product declaring:

    platform_contract_version=1

is asserting that it was built against the guarantees documented here.

The platform rejects products targeting a different contract version.

---

## Contract v1 Guarantees

### Product identity

A product may declare:

- slug
- name
- version
- platform_contract_version
- workspace_key
- landing_route
- workspace_route
- api_prefix
- public/product routers
- tenant-scoped routers
- description

Product slugs and workspace keys must remain unique.

The product slug should be treated as persistent product identity.

---

## Product Discovery

A product package placed under:

    app/products/<package>/

is discoverable when it contains:

    definition.py

The product definition module is loaded automatically.

No central registration edit is required.

---

## Router Composition

Contract v1 supports two router classes.

### Public/product routers

Declared through:

    routers=(...)

They inherit product lifecycle enforcement.

They do not automatically require authentication or tenant context.

Appropriate uses include:

- public product status
- product landing APIs
- public acquisition surfaces
- non-tenant product endpoints

### Tenant routers

Declared through:

    tenant_routers=(...)

They inherit:

- product lifecycle enforcement
- authentication
- tenant context
- user membership enforcement
- tenant lifecycle enforcement
- tenant-to-product ownership enforcement

Products should use tenant routers for customer-owned domain data.

---

## Product Lifecycle

The platform owns runtime Product status.

Current active product behavior:

    status = active

A suspended or inactive product is blocked at the platform boundary.

Product code must not implement a parallel product lifecycle mechanism.

A deployment must not silently reactivate a product that was suspended
by a platform operator.

---

## Tenant Isolation

Tenant-scoped product resources must derive tenant identity from the
trusted platform tenant context.

Request bodies must not control tenant ownership.

Product tables containing tenant-owned data should include:

    tenant_id -> tenants.id

Product queries must scope resources by the authenticated tenant.

Cross-tenant resource access should normally appear as not found rather
than exposing ownership information.

---

## Product Models

Products may own SQLAlchemy models under:

    app/products/<product>/models/

The platform automatically discovers product model packages before
SQLAlchemy metadata is consumed.

Product developers do not need to modify:

    app/models/__init__.py

to register product-owned models.

---

## Product Migrations

Products may own Alembic revisions under:

    app/products/<product>/migrations/versions/

The platform migration wrapper automatically discovers these locations.

Product revisions participate in one global Alembic revision graph.

Contract v1 requires a deterministic single-head migration history.

Product migrations must not create independent unmanaged migration
graphs.

---

## Supported Migration Interface

From the backend directory:

    python scripts/platform_alembic.py heads

    python scripts/platform_alembic.py current

    python scripts/platform_alembic.py revision \
      --product <slug> \
      --autogenerate \
      -m "<message>"

    python scripts/platform_alembic.py upgrade head

    python scripts/platform_alembic.py check

Product developers should use the platform migration wrapper rather than
manually configuring Alembic version locations.

---

## Product Generation

Contract v1 supports simple products:

    python scripts/create_product.py \
      example \
      "Example"

and data-bearing products:

    python scripts/create_product.py \
      assettrack \
      "AssetTrack" \
      --description "Track customer assets." \
      --with-resource asset

The generated product explicitly declares:

    platform_contract_version=1

The generator does not silently target whatever contract version may be
introduced in the future.

---

## Platform-Owned Interfaces

The following are supported Contract v1 interfaces:

- ProductDefinition
- register_product()
- get_product()
- list_products()
- discover_products()
- automatic product model discovery
- product migration discovery
- product lifecycle enforcement
- public router composition
- tenant router composition
- tenant-to-product enforcement
- installed-product synchronization
- product generator
- platform Alembic wrapper

Changes to these interfaces must follow the compatibility policy below.

---

## Internal Implementation

Files and functions not explicitly identified as supported Contract v1
interfaces should be considered internal implementation details.

Third-party products should not depend on internal module structure
unless the contract explicitly exposes it.

---

## Non-Breaking Changes Within v1

The platform may make compatible changes without introducing Contract
v2, including:

- bug fixes
- security fixes that preserve supported interfaces
- internal refactoring
- performance improvements
- new optional ProductDefinition capabilities with safe defaults
- new platform APIs
- new generator options
- new administrative functionality
- additional validation that rejects previously invalid configurations
- documentation improvements
- new lifecycle states when existing active behavior remains compatible

A non-breaking change must not require an existing valid Contract v1
product to modify its code merely to continue loading and operating.

---

## Breaking Changes

A change requires a new platform contract version when it would require
an existing valid Contract v1 product to change its integration code.

Examples include:

- removing or renaming ProductDefinition fields
- changing required router registration semantics
- changing tenant ownership semantics
- changing product discovery conventions
- changing model discovery conventions
- removing supported platform functions
- changing migration ownership rules incompatibly
- requiring new mandatory product metadata with no compatible default
- changing authentication or tenant context in a way that breaks
  existing Contract v1 tenant routers

Breaking changes must not be introduced silently under Contract v1.

---

## Deprecation Policy

Before a supported Contract v1 interface is removed or replaced:

1. the replacement should be documented;
2. the old interface should be marked deprecated;
3. migration guidance should be published;
4. Contract v1 products should continue operating during the
   deprecation window whenever practical;
5. removal should occur only in a contract version where that breaking
   change is permitted.

Security vulnerabilities may require accelerated changes, but those
changes should still be documented.

---

## Contract v2 Introduction

A future Contract v2 must not silently reinterpret:

    platform_contract_version=1

A Contract v1 product must either:

- continue to run under explicitly supported v1 compatibility, or
- fail clearly before serving product traffic.

A v2 product must explicitly declare:

    platform_contract_version=2

Contract upgrades should be intentional developer actions.

---

## Compatibility Testing

Before releasing a platform change intended to remain Contract v1
compatible, the platform should run:

    pytest -q

and validate representative independent products.

Current representative products include:

- JobFlow
- RenewalDesk
- AssetTrack
- ProofVault
- PermitPulse

Data-bearing product validation should include:

- product discovery
- router composition
- lifecycle enforcement
- tenant ownership
- tenant isolation
- model discovery
- migration discovery
- migration graph integrity
- CRUD behavior where applicable

---

## Migration Graph Policy

Contract v1 uses one global migration history.

Requirements:

- exactly one supported head under normal release conditions;
- product revisions must chain into the shared history;
- revision IDs must be unique;
- product revision files remain product-owned;
- migration upgrades must be validated before production deployment;
- `platform_alembic.py check` should be clean after migrations are
  applied.

Multiple unmanaged product heads are not part of Contract v1.

---

## Developer Responsibility

Product developers are responsible for:

- product-specific business logic
- product-specific schemas
- product-specific models
- product-specific tenant resource filtering
- product-specific migrations
- product-specific tests
- maintaining compatibility with the declared platform contract

The platform is responsible for enforcing the shared control-plane
boundaries documented here.

---

## Platform Responsibility

The platform is responsible for:

- authentication
- tenant membership
- tenant lifecycle
- tenant-to-product ownership
- product lifecycle
- product discovery
- router composition
- product synchronization
- product model discovery
- product migration discovery
- supported developer tooling
- compatibility validation

---

## Contract Rule

A product that declares Platform Contract v1 should not need to modify
platform-core registration, routing, model discovery, migration
discovery, or tenant/product authorization code in order to operate.

If a product requires such a modification, either:

- the capability belongs in product code, or
- the platform contract needs to be extended deliberately.
