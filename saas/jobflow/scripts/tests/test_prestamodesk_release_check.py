"""Synthetic public-file and local HTTP tests; never contact production."""
import importlib.util
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

script = Path(__file__).resolve().parents[1] / 'verify-prestamodesk-release.py'
spec = importlib.util.spec_from_file_location('prestamodesk_release_check', script)
check = importlib.util.module_from_spec(spec); spec.loader.exec_module(check)

class ReleaseCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.app = Path(self.temp.name) / 'app'; self.app.mkdir(mode=0o755)
        (self.app / 'assets').mkdir(mode=0o755)
        self.files = {
            'prestamodesk-workspace.html': b'<script src="/assets/shell.js"></script><link href="/assets/style.css?version=1" rel="stylesheet">',
            'assets/shell.js': b'console.log("synthetic");',
            'assets/style.css': b'body {background:url("pixel.png");}',
            'assets/pixel.png': b'synthetic-image-bytes',
        }
        for name, content in self.files.items():
            path = self.app / name; path.write_bytes(content); path.chmod(0o644)
    def tearDown(self):
        self.temp.cleanup()
    def test_discovers_css_assets_and_ignores_external_and_data_urls(self):
        self.assertEqual(check.collect_files(self.app), self.files)
        self.assertIsNone(check.local_asset('https://external.example.test/assets/x.js', 'page.html'))
        self.assertIsNone(check.local_asset('data:image/png;base64,AAA', 'assets/x.css'))
    def test_owner_only_file_fails_even_when_running_as_root(self):
        (self.app / 'assets/shell.js').chmod(0o600)
        with self.assertRaisesRegex(check.CheckError, 'not readable'):
            check.collect_files(self.app)
    def test_directory_without_worker_traversal_fails(self):
        (self.app / 'assets').chmod(0o700)
        with self.assertRaisesRegex(check.CheckError, 'not traversable'):
            check.collect_files(self.app)
    def test_missing_reference_fails(self):
        (self.app / 'assets/shell.js').unlink()
        with self.assertRaisesRegex(check.CheckError, 'Missing'):
            check.collect_files(self.app)
    def test_symlink_escape_and_encoded_traversal_fail(self):
        outside = Path(self.temp.name) / 'outside.js'; outside.write_text('synthetic')
        (self.app / 'assets/shell.js').unlink(); (self.app / 'assets/shell.js').symlink_to(outside)
        with self.assertRaisesRegex(check.CheckError, 'unsafe'):
            check.collect_files(self.app)
        with self.assertRaisesRegex(check.CheckError, 'escapes'):
            check.local_asset('/assets/%2e%2e/private.js', 'page.html')
    def server(self, override=None):
        files = self.files; override = override or {}; hits = []
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                hits.append(self.path)
                name = self.path.lstrip('/')
                content = files.get(name, b'missing')
                status = 200 if name in files else 404
                kind = 'text/html' if name.endswith('.html') else 'application/javascript' if name.endswith('.js') else 'text/css' if name.endswith('.css') else 'image/png'
                status, kind, content = override.get(name, (status, kind, content))
                self.send_response(status); self.send_header('Content-Type', kind)
                if status == 302:
                    self.send_header('Location', '/sign-in')
                self.end_headers(); self.wfile.write(content)
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        self.addCleanup(server.server_close); self.addCleanup(server.shutdown)
        return 'http://127.0.0.1:' + str(server.server_port), hits
    def test_http_success_matches_exact_bytes(self):
        origin, hits = self.server(); check.verify_http(origin, check.collect_files(self.app)); self.assertEqual(len(hits), 4)
    def test_http_403_stops_verification(self):
        origin, _ = self.server({'assets/shell.js': (403, 'text/html', b'denied')})
        with self.assertRaisesRegex(check.CheckError, 'HTTP delivery failed'):
            check.verify_http(origin, self.files)
    def test_redirect_is_not_followed(self):
        origin, hits = self.server({'assets/shell.js': (302, 'text/html', b'redirect')})
        with self.assertRaises(check.CheckError):
            check.verify_http(origin, self.files)
        self.assertNotIn('/sign-in', hits)
    def test_html_fallback_is_rejected_for_asset(self):
        origin, _ = self.server({'assets/shell.js': (200, 'text/html', b'<html>login</html>')})
        with self.assertRaisesRegex(check.CheckError, 'content type'):
            check.verify_http(origin, self.files)
    def test_stale_asset_bytes_are_rejected(self):
        origin, _ = self.server({'assets/shell.js': (200, 'application/javascript', b'old release')})
        with self.assertRaisesRegex(check.CheckError, 'bytes differ'):
            check.verify_http(origin, self.files)
    def test_base_url_rejects_credentials_paths_and_queries(self):
        for url in ['https://user:secret@example.test', 'https://example.test/path', 'https://example.test?token=secret', 'file:///tmp']:
            with self.assertRaises(check.CheckError):
                check.verify_http(url, self.files)
    def test_worker_command_uses_nginx_user_and_does_not_modify_files(self):
        with patch.object(check.subprocess, 'run') as run:
            run.return_value.returncode = 0; check.verify_worker('jobflow-web', self.files)
            command = run.call_args.args[0]
            self.assertEqual(command[:5], ['docker', 'exec', '--user', 'nginx', 'jobflow-web'])
            self.assertNotIn('chmod', command)
            run.return_value.returncode = 1
            with self.assertRaises(check.CheckError):
                check.verify_worker('jobflow-web', self.files)

if __name__ == '__main__':
    unittest.main(verbosity=2)
