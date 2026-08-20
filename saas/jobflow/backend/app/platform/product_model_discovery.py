from importlib import import_module
from pathlib import Path

from app.platform.product_discovery import (
    ProductDiscoveryError,
)


def discover_product_models() -> tuple[str, ...]:
    products_path = (
        Path(__file__).resolve().parents[1]
        / "products"
    )

    discovered = []

    for entry in sorted(products_path.iterdir()):
        if not entry.is_dir():
            continue

        if entry.name.startswith("_"):
            continue

        models_package = entry / "models"

        if not models_package.is_dir():
            continue

        init_file = models_package / "__init__.py"

        if not init_file.is_file():
            continue

        module_name = (
            f"app.products.{entry.name}.models"
        )

        try:
            import_module(module_name)
        except Exception as exc:
            raise ProductDiscoveryError(
                "Failed to load product models "
                f"for {entry.name}: {exc}"
            ) from exc

        discovered.append(entry.name)

    return tuple(discovered)
