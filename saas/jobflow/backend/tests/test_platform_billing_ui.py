from pathlib import Path


WORKSPACE_ROOT = (
    Path(__file__).resolve().parents[2]
)

ADMIN_PAGE = (
    WORKSPACE_ROOT
    / "app"
    / "admin.html"
)


def test_admin_page_has_platform_billing_controls():
    page = ADMIN_PAGE.read_text()

    assert "Platform Billing" in page
    assert 'id="tenantBillingMode"' in page
    assert 'id="tenantBillingProvider"' in page
    assert 'id="tenantBillingStatus"' in page
    assert 'id="tenantBillingCurrency"' in page
    assert 'id="saveTenantBillingButton"' in page
    assert (
        'data-save-tenant-billing="'
        in page
    )


def test_admin_page_explains_manual_billing_safety():
    page = ADMIN_PAGE.read_text()

    assert (
        "Saving this form does not charge "
        "the customer"
        in page
    )
    assert (
        "No charge was created."
        in page
    )


def test_admin_page_updates_billing_through_api():
    page = ADMIN_PAGE.read_text()

    assert (
        "/admin/tenants/${tenantId}/billing"
        in page
    )
    assert '"manual"' in page
    assert 'method: "PUT"' in page
    assert (
        "async function saveTenantBilling("
        in page
    )


def test_admin_page_has_central_billing_workspace():
    page = ADMIN_PAGE.read_text()

    assert 'data-view="billing"' in page
    assert "Billing Platform" in page
    assert 'id="billingView"' in page
    assert 'id="billingAccountList"' in page
    assert 'id="refreshBillingButton"' in page


def test_billing_workspace_has_system_summary():
    page = ADMIN_PAGE.read_text()

    assert 'id="billingTenantCount"' in page
    assert 'id="billingClientCount"' in page
    assert 'id="billingConfiguredCount"' in page
    assert 'id="billingUnconfiguredCount"' in page
    assert 'id="billingActiveCount"' in page
    assert 'id="billingPastDueCount"' in page


def test_billing_workspace_loads_central_api():
    page = ADMIN_PAGE.read_text()

    assert (
        'await apiRequest("/admin/billing")'
        in page
    )
    assert (
        "async function loadBilling()"
        in page
    )
    assert (
        "function renderBillingDirectory("
        in page
    )
    assert "Configure Billing" in page
    assert "Manage Billing" in page


def test_billing_uses_platform_client_identity():
    page = ADMIN_PAGE.read_text()

    assert (
        'row.access_kind === "client"'
        in page
    )
    assert (
        "row.tenant.client_number"
        in page
    )
    assert "Account:" in page
    assert (
        '"Validation workspace"'
        in page
    )


def test_billing_save_confirms_exact_target():
    page = ADMIN_PAGE.read_text()

    assert (
        "const confirmed = window.confirm("
        in page
    )
    assert (
        "Save billing metadata for"
        in page
    )
    assert (
        "This does not create a charge."
        in page
    )
    assert (
        "tenant.client_number"
        in page
    )


def test_validation_workspaces_are_not_billable():
    page = ADMIN_PAGE.read_text()

    assert "<span>Clients</span>" in page
    assert "Not Billable" in page
    assert (
        "Internal validation environment"
        in page
    )
    assert "Billing disabled" in page
