from pathlib import Path

from app.platform import (
    discover_product_migration_locations,
)


def test_discovers_renewaldesk_migrations():
    locations = (
        discover_product_migration_locations()
    )

    names = {
        path.parts[-3]
        for path in locations
    }

    assert "renewaldesk" in names


def test_only_returns_versions_directories():
    locations = (
        discover_product_migration_locations()
    )

    assert locations

    for location in locations:
        assert location.name == "versions"
        assert location.parent.name == "migrations"


def test_ignores_products_without_migrations(
    tmp_path,
):
    backend = tmp_path / "backend"

    (
        backend
        / "app"
        / "products"
        / "without_migrations"
    ).mkdir(
        parents=True,
    )

    locations = (
        discover_product_migration_locations(
            backend
        )
    )

    assert locations == ()


def test_discovers_multiple_product_locations(
    tmp_path,
):
    backend = tmp_path / "backend"

    for product in (
        "alpha",
        "beta",
    ):
        (
            backend
            / "app"
            / "products"
            / product
            / "migrations"
            / "versions"
        ).mkdir(
            parents=True,
        )

    locations = (
        discover_product_migration_locations(
            backend
        )
    )

    assert [
        path.parts[-3]
        for path in locations
    ] == [
        "alpha",
        "beta",
    ]
