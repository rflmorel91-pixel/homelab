import os
from pathlib import Path
import subprocess
import sys

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


def test_product_version_path_resolves_assettrack():
    from scripts.platform_alembic import (
        get_product_version_path,
    )

    path = get_product_version_path(
        "assettrack"
    )

    assert path.name == "versions"
    assert path.parent.name == "migrations"
    assert path.parent.parent.name == "assettrack"


def test_product_version_path_rejects_unknown_product():
    import pytest

    from scripts.platform_alembic import (
        get_product_version_path,
    )

    with pytest.raises(
        ValueError,
        match="Unknown product",
    ):
        get_product_version_path(
            "does-not-exist"
        )


def test_product_version_path_requires_migrations():
    import pytest

    from scripts.platform_alembic import (
        get_product_version_path,
    )

    with pytest.raises(
        ValueError,
        match="does not have a migration",
    ):
        get_product_version_path(
            "proofvault"
        )

def test_cli_help_does_not_require_application_environment(
    tmp_path,
):
    backend_root = (
        Path(__file__).resolve().parents[1]
    )
    environment = os.environ.copy()
    environment.pop(
        "DATABASE_URL",
        None,
    )
    environment.pop(
        "JWT_SECRET",
        None,
    )

    result = subprocess.run(
        [
            sys.executable,
            str(
                backend_root
                / "scripts"
                / "platform_alembic.py"
            ),
            "--help",
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Usage: saas-alembic" in result.stdout
    assert "upgrade REVISION" in result.stdout
    assert result.stderr == ""


def test_cli_command_requires_database_url(
    tmp_path,
):
    backend_root = (
        Path(__file__).resolve().parents[1]
    )
    environment = os.environ.copy()
    environment.pop(
        "DATABASE_URL",
        None,
    )
    environment.pop(
        "JWT_SECRET",
        None,
    )

    result = subprocess.run(
        [
            sys.executable,
            str(
                backend_root
                / "scripts"
                / "platform_alembic.py"
            ),
            "heads",
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert (
        "DATABASE_URL environment variable is required"
        in result.stderr
    )
    assert "Traceback" not in result.stderr


def test_cli_does_not_require_jwt_secret(
    tmp_path,
):
    backend_root = (
        Path(__file__).resolve().parents[1]
    )
    environment = os.environ.copy()
    environment[
        "DATABASE_URL"
    ] = "sqlite+pysqlite:///:memory:"
    environment.pop(
        "JWT_SECRET",
        None,
    )

    result = subprocess.run(
        [
            sys.executable,
            str(
                backend_root
                / "scripts"
                / "platform_alembic.py"
            ),
            "heads",
        ],
        cwd=backend_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        result.stdout + result.stderr
    )
    assert "(head)" in result.stdout
