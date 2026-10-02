from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ADMIN_PAGE = ROOT / "app" / "admin.html"
ADMIN_SCRIPT = (
    ROOT
    / "app"
    / "assets"
    / "admin-208a679dbd82.js"
)


def test_admin_uses_external_fingerprinted_script():
    html = ADMIN_PAGE.read_text()

    assert ADMIN_SCRIPT.is_file()
    assert (
        "/assets/admin-208a679dbd82.js"
        in html
    )


def test_admin_exposes_collector_only_for_prestamodesk():
    script = ADMIN_SCRIPT.read_text()

    for expected in (
        "membershipRoleOptions",
        'productSlug === "prestamodesk"',
        '["collector", "Collector"]',
        "tenantProductSlug",
        "clientInvitationRole",
        "newMembershipRole",
        "membership.role",
    ):
        assert expected in script

    assert (
        "membershipRoleOptions("
        in script
    )
