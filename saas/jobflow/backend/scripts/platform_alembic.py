from pathlib import Path
import sys

from alembic import command
from alembic.config import Config


SOURCE_BACKEND_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(SOURCE_BACKEND_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(SOURCE_BACKEND_ROOT),
    )


from app.platform import (
    discover_product_migration_locations,
    discover_products,
    get_product,
)
from app.platform.installed_product_migrations import (
    installed_product_migration_locations,
)


def platform_migration_root() -> Path:
    from app.platform import migrations

    return Path(
        migrations.__file__
    ).resolve().parent


def workspace_root(
    value: str | None = None,
) -> Path:
    if value is None:
        return Path.cwd().resolve()

    return Path(value).resolve()


def build_config(
    *,
    root: Path | None = None,
) -> Config:
    if root is None:
        root = workspace_root()

    migration_root = (
        platform_migration_root()
    )

    config = Config()

    config.set_main_option(
        "script_location",
        str(migration_root),
    )

    config.set_main_option(
        "file_template",
        "%%(rev)s_%%(slug)s",
    )

    platform_versions = (
        migration_root
        / "versions"
    ).resolve()

    bundled_root = (
        Path(__file__)
        .resolve()
        .parents[1]
    )

    version_locations = [
        platform_versions,
        *discover_product_migration_locations(
            bundled_root
        ),
        *discover_product_migration_locations(
            root
        ),
        *installed_product_migration_locations(),
    ]

    unique_locations: list[Path] = []

    for location in version_locations:
        location = location.resolve()

        if location not in unique_locations:
            unique_locations.append(
                location
            )

    config.set_main_option(
        "version_locations",
        " ".join(
            str(path)
            for path in unique_locations
        ),
    )

    config.set_main_option(
        "path_separator",
        "space",
    )

    config.attributes[
        "workspace_root"
    ] = root

    return config


def get_product_version_path(
    product_slug: str,
    *,
    root: Path | None = None,
) -> Path:
    if root is None:
        root = workspace_root()

    discover_products(
        root=root
    )

    product = get_product(
        product_slug
    )

    if product is None:
        raise ValueError(
            f"Unknown product: {product_slug}"
        )

    package_name = (
        product_slug.replace(
            "-",
            "_",
        )
    )

    expected = (
        root
        / "app"
        / "products"
        / package_name
        / "migrations"
        / "versions"
    ).resolve()

    locations = set(
        discover_product_migration_locations(
            root
        )
    )

    if expected not in locations:
        raise ValueError(
            "Product does not have a migration "
            f"versions directory: {product_slug}"
        )

    return expected


def parse_root(
    argv: list[str],
) -> tuple[Path, list[str]]:
    root = None
    remaining: list[str] = []

    index = 0

    while index < len(argv):
        argument = argv[index]

        if argument == "--root":
            index += 1

            if index >= len(argv):
                raise SystemExit(
                    "--root requires a path"
                )

            root = workspace_root(
                argv[index]
            )
        else:
            remaining.append(
                argument
            )

        index += 1

    if root is None:
        root = workspace_root()

    return root, remaining


def main(
    argv: list[str] | None = None,
) -> int:
    if argv is None:
        argv = sys.argv[1:]

    root, argv = parse_root(argv)

    if not argv:
        print(
            "Usage: saas-alembic "
            "[--root PATH] "
            "<command> [arguments...]",
            file=sys.stderr,
        )
        return 2

    config = build_config(
        root=root
    )

    command_name = argv[0]
    args = argv[1:]

    if command_name == "heads":
        command.heads(config)
        return 0

    if command_name == "current":
        command.current(config)
        return 0

    if command_name == "history":
        command.history(
            config,
            rev_range=(
                args[0]
                if args
                else None
            ),
        )
        return 0

    if command_name == "upgrade":
        if len(args) != 1:
            raise SystemExit(
                "upgrade requires exactly one revision"
            )

        command.upgrade(
            config,
            args[0],
        )
        return 0

    if command_name == "downgrade":
        if len(args) != 1:
            raise SystemExit(
                "downgrade requires exactly one revision"
            )

        command.downgrade(
            config,
            args[0],
        )
        return 0

    if command_name == "revision":
        product_slug = None
        message = None
        autogenerate = False

        index = 0

        while index < len(args):
            argument = args[index]

            if argument == "--product":
                index += 1

                if index >= len(args):
                    raise SystemExit(
                        "--product requires a slug"
                    )

                product_slug = (
                    args[index]
                )

            elif argument in (
                "-m",
                "--message",
            ):
                index += 1

                if index >= len(args):
                    raise SystemExit(
                        "-m/--message requires text"
                    )

                message = args[index]

            elif argument == "--autogenerate":
                autogenerate = True

            else:
                raise SystemExit(
                    "Unsupported revision "
                    f"argument: {argument}"
                )

            index += 1

        if product_slug is None:
            raise SystemExit(
                "revision requires --product"
            )

        if not message:
            raise SystemExit(
                "revision requires "
                "-m/--message"
            )

        try:
            version_path = (
                get_product_version_path(
                    product_slug,
                    root=root,
                )
            )
        except ValueError as exc:
            raise SystemExit(
                str(exc)
            ) from exc

        command.revision(
            config,
            message=message,
            autogenerate=autogenerate,
            head="head",
            version_path=str(
                version_path
            ),
        )

        return 0

    if command_name == "check":
        command.check(config)
        return 0

    raise SystemExit(
        "Unsupported Alembic command: "
        f"{command_name}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
