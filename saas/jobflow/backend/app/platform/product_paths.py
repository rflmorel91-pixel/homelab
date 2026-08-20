from pathlib import Path

import app.products


def register_product_root(
    root: Path,
) -> Path:
    products_path = (
        root.resolve()
        / "app"
        / "products"
    )

    if not products_path.is_dir():
        return products_path

    path_value = str(products_path)

    if path_value not in app.products.__path__:
        app.products.__path__.append(
            path_value
        )

    return products_path


def unregister_product_root(
    root: Path,
) -> None:
    products_path = (
        root.resolve()
        / "app"
        / "products"
    )

    path_value = str(products_path)

    while path_value in app.products.__path__:
        app.products.__path__.remove(
            path_value
        )


def product_roots() -> tuple[Path, ...]:
    discovered: list[Path] = []

    for value in app.products.__path__:
        path = Path(value).resolve()

        if (
            path.is_dir()
            and path not in discovered
        ):
            discovered.append(path)

    return tuple(discovered)
