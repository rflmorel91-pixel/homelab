from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def test_activation_page_uses_fragment_token():
    page = (
        (WORKSPACE_ROOT / "app/accept-invitation.html").read_text()
        + (WORKSPACE_ROOT / "app/assets/accept-invitation-f0f3c6a68515.js").read_text()
    )

    assert 'window.location.hash.slice(1)' in page
    assert 'hash.get("token")' in page
    assert "window.history.replaceState" in page
    assert "?token=" not in page


def test_admin_invitation_form_uses_platform_api():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "admin.html"
    ).read_text() + (WORKSPACE_ROOT / "app/assets/admin-cac3598ae666.js").read_text() + (WORKSPACE_ROOT / "app/assets/admin-dea40d584f53.css").read_text()

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
        (WORKSPACE_ROOT / "app/accept-invitation.html").read_text()
        + (WORKSPACE_ROOT / "app/assets/accept-invitation-f0f3c6a68515.js").read_text()
    )

    assert "payload.product.workspace_route" in page
    assert "window.location.assign(workspaceUrl)" in page
    assert "payload.product.landing_route" not in page
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
    ).read_text() + (WORKSPACE_ROOT / "app/assets/renewaldesk-app-2b95865bd9c7.js").read_text() + (WORKSPACE_ROOT / "app/assets/renewaldesk-app-8d37ae6e9662.css").read_text()

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
    ).read_text() + (WORKSPACE_ROOT / "app/assets/renewaldesk-app-2b95865bd9c7.js").read_text() + (WORKSPACE_ROOT / "app/assets/renewaldesk-app-8d37ae6e9662.css").read_text()

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
    ).read_text() + (WORKSPACE_ROOT / "app/assets/admin-cac3598ae666.js").read_text() + (WORKSPACE_ROOT / "app/assets/admin-dea40d584f53.css").read_text()

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



def test_client_invitation_lifecycle_is_manageable():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "admin.html"
    ).read_text() + (WORKSPACE_ROOT / "app/assets/admin-cac3598ae666.js").read_text() + (WORKSPACE_ROOT / "app/assets/admin-dea40d584f53.css").read_text()

    assert "<h3>Client Invitations</h3>" in page
    assert 'id="clientInvitationRows"' in page
    assert "invitation.status" in page
    assert "invitation.expires_at" in page
    assert "data-revoke-client-invitation" in page
    assert "revokeClientInvitation" in page
    assert "/user-invitations/${invitationId}/revoke" in page



def test_renewaldesk_hides_delete_from_members():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "renewaldesk-app.html"
    ).read_text() + (WORKSPACE_ROOT / "app/assets/renewaldesk-app-2b95865bd9c7.js").read_text() + (WORKSPACE_ROOT / "app/assets/renewaldesk-app-8d37ae6e9662.css").read_text()

    assert "let clientRole = null" in page
    assert "clientRole =" in page
    assert 'clientRole === "owner"' in page
    assert "client.role" in page
    assert 'data-delete-renewal="${item.id}"' in page



def test_renewaldesk_owner_can_manage_client_team():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "renewaldesk-app.html"
    ).read_text() + (WORKSPACE_ROOT / "app/assets/renewaldesk-app-2b95865bd9c7.js").read_text() + (WORKSPACE_ROOT / "app/assets/renewaldesk-app-8d37ae6e9662.css").read_text()

    assert 'id="teamPanel"' in page
    assert 'id="teamInvitationForm"' in page
    assert 'id="teamMemberList"' in page
    assert 'id="teamInvitationList"' in page
    assert 'id="teamActivationLink"' in page
    assert '"/client/team"' in page
    assert '"/client/user-invitations"' in page
    assert "loadClientTeam" in page
    assert 'clientRole !== "owner"' in page
    assert "revokeTeamInvitation" in page



def test_renewaldesk_owner_can_manage_team_memberships():
    page = (
        WORKSPACE_ROOT
        / "app"
        / "renewaldesk-app.html"
    ).read_text() + (WORKSPACE_ROOT / "app/assets/renewaldesk-app-2b95865bd9c7.js").read_text() + (WORKSPACE_ROOT / "app/assets/renewaldesk-app-8d37ae6e9662.css").read_text()

    assert "saveTeamMemberRole" in page
    assert "removeTeamMember" in page
    assert "Save Role" in page
    assert "current_membership_id" in page
    assert "currentMembershipId" in page
    assert '" · You"' in page
    assert '? "hidden"' in page
    assert "[hidden]" in page
    assert "display: none !important;" in page
    assert (
        "`/client/team/memberships/${membershipId}`"
        in page
    )
    assert 'method: "PUT"' in page
    assert 'method: "DELETE"' in page
    assert "Client must retain at least one owner" not in page


def test_renewaldesk_uses_external_csp_assets():
    import hashlib
    import re
    from html.parser import HTMLParser

    class PageParser(HTMLParser):
        def handle_starttag(self, tag, attrs):
            attributes = dict(attrs)
            assert tag != "style"
            assert "style" not in attributes
            assert not any(name.startswith("on") for name in attributes)
            if tag == "script":
                assert attributes.get("src", "").startswith("/assets/")

    page = (WORKSPACE_ROOT / "app/renewaldesk-app.html").read_text()
    PageParser().feed(page)
    paths = re.findall(r'(?:src|href)="(/assets/renewaldesk-app-[^"]+)"', page)
    assert len(paths) == 2
    for path in paths:
        content = (WORKSPACE_ROOT / "app" / path.lstrip("/")).read_bytes()
        assert hashlib.sha256(content).hexdigest()[:12] in path
        if path.endswith(".js"):
            script = content.decode()
            assert not re.search(r'\bon\w+\s*=', script)
            assert not re.search(r'\bstyle\s*=', script)
            for action in ("edit-renewal", "delete-renewal", "save-team-role",
                           "remove-team-member", "revoke-team-invitation"):
                assert f'button[data-{action}]' in script
            assert 'Number.isSafeInteger(id)' in script


def test_accept_invitation_uses_external_csp_assets():
    import hashlib
    from html.parser import HTMLParser

    class AssetParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.assets = []

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            assert tag != "style"
            assert "style" not in attrs
            assert not any(key.startswith("on") for key in attrs)
            if tag == "script":
                assert attrs.get("src", "").startswith("/assets/")
                self.assets.append(attrs["src"])
            if tag == "link" and attrs.get("rel") == "stylesheet":
                assert attrs.get("href", "").startswith("/assets/")
                self.assets.append(attrs["href"])

    page = (WORKSPACE_ROOT / "app/accept-invitation.html").read_text()
    parser = AssetParser()
    parser.feed(page)
    assert len(parser.assets) == 2
    assert {Path(path).suffix for path in parser.assets} == {".js", ".css"}
    for path in parser.assets:
        content = (WORKSPACE_ROOT / "app" / path.lstrip("/")).read_bytes()
        assert hashlib.sha256(content).hexdigest()[:12] in Path(path).name
    assert 'content="no-referrer"' in page
