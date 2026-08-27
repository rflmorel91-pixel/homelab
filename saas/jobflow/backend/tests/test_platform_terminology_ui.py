from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def test_admin_uses_fieldlookers_hierarchy():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "admin.html"
    ).read_text() + (WORKSPACE_ROOT / "app/assets/admin-cac3598ae666.js").read_text() + (WORKSPACE_ROOT / "app/assets/admin-dea40d584f53.css").read_text()

    assert "FieldLookers Platform Administration" in page
    assert "Tenant / Products" in page
    assert "Tenant / Product Directory" in page
    assert "Manage Tenant / Product" in page
    assert "Client &amp; Workspace Access" in page
    assert (
        "Access remains within each tenant/product"
        in page
    )


def test_client_and_workspace_statuses_are_dynamic():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "admin.html"
    ).read_text() + (WORKSPACE_ROOT / "app/assets/admin-cac3598ae666.js").read_text() + (WORKSPACE_ROOT / "app/assets/admin-dea40d584f53.css").read_text()

    assert "currentAccessKind: null" in page
    assert "function currentAccessLabel()" in page
    assert (
        "`${currentAccessLabel()} details loaded.`"
        in page
    )
    assert (
        "`${accessLabel} timezone updated.`"
        in page
    )
    assert (
        "`${accessLabel} suspended. "
        "Access is now blocked.`"
        in page
    )
    assert (
        "`${accessLabel} reactivated. "
        "Access restored.`"
        in page
    )


def test_internal_tenant_language_is_not_visible():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "admin.html"
    ).read_text() + (WORKSPACE_ROOT / "app/assets/admin-cac3598ae666.js").read_text() + (WORKSPACE_ROOT / "app/assets/admin-dea40d584f53.css").read_text()

    assert '"Loading tenant..."' not in page
    assert '"Tenant details loaded."' not in page
    assert '"Suspending tenant..."' not in page
    assert '"Reactivating tenant..."' not in page
    assert '"Updating tenant timezone..."' not in page
    assert '"Tenant timezone updated."' not in page
    assert "<h3>Tenant Access</h3>" not in page
