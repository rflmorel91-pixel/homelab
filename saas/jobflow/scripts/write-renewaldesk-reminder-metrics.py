#!/usr/bin/env python3
import argparse
import json
import os
from datetime import datetime
from pathlib import Path


RESULT_METRICS = {
    "client_count": "client_count",
    "candidate_count": "candidate_count",
    "tracked_delivery_count": "tracked_delivery_count",
    "processed_count": "processed_count",
    "sent_count": "sent_count",
    "failed_count": "failed_count",
    "retry_scheduled_count": "retry_scheduled_count",
}


def timestamp_from_marker(path: Path) -> int:
    if not path.exists():
        return 0

    value = path.read_text().strip().split()[0]

    try:
        parsed = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except (ValueError, IndexError):
        return 0

    return int(parsed.timestamp())


def read_result(path: Path) -> dict:
    if not path.exists():
        return {}

    try:
        result = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}

    return result if isinstance(result, dict) else {}


def metric(
    name: str,
    help_text: str,
    value: int,
) -> list[str]:
    return [
        f"# HELP {name} {help_text}",
        f"# TYPE {name} gauge",
        f"{name} {value}",
    ]


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--status",
        choices=("success", "failure"),
        required=True,
    )
    parser.add_argument(
        "--exit-status",
        type=int,
        required=True,
    )
    parser.add_argument(
        "--attempt-timestamp",
        type=int,
        required=True,
    )
    parser.add_argument(
        "--success-file",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--failure-file",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--result-file",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
    )

    arguments = parser.parse_args()
    result = read_result(arguments.result_file)

    lines = []

    lines.extend(
        metric(
            (
                "fieldlookers_renewaldesk_reminder_"
                "last_attempt_success"
            ),
            (
                "Whether the latest RenewalDesk "
                "reminder cycle succeeded."
            ),
            1 if arguments.status == "success" else 0,
        )
    )

    lines.extend(
        metric(
            (
                "fieldlookers_renewaldesk_reminder_"
                "last_attempt_timestamp_seconds"
            ),
            (
                "Unix timestamp of the latest "
                "RenewalDesk reminder cycle attempt."
            ),
            arguments.attempt_timestamp,
        )
    )

    lines.extend(
        metric(
            (
                "fieldlookers_renewaldesk_reminder_"
                "last_success_timestamp_seconds"
            ),
            (
                "Unix timestamp of the latest successful "
                "RenewalDesk reminder cycle."
            ),
            timestamp_from_marker(
                arguments.success_file
            ),
        )
    )

    lines.extend(
        metric(
            (
                "fieldlookers_renewaldesk_reminder_"
                "last_failure_timestamp_seconds"
            ),
            (
                "Unix timestamp of the latest unresolved "
                "RenewalDesk reminder failure."
            ),
            timestamp_from_marker(
                arguments.failure_file
            ),
        )
    )

    lines.extend(
        metric(
            (
                "fieldlookers_renewaldesk_reminder_"
                "last_exit_status"
            ),
            (
                "Exit status of the latest "
                "RenewalDesk reminder cycle."
            ),
            arguments.exit_status,
        )
    )

    for result_key, metric_suffix in RESULT_METRICS.items():
        value = result.get(result_key, 0)

        if not isinstance(value, int):
            value = 0

        lines.extend(
            metric(
                (
                    "fieldlookers_renewaldesk_reminder_"
                    f"last_success_{metric_suffix}"
                ),
                (
                    "Value reported by the latest successful "
                    "RenewalDesk reminder cycle."
                ),
                value,
            )
        )

    arguments.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = arguments.output.with_suffix(
        arguments.output.suffix + ".tmp"
    )

    temporary.write_text(
        "\n".join(lines) + "\n"
    )

    os.replace(
        temporary,
        arguments.output,
    )


if __name__ == "__main__":
    main()
