#!/usr/bin/env python3
"""Synthetic, isolated SQL library benchmark. Never connects to a running portal."""
import argparse
import json
import statistics
import sys
import tempfile
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from portal.app import Store, is_admin
from portal.library_query import query, refresh
from portal.search import index_document


def measure(size, samples):
    with tempfile.TemporaryDirectory(prefix="margen-benchmark-") as folder:
        store = Store(folder)
        u = store.user("benchmark@example.invalid", "Synthetic owner")
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
                        "Synthetic review " + str(i),
                        "Project " + str(i % 10),
                        "fixture-" + str(i),
                        now,
                        "private",
                    ),
                )
                db.execute(
                    "INSERT INTO versions VALUES(?,?,?,?)", (vid, aid, "0" * 64, now)
                )
                db.execute(
                    "INSERT INTO version_meta VALUES(?,?,?,?,?)",
                    (
                        vid,
                        "published",
                        "Synthetic review " + str(i),
                        "Project " + str(i % 10),
                        "{}",
                    ),
                )
                db.execute(
                    "UPDATE artifacts SET current_version=? WHERE id=?", (vid, aid)
                )
                index_document(
                    db,
                    {
                        "id": aid,
                        "title": "Synthetic review " + str(i),
                        "space": "Project " + str(i % 10),
                        "current_version": vid,
                    },
                    "<p>Synthetic evidence: revenue, operations, decision review.</p>",
                )
            start = time.perf_counter()
            refresh(db)
            projection = time.perf_counter() - start
        result = {}
        for name, params in [
            ("recent", {}),
            ("search", {"q": "revenue", "sort": "relevance"}),
            ("filtered", {"space": "Project 2", "review": "clear"}),
        ]:
            times = []
            for _ in range(samples):
                start = time.perf_counter()
                with store.db() as db:
                    response = query(db, u, params, is_admin)
                times.append((time.perf_counter() - start) * 1000)
            result[name] = {
                "p50_ms": round(statistics.median(times), 2),
                "p95_ms": round(sorted(times)[max(0, int(0.95 * len(times)) - 1)], 2),
                "rows": len(response["artifacts"]),
                "total": response["total"],
            }
        return {
            "artifacts": size,
            "samples": samples,
            "initial_projection_seconds": round(projection, 3),
            "queries": result,
        }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sizes", type=int, nargs="+", default=[100, 1000, 5000])
    p.add_argument("--samples", type=int, default=20)
    a = p.parse_args()
    print(
        json.dumps(
            {
                "environment": "local synthetic SQLite; warm OS cache; no HTTP/render/network cost",
                "results": [measure(n, a.samples) for n in a.sizes],
            },
            indent=2,
        )
    )
