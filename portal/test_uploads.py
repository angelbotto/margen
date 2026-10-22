import base64
import io
import re
import stat
import sys
import tempfile
import time
import unittest
import warnings
import zipfile
from pathlib import Path
from unittest import mock
from fastapi import HTTPException
from fastapi.testclient import TestClient
from portal import test_app as fixtures
from portal import uploads
from portal.uploads import poppler

PLAIN = '<!doctype html><html><head><title>Sitio propio</title><style>body{font-family:"Comic Sans MS";color:#c0ffee}</style></head><body><h1 class="x">Hola</h1><script>document.body.dataset.ok=1</script></body></html>'
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")


def pdf(pages=1):
    objects = ["<</Type/Catalog/Pages 2 0 R>>",
               "<</Type/Pages/Kids[" + " ".join(str(3 + 2 * i) + " 0 R" for i in range(pages)) + "]/Count " + str(pages) + ">>"]
    for i in range(pages):
        stream = "BT /F1 24 Tf 72 720 Td (Pagina " + str(i + 1) + ") Tj ET"
        objects.append("<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Resources<</Font<</F1 " + str(3 + 2 * pages) + " 0 R>>>>/Contents " + str(4 + 2 * i) + " 0 R>>")
        objects.append("<</Length " + str(len(stream)) + ">>stream\n" + stream + "\nendstream")
    objects.append("<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>")
    out, offsets = "%PDF-1.4\n", []
    for i, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += str(i) + " 0 obj\n" + body + "\nendobj\n"
    xref = len(out)
    out += "xref\n0 " + str(len(objects) + 1) + "\n0000000000 65535 f \n" + "".join("%010d 00000 n \n" % o for o in offsets)
    return (out + "trailer\n<</Size " + str(len(objects) + 1) + "/Root 1 0 R>>\nstartxref\n" + str(xref) + "\n%%EOF\n").encode()


def archive(entries, raw=None):
    buffer = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
            for name, data in entries:
                z.writestr(name, data)
            for info, data in raw or []:
                z.writestr(info, data)
    return buffer.getvalue()


def b64(data):
    return base64.b64encode(data if isinstance(data, bytes) else data.encode()).decode()


SITE = [
    ("site/index.html", '<!doctype html><html><head><title>Estático</title><link rel="stylesheet" href="css/main.css"><link rel="icon" href="img/logo.png">'
     '<script src="./js/app.js"></script></head><body><img src="img/logo.png" srcset="img/logo.png 1x, img/logo.png 2x" alt="Logo">'
     '<a href="#top">Arriba</a><a href="https://example.com/">Fuera</a><div style="background:url(img/logo.png)"></div></body></html>'),
    ("site/css/main.css", '@import "base.css"; h1{background:url("../img/logo.png")} @font-face{font-family:X;src:url(../fonts/x.woff2)}'),
    ("site/css/base.css", "body{margin:0}"),
    ("site/js/app.js", 'document.documentElement.dataset.site="</script>"'),
    ("site/img/logo.png", PNG),
    ("site/fonts/x.woff2", b"wOF2fixture"),
]


