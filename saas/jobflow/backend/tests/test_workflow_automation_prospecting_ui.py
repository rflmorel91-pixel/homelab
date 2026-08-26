from pathlib import Path


WORKSPACE_ROOT = (
    Path(__file__).resolve().parents[2]
)

PROSPECTING_PAGE = (
    WORKSPACE_ROOT
    / "app"
    / "prospecting.html"
)


def test_prospecting_operator_page_exists():
    text = PROSPECTING_PAGE.read_text()

    assert "Workflow Automation Package — Prospecting" in text
    assert "New York State" in text
    assert "Small IT providers" in text
    assert "Home-service businesses" not in text
    assert "white-label implementation" in text


def test_prospecting_page_requires_manual_review():
    text = PROSPECTING_PAGE.read_text()

    assert "It never sends messages" in text
    assert "Approve Draft" in text
    assert "Reject Candidate" in text
    assert "No message was sent" in text


def test_prospecting_page_uses_operator_api():
    text = PROSPECTING_PAGE.read_text()

    assert (
        "/api/v1/products/"
        "workflow-automation/prospecting"
        in text
    )
    assert "/campaigns" in text
    assert "/candidates/" in text
    assert 'credentials: "same-origin"' in text


def test_prospecting_page_polls_queued_runs():
    text = PROSPECTING_PAGE.read_text()

    assert "waitForCampaign" in text
    assert "Campaign queued" in text
    assert "window.setTimeout" in text


def test_prospecting_page_supports_manual_intake():
    text = PROSPECTING_PAGE.read_text()

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
