#!/usr/bin/env python3
"""Concurrent ASGI request benchmark against disposable synthetic data only."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
import tempfile
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from portal.app import create_app, COOKIE
from portal.search import index_document


def measure(size, concurrency, samples):
    with tempfile.TemporaryDirectory(prefix="margen-http-") as folder:
        app = create_app(folder, origin="https://benchmark.example.invalid")
        store = app.state.store
        u = store.user("benchmark@example.invalid", "Synthetic owner")
        html = '<meta name="nota-documento" content="synthetic"><p id="evidence">Synthetic capacity evidence for review.</p>'
        sha = hashlib.sha256(html.encode()).hexdigest()
        (store.files / (sha + ".html")).write_text(html)
        with store.db() as db:
            for i in range(size):
                aid = uuid.uuid4().hex
                vid = uuid.uuid4().hex
                now = 1700000000 + i
                db.execute(
                    "INSERT INTO artifacts(id,owner,title,space,document_id,updated,visibility) VALUES(?,?,?,?,?,?,?)",
                    (
                        aid,
                        u["id"],
                        "Synthetic " + str(i),
                        "Synthetic",
                        "fixture-" + str(i),
                        now,
                        "private",
                    ),
                )
                db.execute("INSERT INTO versions VALUES(?,?,?,?)", (vid, aid, sha, now))
                db.execute(
                    "INSERT INTO version_meta VALUES(?,?,?,?,?)",
                    (vid, "published", "Synthetic " + str(i), "Synthetic", "{}"),
                )
                db.execute(
                    "UPDATE artifacts SET current_version=? WHERE id=?", (vid, aid)
                )
                index_document(
                    db,
                    {
                        "id": aid,
                        "title": "Synthetic " + str(i),
                        "space": "Synthetic",
                        "current_version": vid,
                    },
                    html,
                )
        token = store.session(u["id"])

        def request(i):
            # Separate clients model independent readers; no real network or browser rendering.
            with TestClient(
                app,
                base_url="https://benchmark.example.invalid",
                headers={"Cookie": COOKIE + "=" + token},
            ) as c:
                start = time.perf_counter()
                r = c.get(
                    "/api/artifacts",
                    params={
                        "q": "capacity" if i % 2 else "",
                        "limit": 60,
                        "view": "mine",
                    },
                )
                return (time.perf_counter() - start) * 1000, r.status_code

        request(0)
        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            rows = list(pool.map(request, range(samples)))
        seconds = time.perf_counter() - start
        times = sorted(ms for ms, status in rows)
        return {
            "artifacts": size,
            "concurrency": concurrency,
            "requests": samples,
            "p50_ms": round(statistics.median(times), 2),
            "p95_ms": round(times[math.ceil(0.95 * len(times)) - 1], 2),
            "errors": sum(status >= 400 for _, status in rows),
            "requests_per_second": round(samples / seconds, 2),
        }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--size", type=int, default=1000)
    p.add_argument("--samples", type=int, default=40)
    p.add_argument("--concurrency", type=int, nargs="+", default=[1, 4, 8])
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if (
        not 1 <= a.size <= 10000
        or not 2 <= a.samples <= 1000
        or any(not 1 <= c <= 32 for c in a.concurrency)
    ):
        p.error("Use bounded synthetic inputs")
    result = {
        "scope": "Local ASGI TestClient; includes authorization, SQL and telemetry. No external network, browser, concurrent writes or production SLA.",
        "python": sys.version.split()[0],
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "results": [measure(a.size, c, a.samples) for c in a.concurrency],
    }
    a.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
