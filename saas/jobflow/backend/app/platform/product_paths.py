from contextlib import contextmanager
from pathlib import Path
from collections.abc import Iterator

import app.products


def product_path(
    root: Path,
) -> Path:
    return (
        root.resolve()
        / "app"
        / "products"
    )


def register_product_root(
    root: Path,
) -> Path:
    products_path = product_path(root)

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
    products_path = product_path(root)
    path_value = str(products_path)

    while path_value in app.products.__path__:
        app.products.__path__.remove(
            path_value
        )


@contextmanager
def temporary_product_root(
    root: Path | None,
) -> Iterator[None]:
    if root is None:
        yield
        return

    products_path = product_path(root)
    path_value = str(products_path)

    already_registered = (
        path_value
        in app.products.__path__
    )

    register_product_root(root)

    try:
        yield
    finally:
        if not already_registered:
            unregister_product_root(root)


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
