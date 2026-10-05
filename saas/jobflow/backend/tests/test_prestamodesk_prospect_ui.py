from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / "app" / "prestamodesk-solicitar.html"


def read_html():
    return HTML.read_text()


def referenced_asset(suffix):
    html = read_html()

    marker = "/assets/prestamodesk-solicitar-"

    references = [
        token.split('"')[0]
        for token in html.split(marker)[1:]
        if token.split('"')[0].endswith(suffix)
    ]

    assert len(references) == 1

    return (
        ROOT
        / "app"
        / "assets"
        / f"prestamodesk-solicitar-{references[0]}"
    )


def test_prospect_page_has_required_spanish_form():
    html = read_html()
    normalized_html = " ".join(
        html.split()
    )

    for expected in (
        'lang="es"',
        'id="prospectForm"',
        'id="fullName"',
        'id="phone"',
        'id="requestedAmount"',
        'id="contactConsent"',
        "no garantiza aprobación",
        "no conceden préstamos",
    ):
        assert expected in normalized_html


def test_prospect_page_uses_external_hashed_assets():
    css = referenced_asset(".css")
    javascript = referenced_asset(".js")

    assert css.is_file()
    assert javascript.is_file()
    assert "<style" not in read_html()
    assert "<script>" not in read_html()


def test_prospect_script_uses_tenant_scoped_api():
    javascript = referenced_asset(".js").read_text()

    assert (
        "/api/v1/products/prestamodesk"
        "/public/tenants"
    ) in javascript
    assert "consent_to_contact" in javascript
    assert "tenant_id" not in javascript
    assert "converted_borrower_id" not in javascript


def test_nginx_routes_prospect_page_and_api():
    for relative in (
        "nginx/default.conf",
        "staging/nginx.conf",
    ):
        configuration = (
            ROOT / relative
        ).read_text()

        assert (
            "^/prestamodesk/solicitar/"
            "[a-z0-9-]+/?$"
        ) in configuration
        assert (
            "/prestamodesk-solicitar.html"
        ) in configuration
        assert (
            "^/api/v1/products/prestamodesk/"
            "public/tenants/[^/]+"
        ) in configuration
        assert "jobflow_public_request" in configuration


def test_workspace_exposes_prospect_pipeline():
    workspace = (
        ROOT / "app" / "prestamodesk-app.html"
    ).read_text()

    script_reference = next(
        value.split('"', 1)[0]
        for value in workspace.split(
            'src="/assets/'
        )[1:]
        if value.startswith(
            "prestamodesk-app-"
        )
        and value.split('"', 1)[0].endswith(
            ".js"
        )
    )

    script = (
        ROOT
        / "app"
        / "assets"
        / script_reference
    ).read_text()

    for expected in (
        'id="prospectResultCount"',
        'id="publicProspectPageLink"',
        'id="prospectList"',
        "Abrir página pública",
    ):
        assert expected in workspace

    for expected in (
        "renderProspects",
        "/prospects/public-page",
        "data-prospect-status",
        "data-start-prospect-application",
        "Seleccionar tipo y preparar solicitud",
        "openProspectApplication",
    ):
        assert expected in script
