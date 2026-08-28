from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def test_renewaldesk_exposes_password_reset_request():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "renewaldesk-app.html"
    ).read_text() + (WORKSPACE_ROOT / "app/assets/renewaldesk-app-2b95865bd9c7.js").read_text() + (WORKSPACE_ROOT / "app/assets/renewaldesk-app-8d37ae6e9662.css").read_text()

    assert 'id="forgotPasswordButton"' in page
    assert 'id="passwordResetRequestForm"' in page
    assert (
        '"/auth/password-reset/request"'
        in page
    )
    assert 'product_slug: "renewaldesk"' in page
    assert 'id="passwordResetRequestButton"' in page
    assert (
        "passwordResetRequestButton.disabled = true"
        in page
    )
    assert '"Sending..."' in page


def test_password_reset_page_confirms_and_redirects():
    page = (
        (WORKSPACE_ROOT / "app/reset-password.html").read_text()
        + (WORKSPACE_ROOT / "app/assets/reset-password-2258733150ce.js").read_text()
    )

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


def test_reset_password_uses_external_csp_assets():
    import hashlib
    from html.parser import HTMLParser

    class AssetParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.assets = []

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            assert tag != "style"
            assert "style" not in attrs
            assert not any(key.startswith("on") for key in attrs)
            if tag == "script":
                assert attrs.get("src", "").startswith("/assets/")
                self.assets.append(attrs["src"])
            if tag == "link" and attrs.get("rel") == "stylesheet":
                assert attrs.get("href", "").startswith("/assets/")
                self.assets.append(attrs["href"])

    page = (WORKSPACE_ROOT / "app/reset-password.html").read_text()
    parser = AssetParser()
    parser.feed(page)
    assert len(parser.assets) == 2
    assert {Path(path).suffix for path in parser.assets} == {".js", ".css"}
    for path in parser.assets:
        content = (WORKSPACE_ROOT / "app" / path.lstrip("/")).read_bytes()
        assert hashlib.sha256(content).hexdigest()[:12] in Path(path).name
    assert 'content="no-referrer"' in page


def test_password_reset_uses_fragment_token():
    script = (WORKSPACE_ROOT / "app/assets/reset-password-2258733150ce.js").read_text()
    assert "window.location.hash.slice(1)" in script
    assert 'hash.get("token")' in script
    assert "window.history.replaceState" in script
    assert "?token=" not in script
