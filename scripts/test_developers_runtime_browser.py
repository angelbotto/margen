"""Opt-in Chromium regression for every bundled component preview and its opaque origin.

Run explicitly with: python scripts/test_developers_runtime_browser.py
Uses disposable FastAPI accounts/content; never contacts a deployed portal.
Three.js is served from a local copy verified against the preview's SRI (downloaded once
from its pinned cdnjs URL); without it only the 3D recipes fail, explicitly.
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
    'analytics.js': 'NotaAnalitica', 'chart-core.js': 'MargenGraficas', 'embeds.js': 'MargenEmbeds', 'attention-map.js': 'NotaAtencion', 'audio.js': 'NotaAudio', 'charts.js': 'NotaGraficas',
    'code.js': 'NotaCodigo', 'controls.js': 'NotaControles', 'data-explorer.js': 'NotaExplorador',
    'editorial-pieces.js': 'NotaPiezasEditoriales', 'editorial.js': 'NotaEditorial', 'evidence.js': 'NotaEvidencia',
    'fleet.js': 'NotaFlota', 'geography.js': 'NotaGeografia', 'globe.js': 'NotaGlobo', 'handwriting.js': 'NotaMano',
    'interface.js': 'BottifactUI', 'invitation.js': 'NotaInvitacion', 'prototype.js': 'NotaVisores', 'reader.js': 'NotaTemas',
    'relationship-map.js': 'BottifactRelationships', 'reports.js': 'NotaReportes', 'review.js': 'NotaRevision',
    'scene.js': 'NotaEscena', 'sound.js': 'NotaSonido', 'table-model.js': 'BottifactTableModel', 'tables.js': 'NotaTablas',
    'tabs.js': 'NotaPestanas', 'writing.js': 'NotaEscritura',
}
# Marks each runtime draws for its recipe; a generic SVG (such as a copy icon) never counts.
RENDERS = {
    '[data-grafica=barras], [data-grafica=distribucion]': '.grafica-caja svg .grafica-barra',
    '[data-grafica=lineas], [data-grafica=temporal]': '.grafica-caja svg .grafica-trazo',
    '[data-grafica=dispersion]': '.grafica-caja svg .grafica-serie', '[data-grafica=calor]': '[data-nivel]',
    '[data-reporte=cascada]': '.grafica-caja svg .cascada-sube, .grafica-caja svg .cascada-baja',
    '[data-reporte=multiples]': '.grafica-caja svg .grafica-trazo', '[data-reporte=conciliacion]': '.tabla-calculo',
    '[data-reporte=escenario]': 'output', '[data-reporte=recorrido]': '.globo-escena canvas',
    '[data-analitica]': '.analitica-caja svg path, .analitica-caja svg rect, .analitica-caja svg circle',
    '[data-relationship-map]': 'svg', '[data-atencion]': '.atencion-area',
    '[data-evidencia=imagen]': '.ev-pin', '[data-evidencia]:not([data-evidencia=imagen])': '.evidencia-visor [class*=ev-]',
    '[data-escena]': '.escena-caja canvas', '[data-flota]': 'canvas',
    '[data-tabla] [data-sparkline]': 'svg.sparkline', '[data-tabla]': '[data-ordenar], svg.sparkline',
    '[data-explorador]': 'select, input', '[data-pestanas]': '[role=tab][aria-selected=true]',
    '[data-visor]': 'iframe, button', '[data-lenguaje]': 'span[class]', '[data-galeria]': '[data-galeria-pista]',
}
# Recipes reported as plain tables in production; their drawing is required unconditionally.
REQUIRED = {
    'gantt': '.evidencia-visor svg [data-ev-row]', 'sankey': '.evidencia-visor svg .ev-flujo',
    'funnel': '.evidencia-visor svg .ev-solido', 'waterfall': '.grafica-caja svg .cascada-sube',
    'sparkline': 'svg.sparkline', 'coordinates': '.escena-caja canvas', 'attention-map': '.atencion-area',
    'small-multiples': '.grafica-caja svg .grafica-trazo',
}
# Error slots modules fill when their renderer fails (for example, three.js unavailable).
ERRORS = ('[data-error-analitica], [data-error-grafica], [data-error], [data-error-reporte], [data-error-visor], '
          '[data-error-pestanas], .evidencia-error, .grafica-error, .globo-error, .error-componente')
EXPECTED_ERRORS = ()


def pinned_three():
    """Bytes of the pinned three.js build, verified against the preview's SRI; None when unavailable."""
    import base64
    import hashlib
    import os
    import urllib.request
    from portal.developers import THREE
    cache = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache')) / 'margen' / THREE[0].rsplit('/', 3)[-2] / 'three.min.js'
    expected = THREE[1].split('-', 1)[1]
    valid = lambda data: base64.b64encode(hashlib.sha512(data).digest()).decode() == expected
    if cache.is_file() and valid(cache.read_bytes()):
        return cache.read_bytes()
    try:
        data = urllib.request.urlopen(THREE[0], timeout=20).read()
    except OSError:
        return None
    if not valid(data):
        raise AssertionError('three.js de cdnjs no coincide con el SRI fijado')
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(data)
    return data


