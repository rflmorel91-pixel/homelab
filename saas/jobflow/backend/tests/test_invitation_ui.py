from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def test_activation_page_uses_fragment_token():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "accept-invitation.html"
    ).read_text()

    assert 'window.location.hash.slice(1)' in page
    assert 'hash.get("token")' in page
    assert "window.history.replaceState" in page
    assert "?token=" not in page


def test_admin_invitation_form_uses_platform_api():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "admin.html"
    ).read_text()

    assert 'id="inviteUserForm"' in page
    assert 'id="invitationLeadId"' in page
    assert '"/admin/user-invitations"' in page
    assert '"lead_id": leadId' not in page
    assert "lead_id: leadId" in page
    assert 'apiRequest("/leads/")' in page
    assert "lead.status === \"qualified\"" in page
    assert "invitation.product.name" in page
    assert "invitation.activation_path" in page


def test_nginx_routes_and_limits_invitation_acceptance():
    configuration = (
        WORKSPACE_ROOT
        / "nginx"
        / "default.conf"
    ).read_text()

    assert (
        "location = /api/v1/auth/invitations/accept"
        in configuration
    )
    assert (
        "zone=jobflow_invitation_accept"
        in configuration
    )
    assert (
        "location = /accept-invitation"
        in configuration
    )



def test_activation_continues_to_linked_product_landing():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "accept-invitation.html"
    ).read_text()

    assert "payload.product.landing_route" in page
    assert "payload.product.name" in page
    assert "?activated=1" in page


def test_renewaldesk_landing_handles_activation_return():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "renewaldesk.html"
    ).read_text()

    assert 'id="activationNotice"' in page
    assert 'get("activated") === "1"' in page
    assert 'href="/renewaldesk/app"' in page


def test_renewaldesk_discovers_client_access():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "renewaldesk-app.html"
    ).read_text()

    assert (
        '"/auth/products/renewaldesk/access"'
        in page
    )
    assert "const client =" in page
    assert "client.tenant_id" in page
    assert "discoverRenewalDeskAccess" in page
    assert "loginTenantId" not in page
    assert "RenewalDesk Tenant ID" not in page



def test_renewaldesk_displays_discovered_client_context():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "renewaldesk-app.html"
    ).read_text()

    assert 'id="clientContext"' in page
    assert "Client #${client.client_number}" in page
    assert "${client.name}" in page
    assert "${client.role}" in page
    assert "clientContext.textContent" in page
    assert "tenant_id}" not in page



def test_commercial_client_uses_secure_user_invitation():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "admin.html"
    ).read_text()

    assert "<h3>Invite Client User</h3>" in page
    assert 'id="clientInvitationName"' in page
    assert 'id="clientInvitationEmail"' in page
    assert 'id="clientInvitationRole"' in page
    assert 'id="createClientInvitationButton"' in page
    assert 'id="clientInvitationResult"' in page
    assert 'id="copyClientInvitationButton"' in page
    assert (
        '"/user-invitations"'
        in page
    )
    assert (
        "`/admin/tenants/${state.currentTenantId}`"
        in page
    )
    assert "invitation.activation_path" in page
    assert "invitation.client.client_number" in page
    assert "data.tenant.client_number" in page
    assert "<h3>Add Internal Membership</h3>" in page
