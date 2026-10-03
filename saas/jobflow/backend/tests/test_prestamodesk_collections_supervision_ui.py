import re
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPOSITORY_ROOT / "app"
SUPERVISION_PAGE = (
    APP_ROOT
    / "prestamodesk-cobros-supervision.html"
)
PRODUCTION_NGINX = (
    REPOSITORY_ROOT / "nginx" / "default.conf"
)
STAGING_NGINX = (
    REPOSITORY_ROOT / "staging" / "nginx.conf"
)


def supervision_script_path() -> Path:
    html = SUPERVISION_PAGE.read_text()
    match = re.search(
        r'src="(/assets/'
        r'prestamodesk-cobros-supervision-'
        r'[0-9a-f]{12}\.js)"',
        html,
    )
    assert match is not None

    return (
        APP_ROOT
        / match.group(1).removeprefix("/")
    )


def test_supervision_page_uses_fingerprinted_assets():
    assert SUPERVISION_PAGE.is_file()

    html = SUPERVISION_PAGE.read_text()
    script = supervision_script_path()

    assert script.is_file()
    assert (
        "/assets/prestamodesk-cobros-supervision.js"
        not in html
    )
    assert re.search(
        r'href="/assets/prestamodesk-app-'
        r'[0-9a-f]{12}\.css"',
        html,
    )


def test_supervision_page_avoids_inline_code():
    html = SUPERVISION_PAGE.read_text()

    assert not re.search(
        r"<script(?![^>]*\bsrc=)",
        html,
    )
    assert not re.search(r"\sstyle=", html)
    assert not re.search(
        r"\son(?:click|change|submit)=",
        html,
    )


def test_supervision_page_supports_owner_dashboard():
    html = SUPERVISION_PAGE.read_text()
    script = supervision_script_path().read_text()
    contents = html + script

    for element_id in (
        "supervisionWorkspace",
        "supervisionFilterForm",
        "supervisionAsOf",
        "exportSupervisionButton",
        "refreshSupervisionButton",
        "generalSummary",
        "dailyOperationsSummary",
        "agingSummary",
        "promiseSummary",
        "collectorPerformance",
    ):
        assert f'id="{element_id}"' in html

    for expected in (
        "Supervisión de cobros",
        "Resumen general",
        "Exportar CSV",
        "/collections/supervision/export.csv",
        '"Accept": "text/csv"',
        "URL.createObjectURL",
        "Préstamos asignados",
        "Saldo asignado",
        "Préstamos sin asignar",
        "Saldo sin asignar",
        "Prioridades del día",
        "Promesas para hoy",
        "Seguimientos para hoy",
        "Seguimientos vencidos",
        "Antigüedad de la cartera vencida",
        "Total recuperado",
        "Promesas de pago",
        "Desempeño por cobrador",
        "Cumplimiento por cantidad",
        "Cumplimiento por monto",
        "/collections/supervision",
        'client.role !== "owner"',
        'client.role === "collector"',
        '"/prestamodesk/cobros"',
        "todo el historial",
    ):
        assert expected in contents

    for api_field in (
        "data.promises_due_today_count",
        "data.follow_ups_due_today_count",
        "data.overdue_follow_up_count",
        "data.overdue_promise_count",
        "bucket.balance",
    ):
        assert api_field in script

    for invalid_field in (
        "data.promises_due_today",
        "data.follow_ups_due_today",
        "data.overdue_follow_ups",
        "data.overdue_promises",
        "bucket.overdue_balance",
    ):
        assert not re.search(
            rf"\b{re.escape(invalid_field)}\b",
            script,
        )

    assert "collector.total_recovered" not in script


def test_nginx_serves_supervision_with_enforced_csp():
    production = PRODUCTION_NGINX.read_text()
    staging = STAGING_NGINX.read_text()

    for contents in (production, staging):
        assert (
            "location = "
            "/prestamodesk/cobros/supervision {"
            in contents
        )
        assert (
            "try_files "
            "/prestamodesk-cobros-supervision.html "
            "=404;"
            in contents
        )

    assert (
        "cobros/supervision"
        in production
    )
    assert (
        "cobros-supervision"
        in production
    )
    assert (
        "/prestamodesk-cobros-supervision.html "
        '"default-src \'self\';'
        in staging
    )
