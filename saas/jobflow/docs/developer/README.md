# Developer Documentation

## API Consumers

Start with:

- [AssetTrack Developer API v1](assettrack-developer-api-v1.md)

## Product Developers

Start with:

- [Product Development](product-development.md)
- [Platform Contract v1](platform-contract-v1.md)

The platform supports automatically discovered SaaS product packages
with platform-owned routing composition, synchronization, lifecycle
enforcement, and shared control-plane services.

## Product Validation

From the backend directory, validate all products:

    .venv/bin/python scripts/validate_product.py

Validate one product:

    .venv/bin/python scripts/validate_product.py <product-slug>

The command validates Contract v1 definitions, routes, router scopes,
models, and migration discovery without connecting to a database.

## Platform Developer Demonstration

The verified standalone-product developer journey is documented in:

`platform-developer-demonstration.md`

Use this runbook to conduct and record an external developer
demonstration before expanding the platform speculatively.

## Platform Release Policy

Platform package versioning, release gates, artifacts, rollback, and
distribution rules are defined in:

`platform-release-policy.md`

## Current Extension Status

Supported:

- product definitions
- automatic discovery
- router composition
- database product synchronization
- lifecycle enforcement
- generated product scaffolding
- pre-deployment product validation

Now formalized:

- product-specific migration ownership
- Platform Contract v1 compatibility enforcement

Not yet formalized:

- product dependency declarations
- product install/uninstall lifecycle
- multi-version contract compatibility
- external package distribution
