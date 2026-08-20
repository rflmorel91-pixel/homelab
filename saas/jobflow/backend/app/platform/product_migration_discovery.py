from pathlib import Path


def discover_product_migration_locations(
    backend_root: Path | None = None,
) -> tuple[Path, ...]:
    if backend_root is None:
        backend_root = (
            Path(__file__).resolve().parents[2]
        )

    products_path = (
        backend_root
        / "app"
        / "products"
    )

    discovered: list[Path] = []

    if not products_path.is_dir():
        return ()

    for entry in sorted(products_path.iterdir()):
        if not entry.is_dir():
            continue

        if entry.name.startswith("_"):
            continue

        versions = (
            entry
            / "migrations"
            / "versions"
        )

        if versions.is_dir():
            discovered.append(
                versions.resolve()
            )

    return tuple(discovered)
