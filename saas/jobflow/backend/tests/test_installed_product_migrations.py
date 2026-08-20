from app.platform.installed_product_migrations import (
    installed_product_migration_locations,
)


def test_installed_migration_locations_returns_tuple():
    locations = (
        installed_product_migration_locations()
    )

    assert isinstance(
        locations,
        tuple,
    )
