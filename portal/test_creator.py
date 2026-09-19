import json
import unittest
from portal import test_app as fixtures


class CreatorTests(unittest.TestCase):
    setUp = fixtures.PortalTests.setUp
    tearDown = fixtures.PortalTests.tearDown
    client = fixtures.PortalTests.client
    event = fixtures.PortalTests.event

    def test_decision_evidence_and_changed_version(self):
        body = {
            "title": "Decision",
            "project": "Personal",
            "state": "accepted",
            "evidence": [{"artifact": self.a["id"], "quote": "Cifra de ejemplo"}],
        }
        r = self.owner.post("/api/creator/decisions", json=body)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertFalse(
            self.owner.get("/api/creator").json()["decisions"][0]["needs_review"]
        )
        self.assertEqual(self.other.get("/api/creator").json()["decisions"], [])
        self.assertEqual(
            self.other.post("/api/creator/decisions", json=body).status_code, 404
        )
        self.assertEqual(
            self.owner.post(
                "/api/creator/decisions",
                json={
                    **body,
                    "evidence": [{"artifact": self.a["id"], "quote": "Invented"}],
                },
            ).status_code,
            422,
        )
        self.owner.post(
            self.path + "/versions",
            json={"title": "Changed", "html": "<p>New evidence</p>", "publish": True},
        )
        # A draft alone must not invalidate the currently cited published evidence.
        self.assertFalse(
            self.owner.get("/api/creator").json()["decisions"][0]["needs_review"]
        )

    def test_assignment_delivery_and_private_notes(self):
        self.owner.post(self.path + "/review", json=self.event())
        self.owner.post(
            self.path + "/review", json=self.event(id="private", entry_type="note")
        )
        connector = self.owner.post(
            "/api/creator/connectors",
            json={"label": "Test", "agent": "Codex", "device": "Test machine"},
        ).json()
        target = {"connector": connector["id"], "session": "real-fixture-session"}
        r = self.owner.post(
            "/api/creator/jobs",
            json={"artifact": self.a["id"], "threads": ["private"], "target": target},
        )
        self.assertEqual(r.status_code, 422)
        r = self.owner.post(
            "/api/creator/jobs",
            json={
                "artifact": self.a["id"],
                "threads": ["test-event-1"],
                "target": target,
            },
        )
        self.assertEqual(r.status_code, 200, r.text)
        key = r.json()["id"]
        self.assertEqual(self.other.get("/api/creator/jobs/" + key).status_code, 404)
        packet = self.owner.get("/api/creator/jobs/" + key).json()
        self.assertNotIn(
            "private", [i["thread"]["thread"] for i in packet["packet"]["items"]]
        )
        self.assertEqual(
            self.owner.post(
                "/api/creator/jobs/" + key + "/state",
                json={"status": "queued", "revision": 1},
            ).status_code,
            200,
        )
        headers = {"Authorization": "Bearer " + connector["token"]}
        claimed = self.guest.post("/api/connector/claim", headers=headers).json()
        self.assertEqual(claimed["job"], key)
        self.assertIsNone(
            self.guest.post("/api/connector/claim", headers=headers).json()["job"]
        )
        r = self.guest.post(
            "/api/connector/jobs/" + key + "/report",
            headers=headers,
            json={"status": "working", "revision": claimed["revision"]},
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(
            self.guest.get("/api/artifacts", headers=headers).status_code, 401
        )
        self.owner.delete("/api/creator/connectors/" + connector["id"])
        self.assertEqual(
            self.guest.post("/api/connector/claim", headers=headers).status_code, 401
        )

    def test_approved_rules_are_browser_owned(self):
        r = self.owner.post(
            "/api/creator/rules",
            json={"rule": "Explain uncertainty", "project": "Personal"},
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(self.other.get("/api/creator").json()["rules"], [])
        key = r.json()["id"]
        self.owner.delete("/api/creator/rules/" + key)
        self.assertEqual(self.owner.get("/api/creator").json()["rules"], [])

    def test_full_assignment_returns_only_its_draft_and_keeps_feedback_open(self):
        self.owner.post(self.path + "/review", json=self.event())
        c = self.owner.post(
            "/api/creator/connectors",
            json={"label": "Local", "agent": "Codex", "device": "Fixture"},
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
        base = "/api/connector/jobs/" + key
        claim = self.guest.post("/api/connector/claim", headers=headers).json()
        self.assertEqual(
            self.guest.get("/api/connector/pending", headers=headers).json()["jobs"],
            [key],
        )
        revision = self.guest.post(
            base + "/report",
            headers=headers,
            json={"status": "working", "revision": claim["revision"]},
        ).json()["revision"]
        draft = self.guest.post(
            base + "/draft",
            headers=headers,
            json={
                "html": fixtures.HTML.replace("Cifra de ejemplo", "Cifra revisada"),
                "session": "actual-test-session",
            },
        )
        self.assertEqual(draft.status_code, 200, draft.text)
        vid = draft.json()["version"]
        report = {
            "status": "proposed",
            "revision": revision,
            "version": vid,
            "threads": [],
        }
        self.assertEqual(
            self.guest.post(base + "/report", headers=headers, json=report).status_code,
            422,
        )
        report["threads"] = [
            {
                "id": "test-event-1",
                "status": "addressed",
                "explanation": "Corrected the cited text.",
            }
        ]
        self.assertEqual(
            self.guest.post(base + "/report", headers=headers, json=report).status_code,
            200,
        )
        self.assertEqual(
            self.owner.get(self.path).json()["current_version"], self.a["version"]
        )
        comparison = self.owner.get("/api/creator/jobs/" + key + "/comparison")
        self.assertEqual(comparison.status_code, 200, comparison.text)
        self.assertTrue(comparison.json()["changes"])
        job = self.owner.get("/api/creator/jobs/" + key).json()
        self.assertEqual(
            self.owner.post(
                "/api/creator/jobs/" + key + "/state",
                json={"status": "accepted", "revision": job["revision"]},
            ).status_code,
            200,
        )
        self.assertEqual(
            self.owner.get(self.path).json()["current_version"], self.a["version"]
        )
        self.assertFalse(
            self.owner.get(self.path + "/review")
            .json()["snapshot"]["events"][0]
            .get("resolved", False)
        )
        self.assertEqual(
            self.guest.post(
                base + "/draft", headers=headers, json={"html": fixtures.HTML}
            ).status_code,
            404,
        )

    def test_decision_history_and_published_change(self):
        body = {
            "title": "Keep choice",
            "state": "accepted",
            "evidence": [{"artifact": self.a["id"]}],
        }
        key = self.owner.post("/api/creator/decisions", json=body).json()["id"]
        self.owner.post(
            "/api/creator/decisions",
            json={**body, "id": key, "outcome": "Observed later"},
        )
        self.assertEqual(
            len(
                self.owner.get("/api/creator/decisions/" + key + "/history").json()[
                    "items"
                ]
            ),
            2,
        )
        self.assertEqual(
            self.other.get("/api/creator/decisions/" + key + "/history").status_code,
            404,
        )
        self.owner.post(
            self.path + "/versions",
            json={
                "title": "Updated",
                "html": fixtures.HTML.replace("Cifra de ejemplo", "Updated"),
                "mode": "published",
            },
        )
        self.assertTrue(
            self.owner.get("/api/creator").json()["decisions"][0]["needs_review"]
        )
