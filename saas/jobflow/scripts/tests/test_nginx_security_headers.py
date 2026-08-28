"""Exercise actual Nginx responses in a disposable, network-disabled container.

Run directly from any directory with Python 3 and Docker installed.
Use --image with the existing production web image ID to avoid pulling an image.
No production containers, ports, databases, or credentials are used.
"""
import argparse
import http.client
import io
from pathlib import Path
import subprocess
import tempfile
import threading
import time
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[2]
IMAGE = "nginx:1.31.3-alpine"
CONTAINER = ""


def docker(*args, input=None, timeout=15):
    return subprocess.run(
        ["docker", *args], input=input, capture_output=True,
        timeout=timeout, check=True,
    ).stdout


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
                raise RuntimeError(
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
        (html / "renewaldesk.html").write_text("Header test renewaldesk\n")
        # Other HTML files deliberately absent: /admin exercises a real 404.
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
            except (subprocess.SubprocessError, http.client.HTTPException):
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
        paths = {
            "/": 200, "/renewaldesk": 200, "/admin": 404,
            "/api/v1/admin/overview": 401, "/api/not-found": 404,
        }
        for host, enabled in hosts.items():
            for path, status in paths.items():
                with self.subTest(host=host, path=path):
                    response = request(host, path)
                    self.assertEqual(response.status, status)
                    self.assertEqual(
                        response.headers.get_all("Strict-Transport-Security"),
                        ["max-age=300"] if enabled else None,
                    )
                    self.assertIsNone(response.getheader("Content-Security-Policy"))
                    report = response.getheader("Content-Security-Policy-Report-Only")
                    self.assertIsNotNone(report)
                    self.assertIn("https://static.cloudflareinsights.com", report)
                    for name, value in {
                        "X-Content-Type-Options": "nosniff",
                        "X-Frame-Options": "DENY",
                        "Referrer-Policy": "no-referrer",
                        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
                    }.items():
                        self.assertEqual(response.headers.get_all(name), [value])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default=IMAGE)
    args = parser.parse_args()
    IMAGE = args.image
    image_id = docker("image", "inspect", "--format", "{{.Id}}", IMAGE).decode().strip()
    print("Testing Nginx image:", image_id, flush=True)
    unittest.main(argv=[__file__], verbosity=2)
