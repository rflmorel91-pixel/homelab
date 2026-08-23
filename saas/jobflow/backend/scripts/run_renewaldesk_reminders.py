import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys


BACKEND_ROOT = (
    Path(__file__).resolve().parents[1]
)

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(BACKEND_ROOT),
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run one RenewalDesk reminder cycle."
        )
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Inspect active clients and candidates "
            "without writing or sending."
        ),
    )

    return parser.parse_args()


def main() -> int:
    arguments = parse_args()

    from app.database import SessionLocal
    from app.products.renewaldesk.reminder_worker import (
        run_reminder_cycle,
    )

    with SessionLocal() as db:
        summary = run_reminder_cycle(
            db,
            dry_run=arguments.dry_run,
        )

    print(
        json.dumps(
            asdict(summary),
            sort_keys=True,
        )
    )

    if summary.failed_count:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
