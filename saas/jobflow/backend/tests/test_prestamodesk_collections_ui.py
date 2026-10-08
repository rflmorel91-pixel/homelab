import re
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPOSITORY_ROOT / "app"
COLLECTIONS_PAGE = (
    APP_ROOT / "prestamodesk-cobros.html"
)
PRODUCTION_NGINX = (
    REPOSITORY_ROOT / "nginx" / "default.conf"
)
STAGING_NGINX = (
    REPOSITORY_ROOT / "staging" / "nginx.conf"
)


def collections_script_path() -> Path:
    contents = COLLECTIONS_PAGE.read_text()
    match = re.search(
        r'src="(/assets/prestamodesk-cobros-'
        r'[0-9a-f]{12}\.js)"',
        contents,
    )
    assert match is not None

    return (
        APP_ROOT
        / match.group(1).removeprefix("/")
    )


def test_collections_page_uses_fingerprinted_assets():
    assert COLLECTIONS_PAGE.is_file()

    html = COLLECTIONS_PAGE.read_text()
    script = collections_script_path()

    assert script.is_file()
    assert (
        "/assets/prestamodesk-cobros.js"
        not in html
    )
    assert re.search(
        r'href="/assets/prestamodesk-app-'
        r'[0-9a-f]{12}\.css"',
        html,
    )


def test_collections_page_avoids_inline_code():
    html = COLLECTIONS_PAGE.read_text()

    assert not re.search(
        r"<script(?![^>]*\bsrc=)",
        html,
    )
    assert not re.search(r"\sstyle=", html)
    assert not re.search(
        r"\son(?:click|change|submit)=",
        html,
    )


def test_collections_page_supports_required_workflow():
    html = COLLECTIONS_PAGE.read_text()
    script = collections_script_path().read_text()
    contents = html + script

    for element_id in (
        "collectionsWorkspace",
        "supervisionLink",
        "portfolioFilterForm",
        "portfolioAsOf",
        "portfolioCount",
        "portfolioList",
        "collectionDetailPanel",
        "activityForm",
        "activityChannel",
        "activityOutcome",
        "activityContactedAt",
        "activityNextFollowUpAt",
        "activityNotes",
        "promiseForm",
        "promiseAmount",
        "promiseDueDate",
        "promiseNotes",
        "collectionActivityHistory",
        "paymentPromiseHistory",
        "overduePromiseList",
    ):
        assert f'id="{element_id}"' in html

    for expected in (
        "Gestión de cobros",
        "Supervisión",
        "/prestamodesk/cobros/supervision",
        '!["owner", "administrator", "supervisor"].includes(client.role)',
        "Cartera vencida",
        "Registrar gestión",
        "Registrar promesa de pago",
        "Historial de gestiones",
        "Promesas vencidas",
        "/collections/portfolio",
        "/activities",
        "/promises",
        "/cancel",
        "overdue_only",
        "owner",
        "collector",
        "Esta cuenta no tiene acceso",
        "Gestión registrada.",
        "Promesa de pago registrada.",
    ):
        assert expected in contents

    for forbidden in (
        f"{chr(34)}/payments{chr(34)}",
        "/cashier/closings",
        "Cerrar mi caja",
        "Registrar pago",
    ):
        assert forbidden not in contents


def test_nginx_serves_collections_with_enforced_csp():
    production = PRODUCTION_NGINX.read_text()
    staging = STAGING_NGINX.read_text()

    for contents in (production, staging):
        assert (
            "location = /prestamodesk/cobros {"
            in contents
        )
        assert (
            "try_files /prestamodesk-cobros.html "
            "=404;"
            in contents
        )

    assert (
        r"prestamodesk(?:-(?:app|workspace|caja|cobros|cobros-supervision)"
        in production
    )
    assert (
        "/prestamodesk-cobros.html "
        '"default-src \'self\';'
        in staging
    )

def test_collections_page_supports_collector_assignments():
    html = COLLECTIONS_PAGE.read_text()
    script = collections_script_path().read_text()
    contents = html + script

    for element_id in (
        "portfolioTitle",
        "portfolioNotice",
        "assignmentStatusField",
        "assignmentStatus",
        "collectorAssignmentPanel",
        "collectorAssignmentForm",
        "collectorAssignmentUser",
        "releaseCollectorAssignment",
        "collectorAssignmentHistory",
    ):
        assert f'id="{element_id}"' in html

    for expected in (
        "Mi cartera",
        "Sin asignar",
        "Cobrador asignado",
        "Asignar o reasignar",
        "Liberar asignación",
        "/collections/collectors",
        "assignment_status",
        "/assignment",
        "/assignment/release",
        "/assignments",
        "collector_user_id",
        "assigned_collector_display_name",
        "Cobrador asignado.",
        "Asignación liberada.",
    ):
        assert expected in contents
