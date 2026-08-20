from importlib import import_module
from pathlib import Path

from app.platform.installed_product_discovery import (
    installed_product_packages,
)


def installed_product_migration_locations(
) -> tuple[Path, ...]:
    discovered: list[Path] = []

    for package in installed_product_packages():
        module_name = (
            f"saas_products."
            f"{package}.migrations"
        )

        try:
            migrations = import_module(
                module_name
            )
        except ModuleNotFoundError as exc:
            if exc.name == module_name:
                continue

            raise

        versions = (
            Path(
                migrations.__file__
            ).resolve().parent
            / "versions"
        )

        if versions.is_dir():
            discovered.append(
                versions.resolve()
            )

    return tuple(
        sorted(discovered)
    )
