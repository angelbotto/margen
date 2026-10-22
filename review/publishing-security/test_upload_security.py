#!/usr/bin/env python3
"""Expected-behaviour tests for REVIEW-UPLOADS.md. Tests tagged [defect] fail on 508ab5a until fixed.

  MARGEN_ROOT=<tree> python review/publishing-security/test_upload_security.py
Every adversarial input runs in a child process with a wall timeout (and RLIMIT_AS where the OS honours it),
so an unfixed tree fails the test instead of exhausting the machine. HTTP tests need httpx (portal dev deps).
"""
import base64, io, json, os, subprocess, sys, textwrap, unittest, zipfile
from pathlib import Path

ROOT = Path(os.environ.get("MARGEN_ROOT") or Path(__file__).resolve().parents[2])
sys.path.insert(0, str(ROOT))
from portal import uploads  # noqa: E402

MiB = 1024 * 1024


def archive(entries):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in entries:
            z.writestr(name, data)
    return buffer.getvalue()


def bounded(call, payload, timeout=20, memory=1536 * MiB):
    """Runs uploads.<call>(*payload) in a child; returns (seconds, peak RSS MiB, outcome) or a timeout marker."""
    script = textwrap.dedent("""
        import pickle, resource, sys, time
        sys.path.insert(0, sys.argv[1])
        try: resource.setrlimit(resource.RLIMIT_AS, (int(sys.argv[2]), int(sys.argv[2])))
        except (ValueError, OSError): pass
        from portal import uploads
        call, args = pickle.loads(sys.stdin.buffer.read())
        started = time.time()
        try:
            getattr(uploads, call)(*args); outcome = "ok"
        except MemoryError: outcome = "MemoryError"
        except Exception as e: outcome = "%s %s" % (getattr(e, "status_code", type(e).__name__), getattr(e, "detail", ""))
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1048576 if sys.platform == "darwin" else 1024)
        print(__import__("json").dumps([time.time() - started, peak, outcome]))
    """)
    import pickle
    try:
        done = subprocess.run([sys.executable, "-I", "-c", script, str(ROOT), str(memory)], input=pickle.dumps((call, payload)),
                              capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return timeout, None, "timeout"
    return tuple(json.loads(done.stdout.decode().strip().splitlines()[-1])) if done.stdout.strip() else (None, None, done.stderr.decode()[-300:])


class ResourceBounds(unittest.TestCase):
    def test_defect_repeated_asset_rejected_before_amplifying_memory(self):
        """[defect] F1: a 64 KB ZIP whose entry references one 64 KB image 250 times."""
        raw = archive([("index.html", "<html>" + '<img src="a.png">' * 250 + "</html>"), ("a.png", os.urandom(64 * 1024))])
        self.assertLess(len(raw), 80 * 1024)
        seconds, peak, outcome = bounded("zip_site", ("s.zip", raw, None))
        self.assertTrue(outcome.startswith("422"), outcome)
        # 508ab5a: macOS 1.4 GB / 1.5 s, production image 126 MB / 0.4 s. A running 20 MB budget stops after ~240 copies.
        self.assertLess(seconds, 0.25, outcome)
        self.assertLess(peak, 100, "peak RSS MiB for a %d-byte upload; output budget must be enforced while inlining" % len(raw))

    def test_defect_css_import_fanout_is_bounded(self):
        """[defect] F1: <1 KB ZIP, each CSS level @imports the next 34 times (depth 4 = 1.3M expansions)."""
        files = [("index.html", '<link rel="stylesheet" href="c0.css">')]
        files += [("c%d.css" % d, ('@import "c%d.css";' % (d + 1)) * 34) for d in range(4)] + [("c4.css", "body{color:red}" * 4)]
        raw = archive(files)
        seconds, peak, outcome = bounded("zip_site", ("s.zip", raw, None))
        self.assertNotEqual(outcome, "timeout")
        self.assertLess(seconds, 2, outcome)
        self.assertLess(peak, 200, outcome)

    def test_defect_title_regex_is_linear(self):
        """[defect] F2: 120 KB of unclosed <title>; re holds the GIL, so this stalls the whole single-worker portal."""
        seconds, _, outcome = bounded("inspect", ("a.html", b"<title>" * 17000, None), timeout=30)
        self.assertLess(seconds, 1, "inspect took %ss (%s)" % (seconds, outcome))

    def test_defect_head_regex_is_linear(self):
        """[defect] F2: 120 KB of '<head ' without '>' in with_document_id (build path)."""
        seconds, _, outcome = bounded("build", ("a.html", b"<head " * 20000, None, "upload-x", "t"), timeout=30)
        self.assertLess(seconds, 1, "build took %ss (%s)" % (seconds, outcome))


class SinglePageContract(unittest.TestCase):
    """[defect] F3: the contract says linked pages are rejected rather than published as broken navigation."""

    def assertRejectsNavigation(self, markup):
        raw = archive([("index.html", "<html><body>" + markup + "</body></html>"), ("about/index.html", "<h1>About</h1>")])
        with self.assertRaises(Exception, msg=markup) as caught:
            uploads.zip_site("s.zip", raw, None)
        self.assertEqual(getattr(caught.exception, "status_code", None), 422)

    def test_defect_directory_links(self):
        for markup in ('<a href="about/">x</a>', '<a href="/about/">x</a>', '<a href="about">x</a>'):
            with self.subTest(markup=markup):
                self.assertRejectsNavigation(markup)

    def test_defect_embedded_and_redirect_pages(self):
        for markup in ('<iframe src="about/index.html"></iframe>', '<meta http-equiv="refresh" content="0;url=about/index.html">',
                       '<form action="about/index.html"></form>', '<object data="about/index.html"></object>'):
            with self.subTest(markup=markup):
                self.assertRejectsNavigation(markup)

    def test_links_that_are_already_rejected(self):
        for markup in ('<a href="about/index.html">x</a>', '<a href="about/index.html?x=1#y">x</a>', '<a href="about%2Findex.html">x</a>'):
            with self.subTest(markup=markup):
                self.assertRejectsNavigation(markup)


class Preservation(unittest.TestCase):
    def test_defect_inlined_script_cannot_swallow_the_page(self):
        """[defect] F5: '<!--' + '<script' inside an inlined file enters script double-escaped state."""
        raw = archive([("index.html", '<script src="a.js"></script><p id="after">after</p>'), ("a.js", "var s='<!--<script>'")])
        content = uploads.zip_site("s.zip", raw, None)["content"]
        script = content.split("<script>", 1)[1].split("</script>", 1)[0]
        self.assertNotIn("<!--", script)

    def test_defect_document_id_is_inserted_in_the_real_head(self):
        """[defect] F6: the meta must not land inside a comment or script before the real <head>."""
        out = uploads.with_document_id("<!-- <head> --><html><head><title>t</title></head></html>", "upload-x")
        self.assertIn('<head><meta name="nota-documento" content="upload-x">', out.split("-->", 1)[1])

    def test_plain_html_bytes_are_kept(self):
        page = '<!DOCTYPE html>\r\n<html><head data-x="1"><title>T</title></head><body onload="x()"><svg><use href="#a"/></svg></body></html>'
        built, attachments, _ = uploads.build("p.html", page.encode(), None, "upload-x", None)
        self.assertEqual(built.replace('<meta name="nota-documento" content="upload-x">', ""), page)
        self.assertEqual(attachments, [])


class ArchiveParser(unittest.TestCase):
    def rejects(self, raw):
        with self.assertRaises(Exception) as caught:
            uploads.read_zip(raw)
        self.assertEqual(getattr(caught.exception, "status_code", None), 422)

    def test_paths_and_names(self):
        for name in ("../x.css", "a/../../x.css", "/x.css", "C:x.css", "a\\x.css", "a/./x.css", "a//x.css", "x\x01.css", "x\x7f.css"):
            with self.subTest(name=name):
                self.rejects(archive([("index.html", "x"), (name, "x")]))
        self.rejects(archive([("index.html", "x"), ("café.css", "x"), ("CAFÉ.css", "x")]))

    def test_declared_size_lie_and_crc(self):
        raw = bytearray(archive([("index.html", "<h1>" + "x" * 5000 + "</h1>")]))
        central = raw.rindex(b"PK\x01\x02")
        raw[central + 24:central + 28] = (100).to_bytes(4, "little")  # uncompressed size in central directory
        self.rejects(bytes(raw))
        raw = bytearray(archive([("index.html", "<h1>hola</h1>")]))
        raw[raw.index(b"PK\x01\x02") + 16] ^= 0xFF  # CRC
        self.rejects(bytes(raw))

    def test_entry_and_total_expansion_limits(self):
        self.rejects(archive([("index.html", "x"), ("a.txt", b"\0" * (2 * MiB))]))  # 1000:1 ratio
        many = [("index.html", "x")] + [("f%03d.txt" % i, "x") for i in range(401)]
        self.rejects(archive(many))

    def test_runtime_paths_are_not_written_to_disk(self):
        """read_zip keeps contents in memory: traversal cannot write files even if a name slipped through."""
        before = set(Path(ROOT).rglob("*"))
        uploads.zip_site("s.zip", archive([("index.html", '<img src="../../x.png">'), ("x.png", b"png")]), None)
        self.assertEqual(before, set(Path(ROOT).rglob("*")))


class Limits(unittest.TestCase):
    def test_defect_ui_limits_fit_the_body_limit(self):
        """[defect] F4: upload.js allows a 15 MB file plus a 12 MB original; base64 JSON then exceeds MAX_BODY (413)."""
        from portal.app import MAX_BODY
        js = (ROOT / "portal/static/upload.js").read_text()
        self.assertIn("12 * MiB", js)
        worst = (15 * MiB + 12 * MiB) * 4 // 3
        self.assertLessEqual(worst, MAX_BODY)


@unittest.skipUnless(uploads.poppler(), "Poppler not installed")
class PdfWithRealPoppler(unittest.TestCase):
    def test_pdf_page_limit_uses_pdfinfo_not_title(self):
        sys.path.insert(0, str(Path(__file__).parent))
        from pdf_inputs import text_pdf
        raw = text_pdf(0, pages=81)
        with self.assertRaises(Exception) as caught:
            uploads.build("x.pdf", raw, None, "upload-x", "t")
        self.assertIn("80", caught.exception.detail)

    def test_pdf_preview_escapes_metadata_and_text(self):
        sys.path.insert(0, str(Path(__file__).parent))
        from pdf_inputs import text_pdf
        raw = text_pdf(0, title=b"<img src=x onerror=alert(1)>", text=b"<script>alert(2)</script>")
        content, attachments, _ = uploads.build("x.pdf", raw, None, "upload-x", None)
        self.assertNotIn("<img src=x", content)
        self.assertNotIn("<script>alert", content)
        self.assertEqual(base64.b64decode(attachments[0]["data"]), raw)


try:
    from fastapi.testclient import TestClient
    from portal import test_app as fixtures
except Exception:  # httpx missing in the production image
    fixtures = None


@unittest.skipUnless(fixtures, "portal test client unavailable")
class Http(unittest.TestCase):
    if fixtures:
        setUp = fixtures.PortalTests.setUp
        tearDown = fixtures.PortalTests.tearDown
        client = fixtures.PortalTests.client

    def post(self, path, client=None, **body):
        return (client or self.owner).post(path, json=body)

    def html(self):
        return base64.b64encode(b"<html><head><title>T</title></head><body>x</body></html>").decode()

    def test_csrf_and_auth(self):
        for origin in ("null", "https://portal.test.evil", "http://portal.test"):
            c = TestClient(self.app, base_url=fixtures.ORIGIN, headers={"Origin": origin})
            c.cookies = self.owner.cookies
            self.assertEqual(self.post("/api/uploads/inspect", c, name="a.html", data=self.html()).status_code, 403, origin)
        c = TestClient(self.app, base_url=fixtures.ORIGIN, headers={"Authorization": "Bearer nope"})
        self.assertEqual(self.post("/api/uploads", c, name="a.html", data=self.html()).status_code, 401)
        self.assertEqual(self.post("/api/uploads/inspect", self.guest, name="a.html", data=self.html()).status_code, 401)

    def test_malformed_fields(self):
        cases = [dict(name="a.html", data="***"), dict(name="a.html", data=""), dict(name=None, data=self.html()),
                 dict(name="../a.html", data=self.html()), dict(name="a.exe", data=self.html()), dict(name="a.html", data=self.html(), entry=7),
                 dict(name="a.html", data=self.html(), title=["x"]), dict(name="a.html", data=self.html(), space="x" * 61),
                 dict(name="a.html", data=self.html(), mode="public"), dict(name="a.html", data=self.html(), visibility="private"),
                 dict(name="a.pdf", data=self.html())]
        for body in cases:
            with self.subTest(body={k: str(v)[:20] for k, v in body.items()}):
                self.assertEqual(self.post("/api/uploads", **body).status_code, 422)
        with self.store.db() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM versions").fetchone()[0], 1)

    def test_private_default_and_revision_identity(self):
        made = self.post("/api/uploads", name="a.html", data=self.html()).json()
        self.assertEqual(made["visibility"], "private")
        for aid in (made["id"].upper(), made["id"] + "0", "0" * 32):
            self.assertEqual(self.post("/api/uploads", name="a.html", data=self.html(), artifact=aid).status_code, 404, aid)
        self.assertEqual(self.post("/api/uploads", self.other, name="a.html", data=self.html(), artifact=made["id"]).status_code, 404)
        stale = self.post("/api/uploads", name="a.html", data=self.html(), artifact=made["id"], expected_current="f" * 32)
        self.assertEqual(stale.status_code, 409)
        # Without expected_current an unmanaged artifact accepts the revision (last write wins; see F8).
        blind = self.post("/api/uploads", name="a.html", data=base64.b64encode(b"<title>T2</title>").decode(), artifact=made["id"])
        self.assertEqual((blind.status_code, blind.json()["id"]), (200, made["id"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
