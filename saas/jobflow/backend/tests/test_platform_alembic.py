from pathlib import Path

from scripts.platform_alembic import build_config


def test_platform_alembic_includes_platform_versions():
    config = build_config()

    locations = config.get_main_option(
        "version_locations"
    ).split()

    assert any(
        Path(location).name == "versions"
        and Path(location).parent.name
        == "migrations"
        and "app/products" not in location
        for location in locations
    )


def test_platform_alembic_includes_renewaldesk():
    config = build_config()

    locations = config.get_main_option(
        "version_locations"
    ).split()

    assert any(
        "app/products/renewaldesk/"
        "migrations/versions"
        in location
        for location in locations
    )


def test_platform_alembic_uses_space_separator():
    config = build_config()

    assert (
        config.get_main_option(
            "path_separator"
        )
        == "space"
    )
