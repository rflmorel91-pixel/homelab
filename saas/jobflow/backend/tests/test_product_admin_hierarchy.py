from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def test_admin_manages_clients_inside_products():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "admin.html"
    ).read_text()

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
    ).read_text()

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
    ).read_text()

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
    ).read_text()

    assert "Identity &amp; Access" in page
    assert "shared platform identities and security" in page
    assert (
        "Access remains within each tenant/product "
        "and its clients or validation workspaces."
        in page
    )
