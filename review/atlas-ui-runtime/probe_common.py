"""Shared helpers for the independent atlas UI/runtime probes (review only)."""
from __future__ import annotations
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from urllib.parse import quote, urlsplit


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


@contextmanager
def serve(html: Path):
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(html.parent)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/{quote(html.name)}'
    finally:
        server.shutdown()


def offline(context, blocked: list):
    def route(r):
        if urlsplit(r.request.url).hostname == '127.0.0.1' or r.request.url.startswith('data:'):
            r.continue_()
        else:
            blocked.append(r.request.url)
            r.abort()
    context.route('**/*', route)