class UploadTests(unittest.TestCase):
    setUp = fixtures.PortalTests.setUp
    tearDown = fixtures.PortalTests.tearDown
    client = fixtures.PortalTests.client

    def inspect(self, name, data, client=None, **extra):
        return (client or self.owner).post("/api/uploads/inspect", json={"name": name, "data": b64(data), **extra})

    def upload(self, name, data, client=None, **extra):
        return (client or self.owner).post("/api/uploads", json={"name": name, "data": b64(data), **extra})

    def stored(self, version):
        with self.store.db() as db:
            sha = db.execute("SELECT sha FROM versions WHERE id=?", (version,)).fetchone()["sha"]
        return (self.store.files / (sha + ".html")).read_text()

    def test_plain_html_is_preserved_private_and_revised_with_same_id(self):
        report = self.inspect("propio.html", PLAIN)
        self.assertEqual(report.status_code, 200, report.text)
        body = report.json()
        self.assertEqual((body["kind"], body["title"], body["document_id"]), ("html", "Sitio propio", None))
        with self.store.db() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM versions").fetchone()[0], 1)  # inspect no persiste
        first = self.upload("propio.html", PLAIN, space="Equipo")
        self.assertEqual(first.status_code, 200, first.text)
        created = first.json()
        self.assertEqual(created["visibility"], "private")
        stored = self.stored(created["version"])
        docid = stored.split('content="', 1)[1].split('"', 1)[0]
        self.assertTrue(docid.startswith("upload-"))
        self.assertEqual(stored.replace('<meta name="nota-documento" content="' + docid + '">', ""), PLAIN)
        path = "/api/artifacts/" + created["id"]
        meta = self.owner.get(path).json()
        self.assertEqual((meta["title"], meta["space"]), ("Sitio propio", "Equipo"))
        rendered = self.owner.get(path + "/render")
        self.assertIn('body{font-family:"Comic Sans MS";color:#c0ffee}', rendered.text)
        self.assertIn("document.body.dataset.ok=1", rendered.text)
        self.assertIn("sandbox allow-scripts", rendered.headers["content-security-policy"])
        self.assertIn("connect-src 'none'", rendered.headers["content-security-policy"])
        for client in (self.other, self.guest):
            self.assertEqual(client.get(path + "/render").status_code, 404)
        revised = PLAIN.replace("Hola", "Hola otra vez")
        stale = self.upload("propio.html", revised, artifact=created["id"], expected_current="0" * 32)
        self.assertEqual(stale.status_code, 409)
        second = self.upload("propio.html", revised, artifact=created["id"], expected_current=created["version"])
        self.assertEqual(second.status_code, 200, second.text)
        self.assertEqual(second.json()["id"], created["id"])
        self.assertNotEqual(second.json()["version"], created["version"])
        self.assertIn('content="' + docid + '"', self.stored(second.json()["version"]))
        self.assertEqual(len(self.owner.get(path).json()["versions"]), 2)
        original = [{"name": "original.pptx", "data": b64(b"not a pptx")}]
        self.assertEqual(self.upload("propio.html", PLAIN, artifact=created["id"], expected_current=second.json()["version"], attachments=original).status_code, 422)
        original = [{"name": "original.pdf", "data": b64(b"%PDF-1.4 original")}]
        third = self.upload("propio.html", PLAIN + "<p>3</p>", artifact=created["id"], expected_current=second.json()["version"], attachments=original).json()
        self.assertEqual(self.owner.get(path + "/attachments/" + third["version"] + "/original.pdf").content, b"%PDF-1.4 original")
        self.assertEqual(self.other.get(path + "/attachments/" + third["version"] + "/original.pdf").status_code, 404)

    def test_unauthorized_uploads_and_revisions_are_rejected(self):
        self.assertEqual(self.inspect("a.html", PLAIN, client=self.guest).status_code, 401)
        self.assertEqual(self.upload("a.html", PLAIN, client=self.guest).status_code, 401)
        cross = TestClient(self.app, base_url=fixtures.ORIGIN, headers={"Origin": "https://evil.test"})
        cross.cookies = self.owner.cookies
        self.assertEqual(cross.post("/api/uploads", json={"name": "a.html", "data": b64(PLAIN)}).status_code, 403)
        mine = self.upload("a.html", PLAIN).json()
        self.assertEqual(self.upload("a.html", PLAIN, client=self.other, artifact=mine["id"]).status_code, 404)
        self.assertEqual(self.upload("a.html", PLAIN, artifact="../../etc").status_code, 404)
        self.assertEqual(self.upload("a.html", PLAIN, visibility="public").status_code, 422)
        foreign = PLAIN.replace("<head>", '<head><meta name="nota-documento" content="otro-documento">')
        self.assertEqual(self.upload("a.html", foreign, artifact=mine["id"]).status_code, 409)
        self.assertEqual(self.other.get("/api/artifacts/" + mine["id"]).status_code, 404)

    def test_static_zip_inlines_local_assets_without_remote_fetch(self):
        data = archive(SITE)
        report = self.inspect("sitio.zip", data)
        self.assertEqual(report.status_code, 200, report.text)
        body = report.json()
        self.assertEqual((body["kind"], body["entry"], body["title"]), ("zip", "index.html", "Estático"))
        roles = {f["path"]: f["role"] for f in body["files"]}
        self.assertEqual(roles["index.html"], "entry")
        self.assertEqual(roles["css/base.css"], "asset")
        self.assertTrue(any("remotos" in w for w in body["warnings"]))
        created = self.upload("sitio.zip", data).json()
        stored = self.stored(created["version"])
        self.assertNotIn('href="css/main.css"', stored)
        self.assertNotIn('src="./js/app.js"', stored)
        self.assertIn("body{margin:0}", stored)
        self.assertIn("data:image/png;base64,", stored)
        self.assertIn("data:font/woff2;base64,", stored)
        self.assertIn('dataset.site="<\\/script>"', stored)
        self.assertIn('href="https://example.com/"', stored)
        self.assertIn('<a href="#top">', stored)
        self.assertEqual(stored.count("data:image/png"), 6)
        revised = archive([(n, d.replace("Estático", "Estático 2") if n.endswith(".html") else d) for n, d in SITE])
        again = self.upload("sitio.zip", revised, artifact=created["id"], expected_current=created["version"])
        self.assertEqual(again.json()["id"], created["id"])

    def test_multipage_zip_requires_single_entry_page(self):
        pages = [("index.html", '<a href="about.html">Sobre</a>'), ("about.html", "<h1>Sobre</h1>")]
        linked = self.upload("multi.zip", archive(pages))
        self.assertEqual(linked.status_code, 422)
        self.assertIn("about.html", linked.json()["detail"])
        no_index = archive([("a.html", "<h1>A</h1>"), ("b.html", "<h1>B</h1>")])
        self.assertIn("página de entrada", self.inspect("x.zip", no_index).json()["detail"])
        chosen = self.inspect("x.zip", no_index, entry="b.html").json()
        self.assertEqual(chosen["entry"], "b.html")
        self.assertTrue(any("a.html" in w for w in chosen["warnings"]))
        self.assertEqual(self.upload("x.zip", no_index, entry="b.html").status_code, 200)
        self.assertEqual(self.inspect("x.zip", no_index, entry="../b.html").status_code, 422)

    def test_invalid_archives_are_rejected(self):
        index = ("index.html", "<h1>Hola</h1>")
        link = zipfile.ZipInfo("logo.png")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        plain = archive([index, ("secret.css", "x")])
        central = plain.rindex(b"PK\x01\x02")  # zipfile no escribe cifrado: se marca el bit 0 a mano
        encrypted = plain[:central + 8] + bytes([plain[central + 8] | 1]) + plain[central + 9:]
        cases = {
            "traversal": archive([index, ("../escape.css", "x")]),
            "absolute": archive([index, ("/etc/passwd.txt", "x")]),
            "backslash": archive([index, ("css\\..\\x.css", "x")]),
            "drive": archive([index, ("C:/x.css", "x")]),
            "symlink": archive([index], [(link, "/etc/passwd")]),
            "encrypted": encrypted,
            "duplicate": archive([index, ("index.html", "<h1>Otra</h1>")]),
            "case duplicate": archive([index, ("a.css", "x"), ("A.css", "y")]),
            "server code": archive([index, ("api.php", "<?php system($_GET['c']);")]),
            "build file": archive([index, ("package.json", "{}")]),
            "dotfile": archive([index, (".env.json", "{}")]),
            "nested archive": archive([index, ("inner.zip", archive([index]))]),
            "bomb": archive([index, ("big.txt", b"0" * (6 * 1024 * 1024))]),
            "too many": archive([index] + [("f%d.txt" % i, "x") for i in range(400)]),
            "no html": archive([("a.css", "x")]),
            "truncated": archive([index])[:-30],
        }
        for label, data in cases.items():
            with self.subTest(label):
                response = self.inspect("sitio.zip", data)
                self.assertEqual(response.status_code, 422, response.text)
                self.assertEqual(self.upload("sitio.zip", data).status_code, 422)
        self.assertEqual(self.inspect("sitio.zip", b"not a zip").status_code, 422)
        self.assertEqual(self.inspect("sitio.exe", b"MZ").status_code, 422)
        self.assertEqual(self.inspect("a.html", b"\xff\xfe<h1>").status_code, 422)
        self.assertEqual(self.owner.post("/api/uploads/inspect", json={"name": "a.html", "data": "@@"}).status_code, 422)
        self.assertEqual(self.owner.post("/api/uploads/inspect", json={"name": "../a.html", "data": b64(PLAIN)}).status_code, 422)
        with self.store.db() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM artifacts").fetchone()[0], 1)

    def test_pdf_rejections(self):
        self.assertEqual(self.inspect("x.pdf", b"<html>").status_code, 422)
        self.assertEqual(self.upload("x.pdf", b"%PDF-1.4 roto").status_code, 422)
        self.assertEqual(self.upload("x.pdf", b"%PDF-" + b"0" * (12 * 1024 * 1024)).status_code, 422)

    @unittest.skipUnless(poppler(), "Poppler no está instalado")
    def test_pdf_visual_preview_keeps_original_with_version_acl(self):
        report = self.inspect("informe.pdf", pdf(2)).json()
        self.assertEqual((report["kind"], report["pages"], report["preview"]), ("pdf", 2, "visual"))
        created = self.upload("informe.pdf", pdf(2), title="Informe PDF")
        self.assertEqual(created.status_code, 200, created.text)
        created = created.json()
        path = "/api/artifacts/" + created["id"]
        rendered = self.owner.get(path + "/render").text
        self.assertEqual(rendered.count("data:image/jpeg;base64,"), 2)
        self.assertIn("Pagina 2", rendered)
        with self.store.db() as db:
            self.assertIn('"kind": "pdf"', db.execute("SELECT capabilities FROM version_formats WHERE version=?", (created["version"],)).fetchone()[0])
        original = path + "/attachments/" + created["version"] + "/original.pdf"
        self.assertEqual(self.owner.get(original).content, pdf(2))
        self.assertEqual(self.other.get(original).status_code, 404)
        self.assertEqual(self.guest.get(original).status_code, 404)
        html = self.upload("nuevo.html", PLAIN, artifact=created["id"], expected_current=created["version"]).json()
        self.assertEqual(html["id"], created["id"])
        self.assertEqual(self.owner.get(path + "/attachments/" + html["version"] + "/original.pdf").status_code, 404)
        self.assertEqual(self.upload("largo.pdf", pdf(81)).status_code, 422)
        self.assertEqual(self.upload("informe.pdf", pdf(1), attachments=[]).status_code, 422)


