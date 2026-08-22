from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def test_admin_displays_product_client_numbers():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "admin.html"
    ).read_text()

    assert "Client #${client.client_number}" in page
    assert "Client #${data.tenant.client_number}" in page
    assert "Validation workspace · Internal #" in page


def test_commercialization_displays_client_number():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "commercialization.html"
    ).read_text()

    assert "lead.converted_client_number" in page
    assert "Client #${lead.converted_client_number}" in page
    assert "Validation Workspace" in page
    assert "Internal Workspace #" in page
    assert "Manage Client" in page
    assert "Manage Workspace" in page
    assert "Provision Client" in page
    assert "Provisioned validation tenant" not in page
    assert "Internal tenant #" not in page
    assert "Tenant Workspace" not in page
    assert "Provision Tenant" not in page
    assert "Accepted Owner" in page
    assert "Awaiting owner activation" in page
    assert "acceptedOwner.user_id" in page
    assert "owner.lead_id === lead.id" in page
    assert "Select initial tenant owner" not in page
    assert 'id="owner-${lead.id}"' not in page


def test_admin_separates_clients_from_validation_workspaces():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "admin.html"
    ).read_text()

    assert "<h1>Clients</h1>" in page
    assert "Client Directory" in page
    assert "Validation Workspaces" in page
    assert 'id="validationTenantList"' in page
    assert "renderClientRows(clients)" in page
    assert (
        "renderValidationWorkspaceRows("
        in page
    )
    assert "Manage Client" in page
    assert "Manage Workspace" in page


def test_admin_product_directory_opens_product_management():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "admin.html"
    ).read_text()

    assert 'id="productDetailPanel"' in page
    assert 'id="productDetail"' in page
    assert 'data-open-product="${product.id}"' in page
    assert "Manage Product" in page
    assert "async function openProduct(productId)" in page
    assert (
        "`/admin/products/${productId}`"
        in page
    )
    assert "<h3>Clients</h3>" in page
    assert "<h3>Users</h3>" in page
    assert "<h3>Active Leads</h3>" in page
    assert "<h3>Converted History</h3>" in page
    assert "<h3>Validation Workspaces</h3>" in page
    assert "data.active_leads" in page
    assert "data.converted_history" in page
    assert "data.counts.active_leads" in page
    assert "data.counts.converted_records" in page
    assert "Manage Product Leads" in page



def test_admin_uses_shared_platform_branding():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "admin.html"
    ).read_text()

    assert (
        "<title>FieldLookers Platform Administration</title>"
        in page
    )
    assert page.count("<strong>FieldLookers</strong>") == 2
    assert "Lead Commercialization" in page
    assert ">Platform Users<" not in page
    assert "Platform Users" in page
    assert 'href="/app"' not in page
    assert "Client Workspace" not in page
    assert "<strong>JobFlow</strong>" not in page
    assert "<title>JobFlow Administration</title>" not in page
