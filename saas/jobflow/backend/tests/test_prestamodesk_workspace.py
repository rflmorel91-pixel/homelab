"""Workspace delivery and unchanged CSP boundaries in the normal CI suite."""
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class WorkspaceMarkup(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids = []; self.assets = []; self.views = []; self.inline = []
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if "id" in data: self.ids.append(data["id"])
        if "data-pd-view" in data: self.views.append(data["data-pd-view"])
        for field in ("src", "href"):
            if data.get(field, "").startswith("/assets/"): self.assets.append(data[field])
        if tag in {"iframe", "style"} or tag == "script" and "src" not in data:
            self.inline.append(tag)
        if "style" in data or any(key.startswith("on") for key in data): self.inline.append(tag)


def test_workspace_has_valid_assets_and_no_inline_or_frame_content():
    parser = WorkspaceMarkup(); parser.feed((ROOT / "app/prestamodesk-workspace.html").read_text())
    assert not parser.inline
    assert len(parser.ids) == len(set(parser.ids))
    assert parser.views == ["summary", "loans", "cashier", "collections", "supervision", "administration"]
    for asset in parser.assets: assert (ROOT / "app" / asset.lstrip("/")).is_file()
    scripts = "\n".join((ROOT / "app" / asset.lstrip("/")).read_text() for asset in parser.assets if asset.endswith(".js"))
    assert "portfolioImport" not in scripts and "administration/imports" not in scripts
    assert "new Function(" not in scripts and "eval(" not in scripts


def test_workspace_is_routed_with_existing_frame_restrictions():
    for name in ("nginx/default.conf", "staging/nginx.conf"):
        config = (ROOT / name).read_text()
        assert "location = /prestamodesk/workspace {" in config
        assert "try_files /prestamodesk-workspace.html =404;" in config
        assert "frame-ancestors 'none'" in config and "frame-src 'none'" in config
    assert "app|workspace|caja" in (ROOT / "nginx/default.conf").read_text()
    assert '/prestamodesk-workspace.html "default-src' in (ROOT / "staging/nginx.conf").read_text()
