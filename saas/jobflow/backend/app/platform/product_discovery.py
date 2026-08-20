from importlib import import_module
from pathlib import Path


class ProductDiscoveryError(RuntimeError):
    pass


def discover_products() -> tuple[str, ...]:
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

        definition = entry / "definition.py"

        if not definition.is_file():
            continue

        module_name = (
            f"app.products.{entry.name}.definition"
        )

        try:
            import_module(module_name)
        except Exception as exc:
            raise ProductDiscoveryError(
                "Failed to load product "
                f"{entry.name}: {exc}"
            ) from exc

        discovered.append(entry.name)

    return tuple(discovered)
