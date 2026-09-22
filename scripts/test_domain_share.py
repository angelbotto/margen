"""The portable sharing command preserves personal grants and explicit scope."""

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import publish


class ShareTests(unittest.TestCase):
    def run_share(self, *args, supported=True):
        current = {
            "permissions": {"manage": True},
            "visibility": "private",
            "comments": "reviewers",
            "guests": False,
            "grants": [{"email": "person@example.com", "role": "editor"}],
            "domain_grants": [{"domain": "existing.example", "role": "viewer"}],
        }
        if not supported:
            current.pop("domain_grants")
        calls = []

        def request(base, token, path, data=None, method=None):
            if path == "/api/session":
                return {"user": {"id": "owner", "email": "owner@example.com", "verified": True}}
            if data is not None:
                calls.append(copy.deepcopy(data))
                current.update(data)
                if current["visibility"] == "private":
                    current.update(grants=[], domain_grants=[])
                return {"ok": True}
            return copy.deepcopy(current)

        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / "portal.json"
            config.write_text(
                json.dumps(
                    {"server": "https://portal.example", "token": "fixture-only", "account": {"id": "owner", "email": "owner@example.com"}}
                )
            )
            config.chmod(0o600)
            argv = [
                "publish.py",
                "--config",
                str(config),
                "share",
                "--artifact-id",
                "a" * 32,
                *args,
            ]
            with patch("sys.argv", argv), patch.object(
                publish, "request", side_effect=request
            ), patch("sys.stdout", new_callable=io.StringIO):
                publish.main()
        return calls

    def test_additive_share_normalizes_and_preserves_personal_grants(self):
        [body] = self.run_share("--domain", "@TIKIN.IS", "--role", "commenter")
        self.assertEqual(body["visibility"], "invited")
        self.assertEqual(
            body["grants"], [{"email": "person@example.com", "role": "editor"}]
        )
        self.assertEqual(
            body["domain_grants"],
            [
                {"domain": "existing.example", "role": "viewer"},
                {"domain": "tikin.is", "role": "commenter"},
            ],
        )

    def test_removal_and_invalid_requests(self):
        [body] = self.run_share("--remove-domain", "existing.example")
        self.assertEqual(body["domain_grants"], [])
        for args in [
            ("--domain", "*.example.com"),
            ("--domain", "tikin.is", "--visibility", "private"),
            ("--domain", "tikin.is", "--remove-domain", "tikin.is"),
        ]:
            with self.subTest(args=args), self.assertRaises(SystemExit):
                self.run_share(*args)
        with self.assertRaises(SystemExit):
            self.run_share("--domain", "tikin.is", supported=False)


if __name__ == "__main__":
    unittest.main()
