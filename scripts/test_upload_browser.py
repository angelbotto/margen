"""Real portal upload flow, isolated accounts, and authored styling in Chromium/WebKit."""
import io
import os
import unittest
import zipfile
import test_community_marketplace as harness
from portal.test_uploads import pdf
from portal.uploads import poppler


class UploadBrowser(unittest.TestCase):
    tearDown = harness.BrowserTests.tearDown
    page = harness.BrowserTests.page
    assert_layout = harness.BrowserTests.assert_layout

    def setUp(self):
        harness.BrowserTests.setUp(self)
        if os.environ.get('MARGEN_BROWSER') == 'webkit':
            self.browser.close()
            self.browser = self.playwright.webkit.launch()

    def choose(self, name, data):
        page = self.page(self.fixture.owner)
        page.goto('https://portal.test/')
        page.locator('#publish').click()
        page.locator('input[name=file]').set_input_files({'name': name, 'mimeType': 'application/octet-stream', 'buffer': data})
        page.get_by_text('Archivo revisado. Aún no se ha creado ningún artefacto.').wait_for()
        return page

    def publish(self, page):
        page.get_by_role('button', name='Crear artefacto privado').click()
        page.wait_for_url('**/a/*')
        aid = page.url.rsplit('/', 1)[-1]
        result = self.fixture.owner.get('/api/artifacts/' + aid).json()
        self.assertEqual(result['visibility'], 'private')
        self.assertEqual(self.fixture.other.get('/api/artifacts/' + aid).status_code, 404)
        return page.frame_locator('#artifact-frame')

    def test_plain_html_is_private_and_keeps_its_design(self):
        page = self.choose('own.html', b'<!doctype html><title>My own layout</title><style>body{background:#153d40;color:white;font:24px Georgia;padding:40px}</style><h1>Authored document</h1>')
        self.assert_layout(page)
        frame = self.publish(page)
        frame.get_by_role('heading', name='Authored document').wait_for()
        self.assertEqual(frame.locator('body').evaluate('e=>getComputedStyle(e).backgroundColor'), 'rgb(21, 61, 64)')
        self.assertEqual(frame.locator('.pie').count(), 0)
        self.assertFalse(self.errors, self.errors)

    def test_zip_local_assets_work_without_server_build(self):
        out = io.BytesIO()
        with zipfile.ZipFile(out, 'w') as z:
            z.writestr('site/index.html', '<title>Packaged page</title><link rel="stylesheet" href="assets/style.css"><h1>ZIP page</h1><script src="assets/main.js"></script>')
            z.writestr('site/assets/style.css', 'h1{color:rgb(10,120,80)}')
            z.writestr('site/assets/main.js', 'document.querySelector("h1").dataset.ready="yes";')
        page = self.choose('site.zip', out.getvalue())
        frame = self.publish(page)
        title = frame.locator('h1[data-ready=yes]'); title.wait_for()
        self.assertEqual(title.evaluate('e=>getComputedStyle(e).color'), 'rgb(10, 120, 80)')
        self.assertFalse(self.errors, self.errors)

    @unittest.skipUnless(poppler(), 'PDF preview requires Poppler')
    def test_pdf_has_page_preview_and_original(self):
        page = self.choose('report.pdf', pdf(2))
        page.get_by_text('2 páginas · vista previa visual', exact=False).wait_for()
        frame = self.publish(page)
        frame.locator('img').first.wait_for()
        self.assertEqual(frame.locator('img').count(), 2)
        download = frame.get_by_role('link', name='Descargar original')
        self.assertIn('/attachments/', download.get_attribute('href'))
        self.assertEqual(self.fixture.owner.get(download.get_attribute('href')).content, pdf(2))
        self.assertFalse(self.errors, self.errors)


if __name__ == '__main__': unittest.main()
