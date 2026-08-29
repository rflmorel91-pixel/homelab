#!/usr/bin/env python3
"""Enforce reviewed HIGH/CRITICAL container findings."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import sys


BLOCKING_SEVERITIES = {"HIGH", "CRITICAL"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Reject fixable, unreviewed, expired, duplicate, "
            "or stale HIGH/CRITICAL container findings."
        )
    )
    parser.add_argument(
        "--exceptions",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "--report",
        action="append",
        required=True,
        metavar="IMAGE=PATH",
    )
    parser.add_argument(
        "--today",
        type=date.fromisoformat,
        default=date.today(),
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


def load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read JSON: {path}") from error


def report_arguments(
    values: list[str],
) -> list[tuple[str, Path]]:
    reports = []

    for value in values:
        image, separator, raw_path = value.partition("=")

        if not separator or not image or not raw_path:
            raise ValueError(
                "--report must use IMAGE=PATH"
            )

        reports.append((image, Path(raw_path)))

    return reports


def exception_key(record: dict[str, object]) -> tuple[str, str, str]:
    return (
        str(record["image"]),
        str(record["vulnerability"]),
        str(record["package"]),
    )


def load_exceptions(
    path: Path,
) -> dict[tuple[str, str, str], dict[str, object]]:
    document = load_json(path)

    if not isinstance(document, dict):
        raise ValueError("Exception document must be an object")

    records = document.get("exceptions")

    if not isinstance(records, list):
        raise ValueError(
            "Exception document must contain an exceptions list"
        )

    indexed = {}

    required = {
        "image",
        "vulnerability",
        "package",
        "accepted_at",
        "expires_on",
        "owner",
        "rationale",
    }

    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Every exception must be an object")

        missing = required - record.keys()

        if missing:
            raise ValueError(
                "Exception is missing fields: "
                + ", ".join(sorted(missing))
            )

        date.fromisoformat(str(record["accepted_at"]))
        date.fromisoformat(str(record["expires_on"]))

        for field in (
            "image",
            "vulnerability",
            "package",
            "owner",
            "rationale",
        ):
            if not str(record[field]).strip():
                raise ValueError(
                    f"Exception field cannot be empty: {field}"
                )

        key = exception_key(record)

        if key in indexed:
            raise ValueError(
                "Duplicate exception: " + "/".join(key)
            )

        indexed[key] = record

    return indexed


def findings_for_report(
    image: str,
    path: Path,
) -> list[dict[str, str]]:
    document = load_json(path)

    if not isinstance(document, dict):
        raise ValueError(f"Report must be an object: {path}")

    findings = []

    for result in document.get("Results") or []:
        if not isinstance(result, dict):
            continue

        for finding in result.get("Vulnerabilities") or []:
            if not isinstance(finding, dict):
                continue

            severity = str(finding.get("Severity") or "").upper()

            if severity not in BLOCKING_SEVERITIES:
                continue

            vulnerability = str(
                finding.get("VulnerabilityID") or ""
            )
            package = str(finding.get("PkgName") or "")

            if not vulnerability or not package:
                raise ValueError(
                    f"Incomplete blocking finding in {path}"
                )

            findings.append(
                {
                    "image": image,
                    "vulnerability": vulnerability,
                    "package": package,
                    "severity": severity,
                    "fixed": str(
                        finding.get("FixedVersion") or ""
                    ),
                }
            )

    unique = {
        (
            finding["image"],
            finding["vulnerability"],
            finding["package"],
        ): finding
        for finding in findings
    }

    return list(unique.values())


def main() -> int:
    args = parse_args()

    try:
        exceptions = load_exceptions(args.exceptions)
        reports = report_arguments(args.report)
        findings = []

        for image, path in reports:
            findings.extend(findings_for_report(image, path))

    except ValueError as error:
        print(f"POLICY ERROR: {error}", file=sys.stderr)
        return 2

    violations = []
    accepted = []
    used = set()

    for finding in sorted(
        findings,
        key=lambda item: (
            item["image"],
            item["package"],
            item["vulnerability"],
        ),
    ):
        key = (
            finding["image"],
            finding["vulnerability"],
            finding["package"],
        )
        exception = exceptions.get(key)

        if finding["fixed"]:
            violations.append(
                (*key, "fixed version available")
            )
            continue

        if exception is None:
            violations.append(
                (*key, "no reviewed exception")
            )
            continue

        expires_on = date.fromisoformat(
            str(exception["expires_on"])
        )

        if expires_on < args.today:
            violations.append(
                (*key, f"exception expired {expires_on}")
            )
            continue

        used.add(key)
        accepted.append((*key, str(expires_on)))

    for key in sorted(exceptions.keys() - used):
        if not any(
            violation[:3] == key
            for violation in violations
        ):
            violations.append(
                (*key, "stale exception has no finding")
            )

    if violations:
        print("CONTAINER SECURITY POLICY FAILED")

        for image, vulnerability, package, reason in violations:
            print(
                f"BLOCKED image={image} "
                f"id={vulnerability} "
                f"package={package} "
                f"reason={reason}"
            )

        return 1

    print(
        "CONTAINER SECURITY POLICY PASSED: "
        f"{len(findings)} blocking-severity findings, "
        f"{len(accepted)} active reviewed exceptions."
    )

    for image, vulnerability, package, expires_on in accepted:
        print(
            f"ACCEPTED image={image} "
            f"id={vulnerability} "
            f"package={package} "
            f"expires={expires_on}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
