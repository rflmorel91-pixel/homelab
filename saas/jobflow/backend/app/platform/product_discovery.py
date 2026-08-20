from importlib import import_module
from pathlib import Path

from app.platform.product_paths import (
    product_roots,
    temporary_product_root,
)


class ProductDiscoveryError(RuntimeError):
    pass


def discover_products(
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

                definition = (
                    entry
                    / "definition.py"
                )

                if not definition.is_file():
                    continue

                module_name = (
                    "app.products."
                    f"{entry.name}.definition"
                )

                try:
                    import_module(module_name)
                except Exception as exc:
                    raise ProductDiscoveryError(
                        "Failed to load product "
                        f"{entry.name}: {exc}"
                    ) from exc

                if entry.name not in discovered:
                    discovered.append(
                        entry.name
                    )

    return tuple(
        sorted(discovered)
    )
