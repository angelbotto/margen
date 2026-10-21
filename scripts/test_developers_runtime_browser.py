"""Opt-in Chromium regression for every bundled component preview and its opaque origin.

Run explicitly with: python scripts/test_developers_runtime_browser.py
Uses disposable FastAPI accounts/content; never contacts a deployed portal.
Three.js is fetched from its pinned cdnjs URL, the only network a preview may use.
"""
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from playwright.sync_api import sync_playwright
from portal import test_developers as fixtures
from portal.developers import bundled

WIDTHS = (300, 375, 768, 1024, 1440)
# Global each reviewed module publishes once it has executed inside the preview.
GLOBALS = {
    'analytics.js': 'NotaAnalitica', 'attention-map.js': 'NotaAtencion', 'audio.js': 'NotaAudio', 'charts.js': 'NotaGraficas',
    'code.js': 'NotaCodigo', 'controls.js': 'NotaControles', 'data-explorer.js': 'NotaExplorador',
    'editorial-pieces.js': 'NotaPiezasEditoriales', 'editorial.js': 'NotaEditorial', 'evidence.js': 'NotaEvidencia',
    'fleet.js': 'NotaFlota', 'geography.js': 'NotaGeografia', 'globe.js': 'NotaGlobo', 'handwriting.js': 'NotaMano',
    'interface.js': 'BottifactUI', 'invitation.js': 'NotaInvitacion', 'prototype.js': 'NotaVisores', 'reader.js': 'NotaTemas',
    'relationship-map.js': 'BottifactRelationships', 'reports.js': 'NotaReportes', 'review.js': 'NotaRevision',
    'scene.js': 'NotaEscena', 'sound.js': 'NotaSonido', 'table-model.js': 'BottifactTableModel', 'tables.js': 'NotaTablas',
    'tabs.js': 'NotaPestanas', 'writing.js': 'NotaEscritura',
}
# Rendered output that only exists after the recipe's runtime ran; selectors are visible, sized elements.
RENDERS = {
    '[data-grafica]:not([data-grafica=calor])': 'svg', '[data-grafica=calor]': '[data-nivel]',
    '[data-analitica]': 'svg', '[data-relationship-map]': 'svg', '[data-escena]': 'canvas', '[data-flota]': 'canvas',
    '[data-recorrido-globo]': 'canvas', '[data-atencion]': 'svg', '[data-evidencia]': 'svg, canvas, button',
    '[data-explorador]': 'select, input', '[data-pestanas]': '[role=tab][aria-selected=true]', '[data-tabla]': '[data-ordenar], svg',
    '[data-reporte=escenario]': 'output', '[data-visor]': 'iframe, button', '[data-lenguaje]': 'span[class]',
    '[data-galeria]': '[data-galeria-pista]',
}
EXPECTED_ERRORS = ()


def components():
    return [item for item in bundled().values() if item['kind'] == 'component']


class BundledPreviewBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import urllib.request
        from portal.developers import THREE
        try:
            urllib.request.urlopen(urllib.request.Request(THREE[0], method='HEAD'), timeout=10).close()
        except OSError as error:
            raise unittest.SkipTest('cdnjs no responde; las escenas 3D necesitan three.js fijado: ' + str(error))
        cls.fixture = fixtures.DevelopersTests()
        cls.fixture.setUp()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.fixture.tearDown()

    def harness(self):
        context = self.browser.new_context(viewport={'width': 1500, 'height': 900}, reduced_motion='reduce')
        fixture = self.fixture

        def proxy(route):
            request = route.request
            if request.url == 'https://portal.test/preview-harness':
                route.fulfill(content_type='text/html', body='<html><body style="margin:0"><h1>Parent</h1><iframe title="Preview" style="border:0;height:700px;width:1440px"></iframe></body></html>')
                return
            response = fixture.guest.request(request.method, request.url, follow_redirects=False)
            headers = {key: value for key, value in response.headers.items()
                       if key not in {'content-encoding', 'content-length'}}
            route.fulfill(status=response.status_code, headers=headers, body=response.content)

        context.route('https://portal.test/**', proxy)
        context.route('https://fonts.googleapis.com/**', lambda route: route.abort())
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('console', lambda message: message.type == 'error' and errors.append(message.text))
        page.goto('https://portal.test/preview-harness')
        return context, page, errors

    def load(self, page, item):
        sandbox = 'allow-scripts' if item['preview_runtime'] else ''
        page.locator('iframe').evaluate('(frame, [sandbox, url]) => { frame.style.width = "1440px"; frame.setAttribute("sandbox", sandbox); frame.src = url; }',
                                        [sandbox, '/api/developers/items/' + item['id'] + '/preview'])
        frame = page.frame_locator('iframe')
        frame.locator('main.hoja').wait_for()
        page.wait_for_load_state('load')
        page.wait_for_timeout(900 if {'scene.js', 'globe.js', 'fleet.js'} & set(item['preview_runtime']) else 250)
        return frame

    def test_every_bundled_component_renders_its_runtime_without_overflow(self):
        context, page, errors = self.harness()
        failures = []
        try:
            for item in components():
                with self.subTest(slug=item['slug']):
                    errors.clear()
                    frame = self.load(page, item)
                    body = frame.locator('body')
                    missing = body.evaluate('(_, names) => names.filter(name => !(name in window))', [GLOBALS[name] for name in item['preview_runtime']]
                                           # Pinned three.js arrives only through its integrity-checked script tag.
                                           + (['THREE'] if {'scene.js', 'globe.js'} & set(item['preview_runtime']) else []))
                    if missing:
                        failures.append(item['slug'] + ': no ejecutó ' + ', '.join(missing))
                    for owner, output in RENDERS.items():
                        hosts = frame.locator('main.hoja').locator(owner)
                        if item['preview_runtime'] and hosts.count():
                            visible = hosts.evaluate_all("(nodes, output) => nodes.some(node => node.getClientRects().length) && nodes.filter(node => node.getClientRects().length).every(node => [...node.querySelectorAll(output)].some(n => { const r = n.getBoundingClientRect(); return r.width > 4 && r.height > 4; }))", output)
                            if not visible:
                                failures.append(item['slug'] + ': ' + owner + ' sin ' + output + ' visible')
                    failed = body.evaluate("() => [...document.querySelectorAll('[data-error-analitica],[data-error-grafica],[data-error],.error-componente')].map(n => n.textContent.trim()).filter(Boolean)")
                    if failed:
                        failures.append(item['slug'] + ': error visible ' + '; '.join(failed))
                    for width in WIDTHS:
                        page.locator('iframe').evaluate('(frame, width) => { frame.style.width = width + "px"; }', width)
                        overflow = body.evaluate('() => document.documentElement.scrollWidth - document.documentElement.clientWidth')
                        if overflow > 1:
                            failures.append(item['slug'] + ': overflow ' + str(overflow) + 'px a ' + str(width))
                    if not item['preview_runtime']:
                        self.assertEqual(body.evaluate('() => document.scripts.length'), 0)
                    unexpected = [e for e in errors if not any(text in e for text in EXPECTED_ERRORS)]
                    if unexpected:
                        failures.append(item['slug'] + ': errores ' + ' | '.join(unexpected)[:400])
            self.assertEqual(failures, [], '\n' + '\n'.join(failures))
        finally:
            context.close()

    def test_runtime_previews_respond_to_the_reader(self):
        context, page, errors = self.harness()
        try:
            frame = self.load(page, bundled()['component-data-explorer'])
            rows = frame.locator('[data-explorador] tbody tr')
            before = rows.count()
            frame.locator('[data-explorador] input[name=buscar]').fill('zzzz-sin-coincidencias')
            page.wait_for_timeout(300)
            self.assertLess(frame.locator('[data-explorador] tbody tr:visible').count(), before)

            frame = self.load(page, bundled()['component-tabs'])
            frame.locator('[role=tab]').nth(1).click()
            self.assertEqual(frame.locator('[role=tab]').nth(1).get_attribute('aria-selected'), 'true')
            self.assertEqual(frame.locator('[role=tabpanel]:visible').count(), 1)

            frame = self.load(page, bundled()['component-totals'])
            order = lambda: frame.locator('[data-tabla] tbody tr').all_text_contents()
            first = order()
            frame.locator('[data-ordenar]').last.click()
            second = order()
            frame.locator('[data-ordenar]').last.click()
            self.assertNotEqual(order(), second)
            self.assertEqual(sorted(first), sorted(second))

            frame = self.load(page, bundled()['component-scenario'])
            result = frame.locator('[data-resultado]').text_content()
            frame.locator('input[name=despues]').fill('1')
            frame.locator('input[name=despues]').dispatch_event('input')
            page.wait_for_timeout(200)
            self.assertNotEqual(frame.locator('[data-resultado]').text_content(), result)

            frame = self.load(page, bundled()['component-prototype'])
            frame.locator('[data-ancho-visor="768"]').first.click()
            self.assertEqual(frame.locator('[data-ancho-visor="768"]').first.get_attribute('aria-pressed'), 'true')
            self.assertEqual(errors, [])
        finally:
            context.close()

    def test_runtime_frames_stay_opaque_and_community_never_runs(self):
        context, page, errors = self.harness()
        try:
            frame = self.load(page, bundled()['component-route-map'])
            self.assertEqual(frame.locator('body').evaluate("() => { try { return parent.document.body.textContent; } catch (error) { return error.name; } }"), 'SecurityError')
            self.assertEqual(frame.locator('body').evaluate("() => { try { return localStorage.length; } catch (error) { return error.name; } }"), 'SecurityError')
            package = self.fixture.package('component')
            package['content'] = '<section><img src="data:," onerror="window.ran=1"><a href="javascript:window.ran=1">x</a><script>window.ran=1</script>' + bundled()['component-line-chart']['content'] + '</section>'
            key = self.fixture.submit(package)
            response = self.fixture.owner.get('/api/developers/items/' + key + '/preview')
            policy = response.headers['content-security-policy']
            self.assertIn("script-src 'none'", policy)
            self.assertNotIn('allow-scripts', policy)
            self.assertNotIn('allow-same-origin', policy)
            for active in ('<script', 'onerror', 'javascript:'):
                self.assertNotIn(active, response.text)
        finally:
            context.close()


if __name__ == '__main__':
    unittest.main()
