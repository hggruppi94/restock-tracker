"""
Local web server for the dashboard.

Serves the tracker folder at http://localhost:8765 and saves the restock
info you enter on the dashboard to store-notes.json in this folder.
Only reachable from this computer (bound to 127.0.0.1).
"""

import functools
import http.server
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTES_FILE = HERE / "store-notes.json"
PORT = 8765
MAX_BODY = 2_000_000


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/api/store-notes":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0 or length > MAX_BODY:
            self.send_error(413)
            return
        try:
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError("expected an object")
        except ValueError as e:
            self.send_error(400, str(e))
            return
        tmp = NOTES_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(tmp, NOTES_FILE)
        self.send_response(204)
        self.end_headers()

    def end_headers(self):
        # Always serve fresh data files to the dashboard.
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass  # keep the window quiet


if __name__ == "__main__":
    handler = functools.partial(Handler, directory=str(HERE))
    with http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler) as srv:
        print(f"Dashboard at http://localhost:{PORT}/index.html")
        srv.serve_forever()
