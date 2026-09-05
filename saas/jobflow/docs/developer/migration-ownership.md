# Migration ownership

The platform has one canonical migration graph assembled by
`scripts/platform_alembic.py`.

## Canonical locations

Platform-owned historical and shared-schema revisions live in
`backend/app/platform/migrations/versions/`.

Product-owned revisions live in
`backend/app/products/<product>/migrations/versions/`.

Installed standalone products may contribute their declared migration
versions directories through the platform product contract.

The removed `backend/migrations/` directory is not a migration source
and must not be recreated.

## Historical JobFlow revisions

Existing applied JobFlow-era revisions remain platform-owned in the
canonical platform tree. Their revision identifiers, parent links and
contents must not be rewritten.

JobFlow is legacy and read-only. New JobFlow behavior and new JobFlow
schema migrations are not permitted. RenewalDesk, Workflow Automation,
and AssetTrack are active products and own new product-specific schema
changes in their respective migration trees.

## Enforcement

Every platform Alembic configuration validates that each discovered
revision identifier has exactly one owner. A duplicate identifier in
any platform, product or installed-product location stops the migration
command before database operations begin.

Use only the platform wrapper:

    cd saas/jobflow/backend
    python scripts/platform_alembic.py heads
    python scripts/platform_alembic.py current
    python scripts/platform_alembic.py upgrade head
    python scripts/platform_alembic.py check

Create an active-product migration with:

    python scripts/platform_alembic.py revision \
      --product <slug> \
      --autogenerate \
      -m "<message>"

Never invoke an obsolete migration directory directly. Never rename,
copy or rewrite an applied revision.
