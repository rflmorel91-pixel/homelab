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
    assert "Manage Client" in page


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
