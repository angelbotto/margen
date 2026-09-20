"""Bounded durable operational measurements; no URLs, identities or document bodies."""

import math
import sqlite3
import threading
import time
from contextlib import closing


class Metrics:
    def __init__(self, root):
        self.path = root / "telemetry.sqlite3"
        self.lock = threading.Lock()
        with closing(sqlite3.connect(self.path)) as db:
            db.executescript(
                "PRAGMA journal_mode=WAL; CREATE TABLE IF NOT EXISTS requests(id INTEGER PRIMARY KEY,at INTEGER NOT NULL,route TEXT NOT NULL,ms REAL NOT NULL,status INTEGER NOT NULL); CREATE INDEX IF NOT EXISTS requests_at ON requests(at);"
            )

    def record(self, route, ms, status):
        # Route templates only. Unknown routes never contain arbitrary path content.
        with self.lock, closing(sqlite3.connect(self.path, timeout=2)) as db:
            now = int(time.time())
            db.execute(
                "INSERT INTO requests(at,route,ms,status) VALUES(?,?,?,?)",
                (now, route, round(ms, 2), status),
            )
            db.execute(
                "DELETE FROM requests WHERE at<? OR id <= (SELECT coalesce(max(id),0)-50000 FROM requests)",
                (now - 30 * 86400,),
            )
            db.commit()

    def report(self):
        with self.lock, closing(sqlite3.connect(self.path)) as db:
            rows = db.execute(
                "SELECT at,route,ms,status FROM requests ORDER BY id"
            ).fetchall()
        groups = {}
        for at, route, ms, status in rows:
            g = groups.setdefault(route, {"times": [], "errors": 0})
            g["times"].append(ms)
            g["errors"] += status >= 500

        def percentile(values, p):
            return values[max(0, math.ceil(len(values) * p) - 1)]

        return {
            "window": "Last 30 days, up to 50000 requests; persists across restarts",
            "since": rows[0][0] if rows else None,
            "until": rows[-1][0] if rows else None,
            "samples": len(rows),
            "routes": [
                dict(
                    route=k,
                    samples=len(g["times"]),
                    p50_ms=percentile(sorted(g["times"]), 0.5),
                    p95_ms=percentile(sorted(g["times"]), 0.95),
                    server_errors=g["errors"],
                )
                for k, g in groups.items()
            ],
        }
