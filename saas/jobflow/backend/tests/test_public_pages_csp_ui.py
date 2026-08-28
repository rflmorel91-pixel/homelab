"""Guard all public intake pages against reintroducing inline CSP content."""
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


class AssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.assets = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        assert tag != "style", "Inline style block"
        assert "style" not in attrs, "Inline style attribute"
        assert not any(key.startswith("on") for key in attrs), "Inline handler"
        if tag == "script":
            assert attrs.get("src", "").startswith("/assets/")
            self.assets.append(attrs["src"])
        if tag == "link" and attrs.get("rel") == "stylesheet":
            assert attrs.get("href", "").startswith("/assets/")
            self.assets.append(attrs["href"])


def test_public_pages_use_external_content_hashed_assets():
    for name in ("index", "renewaldesk", "request", "workflow-automation"):
        page = (WORKSPACE_ROOT / "app" / f"{name}.html").read_text()
        parser = AssetParser()
        parser.feed(page)
        assert len(parser.assets) == 2, name
        assert {Path(asset).suffix for asset in parser.assets} == {".js", ".css"}
        for asset in parser.assets:
            content = (WORKSPACE_ROOT / "app" / asset.lstrip("/")).read_bytes()
            assert sha256(content).hexdigest()[:12] in Path(asset).name
