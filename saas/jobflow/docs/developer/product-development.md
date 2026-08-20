# SaaS Platform Product Development

## Purpose

This platform is designed to host independently developed SaaS products
on shared platform infrastructure.

A product developer should be able to add a product without modifying
platform-core registration, routing, synchronization, or lifecycle code.

The platform owns the reusable control plane.
Products own their product-specific application behavior.

## Architecture Boundary

### Platform owns

The platform is responsible for:

- product discovery
- product registration
- product metadata synchronization
- API router composition
- product lifecycle enforcement
- users and authentication
- tenants and memberships
- platform administration
- commercialization infrastructure
- audit infrastructure
- shared database/session infrastructure

### Product owns

A product may own:

- product-specific API routers
- product-specific business logic
- product-specific schemas
- product-specific data models
- product-specific frontend/workspace behavior
- product-specific tests
- product-specific migrations, once the migration contract is formalized

A product must declare itself through `ProductDefinition`.

## Supported Developer Interface

The supported extension interface currently consists of:

- `ProductDefinition`
- `register_product()`
- `get_product()`
- `list_products()`
- automatic product discovery
- product router composition
- product lifecycle enforcement
- installed-product database synchronization
- the product generator

Anything not explicitly identified as part of the developer contract
should currently be considered internal.

## Creating a Product

From the backend directory:

    python scripts/create_product.py \
      client-portal \
      "Client Portal" \
      --description "Client collaboration and document exchange."

The generator creates:

    app/products/client_portal/
        __init__.py
        api.py
        definition.py

    tests/
        test_client_portal_product.py

No platform-core registration edit is required.

## Product Package Discovery

The platform scans `app/products/`.

A directory is considered an installable product package when it
contains `definition.py`.

The platform imports:

    app.products.<package>.definition

The definition module registers its `ProductDefinition`.

Directories beginning with `_` are ignored.
Directories without `definition.py` are ignored.
Failure to import a discovered product is a platform startup error.

## ProductDefinition Contract

A product declares:

    ProductDefinition(
        slug="example",
        name="Example",
        version="1.0.0",
        workspace_key="example",
        landing_route="/example",
        workspace_route="/example/app",
        api_prefix="/api/v1/products/example",
        routers=(router,),
        description="Example SaaS product.",
    )

### slug

Stable machine identifier for the product.

Requirements:

- non-empty
- lowercase
- letters, numbers, and hyphens only
- unique across installed products

The slug should be treated as a persistent product identity.

### name

Human-readable product name.

### version

Developer-declared product version.

The platform currently validates that a version exists but does not yet
enforce semantic-version compatibility.

### workspace_key

Stable and unique workspace identifier.

### landing_route

Declared public landing route.

### workspace_route

Declared product workspace route.

### api_prefix

Base path under which product routers are composed.

Independent products should normally use:

    /api/v1/products/<slug>

### routers

Tuple of FastAPI `APIRouter` instances owned by the product.

The platform mounts these automatically.

### description

Human-readable product description.

## Routing Contract

Product routers define paths relative to their product API prefix.

For example, a router with:

    prefix="/projects"

and a product with:

    api_prefix="/api/v1/products/example"

produces:

    /api/v1/products/example/projects

Product developers must not manually register product routers in
`app/main.py`.

Router composition is platform-owned.

## Lifecycle Contract

Every product router composed through `ProductDefinition` automatically
inherits platform lifecycle enforcement.

Before a product API executes, the platform verifies that the database
Product exists and has:

    status = active

If the product does not exist:

    503 Product is unavailable

If the product is not active:

    403 Product is <status>

Products must not implement parallel product-status mechanisms.

Lifecycle state is platform-owned.

## Product Synchronization

At application startup, installed product definitions are synchronized
with database Product records.

New installed products are created with:

    status = active

Developer-owned metadata may evolve with the installed definition.

Currently developer-owned metadata includes:

- name
- workspace_key

Operator-owned runtime state currently includes:

- status

A deployment must not silently reactivate a product that an operator
suspended.

## Tenant and Product Ownership

Tenants and commercialization leads are product-aware.

A tenant belongs to a product.
A lead belongs to a product.

Provisioning a qualified lead into a tenant preserves product ownership.

Products must not assume every tenant belongs to them.

## Commercialization Contract

Public lead acquisition is product-scoped:

    /api/v1/public/products/<product-slug>/leads

This allows shared commercialization infrastructure to support multiple
SaaS products.

## Testing Contract

Every product should verify at minimum:

1. automatic discovery;
2. expected product identity;
3. automatic router composition;
4. Product database synchronization;
5. inherited lifecycle enforcement.

The generator creates these baseline tests automatically.

Product-specific business behavior requires additional product-owned
tests.

Before integration:

    pytest -q
    alembic check
    git diff --check

## Platform-Core Files

Product developers should normally not modify:

    app/main.py
    app/platform/products.py
    app/platform/product_discovery.py
    app/platform/product_sync.py
    app/platform/product_context.py
    app/products/__init__.py

A product requiring changes to these files is requesting a platform
capability or contract change.

## Product Directory Convention

Recommended structure:

    app/products/<product_package>/
        __init__.py
        definition.py
        api.py
        models/
        schemas/
        services/

Only required components need to exist.

## Database and Migration Boundary

Product-specific models and migration ownership are supported by
Platform Contract v1.

Product models may live under:

    app/products/<product>/models/

and are discovered automatically.

Product migration revisions may live under:

    app/products/<product>/migrations/versions/

The platform Alembic wrapper discovers product migration locations and
keeps product revisions in the shared deterministic migration graph.

From the backend directory:

    python scripts/platform_alembic.py revision       --product <slug>       --autogenerate       -m "<message>"

    python scripts/platform_alembic.py upgrade head

    python scripts/platform_alembic.py check

Contract v1 currently requires one global Alembic head.

Product removal and independent migration graphs are not yet supported
developer contracts.

## Compatibility

`ProductDefinition` is a supported Platform Contract v1 developer API.

Every product declares:

    platform_contract_version=1

The platform rejects products targeting an incompatible contract
version before they are loaded for operation.

See:

    docs/developer/platform-contract-v1.md

for compatibility, breaking-change, deprecation, and future Contract v2
policy.

## Developer Rule of Thumb

If adding a product requires editing platform registration code, the
extension contract is incomplete.

If a capability benefits every product, it probably belongs in the
platform.

If behavior is unique to one SaaS application, it probably belongs
inside that product package.