def components():
    return [item for item in bundled().values() if item['kind'] == 'component']


class BundledPreviewBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.three = pinned_three()
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
        three = self.three
        # Local verified bytes keep the sweep deterministic; the browser still enforces the SRI attribute.
        context.route('https://cdnjs.cloudflare.com/**', lambda route: route.fulfill(
            body=three, content_type='application/javascript', headers={'Access-Control-Allow-Origin': '*'}) if three else route.abort())
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
                    if self.three is None and {'scene.js', 'globe.js', 'fleet.js'} & set(item['preview_runtime']):
                        failures.append(item['slug'] + ': three.js 0.160.1 no disponible (sin caché verificada ni red)')
                        continue
                    errors.clear()
                    frame = self.load(page, item)
                    body = frame.locator('body')
                    missing = body.evaluate('(_, names) => names.filter(name => !(name in window))', [GLOBALS[name] for name in item['preview_runtime']]
                                           # Pinned three.js arrives only through its integrity-checked script tag.
                                           + (['THREE'] if {'scene.js', 'globe.js'} & set(item['preview_runtime']) else []))
                    if missing:
                        failures.append(item['slug'] + ': no ejecutó ' + ', '.join(missing))
                    # Hosts come from the recipe source, so a preview that drops the markup cannot skip the check.
                    owners = body.evaluate("(_, [source, owners]) => { const recipe = new DOMParser().parseFromString(source, 'text/html'); return owners.filter(owner => recipe.querySelector(owner)); }", [item['content'], list(RENDERS)])
                    for owner in owners:
                        output = RENDERS[owner]
                        hosts = frame.locator('main.hoja').locator(owner)
                        visible = hosts.evaluate_all("(nodes, output) => nodes.some(node => node.getClientRects().length) && nodes.filter(node => node.getClientRects().length).every(node => [...node.querySelectorAll(output)].some(n => { const r = n.getBoundingClientRect(); return r.width > 0 && r.height > 0; }))", output)
                        if not visible:
                            failures.append(item['slug'] + ': ' + owner + ' sin ' + output + ' visible')
                    # Every report host must hold a live NotaReportes instance, not just its static table.
                    if body.evaluate("() => document.querySelectorAll('[data-reporte]').length && ![...document.querySelectorAll('[data-reporte]')].every(host => window.NotaReportes?.get(host))"):
                        failures.append(item['slug'] + ': reporte sin instancia de NotaReportes')
                    if item['slug'] in REQUIRED:
                        drawn = body.evaluate("(_, selector) => [...document.querySelectorAll(selector)].some(n => { const r = n.getBoundingClientRect(); return r.width > 0 && r.height > 0; })", REQUIRED[item['slug']])
                        if not drawn:
                            failures.append(item['slug'] + ': sin ' + REQUIRED[item['slug']] + ' (requerido)')
                    failed = body.evaluate("(_, selector) => [...document.querySelectorAll(selector)].filter(n => n.getClientRects().length && n.textContent.trim()).map(n => n.textContent.trim())", ERRORS)
                    if failed:
                        failures.append(item['slug'] + ': error visible ' + '; '.join(failed))
                    for width in WIDTHS:
                        page.locator('iframe').evaluate('(frame, width) => { frame.style.width = width + "px"; }', width)
                        # Static recipes run without scripts, so frames are counted in the parent harness.
                        page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
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

            frame = self.load(page, bundled()['component-reconciliation'])
            self.assertTrue(frame.locator('[data-reporte]').evaluate('host => !!window.NotaReportes.get(host)'))
            cells = frame.locator('[data-reporte] tbody tr td:nth-of-type(3)').all_text_contents()
            self.assertEqual([int(c.replace('−', '-').replace('+', '')) for c in cells], [-2, 0, 3])
            total = frame.locator('[data-reporte] tfoot td').all_text_contents()[:3]
            self.assertEqual([int(c.replace('−', '-').replace('+', '').replace('.', '')) for c in total], [230, 231, 1])

            frame = self.load(page, bundled()['component-gantt'])
            choice = frame.locator('.evidencia-controles select')
            detail = frame.locator('.evidencia-detalle').text_content()
            choice.select_option(index=2)
            self.assertNotEqual(frame.locator('.evidencia-detalle').text_content(), detail)
            self.assertEqual(frame.locator('.evidencia-visor .ev-elegido[data-ev-row="2"]').count(), 1)

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
