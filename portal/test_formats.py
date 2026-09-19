import base64
import unittest
from portal import test_app as fixtures
from portal.formats import describe


class FormatTests(unittest.TestCase):
    setUp = fixtures.PortalTests.setUp
    tearDown = fixtures.PortalTests.tearDown
    client = fixtures.PortalTests.client

    def test_original_access_and_version_identity(self):
        html = (
            fixtures.HTML
            + '<a href="original.pdf" data-margen-original="original.pdf">Original</a>'
        )

        def publish(data):
            return self.owner.post(
                self.path + "/versions",
                json={
                    "html": html,
                    "title": "PDF",
                    "attachments": [
                        {
                            "name": "original.pdf",
                            "data": base64.b64encode(data).decode(),
                        }
                    ],
                },
            )

        first = publish(b"%PDF-1.7\nfixture one")
        self.assertEqual(first.status_code, 200, first.text)
        second = publish(b"%PDF-1.7\nfixture two")
        self.assertNotEqual(first.json()["version"], second.json()["version"])
        url = self.path + "/attachments/" + second.json()["version"] + "/original.pdf"
        self.assertEqual(self.owner.get(url).content, b"%PDF-1.7\nfixture two")
        self.assertEqual(self.other.get(url).status_code, 404)
        self.assertIn(url, self.owner.get(self.path + "/render").text)
        self.assertEqual(publish(b"not a pdf").status_code, 422)

    def test_independent_format_contract(self):
        self.assertEqual(
            describe('<section class="slide"></section>' * 2)["kind"], "presentation"
        )
        self.assertEqual(
            describe('<meta name="margen-format" content="chapters">')["navigation"],
            "chapters",
        )
        self.assertEqual(
            describe('<meta name="margen-format" content="pdf">')["editable_original"],
            False,
        )
        r = self.owner.post(
            self.path + "/versions",
            json={
                "html": fixtures.HTML,
                "title": "No",
                "attachments": [
                    {"name": "bad.PDF", "data": base64.b64encode(b"not pdf").decode()}
                ],
            },
        )
        self.assertEqual(r.status_code, 422)
