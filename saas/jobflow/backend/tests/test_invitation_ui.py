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
