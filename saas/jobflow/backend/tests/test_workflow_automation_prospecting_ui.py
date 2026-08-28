from pathlib import Path


WORKSPACE_ROOT = (
    Path(__file__).resolve().parents[2]
)

PROSPECTING_PAGE = (
    WORKSPACE_ROOT
    / "app"
    / "prospecting.html"
)

COMMERCIALIZATION_PAGE = (
    WORKSPACE_ROOT
    / "app"
    / "commercialization.html"
)


def prospecting_source():
    return PROSPECTING_PAGE.read_text() + (
        WORKSPACE_ROOT / "app/assets/prospecting-a1ff52b499b0.js"
    ).read_text()


def test_prospecting_operator_page_exists():
    text = prospecting_source()

    assert "Workflow Automation Package — Prospecting" in text
    assert "New York State" in text
    assert "Small IT providers" in text
    assert "Home-service businesses" not in text
    assert "white-label implementation" in text


def test_prospecting_page_requires_manual_review():
    text = prospecting_source()

    assert "It never sends messages" in text
    assert "Approve Draft" in text
    assert "Reject Candidate" in text
    assert "No message was sent" in text


def test_prospecting_page_uses_operator_api():
    text = prospecting_source()

    assert (
        "/api/v1/products/"
        "workflow-automation/prospecting"
        in text
    )
    assert "/campaigns" in text
    assert "/candidates/" in text
    assert 'credentials: "same-origin"' in text


def test_prospecting_page_polls_queued_runs():
    text = prospecting_source()

    assert "waitForCampaign" in text
    assert "Campaign queued" in text
    assert "window.setTimeout" in text


def test_prospecting_page_supports_manual_intake():
    text = prospecting_source()

    assert 'id="manualCandidateForm"' in text
    assert 'id="manualCampaignId"' in text
    assert 'id="manualBusinessName"' in text
    assert 'id="manualWebsiteUrl"' in text
    assert 'id="manualEmail"' in text
    assert 'id="manualEvidenceUrl"' in text
    assert 'id="manualEvidenceFact"' in text
    assert 'id="manualFitScore"' in text
    assert 'id="manualOutreachSubject"' in text
    assert 'id="manualOutreachBody"' in text
    assert 'method: "POST"' in text
    assert 'await apiRequest("/candidates"' in text
    assert "Add to Review Queue" in text
    assert (
        "Candidate added for review."
        in text
    )
    assert "No message was sent." in text


def test_prospecting_page_tracks_manual_outreach():
    text = prospecting_source()

    assert "Outreach activity" in text
    assert "Mark Sent" in text
    assert "Record Follow-Up" in text
    assert "Record Reply" in text
    assert "Do Not Contact" in text
    assert "recordOutreachSent" in text
    assert "recordFollowUp" in text
    assert "recordReply" in text
    assert "recordSuppression" in text
    assert "outreach/sent" in text
    assert "outreach/follow-up" in text
    assert "outreach/reply" in text
    assert "outreach/suppression" in text
    assert (
        "This permanently suppresses the candidate"
        in text
    )
    assert "It never sends messages." in text


def test_operator_page_has_due_follow_up_view():
    text = prospecting_source()

    assert 'id="dueFollowUpList"' in text
    assert 'apiRequest("/follow-ups/due")' in text
    assert '"Overdue"' in text
    assert '"Due Today"' in text
    assert '"Upcoming"' in text
    assert "showCandidate" in text
    assert "/commercialization#lead-" in text
    assert "Record Follow-Up" in text

    commercialization_text = (
        COMMERCIALIZATION_PAGE.read_text()
        + (
            WORKSPACE_ROOT / "app/assets/commercialization-38f725758156.js"
        ).read_text()
    )
    assert 'id="lead-${lead.id}"' in (
        commercialization_text
    )


def test_prospecting_csp_assets():
    import hashlib
    import re
    from html.parser import HTMLParser

    class CspParser(HTMLParser):
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            assert tag != "style"
            assert "style" not in attrs
            assert not any(name.startswith("on") for name in attrs)
            if tag == "script":
                assert attrs.get("src")

    page = PROSPECTING_PAGE.read_text()
    CspParser().feed(page)
    references = re.findall(
        r'(?:src|href)="(/assets/prospecting-[a-f0-9]{12}\.(?:js|css))"', page
    )
    assert len(references) == 2
    for reference in references:
        asset = WORKSPACE_ROOT / "app" / reference.lstrip("/")
        content = asset.read_bytes()
        assert hashlib.sha256(content).hexdigest()[:12] in asset.name
        if asset.suffix == ".js":
            script = content.decode()
            assert not re.search(r"\bon\w+\s*=|\bstyle\s*=", script)
            assert 'event.preventDefault()' in script
            for action in ("run", "review", "show", "follow-up", "sent", "reply", "suppress"):
                assert f'data-prospect-action="{action}"' in script
                assert f'case "{action}":' in script
            for container in ("campaignList", "candidateList", "dueFollowUpList"):
                assert f'bindProspectActions({container})' in script
        else:
            assert "#agentStatus" in content.decode()
