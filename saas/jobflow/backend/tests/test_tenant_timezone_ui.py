from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def test_admin_exposes_audited_tenant_timezone_control():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "admin.html"
    ).read_text()

    assert "<h3>Workspace Timezone</h3>" in page
    assert 'id="tenantTimezoneInput"' in page
    assert 'id="tenantTimezoneOptions"' in page
    assert 'value="America/New_York"' in page
    assert 'data-save-tenant-timezone="' in page
    assert (
        "async function saveTenantTimezone("
        in page
    )
    assert (
        "`/admin/tenants/${tenantId}/timezone`"
        in page
    )
    assert 'method: "PUT"' in page
    assert "timezone_name: timezoneName" in page
    assert (
        '"[data-save-tenant-timezone]"'
        in page
    )
