import re
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPOSITORY_ROOT / "app"

LANDING_PAGE = APP_ROOT / "prestamodesk.html"
WORKSPACE_PAGE = APP_ROOT / "prestamodesk-app.html"

PRODUCTION_NGINX = (
    REPOSITORY_ROOT / "nginx" / "default.conf"
)
STAGING_NGINX = (
    REPOSITORY_ROOT / "staging" / "nginx.conf"
)


def page_asset_paths(page: Path) -> list[Path]:
    contents = page.read_text()

    references = re.findall(
        r'(?:href|src)="(/assets/[^"]+)"',
        contents,
    )

    return [
        APP_ROOT / reference.removeprefix("/")
        for reference in references
    ]


def test_prestamodesk_pages_reference_existing_assets():
    for page in (LANDING_PAGE, WORKSPACE_PAGE):
        assert page.is_file()

        assets = page_asset_paths(page)
        assert assets

        for asset in assets:
            assert asset.is_file(), asset


def test_prestamodesk_assets_are_fingerprinted():
    landing = LANDING_PAGE.read_text()
    workspace = WORKSPACE_PAGE.read_text()

    css_pattern = (
        r"/assets/prestamodesk-app-"
        r"[0-9a-f]{12}\.css"
    )
    js_pattern = (
        r"/assets/prestamodesk-app-"
        r"[0-9a-f]{12}\.js"
    )

    assert re.search(css_pattern, landing)
    assert re.search(css_pattern, workspace)
    assert re.search(js_pattern, workspace)

    assert "/assets/prestamodesk-app.css" not in landing
    assert "/assets/prestamodesk-app.css" not in workspace
    assert "/assets/prestamodesk-app.js" not in workspace


def test_prestamodesk_pages_avoid_inline_code():
    for page in (LANDING_PAGE, WORKSPACE_PAGE):
        contents = page.read_text()

        assert not re.search(
            r"<script(?![^>]*\bsrc=)",
            contents,
        )
        assert not re.search(
            r"\sstyle=",
            contents,
        )
        assert not re.search(
            r"\son(?:click|change|submit)=",
            contents,
        )


def test_production_nginx_serves_prestamodesk_pages():
    contents = PRODUCTION_NGINX.read_text()

    assert "location = /prestamodesk {" in contents
    assert (
        "try_files /prestamodesk.html =404;"
        in contents
    )
    assert "location = /prestamodesk/app {" in contents
    assert (
        "try_files /prestamodesk-app.html =404;"
        in contents
    )

    assert (
        r"~^/prestamodesk(?:-app\.html|/app)"
        in contents
    )
    assert (
        r"~^/prestamodesk(?:\.html)?"
        in contents
    )


def test_staging_nginx_serves_prestamodesk_pages():
    contents = STAGING_NGINX.read_text()

    assert (
        "/prestamodesk.html "
        "\"default-src 'self';"
        in contents
    )
    assert (
        "/prestamodesk-app.html "
        "\"default-src 'self';"
        in contents
    )
    assert "location = /prestamodesk {" in contents
    assert "location = /prestamodesk/app {" in contents


def test_prestamodesk_workspace_supports_password_reset():
    html = WORKSPACE_PAGE.read_text()

    script_path = next(
        asset
        for asset in page_asset_paths(WORKSPACE_PAGE)
        if asset.suffix == ".js"
    )
    script = script_path.read_text()

    for element_id in (
        "forgotPasswordButton",
        "passwordResetRequestForm",
        "passwordResetEmail",
        "passwordResetRequestButton",
        "backToSignInButton",
    ):
        assert f'id="{element_id}"' in html

    assert "/auth/password-reset/request" in script
    assert 'product_slug: "prestamodesk"' in script
    assert "¿Olvidó su contraseña?" in html


def test_prestamodesk_workspace_supports_vehicle_loans():
    html = WORKSPACE_PAGE.read_text()

    script_path = next(
        asset
        for asset in page_asset_paths(WORKSPACE_PAGE)
        if asset.suffix == ".js"
    )
    script = script_path.read_text()

    for element_id in (
        "loanType",
        "vehicleLoanFields",
        "vehicleCashPrice",
        "vehicleDownPayment",
        "vehicleMake",
        "vehicleModel",
        "vehicleYear",
        "vehicleColor",
        "vehicleVin",
        "vehicleLicensePlate",
        "vehicleSeller",
        "vehicleNotes",
    ):
        assert f'id="{element_id}"' in html

    for expected in (
        "updateVehicleLoanFields",
        "updateVehicleFinancedAmount",
        "buildLoanPayload",
        "vehicle_cash_price",
        "vehicle_down_payment",
        "vehicle_license_plate",
        "Vehículo financiado",
    ):
        assert expected in script


def test_prestamodesk_workspace_manages_applications():
    html = WORKSPACE_PAGE.read_text()

    script_path = next(
        asset
        for asset in page_asset_paths(WORKSPACE_PAGE)
        if asset.suffix == ".js"
    )
    script = script_path.read_text()

    for element_id in (
        "openApplicationCount",
        "applicationResultCount",
        "applicationList",
    ):
        assert f'id="{element_id}"' in html

    for expected in (
        "Solicitudes de préstamo",
        "Iniciar revisión",
        "Aprobar",
        "Rechazar",
        "Convertir en préstamo",
        "Ver préstamo",
        'data-application-status="reviewing"',
        'data-application-status="approved"',
        'data-application-status="rejected"',
        "data-convert-application",
        "data-application-loan",
        "${PRODUCT_BASE}/applications",
        "/convert",
        "window.confirm",
        "result.loan_id",
        "renderApplications",
    ):
        assert expected in (
            html + script
        )

def test_prestamodesk_payment_form_supports_payment_date():
    html = WORKSPACE_PAGE.read_text()

    script_path = next(
        asset
        for asset in page_asset_paths(WORKSPACE_PAGE)
        if asset.suffix == ".js"
    )
    script = script_path.read_text()

    assert "Fecha del pago" in html
    assert 'id="paymentDate"' in html
    assert 'type="date"' in html

    for expected in (
        'getElementById(\n  "paymentDate"\n)',
        "setDefaultPaymentDate",
        "paid_at: paymentDate.value",
        "T12:00:00Z",
        "paymentForm.reset();",
    ):
        assert expected in script
