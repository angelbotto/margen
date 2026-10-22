#!/usr/bin/env python3
"""Casos límite de charts.js/chart-core.js en navegador: calor constante, meta negativa, líneas en cero,
calor denso y SVG exportado autónomo. Sin red.

  python scripts/test_chart_edges.py            # chromium y webkit, 320 y 1440, claro y oscuro
  MARGEN_BROWSER=webkit python scripts/test_chart_edges.py
"""
import os, re, sys, tempfile, threading, unittest
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from contract_artifact import build

ENGINES = [os.environ['MARGEN_BROWSER']] if os.environ.get('MARGEN_BROWSER') else ['chromium', 'webkit']
WIDTHS, MODES = [320, 1440], ['light', 'dark']


def figure(fid, kind, heads, rows, **data):
    attrs = ' '.join(f'data-{k}="{v}"' for k, v in data.items())
    head = ''.join(f'<th scope="col">{h}</th>' for h in heads)
    body = ''.join(f'<tr><th scope="row">{r[0]}</th>' + ''.join(f'<td data-valor="{v}">{v}</td>' for v in r[1:]) + '</tr>' for r in rows)
    return (f'<figure class="ancho" id="{fid}" data-grafica="{kind}" {attrs}><details><summary>Datos</summary>'
            f'<div class="tabla-caja" tabindex="0" role="region" aria-label="Datos {fid}"><table><caption>{fid}</caption>'
            f'<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div></details></figure>')


LETTERS = [chr(65 + i) for i in range(31)]
PAGE = ''.join([
    figure('cero', 'calor', ['Día', 'A', 'B', 'C'], [['L', 0, 0, 0], ['M', 0, 0, 0]], unidad='eventos'),
    figure('cinco', 'calor', ['Día', 'A', 'B'], [['L', 5, 5], ['M', 5, 5]], unidad='eventos'),
    figure('pico', 'calor', ['Día', 'A', 'B', 'C'], [['L', 0, 0, 0], ['M', 0, 0, 5]], unidad='eventos'),
    figure('meta', 'meta', ['KPI', 'Valor', 'Meta'], [['NPS', -12, 40], ['CSAT', 30, 40]], unidad='puntos'),
    figure('meta-negativa', 'meta', ['KPI', 'Valor', 'Meta'], [['Pérdida', -50, -20]], unidad='millones'),
    figure('lineas', 'lineas', ['Mes', 'Altas'], [['Ene', 0], ['Feb', 0], ['Mar', 0]], unidad='altas'),
    figure('denso', 'calor', ['Fila'] + LETTERS[:26], [['Una fila con rótulo largo'] + list(range(26))], unidad='u'),
    figure('muy-denso', 'calor', ['Fila'] + LETTERS, [['Una fila con rótulo largo'] + list(range(31))], unidad='u'),
    figure('apiladas', 'columnas', ['Trimestre', 'Norte', 'Centro', 'Sur'], [['T1', 4, 3, 2], ['T2', 5, 2, 4], ['T3', 6, 4, 1]], unidad='millones', apilado='si'),
])

STATE = r"""id => {
  const f = document.getElementById(id), svg = f.querySelector('svg.mg-svg');
  if (!svg) return {error: f.querySelector('.grafica-error')?.textContent || 'sin svg'};
  const sr = svg.getBoundingClientRect(), box = svg.parentElement;
  return {
    fills: [...svg.querySelectorAll('.mg-calor-celda')].map(r => r.style.fill),
    legend: [...f.querySelectorAll('.calor-leyenda li')].map(l => l.textContent),
    levels: [...f.querySelectorAll('td[data-nivel]')].map(td => td.dataset.nivel),
    yTicks: [...svg.querySelectorAll('[data-tick-y]')].map(l => +l.dataset.tickY),
    bars: [...svg.querySelectorAll('rect.grafica-barra')].map(r => ({x: +r.getAttribute('x'), w: +r.getAttribute('width')})),
    xMin: +svg.dataset.xMin, zeroX: (() => { const z = svg.querySelector('[data-tick-x="0"]'); return z ? +z.getAttribute('x1') : null; })(),
    outside: [...svg.querySelectorAll('rect,text')].filter(n => { const r = n.getBoundingClientRect(); return r.width && (r.right > sr.right + 1 || r.left < sr.left - 1); }).length,
    scroll: box.scrollWidth > box.clientWidth + 1, role: box.getAttribute('role'), tab: box.tabIndex, label: box.getAttribute('aria-label') || '',
    pageOverflow: document.documentElement.scrollWidth > innerWidth + 1,
  };
}"""


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


