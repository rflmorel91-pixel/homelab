from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def test_admin_exposes_audited_access_timezone_control():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "admin.html"
    ).read_text()

    assert "data.tenant.client_number" in page
    assert '"Client"' in page
    assert '"Workspace"' in page
    assert "} Timezone" in page
    assert (
        "`${accessLabel} timezone updated.`"
        in page
    )
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
