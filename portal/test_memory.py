"""Working-memory isolation, evidence and lifecycle regression tests."""

import json
import time
import unittest
from unittest.mock import patch
from portal import test_app as fixtures
from portal.app import create_app
from portal.telemetry import Metrics


class MemoryTests(unittest.TestCase):
    setUp = fixtures.PortalTests.setUp
    tearDown = fixtures.PortalTests.tearDown
    client = fixtures.PortalTests.client
    event = fixtures.PortalTests.event
    access = fixtures.PortalTests.access

    def claim(self, **values):
        body = {
            "statement": "Capacity is 20",
            "subject": "Capacity, orders/day",
            "period": "September",
            "value": "20",
            "project": "Personal",
            "evidence": [{"artifact": self.a["id"], "quote": "Cifra de ejemplo"}],
            **values,
        }
        return self.owner.post("/api/creator/claims", json=body)

    def test_claim_citations_isolation_history_and_conflicts(self):
        r = self.claim()
        self.assertEqual(r.status_code, 200, r.text)
        key = r.json()["id"]
        self.assertEqual(self.other.get("/api/creator/memory").json()["claims"], [])
        self.assertEqual(
            self.other.get("/api/creator/claims/" + key + "/history").status_code, 404
        )
        self.assertEqual(
            self.claim(
                evidence=[{"artifact": self.a["id"], "quote": "Invented"}]
            ).status_code,
            422,
        )
        self.assertEqual(self.claim(id=key).status_code, 409)
        self.assertEqual(
            self.claim(id=key, updated=r.json()["updated"], value="30").status_code, 200
        )
        self.assertEqual(
            len(
                self.owner.get("/api/creator/claims/" + key + "/history").json()[
                    "items"
                ]
            ),
            2,
        )
        other = self.claim(value="40").json()["id"]
        candidates = self.owner.get("/api/creator/memory").json()["contradictions"]
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["state"], "suggested")
        self.assertEqual(
            self.other.post(
                "/api/creator/contradictions",
                json={
                    "left": key,
                    "right": other,
                    "state": "confirmed",
                    "reason": "test",
                },
            ).status_code,
            404,
        )
        self.assertEqual(
            self.owner.post(
                "/api/creator/contradictions",
                json={
                    "left": key,
                    "right": other,
                    "state": "dismissed",
                    "reason": "Different methodology",
                },
            ).status_code,
            200,
        )
        self.assertEqual(
            self.owner.get("/api/creator/memory").json()["contradictions"][0]["state"],
            "dismissed",
        )

    def test_brief_excludes_private_notes_and_preserves_links(self):
        self.owner.post(self.path + "/review", json=self.event())
        self.owner.post(
            self.path + "/review",
            json=self.event(
                id="private", entry_type="note", text="PRIVATE_NOTE_CANARY"
            ),
        )
        self.claim()
        text = self.owner.get("/api/creator/brief").json()["text"]
        self.assertIn(self.a["id"], text)
        self.assertIn(self.a["version"], text)
        self.assertNotIn("PRIVATE_NOTE_CANARY", text)
        self.assertNotIn(
            self.a["id"], self.other.get("/api/creator/brief").json()["text"]
        )
        self.assertEqual(
            self.owner.post(
                "/api/creator/sessions", json={"session": "invented"}
            ).status_code,
            422,
        )

    def test_anchor_context_disambiguates_without_silent_repair(self):
        from portal.workflows import anchor_status

        html = '<p id="new">North Capacity is 20 orders.</p><p>South Capacity is 20 orders.</p>'
        anchor = {"reference": "old", "quote": "Capacity is 20"}
        self.assertEqual(anchor_status(anchor, html), "ambiguous")
        self.assertEqual(anchor_status({**anchor, "prefix": "North"}, html), "moved")
        self.assertEqual(anchor_status({**anchor, "reference": "#new"}, html), "exact")
        self.assertEqual(
            anchor_status(
                {**anchor, "quote": "Capacity is 30", "reference": "new"}, html
            ),
            "changed",
        )

    def test_metrics_survive_restart_and_use_templates(self):
        self.owner.get(self.path)
        report = Metrics(self.store.root).report()
        self.assertGreater(report["samples"], 0)
        self.assertNotIn(self.a["id"], json.dumps(report))
        self.assertIn("/api/artifacts/{aid}", [r["route"] for r in report["routes"]])

    def test_analytics_requires_access_excludes_owner_and_is_opt_in(self):
        self.assertFalse(
            self.owner.get(self.path + "/analytics-config").json()["enabled"]
        )
        self.assertEqual(
            self.guest.post(self.path + "/visit", json={}).status_code, 404
        )
        self.owner.put("/api/creator/analytics", json={"enabled": True})
        self.assertFalse(
            self.owner.post(self.path + "/visit", json={}).json()["recorded"]
        )
        self.access(visibility="public", comments="readers", grants=[])
        self.assertFalse(
            self.guest.post(self.path + "/visit", json={}, headers={"DNT": "1"}).json()[
                "recorded"
            ]
        )
        self.assertTrue(
            self.guest.post(self.path + "/visit", json={}).json()["recorded"]
        )
        self.assertEqual(
            self.owner.get("/api/creator/analytics").json()["rows"][0]["views"], 1
        )
        self.assertEqual(self.other.get("/api/creator/analytics").json()["rows"], [])

    def test_cancel_ack_and_expired_lease(self):
        self.owner.post(self.path + "/review", json=self.event())
        c = self.owner.post(
            "/api/creator/connectors",
            json={"label": "Test", "agent": "Codex", "device": "Synthetic"},
        ).json()
        key = self.owner.post(
            "/api/creator/jobs",
            json={
                "artifact": self.a["id"],
                "threads": ["test-event-1"],
                "target": {"connector": c["id"]},
            },
        ).json()["id"]
        self.owner.post(
            "/api/creator/jobs/" + key + "/state",
            json={"status": "queued", "revision": 1},
        )
        headers = {"Authorization": "Bearer " + c["token"]}
        claim = self.guest.post("/api/connector/claim", headers=headers).json()
        rev = self.guest.post(
            "/api/connector/jobs/" + key + "/report",
            headers=headers,
            json={"status": "working", "revision": claim["revision"]},
        ).json()["revision"]
        url = "/api/connector/jobs/" + key + "/heartbeat"
        self.assertTrue(
            self.guest.post(url, headers=headers, json={"revision": rev}).json()[
                "continue"
            ]
        )
        with self.store.db() as db:
            db.execute(
                "UPDATE job_leases SET expires=? WHERE job=?",
                (int(time.time()) - 1, key),
            )
        self.assertEqual(
            self.owner.get("/api/creator").json()["jobs"][0]["status"], "failed"
        )
        self.assertFalse(
            self.guest.post(url, headers=headers, json={"revision": rev}).json()[
                "continue"
            ]
        )
        self.assertFalse(
            self.guest.post(
                url, headers=headers, json={"revision": rev, "stopped": True}
            ).json()["continue"]
        )
        self.assertEqual(
            self.owner.get("/api/creator").json()["jobs"][0]["execution"]["stopped"], 1
        )

    def test_shared_views_do_not_grant_document_access(self):
        key = "synthetic-view"
        self.owner.put(
            "/api/context/views/" + key,
            json={
                "name": "Shared filters",
                "kind": "table",
                "body": {"params": {"q": "evidence"}, "items": []},
            },
        )
        self.assertEqual(
            self.owner.put(
                "/api/context/views/" + key + "/access",
                json={"emails": ["other@example.com"]},
            ).status_code,
            200,
        )
        shared = self.other.get("/api/context/views").json()["items"][0]
        self.assertTrue(shared["shared"])
        self.assertFalse(shared["can_manage"])
        self.assertEqual(self.other.get(self.path).status_code, 404)
        self.assertEqual(
            self.other.put(
                "/api/context/views/" + key + "/access", json={"emails": []}
            ).status_code,
            404,
        )
        self.owner.put("/api/context/views/" + key + "/access", json={"emails": []})
        self.assertEqual(self.other.get("/api/context/views").json()["items"], [])

    def test_evidence_search_and_graph_only_include_owned_sources(self):
        self.claim()
        result = self.owner.get("/api/creator/evidence-search?q=Cifra").json()
        self.assertEqual(result["items"][0]["version"], self.a["version"])
        self.assertEqual(
            self.other.get("/api/creator/evidence-search?q=Cifra").json()["items"], []
        )
        self.assertTrue(
            any(
                n["kind"] == "claim"
                for n in self.owner.get("/api/creator/graph").json()["network"]["nodes"]
            )
        )
        self.assertFalse(
            any(
                n["kind"] == "claim"
                for n in self.other.get("/api/creator/graph").json()["network"]["nodes"]
            )
        )


if __name__ == "__main__":
    unittest.main()