class StructureTests(unittest.TestCase):
    def rejected(self, call, *args):
        with self.assertRaises(HTTPException) as caught:
            call(*args)
        self.assertEqual(caught.exception.status_code, 422)
        return caught.exception.detail

    def site(self, markup, *extra):
        return archive([("index.html", "<html><head><title>T</title></head><body>" + markup + "</body></html>"), *extra])

    def test_directory_embedded_and_redirect_navigation_is_rejected(self):
        about = ("about/index.html", "<h1>About</h1>")
        for markup in ('<a href="about/">x</a>', '<a href="/about/">x</a>', '<a href="about">x</a>', '<a href="contact">x</a>',
                       '<iframe src="about/index.html"></iframe>', '<frame src="about/">', '<object data="about/"></object>',
                       '<embed src="about/index.html">', '<meta http-equiv="refresh" content="0; URL=\'about/\'">',
                       '<form action="about/"></form>', '<button formaction="/contact.html">x</button>',
                       '<link rel="next" href="about/">', '<svg><a xlink:href="about/">x</a></svg>'):
            with self.subTest(markup=markup):
                detail = self.rejected(uploads.zip_site, "s.zip", self.site(markup, about, ("contact.html", "<h1>C</h1>")), None)
                self.assertRegex(detail, r"about/index\.html|contact\.html")

    def test_links_to_self_assets_and_missing_pages_still_publish(self):
        site = uploads.zip_site("s.zip", self.site('<a href="/">Inicio</a><a href="./">Inicio</a><a href="index.html#x">x</a>'
                                                   '<a href="docs/">faltante</a><a href="notes.txt">Notas</a><form action="/api"></form>',
                                                   ("notes.txt", b"hola")), None)
        self.assertIn('href="data:text/plain;base64,aG9sYQ=="', site["content"])
        self.assertTrue(any("docs/" in w for w in site["warnings"]))

    def test_base_href_that_changes_resolution_is_rejected(self):
        self.assertIn("base href", self.rejected(uploads.zip_site, "s.zip", self.site('<base href="https://cdn.example/">'), None))
        self.assertIn("base href", self.rejected(uploads.zip_site, "s.zip", self.site('<base href="sub/">'), None))
        self.assertEqual(uploads.zip_site("s.zip", self.site('<base href="./" target="_blank">'), None)["entry"], "index.html")

    def test_inlined_script_cannot_swallow_the_page_and_drops_fallback_body(self):
        raw = archive([("index.html", '<script src="a.js">fallback()</script><p id="after">after</p>'),
                       ("a.js", "var s='<!--<script>'; var e='</SCRIPT>'")])
        content = uploads.zip_site("s.zip", raw, None)["content"]
        script = content.split("<script>", 1)[1].split("</script>", 1)[0]
        self.assertEqual(script, "var s='<\\!--<script>'; var e='<\\/SCRIPT>'")
        self.assertNotIn("fallback", content)
        self.assertIn('<p id="after">after</p>', content)

    def test_identity_and_title_come_from_parsed_head_only(self):
        html = ('<!-- <head><meta name="nota-documento" content="comentario"> --><html><head data-x="1">'
                '<script>const a = "<title>falso</title><meta name=\\"nota-documento\\" content=\\"script\\">"</script>'
                '<template><title>plantilla</title><meta name="nota-documento" content="plantilla"></template>'
                '<title>Real</title></head><body><h1>H</h1></body></html>')
        self.assertEqual(uploads.metadata(html)["title"], "Real")
        self.assertIsNone(uploads.declared_id(html))
        # A textual copy before the real <head> would win in publish(): refuse instead of publishing another identity.
        self.assertIn("comentario o script", self.rejected(uploads.with_document_id, html, "upload-x"))
        clean = html.split("-->", 1)[1]
        out = uploads.with_document_id(clean, "upload-x")
        self.assertIn('<head data-x="1"><meta name="nota-documento" content="upload-x">', out)
        self.assertEqual(uploads.DOCUMENT_ID.search(out)[1], "upload-x")
        # The template copy precedes the declared meta, so publish() would read "plantilla".
        late = clean.replace("<title>Real", '<meta name="nota-documento" content="propio"><title>Real')
        self.assertIn("comentario o script", self.rejected(uploads.with_document_id, late, "upload-x"))
        declared = clean.replace('<head data-x="1">', '<head data-x="1"><meta name="nota-documento" content="propio">')
        self.assertEqual(uploads.with_document_id(declared, "upload-x"), declared)
        report = uploads.inspect("a.html", declared.encode(), None)
        self.assertEqual((report["document_id"], report["title"]), ("propio", "Real"))
        self.assertEqual(uploads.title_of("<p>sin título</p><h1>Encabezado</h1>", "f"), "Encabezado")

    def test_metadata_stops_at_body_and_handles_unclosed_markup_quickly(self):
        for content in ("<title>" * 200000, "<head " * 200000, "<html><head><title>T</title></head><body>" + "<p>x</p>" * 2000000,
                        "<!--" + "x" * 5000000):
            started = time.monotonic()
            uploads.with_document_id(content, "upload-x")
            self.assertLess(time.monotonic() - started, 1.5, content[:20])

    def test_upload_ui_body_limit_matches_portal(self):
        from portal.app import MAX_BODY
        js = (Path(__file__).parent / "static/upload.js").read_text()
        self.assertEqual(eval(re.search(r"MAX_BODY = (\d+) \* MiB", js)[1]) * 1024 * 1024, MAX_BODY)


