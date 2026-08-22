from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def test_admin_displays_product_client_numbers():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "admin.html"
    ).read_text()

    assert "Client #${tenant.client_number}" in page
    assert "Client #${data.tenant.client_number}" in page
    assert "Validation tenant · Internal #" in page


def test_commercialization_displays_client_number():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "commercialization.html"
    ).read_text()

    assert "lead.converted_client_number" in page
    assert "Client #${lead.converted_client_number}" in page
    assert "Manage Client" in page
