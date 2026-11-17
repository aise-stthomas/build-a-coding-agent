"""Run the payments server over HTTP on this machine, the way the function serves it.

  uv run serve_http.py                      then, in another terminal:
  PAYMENTS_URL=http://localhost:8765/mcp uv run main_2_servers.py
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from src.function.handler import handler


class MCP(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"])).decode()
        out = handler({"requestContext": {"http": {"method": "POST"}}, "body": body}, None)
        self.send_response(out["statusCode"])
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(out["body"].encode())

    def log_message(self, fmt, *args):
        print("POST", json.loads(self.headers.get("X-Debug", "{}")) or "", *args)


print("payments server on http://localhost:8765/mcp")
HTTPServer(("localhost", 8765), MCP).serve_forever()
