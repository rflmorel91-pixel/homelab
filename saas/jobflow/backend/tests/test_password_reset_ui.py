from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def test_renewaldesk_exposes_password_reset_request():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "renewaldesk-app.html"
    ).read_text()

    assert 'id="forgotPasswordButton"' in page
    assert 'id="passwordResetRequestForm"' in page
    assert (
        '"/auth/password-reset/request"'
        in page
    )
    assert 'product_slug: "renewaldesk"' in page


def test_password_reset_page_confirms_and_redirects():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "reset-password.html"
    ).read_text()

    assert 'id="resetForm"' in page
    assert 'minlength="12"' in page
    assert (
        "/auth/password-reset/confirm"
        in page
    )
    assert "payload.product.workspace_route" in page
    assert "window.location.assign(workspaceUrl)" in page


def test_nginx_rate_limits_password_reset():
    config = (
        WORKSPACE_ROOT
        / "nginx"
        / "default.conf"
    ).read_text()

    assert "zone=jobflow_password_reset" in config
    assert (
        "^/api/v1/auth/password-reset/"
        "(request|confirm)$"
        in config
    )
    assert "location = /reset-password" in config
