"""Read-only checks of PréstamoDesk public files and deployed bytes."""
from __future__ import annotations
import argparse
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import posixpath
import re
import stat
import subprocess
import sys
from urllib.parse import unquote, urljoin, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

class CheckError(RuntimeError):
    pass

class AssetParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.references = []
    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ("src", "href") and value:
                self.references.append(value)


def local_asset(reference: str, source: str) -> str | None:
    parsed = urlsplit(reference)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    path = unquote(urlsplit(urljoin("https://local.invalid/" + source, reference)).path)
    path = posixpath.normpath(path)
    if not path.startswith("/assets/"):
        if "/assets/" in parsed.path:
            raise CheckError("Asset reference escapes assets directory")
        return None
    if "\x00" in path or "\\" in path:
        raise CheckError("Invalid asset reference")
    return path.lstrip("/")


def collect_files(app: Path) -> dict[str, bytes]:
    pages = sorted(app.glob("prestamodesk*.html"))
    if not pages:
        raise CheckError("No PréstamoDesk pages found")
    if not (app / "prestamodesk-workspace.html").is_file():
        raise CheckError("Unified workspace page missing")
    pending = [page.name for page in pages]; result = {}
    while pending:
        name = pending.pop()
        if name in result:
            continue
        path = app / name
        if not path.is_file() or not path.resolve().is_relative_to(app.resolve()):
            raise CheckError("Missing or unsafe public file: " + name)
        # Nginx workers do not run as the checkout owner. Root's os.access()
        # would conceal the owner-only permission failure this check detects.
        if not stat.S_IMODE(path.stat().st_mode) & stat.S_IROTH:
            raise CheckError("Public file is not readable by Nginx workers: " + name + " (expected other-read permission)")
        parent = path.parent
        while True:
            if not stat.S_IMODE(parent.stat().st_mode) & stat.S_IXOTH:
                raise CheckError("Public directory is not traversable by Nginx workers: " + str(parent.relative_to(app.parent)))
            if parent == app:
                break
            parent = parent.parent
        content = path.read_bytes(); result[name] = content
        references = []
        if path.suffix == ".html":
            parser = AssetParser(); parser.feed(content.decode("utf-8")); references = parser.references
        elif path.suffix == ".css":
            references = re.findall(r"url\(\s*['\"]?([^)'\"\s]+)", content.decode("utf-8"))
            references += re.findall(r"@import\s+['\"]([^'\"]+)['\"]", content.decode("utf-8"))
        for reference in references:
            asset = local_asset(reference, name)
            if asset:
                pending.append(asset)
    return result


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def verify_http(base_url: str, files: dict[str, bytes], opener=None) -> None:
    parsed = urlsplit(base_url)
    if parsed.scheme not in ("https", "http") or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/"):
        raise CheckError("Base URL must be an HTTP(S) origin without credentials or a path")
    opener = opener or build_opener(NoRedirect())
    types = {".html": {"text/html"}, ".js": {"application/javascript", "text/javascript"}, ".css": {"text/css"}}
    for name, expected in sorted(files.items()):
        request = Request(base_url.rstrip("/") + "/" + name, headers={"User-Agent": "PrestamoDesk-Release-Check/1.0", "Accept-Encoding": "identity", "Cache-Control": "no-cache"})
        try:
            with opener.open(request, timeout=20) as response:
                if response.status != 200:
                    raise CheckError("Unexpected HTTP status for " + name)
                content_type = response.headers.get_content_type()
                if Path(name).suffix in types and content_type not in types[Path(name).suffix]:
                    raise CheckError("Unexpected content type for " + name)
                content = response.read(len(expected) + 1)
                if hashlib.sha256(content).digest() != hashlib.sha256(expected).digest():
                    raise CheckError("Deployed bytes differ from checkout: " + name)
        except CheckError:
            raise
        except __import__("urllib.error", fromlist=["HTTPError"]).HTTPError as error:
            status = error.code
            error.close()
            raise CheckError("HTTP delivery failed for " + name + " (HTTP " + str(status) + ")") from None
        except Exception as error:
            # Avoid exposing response bodies, cookies or private URL parameters.
            raise CheckError("HTTP delivery failed for " + name + " (" + type(error).__name__ + ")") from None


def verify_worker(container: str, files: dict[str, bytes]) -> None:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", container):
        raise CheckError("Invalid container name")
    paths = ["/usr/share/nginx/html/" + name for name in sorted(files)]
    result = subprocess.run(["docker", "exec", "--user", "nginx", container, "sh", "-c", 'for path do test -f "$path" && test -r "$path" || exit 1; done', "check-public-files", *paths], capture_output=True)
    if result.returncode:
        raise CheckError("Nginx worker cannot read one or more public files, or container check failed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-root", type=Path, default=Path(__file__).resolve().parents[1] / "app")
    parser.add_argument("--base-url", help="Also verify HTTP status, content type and exact deployed bytes")
    parser.add_argument("--container", help="Also verify readability as the container's nginx user")
    args = parser.parse_args()
    try:
        files = collect_files(args.app_root.resolve())
        print(f"PUBLIC FILE CHECK PASSED: {len(files)} pages/assets; permissions and references verified.")
        if args.container:
            verify_worker(args.container, files); print("NGINX WORKER CHECK PASSED")
        if args.base_url:
            verify_http(args.base_url, files); print("PUBLIC DELIVERY CHECK PASSED: HTTP 200, content types and checkout bytes verified.")
    except (CheckError, OSError, UnicodeError) as error:
        print("RELEASE CHECK FAILED: " + str(error), file=sys.stderr); return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
