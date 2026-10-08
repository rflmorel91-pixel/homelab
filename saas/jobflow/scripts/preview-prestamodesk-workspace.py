"""Loopback-only visual preview. Synthetic responses; all API writes rejected."""
import argparse
import json
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'app'


class Preview(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(APP), **kwargs)

    def send_json(self, data, status=200):
        payload = json.dumps(data).encode()
        self.send_response(status); self.send_header('Content-Type', 'application/json'); self.send_header('Cache-Control', 'no-store'); self.send_header('Content-Length', str(len(payload))); self.end_headers(); self.wfile.write(payload)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path in ('/prestamodesk/workspace', '/prestamodesk-workspace.html'):
            html = (APP / 'prestamodesk-workspace.html').read_text().replace('<body>', '<body><div class="pd-message pd-global-message" role="note">Vista previa · datos ficticios. Solo navegación; las operaciones están desactivadas.</div>')
            payload = html.encode(); self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.send_header('Content-Length', str(len(payload))); self.end_headers(); self.wfile.write(payload); return
        if not path.startswith('/api/'):
            return super().do_GET()
        if path.endswith('/health'):
            return self.send_json({'status': 'vista previa'})
        if path.endswith('/access'):
            return self.send_json({'clients': [{'tenant_id': 999, 'client_number': 1, 'name': 'VISTA PREVIA · Negocio ficticio', 'role': 'owner'}]})
        if path.endswith('/public-page'):
            return self.send_json({'tenant_slug': 'preview-synthetic'})
        if path.endswith('/late-fee-policy'):
            return self.send_json({'detail': 'Sin política en la vista previa'}, 404)
        if path.endswith('/team'):
            return self.send_json({'members': [], 'assignable_roles': ['collector', 'cashier'], 'roles': []})
        if path.endswith('/invitations'):
            return self.send_json({'invitations': []})
        if path.endswith('/supervision'):
            # All displayed metrics are zero because the visual preview has no records.
            source = next((APP / 'assets').glob('prestamodesk-cobros-supervision-*.js')).read_text()
            data = {key: 0 for key in re.findall(r'data\.([a-z_]+)', source)}
            data.update(aging_buckets=[], collectors=[])
            return self.send_json(data)
        return self.send_json([])

    def do_POST(self):
        self.send_json({'detail': 'Vista previa visual: no guarda préstamos, pagos ni cambios.'}, 405)
    do_PUT = do_PATCH = do_DELETE = do_POST


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=18446)
    args = parser.parse_args()
    print(f'Visual preview: http://127.0.0.1:{args.port}/prestamodesk/workspace', flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), Preview).serve_forever()
