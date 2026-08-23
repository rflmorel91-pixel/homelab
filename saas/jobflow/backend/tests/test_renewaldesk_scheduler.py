import os
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]

WRAPPER = (
    WORKSPACE_ROOT
    / "scripts"
    / "run-renewaldesk-reminder-cycle.sh"
)

SERVICE = (
    WORKSPACE_ROOT
    / "systemd"
    / "fieldlookers-renewaldesk-reminders.service"
)

TIMER = (
    WORKSPACE_ROOT
    / "systemd"
    / "fieldlookers-renewaldesk-reminders.timer"
)


def test_reminder_cycle_wrapper_is_executable():
    assert WRAPPER.is_file()
    assert os.access(WRAPPER, os.X_OK)


def test_reminder_cycle_wrapper_has_overlap_guard():
    script = WRAPPER.read_text()

    assert "set -Eeuo pipefail" in script
    assert 'flock -n 9' in script
    assert '"reason":"already_running"' in script


def test_reminder_cycle_wrapper_runs_client_worker():
    script = WRAPPER.read_text()

    assert "docker exec" in script
    assert "jobflow-api" in script
    assert (
        "scripts/run_renewaldesk_reminders.py"
        in script
    )
    assert 'worker_arguments+=("--dry-run")' in script


def test_reminder_cycle_wrapper_tracks_results():
    script = WRAPPER.read_text()

    assert "last-reminder-success" in script
    assert "last-reminder-failure" in script
    assert "last-reminder-cycle.json" in script
    assert '"${status}"' in script
    assert 'rm -f "${FAILURE_FILE}"' in script


def test_reminder_service_runs_repository_wrapper():
    service = SERVICE.read_text()

    assert (
        "Description=FieldLookers RenewalDesk "
        "client reminder cycle"
        in service
    )
    assert "Type=oneshot" in service
    assert "User=rflmorel" in service
    assert (
        "WorkingDirectory=/home/rflmorel/"
        "homelab/saas/jobflow"
        in service
    )
    assert (
        "ExecStart=/home/rflmorel/homelab/"
        "saas/jobflow/scripts/"
        "run-renewaldesk-reminder-cycle.sh"
        in service
    )
    assert "TimeoutStartSec=10min" in service


def test_reminder_timer_runs_every_five_minutes():
    timer = TIMER.read_text()

    assert "OnCalendar=*-*-* *:0/5:00" in timer
    assert "Persistent=true" in timer
    assert "AccuracySec=30s" in timer
    assert (
        "Unit=fieldlookers-renewaldesk-"
        "reminders.service"
        in timer
    )
    assert "WantedBy=timers.target" in timer

def test_dry_run_does_not_replace_production_markers():
    script = WRAPPER.read_text()

    assert 'dry_run="false"' in script
    assert 'dry_run="true"' in script
    assert (
        script.count(
            'if [[ "${dry_run}" == "true" ]]'
        )
        == 2
    )

    success_guard = script.index(
        'if [[ "${dry_run}" == "true" ]]'
    )
    success_marker = script.index(
        '> "${SUCCESS_FILE}.tmp"'
    )

    assert success_guard < success_marker


def test_wrapper_publishes_prometheus_metrics():
    script = WRAPPER.read_text()

    assert (
        "write-renewaldesk-reminder-metrics.py"
        in script
    )
    assert "publish_metrics \"success\" 0" in script
    assert (
        'publish_metrics "failure" "${status}"'
        in script
    )
    assert (
        "fieldlookers-renewaldesk-reminders.prom"
        in script
    )

def test_wrapper_publishes_uptime_kuma_heartbeat():
    script = WRAPPER.read_text()

    assert (
        'PUSH_URL="${FIELDLOOKERS_'
        'REMINDER_PUSH_URL:-}"'
        in script
    )
    assert "publish_push() {" in script
    assert '"status=${status}"' in script
    assert '"msg=${message}"' in script
    assert 'endpoint="${PUSH_URL%%\\?*}"' in script
    assert '"${endpoint}"' in script
    assert (
        "RenewalDesk Client reminder cycle succeeded"
        in script
    )
    assert (
        "RenewalDesk Client reminder cycle failed "
        "with exit ${status}"
        in script
    )


def test_service_reads_protected_push_environment():
    service = SERVICE.read_text()

    assert (
        "EnvironmentFile=-/etc/fieldlookers/"
        "renewaldesk-reminders.env"
        in service
    )
