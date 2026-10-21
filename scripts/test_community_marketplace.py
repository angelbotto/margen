"""Synthetic real-browser acceptance for visual creation and community reuse.

Uses FastAPI TestClient behind a Playwright route: HTTPS, real portal assets,
real API authorization, disposable accounts/data; no production credentials.
"""
import json
import sys
import unittest
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
from portal import test_developers as fixtures


class BrowserTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.DevelopersTests()
        self.fixture.setUp()
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch()
        self.errors = []

    def tearDown(self):
        self.browser.close()
        self.playwright.stop()
        self.fixture.tearDown()

    def page(self, client):
        context = self.browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
        def proxy(route):
            req = route.request
            headers = {k: v for k, v in req.headers.items() if k not in {'host', 'cookie', 'accept-encoding'}}
            response = client.request(req.method, req.url, headers=headers, content=req.post_data_buffer, follow_redirects=False)
            headers = {k: v for k, v in response.headers.items() if k not in {'content-encoding', 'content-length'}}
            route.fulfill(status=response.status_code, headers=headers, body=response.content)
        context.route('https://portal.test/**', proxy)
        context.route('https://fonts.googleapis.com/**', lambda route: route.abort())
        page = context.new_page()
        page.on('pageerror', lambda error: self.errors.append(error.stack))
        return page

    def open_catalog(self, page, item=''):
        page.goto('https://portal.test/?view=developers' + ('&item=' + item if item else ''))
        page.get_by_role('heading', name='Dale tu forma a Margen.').wait_for()

    def assert_layout(self, page):
        for width in (1440, 390, 320, 300):
            page.set_viewport_size({'width': width, 'height': 950})
            self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), f'Page overflow at {width}')
            dialog = page.locator('dialog[open]')
            if dialog.count():
                self.assertTrue(dialog.evaluate('(e) => e.scrollWidth <= e.clientWidth + 1'), f'Dialog overflow at {width}')

    def test_create_share_use_theme_and_reader_controls(self):
        page = self.page(self.fixture.owner)
        self.open_catalog(page)
        self.assert_layout(page)
        page.get_by_role('button', name='Crear un tema', exact=True).click()
        studio = page.locator('.community-studio')
        studio.get_by_label('Nombre', exact=True).fill('Jardín de prueba')
        studio.get_by_label('Tipografía de títulos').select_option('source-serif')
        studio.get_by_label('Tipografía del texto').select_option('manrope')
        studio.locator('[data-token=papel]').fill('#f1ede3')
        studio.locator('.studio-sample select').select_option('dark')
        studio.locator('[data-token=papel]').fill('#142421')
        studio.get_by_text('Vista previa · oscuro', exact=True).wait_for()
        self.assert_layout(page)
        frame = page.frame_locator('.studio-preview')
        self.assertEqual(frame.locator('html').get_attribute('data-color-mode'), 'dark')
        self.assertIn('Source Serif 4', frame.locator('h1').evaluate('(e)=>getComputedStyle(e).fontFamily'))
        self.assertIn('Manrope', frame.locator('main').evaluate('(e)=>getComputedStyle(e).fontFamily'))
        self.assertGreaterEqual(frame.locator('h1 + p').evaluate('(e)=>e.getBoundingClientRect().top-e.previousElementSibling.getBoundingClientRect().bottom'), 13)
        self.assertEqual(frame.locator('html').evaluate('(e)=>getComputedStyle(e).getPropertyValue("--papel").trim()'), '#142421')
        studio.get_by_role('button', name='Guardar para mí', exact=True).click()
        detail = page.locator('.developer-dialog')
        detail.get_by_role('heading', name='Jardín de prueba').wait_for()
        key = parse_qs(urlsplit(page.url).query)['item'][0]
        self.assertEqual(self.fixture.guest.get('/api/developers/items/' + key).status_code, 404)
        detail.get_by_role('checkbox').check()
        detail.get_by_role('button', name='Compartir por enlace', exact=True).click()
        detail.get_by_label('Enlace para compartir').wait_for()
        anonymous = self.page(self.fixture.guest)
        self.open_catalog(anonymous, key)
        anonymous.locator('.developer-dialog').get_by_role('heading', name='Jardín de prueba').wait_for()
        self.assertEqual(anonymous.get_by_role('button', name='Crear mi versión').count(), 0)
        other = self.page(self.fixture.other)
        self.open_catalog(other, key)
        other.get_by_role('button', name='Crear artefacto con este tema').click()
        other.wait_for_url('**/a/*')
        aid = urlsplit(other.url).path.split('/')[-1]
        self.assertEqual(self.fixture.other.get('/api/artifacts/' + aid).json()['visibility'], 'private')
        other.goto('https://portal.test/api/artifacts/' + aid + '/render')
        other.wait_for_function('document.documentElement.hasAttribute("data-margen-community-theme")')
        self.assertIn('Source Serif 4', other.locator('h1').first.evaluate('(e)=>getComputedStyle(e).fontFamily'))
        # Reader controls dispatch genuine change events even inside their collapsed menu.
        other.locator('[data-elegir-modo][value=dark]').evaluate('(e)=>{e.checked=true;e.dispatchEvent(new Event("change",{bubbles:true}))}')
        self.assertEqual(other.locator('html').evaluate('(e)=>getComputedStyle(e).getPropertyValue("--papel").trim()'), '#142421')
        style = other.locator('[data-elegir-estilo]').last
        style.evaluate('(e)=>{e.checked=true;e.dispatchEvent(new Event("change",{bubbles:true}))}')
        self.assertIsNotNone(other.locator('html').get_attribute('data-community-typography-override'))
        other.locator('[data-elegir-tema]').first.evaluate('(e)=>{e.checked=true;e.dispatchEvent(new Event("change",{bubbles:true}))}')
        self.assertIsNone(other.locator('html').get_attribute('data-margen-community-theme'))
        other.locator('[data-community-theme]').evaluate('(e)=>e.click()')
        self.assertIsNotNone(other.locator('html').get_attribute('data-margen-community-theme'))
        self.assertIsNone(other.locator('html').get_attribute('data-community-typography-override'))
        self.assertFalse(self.errors, self.errors)

    def test_visual_component_fork_and_hostile_svg_reuse(self):
        page = self.page(self.fixture.owner)
        self.open_catalog(page)
        page.get_by_role('button', name='Crear un componente', exact=True).click()
        studio = page.locator('.community-studio')
        studio.get_by_label('Nombre', exact=True).fill('Un proceso claro')
        studio.get_by_label('Tipo de componente').select_option('diagram')
        studio.get_by_label('Contenido · hasta 12 bloques').fill('Investigar\nProponer\nDecidir')
        studio.get_by_role('checkbox').check()
        studio.get_by_role('button', name='Compartir por enlace', exact=True).click()
        detail = page.locator('.developer-dialog')
        detail.get_by_role('heading', name='Un proceso claro').wait_for()
        detail.get_by_role('button', name='Crear mi versión').click()
        studio = page.locator('.community-studio')
        self.assertEqual(studio.get_by_label('Tipo de componente').input_value(), 'diagram')
        self.assertEqual(studio.get_by_label('Contenido · hasta 12 bloques').input_value(), 'Investigar\nProponer\nDecidir')
        self.assert_layout(page)
        studio.get_by_role('button', name='Cerrar', exact=True).click()
        payloads = [
            '<svg><style><img src=x onerror="window.reviewExecuted=1"></style></svg>',
            '<svg><foreignObject><img src=x onerror="window.reviewExecuted=1"></foreignObject></svg>',
            '<math><mtext><table><mglyph><style><!--</style><img title="--><img src=x onerror=window.reviewExecuted=1>">',
            '<svg><a xlink:href="javascript:window.reviewExecuted=1"><text>Unsafe link</text></a></svg>',
        ]
        for index, payload in enumerate(payloads):
            package = self.fixture.package('component')
            package.update(slug='attack-' + str(index), content=payload + '<p>Visible content</p>')
            key = self.fixture.submit(package, 'shared')
            created = self.fixture.other.post('/api/developers/items/' + key + '/use', json={}).json()
            target = self.page(self.fixture.other)
            target.goto('https://portal.test/api/artifacts/' + created['id'] + '/render')
            target.get_by_text('Visible content', exact=True).wait_for()
            self.assertIsNone(target.evaluate('window.reviewExecuted'))
            self.assertEqual(target.locator('[onerror], [onload], [href^="javascript:"]').count(), 0)
        self.assertFalse(self.errors, self.errors)


if __name__ == '__main__':
    unittest.main()
