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

    assert "Product #6 Prospecting Agent" in text
    assert "New York State" in text
    assert "Small IT providers" in text
    assert "Home-service businesses" in text


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
