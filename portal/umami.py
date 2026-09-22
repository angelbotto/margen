"""Bounded server-side Umami reporting; no credentials or raw sessions leave here."""
import json
import os
import re
import threading
import time
from collections import OrderedDict
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class UmamiReports:
    def __init__(self, configuration):
        self.configuration = configuration
        self.cache = OrderedDict()
        self.lock = threading.Lock()
        self.token = None
        self.token_until = 0

    def request(self, url, body=None, token=None, share_token=None):
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        if share_token:
            headers["x-umami-share-token"] = share_token
        if body is not None:
            headers["Content-Type"] = "application/json"
        req = Request(url, data=json.dumps(body).encode() if body is not None else None, headers=headers)
        with build_opener(NoRedirect).open(req, timeout=4) as response:
            raw = response.read(100001)
            if len(raw) > 100000:
                raise ValueError("Oversized analytics response")
            return json.loads(raw)

    def stats(self, artifact, start, end):
        config = self.configuration()
        if not config:
            return None
        origin = (os.environ.get("MARGEN_UMAMI_API_ORIGIN") or config["origin"]).rstrip("/")
        parsed = urlsplit(origin)
        if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
            return None
        # API_ORIGIN is operator-only configuration, never derived from reader input.
        # Bucket the end timestamp: all readers share one bounded cache entry per period.
        key = (origin, config["website"], artifact, start, end // 300000)
        now = time.monotonic()
        with self.lock:
            cached = self.cache.get(key)
            if cached and cached[0] > now:
                self.cache.move_to_end(key)
                return cached[1]
            result = None
            try:
                token = os.environ.get("MARGEN_UMAMI_TOKEN")
                share_id = os.environ.get("MARGEN_UMAMI_SHARE_ID")
                share_token = None
                if share_id:
                    if not re.fullmatch(r"[a-zA-Z0-9]{8,50}", share_id):
                        raise ValueError("Invalid reporting credential")
                    if not self.token or self.token_until <= now:
                        auth = self.request(origin + "/api/share/" + share_id)
                        if auth.get("websiteId") != config["website"]:
                            raise ValueError("Reporting website mismatch")
                        self.token = auth["token"]
                        self.token_until = now + 3600
                    share_token = self.token
                elif not token:
                    username = os.environ.get("MARGEN_UMAMI_USERNAME")
                    password = os.environ.get("MARGEN_UMAMI_PASSWORD")
                    if not username or not password:
                        return None
                    if not self.token or self.token_until <= now:
                        self.token = self.request(origin + "/api/auth/login", {"username": username, "password": password})["token"]
                        self.token_until = now + 3600
                    token = self.token
                version = os.environ.get("MARGEN_UMAMI_API_VERSION", "3")
                if version not in ("2", "3"):
                    raise ValueError("Unsupported Umami API")
                # v3 renamed url to path. Never fall back to an unfiltered website total.
                query = {"startAt": start, "endAt": end, "path" if version == "3" else "url": "/a/" + artifact}
                data = self.request(origin + "/api/websites/" + config["website"] + "/stats?" + urlencode(query), token=token, share_token=share_token)
                def count(name):
                    value = data[name]
                    if isinstance(value, dict):
                        value = value.get("value")
                    if type(value) is not int or value < 0:
                        raise ValueError("Invalid analytics count")
                    return value
                result = {"views": count("pageviews"), "visitors": count("visitors"), "source": "umami"}
            except Exception:
                # Analytics must not break reading or expose provider errors/credentials.
                self.token = None
                self.token_until = 0
            self.cache[key] = (now + (300 if result is not None else 30), result)
            self.cache.move_to_end(key)
            while len(self.cache) > 256:
                self.cache.popitem(last=False)
            return result
