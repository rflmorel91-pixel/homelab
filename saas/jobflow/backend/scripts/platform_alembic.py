from pathlib import Path
import sys


BACKEND_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(BACKEND_ROOT),
    )


from alembic import command
from alembic.config import Config

from app.platform import (
    discover_product_migration_locations,
)


def build_config() -> Config:
    backend_root = BACKEND_ROOT

    ini_path = backend_root / "alembic.ini"

    config = Config(str(ini_path))

    platform_versions = (
        backend_root
        / "migrations"
        / "versions"
    ).resolve()

    version_locations = [
        platform_versions,
        *discover_product_migration_locations(
            backend_root
        ),
    ]

    config.set_main_option(
        "version_locations",
        " ".join(
            str(path)
            for path in version_locations
        ),
    )

    config.set_main_option(
        "path_separator",
        "space",
    )

    return config


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print(
            "Usage: platform_alembic.py "
            "<command> [arguments...]",
            file=sys.stderr,
        )
        return 2

    config = build_config()

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
            rev_range=args[0] if args else None,
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

    if command_name == "check":
        command.check(config)
        return 0

    raise SystemExit(
        f"Unsupported Alembic command: "
        f"{command_name}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
