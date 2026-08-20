from importlib import import_module
from pathlib import Path

from app.platform.installed_product_discovery import (
    import_installed_product_models,
    installed_product_packages,
)
from app.platform.product_discovery import (
    ProductDiscoveryError,
)
from app.platform.product_paths import (
    product_roots,
    temporary_product_root,
)


def discover_product_models(
    root: Path | None = None,
) -> tuple[str, ...]:
    discovered: list[str] = []

    with temporary_product_root(root):
        for products_path in product_roots():
            for entry in sorted(
                products_path.iterdir()
            ):
                if not entry.is_dir():
                    continue

                if entry.name.startswith("_"):
                    continue

                models_package = (
                    entry
                    / "models"
                )

                if not models_package.is_dir():
                    continue

                init_file = (
                    models_package
                    / "__init__.py"
                )

                if not init_file.is_file():
                    continue

                module_name = (
                    "app.products."
                    f"{entry.name}.models"
                )

                try:
                    import_module(module_name)
                except Exception as exc:
                    raise ProductDiscoveryError(
                        "Failed to load product models "
                        f"for {entry.name}: {exc}"
                    ) from exc

                if entry.name not in discovered:
                    discovered.append(
                        entry.name
                    )

    for package in installed_product_packages():
        try:
            has_models = (
                import_installed_product_models(
                    package
                )
            )
        except Exception as exc:
            raise ProductDiscoveryError(
                "Failed to load installed product "
                f"models for {package}: {exc}"
            ) from exc

        if (
            has_models
            and package not in discovered
        ):
            discovered.append(
                package
            )

    return tuple(
        sorted(discovered)
    )
