"""Local request-translation proxy for running R2ABench's judges against OpenAI.

R2ABench's L2/ReqCov judge was run through a third-party gateway that accepts
``max_tokens`` and a GLM-specific ``thinking`` field. OpenAI's current models
reject both. Rather than edit R2ABench's evaluation code, this proxy sits between
it and the upstream API and changes only those two transport fields:

  max_tokens -> max_completion_tokens    (same limit, renamed)
  thinking   -> removed                  (GLM-only switch; no OpenAI equivalent)

Prompt, model, temperature, response_format and the response body are passed
through unchanged.
"""
from __future__ import annotations

import json
import logging
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

logger = logging.getLogger(__name__)

__all__ = ["start_proxy"]


def _translate(body: dict) -> dict:
    body = dict(body)
    if "max_tokens" in body and "max_completion_tokens" not in body:
        body["max_completion_tokens"] = body.pop("max_tokens")
    body.pop("thinking", None)
    return body


def start_proxy(upstream: str, host: str = "127.0.0.1", port: int = 0) -> tuple[str, ThreadingHTTPServer]:
    """Start the proxy in a daemon thread; return (base_url, server)."""
    upstream = upstream.rstrip("/")

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802 (http.server API)
            raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            try:
                payload = json.dumps(_translate(json.loads(raw))).encode()
            except json.JSONDecodeError:
                payload = raw
            req = urllib.request.Request(
                upstream + self.path, data=payload, method="POST",
                headers={"Authorization": self.headers.get("Authorization", ""),
                         "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=600) as resp:
                    status, data = resp.status, resp.read()
            except urllib.error.HTTPError as e:
                status, data = e.code, e.read()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, fmt: str, *args) -> None:
            logger.debug(fmt, *args)

    server = ThreadingHTTPServer((host, port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base_url = f"http://{host}:{server.server_address[1]}"
    logger.info("judge proxy %s -> %s", base_url, upstream)
    return base_url, server
