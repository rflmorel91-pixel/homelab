from importlib import import_module
from importlib.util import find_spec
import pkgutil


def installed_product_packages() -> tuple[str, ...]:
    try:
        import saas_products
    except ModuleNotFoundError:
        return ()

    discovered: list[str] = []

    for module in pkgutil.iter_modules(
        saas_products.__path__
    ):
        if not module.ispkg:
            continue

        if module.name.startswith("_"):
            continue

        definition_module = (
            f"saas_products."
            f"{module.name}.definition"
        )

        try:
            definition = find_spec(
                definition_module
            )
        except (
            ImportError,
            ModuleNotFoundError,
            AttributeError,
        ):
            continue

        if definition is None:
            continue

        discovered.append(
            module.name
        )

    return tuple(
        sorted(discovered)
    )


def import_installed_product(
    package: str,
) -> None:
    import_module(
        f"saas_products.{package}.definition"
    )


def import_installed_product_models(
    package: str,
) -> bool:
    try:
        import_module(
            f"saas_products.{package}.models"
        )
    except ModuleNotFoundError as exc:
        expected = (
            f"saas_products.{package}.models"
        )

        if exc.name == expected:
            return False

        raise

    return True