class PdfLimitTests(unittest.TestCase):
    def run_tool(self, script, seconds=5):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(HTTPException) as caught:
                uploads.bounded_run(["/bin/sh", "-c", script], folder, time.monotonic() + seconds)
        return caught.exception.detail

    def test_limit_failures_are_reported_as_too_heavy_not_damaged(self):
        self.assertEqual(self.run_tool("kill -XCPU $$"), uploads.PDF_HEAVY)
        self.assertEqual(self.run_tool("kill -ABRT $$"), uploads.PDF_HEAVY)
        self.assertEqual(self.run_tool("echo 'Out of memory' >&2; exit 99"), uploads.PDF_HEAVY)
        self.assertEqual(self.run_tool("echo 'MemoryError' >&2; exit 1"), uploads.PDF_HEAVY)
        self.assertIn("dañado o protegido", self.run_tool("exit 1"))
        started = time.monotonic()
        self.assertEqual(self.run_tool("sleep 5", 0.5), uploads.PDF_SLOW)
        self.assertLess(time.monotonic() - started, 2)

    def test_child_limits_fit_the_production_container(self):
        captured = []
        real = uploads.subprocess.Popen
        def spy(argv, **kwargs):
            captured.append(argv[2])
            return real(["/bin/sh", "-c", "exit 0"], **kwargs)
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(uploads.subprocess, "Popen", spy):
            uploads.bounded_run(["true"], folder, time.monotonic() + 20)
        self.assertIn("ulimit -v " + str(384 * 1024), captured[0])
        self.assertRegex(captured[0], r"ulimit -t (20|21);")
        self.assertLessEqual(uploads.PDF_CHILD_MEMORY, 384 * 1024 * 1024)

    @unittest.skipUnless(sys.platform.startswith("linux"), "macOS ignora ulimit -v")
    def test_child_needing_900_mib_fails_safely(self):
        # Stand-in for a Poppler child: the production cap stops it before the 768 MiB container OOM killer.
        self.assertEqual(self.run_tool(sys.executable + " -c \"b = b'x' * (900 << 20)\"", 30), uploads.PDF_HEAVY)

    @unittest.skipUnless(poppler(), "Poppler no está instalado")
    def test_one_deadline_covers_metadata_and_pages(self):
        with mock.patch.object(uploads, "PDF_TIMEOUT", 0):
            with self.assertRaises(HTTPException) as caught:
                uploads.build("x.pdf", pdf(1), None, "upload-x", "t")
        self.assertEqual(caught.exception.detail, uploads.PDF_SLOW)
        self.assertEqual(uploads.PDF_SLOTS._value, 1)


if __name__ == "__main__":
    unittest.main()