class ChartEdges(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        path = Path(cls.tmp.name) / 'edges.html'
        path.write_text(build('Casos límite', [{'id': 'uno', 'titulo': 'Uno', 'html': '<section class="seccion" id="s"><h2>Gráficas</h2><p>Casos límite.</p></section>' + PAGE}],
                              description='fixture', document_id='chart-edges', theme='editorial', mode='light', date='2026-10-22'))
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=cls.tmp.name))
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}/edges.html'
        cls.pw = sync_playwright().start()
        cls.browsers = {e: getattr(cls.pw, e).launch() for e in ENGINES}

    @classmethod
    def tearDownClass(cls):
        for b in cls.browsers.values():
            b.close()
        cls.pw.stop(); cls.server.shutdown(); cls.tmp.cleanup()

    def open(self, engine, width, mode):
        ctx = self.browsers[engine].new_context(viewport={'width': width, 'height': 900}, color_scheme=mode, reduced_motion='reduce', accept_downloads=True)
        ctx.route('**/*', lambda r: r.continue_() if urlsplit(r.request.url).hostname == '127.0.0.1' or r.request.url.startswith(('data:', 'blob:')) else r.abort())
        page = ctx.new_page(); errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(self.url)
        page.evaluate("t => { document.documentElement.setAttribute('data-theme', t); document.dispatchEvent(new CustomEvent('nota:tema')); }", mode)
        page.wait_for_function("document.querySelectorAll('figure[data-grafica] svg.mg-svg, figure[data-grafica] .grafica-error').length === 9")
        page.wait_for_timeout(150)
        return ctx, page, errors

    def matrix(self, check):
        for engine in ENGINES:
            for width in WIDTHS:
                for mode in MODES:
                    with self.subTest(engine=engine, width=width, mode=mode):
                        ctx, page, errors = self.open(engine, width, mode)
                        try:
                            check(page, width)
                            self.assertEqual(errors, [])
                        finally:
                            ctx.close()

    def test_edges(self):
        self.matrix(self.check_edges)

    def test_standalone_svg_export(self):
        self.matrix(self.check_export)

    def check_edges(self, page, width):
        s = {fid: page.evaluate(STATE, fid) for fid in ['cero', 'cinco', 'pico', 'meta', 'meta-negativa', 'lineas', 'denso', 'muy-denso', 'apiladas']}
        for fid, st in s.items():
            self.assertNotIn('error', st, fid)
            self.assertFalse(st['pageOverflow'], fid)
        # Calor todo en cero: nivel mínimo, leyenda sin rango inventado; tabla y figura coinciden.
        self.assertEqual(set(s['cero']['fills']), {'var(--calor-0)'})
        self.assertEqual(s['cero']['legend'][0], 'Todas las celdas: 0 · sin variación')
        self.assertEqual(set(s['cero']['levels']), {'0'})
        # Constante distinta de cero: nivel neutro, nunca el máximo.
        self.assertEqual(set(s['cinco']['fills']), {'var(--calor-2)'})
        self.assertFalse(any(' a ' in l for l in s['cinco']['legend'][:1]), s['cinco']['legend'])
        # Dos cortes (muchos ceros y un pico): los ceros no se pintan como el pico.
        self.assertEqual(s['pico']['fills'].count('var(--calor-4)'), 1)
        self.assertEqual(s['pico']['fills'].count('var(--calor-0)'), 5)
        # Meta: el negativo se dibuja hacia la izquierda del cero, con longitud proporcional.
        neg, pos = s['meta']['bars']
        self.assertLess(s['meta']['xMin'], -12)
        self.assertGreater(neg['w'], 1)
        self.assertAlmostEqual(neg['x'] + neg['w'], s['meta']['zeroX'], delta=.6)
        self.assertAlmostEqual(neg['w'] / pos['w'], 12 / 30, delta=.02)
        self.assertLessEqual(s['meta-negativa']['xMin'], -50)
        # Líneas en cero (conteos): el eje empieza en 0, sin negativos inventados.
        self.assertEqual(min(s['lineas']['yTicks']), 0)
        # Calor denso: nada fuera del SVG. A 320 px, 26 columnas caben cediendo el rótulo; 31 se desplazan declaradas.
        for fid in ['denso', 'muy-denso']:
            self.assertEqual(s[fid]['outside'], 0, fid)
        self.assertFalse(s['denso']['scroll'])
        if width == 320:
            self.assertTrue(s['muy-denso']['scroll'])
            self.assertEqual((s['muy-denso']['role'], s['muy-denso']['tab']), ('region', 0))
            self.assertIn('desplazable', s['muy-denso']['label'])
        else:
            self.assertFalse(s['muy-denso']['scroll'])
            self.assertIsNone(s['muy-denso']['role'])

    def check_export(self, page, width):
        with page.expect_download() as info:
            page.locator('#apiladas .mg-exportar button').nth(1).click()
        text = Path(info.value.path()).read_text()
        root = ElementTree.fromstring(text.split('\n', 1)[1])
        ns = '{http://www.w3.org/2000/svg}'
        self.assertEqual(root.get('role'), 'img')
        self.assertEqual(root.get('aria-label'), 'apiladas')
        self.assertNotRegex(text, r'flechas|Enter para|Escape|var\(|currentColor|https?://(?!www\.w3\.org)')
        desc = root.find(ns + 'desc').text
        self.assertIn('Leyenda: Norte, Centro, Sur', desc)
        legend = [t.text for t in root.iter(ns + 'text') if t.text in ('Norte', 'Centro', 'Sur')]
        self.assertEqual(legend, ['Norte', 'Centro', 'Sur'])
        heat = page.evaluate("() => MargenGraficas.legendOf(document.getElementById('cero')).map(l => l.name)")
        self.assertEqual(heat, ['Todas las celdas: 0 · sin variación', 'Sin dato ≠ 0'])
        # Abierto solo, sin hoja de estilos: pinta, y la leyenda queda dentro del lienzo.
        blank = page.context.new_page()
        blank.set_content(text.split('\n', 1)[1])
        geo = blank.evaluate("""() => { const s = document.querySelector('svg'), r = s.getBoundingClientRect();
          const names = [...s.querySelectorAll('text')].filter(t => ['Norte', 'Centro', 'Sur'].includes(t.textContent));
          return {inside: names.every(t => { const b = t.getBoundingClientRect(); return b.width > 0 && b.right <= r.right + 1 && b.bottom <= r.bottom + 1; }),
                  swatches: names.map(t => getComputedStyle(t.previousElementSibling).fill)}; }""")
        blank.close()
        self.assertTrue(geo['inside'], width)
        self.assertEqual(len(set(geo['swatches'])), 3, geo)
        self.assertFalse(any(re.match(r'none|rgba\(0, 0, 0, 0\)', c) for c in geo['swatches']), geo)


if __name__ == '__main__':
    unittest.main(verbosity=2)
