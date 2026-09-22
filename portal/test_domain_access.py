"""Domain audiences must agree across direct access, queries, review and citations."""

import unittest
from portal import test_app as fixtures

HTML = fixtures.HTML
from portal.domain_access import normalize_domain, verified_domain


class DomainAccessTests(unittest.TestCase):
    setUp = fixtures.PortalTests.setUp
    tearDown = fixtures.PortalTests.tearDown
    client = fixtures.PortalTests.client
    event = fixtures.PortalTests.event

    def share(self, domains=None, **fields):
        return self.owner.put(
            self.path + "/access",
            json={
                "visibility": "invited",
                "grants": [],
                "comments": "reviewers",
                "domain_grants": (
                    domains
                    if domains is not None
                    else [{"domain": "@TIKIN.IS", "role": "commenter"}]
                ),
                **fields,
            },
        )

    def test_exact_verified_domain_and_revocation(self):
        self.assertEqual(self.share().status_code, 200)
        member = self.client("member@tikin.is", "Member")
        detail = member.get(self.path).json()
        self.assertTrue(detail["permissions"]["comment"])
        self.assertFalse(detail["permissions"]["edit"])
        self.assertFalse(detail["permissions"]["manage"])
        self.assertEqual(detail["domain_grants"], [])
        self.assertEqual(detail["grants"], [])
        for email in [
            "outsider@eviltikin.is",
            "sub@team.tikin.is",
            "suffix@tikin.is.evil.com",
            "other@liftit.co",
        ]:
            with self.subTest(email=email):
                outsider = self.client(email, "Outside")
                self.assertEqual(outsider.get(self.path).status_code, 404)
                self.assertEqual(
                    outsider.get("/api/artifacts?view=shared").json()["total"], 0
                )
        with self.store.db() as db:
            db.execute("UPDATE users SET verified=0 WHERE email='member@tikin.is'")
        self.assertEqual(member.get(self.path).status_code, 404)
        with self.store.db() as db:
            db.execute("UPDATE users SET verified=1 WHERE email='member@tikin.is'")
        self.assertEqual(
            member.get(self.path + "/render?version=" + self.a["version"]).status_code,
            200,
        )
        self.assertEqual(
            member.post(self.path + "/review", json=self.event()).status_code, 200
        )
        self.assertEqual(self.share([]).status_code, 200)
        self.assertEqual(member.get(self.path).status_code, 404)
        self.assertEqual(
            member.get(self.path + "/render?version=" + self.a["version"]).status_code,
            404,
        )
        self.assertEqual(member.get("/api/artifacts?view=shared").json()["total"], 0)

    def test_queries_context_and_explicit_role_precedence(self):
        self.share()
        member = self.client("member@tikin.is", "Member")
        for url in [
            "/api/artifacts?view=shared",
            "/api/artifacts?q=Cifra",
            "/api/artifacts?graph=1",
        ]:
            response = member.get(url)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertIn(self.a["id"], response.text)
        # Exercise the legacy bookmark path as well as the SQL-first library.
        member.post(
            "/api/bookmarks",
            json={"title": "Reference", "url": "https://example.org", "space": "Team"},
        )
        self.assertIn(self.a["id"], member.get("/api/artifacts?view=shared").text)
        target = self.owner.post(
            "/api/artifacts",
            json={
                "title": "Target",
                "html": HTML.replace("informe-prueba", "target-document"),
            },
        ).json()
        self.owner.post(
            "/api/context/links",
            json={
                "source": self.a["id"],
                "target": target["id"],
                "kind": "cites",
                "quote": "Cifra de ejemplo",
            },
        )
        self.assertEqual(
            member.get("/api/context/links?artifact=" + self.a["id"]).json()["items"],
            [],
        )
        self.owner.put(
            "/api/artifacts/" + target["id"] + "/access",
            json={
                "visibility": "invited",
                "domain_grants": [{"domain": "tikin.is", "role": "viewer"}],
            },
        )
        self.assertEqual(
            len(
                member.get("/api/context/links?artifact=" + self.a["id"]).json()[
                    "items"
                ]
            ),
            1,
        )
        self.share(grants=[{"email": "member@tikin.is", "role": "viewer"}])
        p = member.get(self.path).json()["permissions"]
        self.assertEqual(p["role"], "viewer")
        self.assertFalse(p["comment"])
        listed = member.get("/api/artifacts?view=shared").json()["artifacts"]
        self.assertFalse(
            next(a for a in listed if a["id"] == self.a["id"])["permissions"]["comment"]
        )
        self.share(grants=[{"email": "member@tikin.is", "role": "editor"}])
        self.assertTrue(member.get(self.path).json()["permissions"]["edit"])

    def test_domain_does_not_expose_drafts_or_private_notes(self):
        self.share()
        member = self.client("member@tikin.is", "Member")
        self.owner.post(
            self.path + "/review",
            json=self.event(
                id="private-note", entry_type="note", text="Private thought"
            ),
        )
        self.assertNotIn("Private thought", member.get(self.path + "/review").text)
        draft = self.owner.post(
            self.path + "/versions",
            json={"title": "Draft", "html": HTML, "mode": "draft"},
        ).json()
        self.assertNotIn(draft["version"], member.get(self.path).text)
        self.assertEqual(
            member.get(self.path + "/render?version=" + draft["version"]).status_code,
            404,
        )
        self.assertEqual(
            member.put(
                self.path + "/access", json={"visibility": "public"}
            ).status_code,
            404,
        )
        self.assertEqual(
            member.post(
                self.path + "/versions", json={"title": "Changed", "html": HTML}
            ).status_code,
            404,
        )

    def test_validation_is_atomic_and_private_clears_all_grants(self):
        self.share()
        for domains in [
            [{"domain": d, "role": "commenter"}]
            for d in [
                "*.tikin.is",
                "https://tikin.is",
                "tikin.is/path",
                "tikin.is evil.com",
                "@",
                "user@tikin.is",
                "127.0.0.1",
                "tíkin.is",
            ]
        ] + [
            [{"domain": "tikin.is", "role": "editor"}],
            None,
            "tikin.is",
            [None],
            [{"domain": "tikin.is", "role": "viewer"}] * 26,
        ]:
            response = self.owner.put(
                self.path + "/access",
                json={"visibility": "invited", "domain_grants": domains},
            )
            self.assertEqual(response.status_code, 422, str(domains))
            self.assertEqual(
                self.owner.get(self.path).json()["domain_grants"],
                [{"domain": "tikin.is", "role": "commenter"}],
            )
        # Omission by an old client preserves domains; an explicit empty list revokes them.
        self.owner.put(
            self.path + "/access",
            json={
                "visibility": "invited",
                "grants": [{"email": "other@example.com", "role": "editor"}],
            },
        )
        self.assertEqual(len(self.owner.get(self.path).json()["domain_grants"]), 1)
        self.owner.put(self.path + "/access", json={"visibility": "private"})
        detail = self.owner.get(self.path).json()
        self.assertEqual(detail["domain_grants"], [])
        self.assertEqual(detail["grants"], [])

    def test_multiple_domains_and_new_members(self):
        self.share(
            [
                {"domain": "tikin.is", "role": "commenter"},
                {"domain": "liftit.co", "role": "viewer"},
            ]
        )
        for domain, comment in [("tikin.is", True), ("liftit.co", False)]:
            person = self.client("new@" + domain, "New member")
            detail = person.get(self.path).json()
            self.assertEqual(detail["permissions"]["comment"], comment)
            self.assertEqual(
                person.get("/api/artifacts?view=shared").json()["total"], 1
            )
        self.assertEqual(
            verified_domain({"email": "x@tikin.is", "verified": False}), ""
        )
        self.assertEqual(normalize_domain(" @TIKIN.IS "), "tikin.is")

    def test_stale_manager_save_cannot_restore_a_revoked_domain(self):
        self.share()
        old = self.owner.get(self.path).json()["access_revision"]
        self.share([])
        result = self.owner.put(
            self.path + "/access",
            json={
                "visibility": "invited",
                "expected_access": old,
                "domain_grants": [{"domain": "tikin.is", "role": "commenter"}],
            },
        )
        self.assertEqual(result.status_code, 409)
        self.assertEqual(self.owner.get(self.path).json()["domain_grants"], [])
