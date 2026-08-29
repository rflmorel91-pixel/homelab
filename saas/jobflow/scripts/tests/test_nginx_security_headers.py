"""Exercise actual Nginx responses in a disposable, network-disabled container.

Run directly from any directory with Python 3 and Docker installed.
Use --image with the existing production web image ID to avoid pulling an image.
No production containers, ports, databases, or credentials are used.
"""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from html.parser import HTMLParser
import argparse
import http.client
import io
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[2]
IMAGE = "nginx:1.31.3-alpine"
CONTAINER = ""
EXPECTED_CSP = "default-src 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'; frame-src 'none'; form-action 'self'; script-src 'self'; script-src-attr 'none'; style-src 'self'; style-src-attr 'none'; img-src 'self'; font-src 'self'; connect-src 'self'; worker-src 'none'"


def docker(*args, input=None, timeout=15):
    return subprocess.run(
        ["docker", *args], input=input, capture_output=True,
        timeout=timeout, check=True,
    ).stdout


class HTTPProbeError(RuntimeError):
    """The fixture did not return a usable HTTP response."""


class ResponseSocket:
    def __init__(self, data):
        self.data = data

    def makefile(self, *args, **kwargs):
        return io.BytesIO(self.data)


def request(host, path):
    wire = (
        f"GET {path} HTTP/1.1\r\nHost: {host}\r\n"
        "Connection: close\r\n\r\n"
    ).encode("ascii")
    # Keep stdin open until the server closes the HTTP connection.
    command = ["docker", "exec", "-i", CONTAINER,
               "nc", "-w", "3", "127.0.0.1", "80"]
    with subprocess.Popen(command, stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
        timer = threading.Timer(8, proc.kill)
        timer.start()
        try:
            proc.stdin.write(wire)
            proc.stdin.flush()
            raw = proc.stdout.read()
            proc.wait(timeout=2)
            if proc.returncode or not raw:
                raise HTTPProbeError(
                    "HTTP probe failed: " + proc.stderr.read().decode(errors="replace")
                )
        finally:
            timer.cancel()
            if proc.poll() is None:
                proc.kill()
                proc.wait()
    response = http.client.HTTPResponse(ResponseSocket(raw))
    response.begin()
    return response


class SecurityHeaders(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global CONTAINER
        cls.temp = tempfile.TemporaryDirectory(prefix="jobflow-header-test-")
        cls.addClassCleanup(cls.temp.cleanup)
        root = Path(cls.temp.name)
        source = (ROOT / "nginx/default.conf").read_text()
        # Substitute only the unavailable upstream, preserving header directives,
        # routing, error handling, and the complete production server block.
        if "http://jobflow-api:8001" not in source:
            raise RuntimeError("Expected upstream missing; review fixture setup.")
        source = source.replace("http://jobflow-api:8001", "http://127.0.0.1:8001")
        (root / "default.conf").write_text(source)
        (root / "nginx.conf").write_text(
            "pid /tmp/nginx.pid;\nerror_log /dev/stderr warn;\n"
            "events {}\nhttp {\naccess_log off;\n"
            "include /etc/nginx/test-server.conf;\n"
            "server { listen 127.0.0.1:8001;\n"
            "location = /api/v1/admin/overview { return 401; }\n"
            "location / { return 404; }\n}\n}\n"
        )
        html = root / "html"
        html.mkdir()
        (html / "index.html").write_text("Header test index\n")
        for name in ("renewaldesk.html", "workflow-automation.html"):
            shutil.copyfile(ROOT / "app" / name, html / name)
        shutil.copytree(ROOT / "app/assets", html / "assets")
        for name in ("app", "renewaldesk-app", "commercialization", "prospecting",
                     "reset-password", "accept-invitation", "request"):
            (html / f"{name}.html").write_text(f"Excluded fixture: {name}\n")
        # admin.html deliberately absent: /admin exercises a real 404.
        CONTAINER = "jobflow-header-test-" + uuid.uuid4().hex[:12]
        cls.addClassCleanup(cls.remove_container)
        docker(
            "run", "--detach", "--pull=never", "--name", CONTAINER,
            "--network", "none", "--read-only",
            "--memory", "128m", "--cpus", "0.5", "--pids-limit", "64",
            "--tmpfs", "/var/cache/nginx", "--tmpfs", "/tmp",
            "--mount", f"type=bind,src={root / 'nginx.conf'},dst=/etc/nginx/nginx.conf,readonly",
            "--mount", f"type=bind,src={root / 'default.conf'},dst=/etc/nginx/test-server.conf,readonly",
            "--mount", f"type=bind,src={html},dst=/usr/share/nginx/html,readonly",
            "--entrypoint", "nginx", IMAGE, "-g", "daemon off;",
        )
        for _ in range(20):
            try:
                if request("localhost", "/").status == 200:
                    return
            except (HTTPProbeError, subprocess.SubprocessError, http.client.HTTPException):
                pass
            time.sleep(0.25)
        raise RuntimeError("Fixture did not become ready; check image has nginx and nc.")

    @staticmethod
    def remove_container():
        subprocess.run(
            ["docker", "rm", "--force", CONTAINER],
            capture_output=True, timeout=15, check=False,
        )

    def test_host_scope_and_existing_headers(self):
        hosts = {
            "jobflow.fieldlookers.com": True,
            "JOBFLOW.FIELDLOOKERS.COM": True,
            "jobflow.fieldlookers.com:443": True,
            "fieldlookers.com": False,
            "renewaldesk.fieldlookers.com": False,
            "child.jobflow.fieldlookers.com": False,
            "jobflow.fieldlookers.com.example.test": False,
            "localhost": False,
            "127.0.0.1": False,
        }
        # path -> (status, approved final document on the approved host)
        paths = {
            "/": (200, False),
            "/renewaldesk": (200, True),
            "/renewaldesk.html": (200, True),
            "/renewaldesk?probe=1": (200, True),
            "/workflow-automation": (200, True),
            "/workflow-automation.html": (200, True),
            "/workflow-automation.html?probe=1": (200, True),
            "/renewaldesk/": (200, False),
            "/workflow-automation/": (200, False),
            "/missing-public-page": (200, False),
            "/app": (200, False),
            "/app.html": (200, False),
            "/renewaldesk/app": (200, False),
            "/commercialization": (200, False),
            "/prospecting": (200, False),
            "/reset-password": (200, False),
            "/accept-invitation": (200, False),
            "/request/synthetic-client": (200, False),
            "/admin": (404, False),
            "/api/v1/admin/overview": (401, False),
            "/api/not-found": (404, False),
        }
        cases = [(host, enabled, path, status, document)
                 for host, enabled in hosts.items()
                 for path, (status, document) in paths.items()]

        def fetch(case):
            try:
                return case, request(case[0], case[2]), None
            except Exception as error:
                return case, None, error

        print(f"Checking {len(cases)} host/path cases (four workers).", flush=True)
        # Bound parallelism keeps the existing EOF-safe probe without multiplying
        # its nc shutdown delay across the expanded matrix. No rate-limited URLs.
        with ThreadPoolExecutor(max_workers=4) as pool:
            for case, response, error in pool.map(fetch, cases):
                host, enabled, path, status, document = case
                with self.subTest(host=host, path=path):
                    if error is not None:
                        raise error
                    self.assertEqual(response.status, status)
                    self.assertEqual(
                        response.headers.get_all("Strict-Transport-Security"),
                        ["max-age=300"] if enabled else None,
                    )
                    self.assertEqual(
                        response.headers.get_all("Content-Security-Policy"),
                        [EXPECTED_CSP] if enabled and document else None,
                    )
                    self.assertEqual(
                        response.headers.get_all("Content-Security-Policy-Report-Only"),
                        [EXPECTED_CSP],
                    )
                    if document:
                        name = "renewaldesk" if path.startswith("/renewaldesk") else "workflow-automation"
                        self.assertEqual(response.read(), (ROOT / "app" / f"{name}.html").read_bytes())
                    for name, value in {
                        "X-Content-Type-Options": "nosniff",
                        "X-Frame-Options": "DENY",
                        "Referrer-Policy": "no-referrer",
                        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
                    }.items():
                        self.assertEqual(response.headers.get_all(name), [value])

    def test_approved_pages_external_assets(self):
        class Assets(HTMLParser):
            def __init__(self):
                super().__init__()
                self.assets = []
                self.violations = []

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == "style" or "style" in attrs or any(k.startswith("on") for k in attrs):
                    self.violations.append("inline style or event handler")
                if tag == "script":
                    self.assets.append(attrs.get("src", ""))
                if tag == "link" and attrs.get("rel") == "stylesheet":
                    self.assets.append(attrs.get("href", ""))

        for page in ("renewaldesk", "workflow-automation"):
            with self.subTest(page=page):
                parser = Assets()
                parser.feed((ROOT / "app" / f"{page}.html").read_text())
                self.assertEqual(parser.violations, [])
                self.assertEqual(len(parser.assets), 2)
                for asset in parser.assets:
                    self.assertTrue(asset.startswith("/assets/"))
                    self.assertNotIn("..", Path(asset).parts)
                    content = (ROOT / "app" / asset.lstrip("/")).read_bytes()
                    self.assertIn(sha256(content).hexdigest()[:12], asset)
                    response = request("jobflow.fieldlookers.com", asset)
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.read(), content)
                    self.assertIsNone(response.getheader("Content-Security-Policy"))
                    self.assertEqual(response.getheader("Content-Security-Policy-Report-Only"), EXPECTED_CSP)
                    self.assertEqual(response.getheader("Strict-Transport-Security"), "max-age=300")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default=IMAGE)
    args = parser.parse_args()
    IMAGE = args.image
    image_id = docker("image", "inspect", "--format", "{{.Id}}", IMAGE).decode().strip()
    print("Testing Nginx image:", image_id, flush=True)
    unittest.main(argv=[__file__], verbosity=2)
