import json
import subprocess
import sys
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]

WRITER = (
    WORKSPACE_ROOT
    / "scripts"
    / "write-renewaldesk-reminder-metrics.py"
)


def run_writer(
    tmp_path,
    *,
    status,
    exit_status,
):
    success_file = tmp_path / "success"
    failure_file = tmp_path / "failure"
    result_file = tmp_path / "result.json"
    output_file = tmp_path / "metrics.prom"

    success_file.write_text(
        "2026-08-23T22:00:10Z\n"
    )

    result_file.write_text(
        json.dumps(
            {
                "client_count": 2,
                "candidate_count": 1,
                "tracked_delivery_count": 1,
                "processed_count": 1,
                "sent_count": 1,
                "failed_count": 0,
                "retry_scheduled_count": 0,
            }
        )
    )

    if status == "failure":
        failure_file.write_text(
            "2026-08-23T22:05:10Z exit=2\n"
        )

    subprocess.run(
        [
            sys.executable,
            str(WRITER),
            "--status",
            status,
            "--exit-status",
            str(exit_status),
            "--attempt-timestamp",
            "1787522710",
            "--success-file",
            str(success_file),
            "--failure-file",
            str(failure_file),
            "--result-file",
            str(result_file),
            "--output",
            str(output_file),
        ],
        check=True,
    )

    return output_file.read_text()


def test_success_metrics_are_published(tmp_path):
    metrics = run_writer(
        tmp_path,
        status="success",
        exit_status=0,
    )

    assert (
        "fieldlookers_renewaldesk_reminder_"
        "last_attempt_success 1"
        in metrics
    )
    assert (
        "fieldlookers_renewaldesk_reminder_"
        "last_exit_status 0"
        in metrics
    )
    assert (
        "fieldlookers_renewaldesk_reminder_"
        "last_success_client_count 2"
        in metrics
    )
    assert (
        "fieldlookers_renewaldesk_reminder_"
        "last_success_sent_count 1"
        in metrics
    )


def test_failure_metrics_preserve_last_success(tmp_path):
    metrics = run_writer(
        tmp_path,
        status="failure",
        exit_status=2,
    )

    assert (
        "fieldlookers_renewaldesk_reminder_"
        "last_attempt_success 0"
        in metrics
    )
    assert (
        "fieldlookers_renewaldesk_reminder_"
        "last_exit_status 2"
        in metrics
    )
    assert (
        "fieldlookers_renewaldesk_reminder_"
        "last_failure_timestamp_seconds "
        "1787522710"
        in metrics
    )
    assert (
        "fieldlookers_renewaldesk_reminder_"
        "last_success_client_count 2"
        in metrics
    )
