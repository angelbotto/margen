"""Workspace aggregation and graph evidence regressions."""

import json
import time
import unittest
from datetime import datetime, timezone, timedelta
from portal import test_app as fixtures


class WorkspaceTests(unittest.TestCase):
    setUp = fixtures.PortalTests.setUp
    tearDown = fixtures.PortalTests.tearDown
    client = fixtures.PortalTests.client

    def test_analytics_aggregates_before_limits_and_scopes_owners(self):
        ids = [self.a["id"]]
        for i in range(7):
            r = self.owner.post(
                "/api/artifacts",
                json={
                    "title": f"Document {i}",
                    "space": "Research",
                    "html": fixtures.HTML.replace("informe-prueba", f"workspace-{i}"),
                },
            )
            self.assertEqual(r.status_code, 200, r.text)
            ids.append(r.json()["id"])
        with self.store.db() as db:
            for aid in ids:
                db.executemany(
                    "INSERT INTO artifact_visits VALUES(?,?,?)",
                    [
                        (
                            aid,
                            (
                                datetime.now(timezone.utc).date() - timedelta(days=i)
                            ).isoformat(),
                            2,
                        )
                        for i in range(300)
                    ],
                )
            db.execute(
                "INSERT INTO artifact_visits VALUES(?,?,99)",
                (
                    ids[0],
                    (datetime.now(timezone.utc).date() + timedelta(days=1)).isoformat(),
                ),
            )
        response = self.owner.get("/api/creator/analytics/summary?days=365").json()
        self.assertEqual(response["total"], 4800)
        self.assertEqual(response["active_artifacts"], 8)
        self.assertEqual(sum(x["views"] for x in response["ranking"]), 4800)
        self.assertEqual(
            self.owner.get("/api/creator/analytics/summary?days=7").json()["total"], 112
        )
        self.assertEqual(
            self.owner.get(
                "/api/creator/analytics/summary?days=7&project=Research"
            ).json()["total"],
            98,
        )
        self.assertEqual(
            self.other.get("/api/creator/analytics/summary").json()["total"], 0
        )
        self.assertEqual(
            self.other.get("/api/creator/analytics/summary").json()["spaces"], []
        )
        self.assertEqual(
            self.guest.get("/api/creator/analytics/summary").status_code, 401
        )
        for days in ["oops", "0", "9999"]:
            self.assertEqual(
                self.owner.get(
                    "/api/creator/analytics/summary?days=" + days
                ).status_code,
                422,
            )

    def test_graph_preserves_topics_collections_and_manual_classification(self):
        with self.store.db() as db:
            db.execute(
                "INSERT INTO artifact_meta VALUES(?,?,?,0)",
                (
                    self.a["id"],
                    json.dumps(["capacity"]),
                    json.dumps(["Quarterly review"]),
                ),
            )
        graph = self.owner.get("/api/creator/graph").json()
        kinds = {n["kind"] for n in graph["network"]["nodes"]}
        self.assertTrue({"space", "topic", "collection"} <= kinds)
        topic = next(n for n in graph["network"]["nodes"] if n["kind"] == "topic")
        self.assertEqual(topic["title"], "capacity")
        self.assertIn(
            "Tema manual",
            next(
                e["reason"]
                for e in graph["network"]["edges"]
                if e["target"] == topic["id"]
            ),
        )
        self.assertEqual(
            self.other.get("/api/creator/graph").json()["network"]["nodes"], []
        )


if __name__ == "__main__":
    unittest.main()
