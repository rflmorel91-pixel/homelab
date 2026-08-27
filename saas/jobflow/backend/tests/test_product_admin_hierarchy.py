from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def test_admin_manages_clients_inside_products():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "admin.html"
    ).read_text() + (WORKSPACE_ROOT / "app/assets/admin-cac3598ae666.js").read_text() + (WORKSPACE_ROOT / "app/assets/admin-dea40d584f53.css").read_text()

    assert 'data-view="products"' in page
    assert 'data-view="tenants"' not in page
    assert "<h3>Clients</h3>" in page
    assert "<h3>Users</h3>" in page
    assert "Manage Client" in page
    assert "Manage Workspace" in page

    product_detail = page.index(
        'id="productDetailPanel"'
    )
    tenant_detail = page.index(
        'id="tenantDetailPanel"'
    )
    hidden_directory = page.index(
        'id="tenantsView"'
    )

    assert product_detail < tenant_detail
    assert tenant_detail < hidden_directory


def test_tenant_detail_loads_owning_product_context():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "admin.html"
    ).read_text() + (WORKSPACE_ROOT / "app/assets/admin-cac3598ae666.js").read_text() + (WORKSPACE_ROOT / "app/assets/admin-dea40d584f53.css").read_text()

    assert (
        "state.currentProductId"
        "\n        !== data.tenant.product_id"
        in page
    )
    assert (
        "await openProduct("
        "\n          data.tenant.product_id"
        in page
    )
    assert 'showView("products");' in page


def test_stale_tenant_navigation_cannot_render():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "admin.html"
    ).read_text() + (WORKSPACE_ROOT / "app/assets/admin-cac3598ae666.js").read_text() + (WORKSPACE_ROOT / "app/assets/admin-dea40d584f53.css").read_text()

    assert "tenantNavigationGeneration: 0" in page
    assert (
        "const navigationGeneration ="
        "\n      ++state.tenantNavigationGeneration"
        in page
    )
    assert (
        page.count(
            "!== state.tenantNavigationGeneration"
        )
        >= 3
    )
    assert (
        '"tenantDetailPanel"'
        '\n    ).classList.add("hidden");'
        in page
    )
    assert (
        "state.currentTenantId = tenantId;"
        in page
    )


def test_global_users_are_identity_registry_only():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "admin.html"
    ).read_text() + (WORKSPACE_ROOT / "app/assets/admin-cac3598ae666.js").read_text() + (WORKSPACE_ROOT / "app/assets/admin-dea40d584f53.css").read_text()

    assert "Identity &amp; Access" in page
    assert "shared platform identities and security" in page
    assert (
        "Access remains within each tenant/product "
        "and its clients or validation workspaces."
        in page
    )


def test_admin_assets_are_external_and_local():
    from html.parser import HTMLParser

    class PageParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.scripts = []
            self.styles = []
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            assert "style" not in attrs
            assert not any(key.startswith("on") for key in attrs)
            assert tag != "style"
            if tag == "script":
                assert attrs.get("src", "").startswith("/assets/admin-")
                assert "async" not in attrs and "type" not in attrs
                self.scripts.append(attrs["src"])
            if tag == "link" and attrs.get("rel") == "stylesheet":
                self.styles.append(attrs["href"])

    page = (WORKSPACE_ROOT / "app/admin.html").read_text()
    parser = PageParser()
    parser.feed(page)
    assert len(parser.scripts) == len(parser.styles) == 1
    for url in parser.scripts + parser.styles:
        assert url.startswith("/assets/admin-")
        assert (WORKSPACE_ROOT / "app" / url.lstrip("/")).is_file()
    assert page.index('<script src=') > page.index('id="adminLoginForm"')


def test_admin_dynamic_markup_has_no_inline_handlers_or_styles():
    import re
    from html.parser import HTMLParser

    class ScriptParser(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag == "script":
                self.src = dict(attrs)["src"]

    parser = ScriptParser()
    parser.feed((WORKSPACE_ROOT / "app/admin.html").read_text())
    script = (WORKSPACE_ROOT / "app" / parser.src.lstrip("/")).read_text()
    assert not re.search(r"\b(?:style|on[a-z]+)\s*=", script, re.I)
    assert "initializeAdmin();" in script
