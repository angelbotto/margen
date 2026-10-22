#!/usr/bin/env python3
"""Expected-behaviour tests for the defects in REVIEW-ATLAS-UI-RUNTIME.md. They fail until fixed.

  MARGEN_ROOT=<tree> MARGEN_BROWSER=chromium|webkit python test_defects.py
MARGEN_ROOT defaults to this worktree. Builds small documents through the shared contract; no network.
"""
import os, sys, tempfile, unittest
from html import escape
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
from probe_common import serve, offline
ROOT = Path(os.environ.get('MARGEN_ROOT') or Path(__file__).resolve().parents[2]); sys.path.insert(0, str(ROOT / 'scripts'))
from contract_artifact import build
ENGINE = os.environ.get('MARGEN_BROWSER', 'chromium')

def code(i, body, lang='javascript'):
    return f'<div class="codigo"><div class="cab"><span>{lang}</span></div><pre tabindex="0" aria-label="c{i}"><code id="c{i}" data-lenguaje="{lang}" data-lineas>{body}</code></pre></div>'

def heat(i, rows):
    head = '<tr><th scope="col">Día</th><th scope="col">A</th><th scope="col">B</th></tr>'
    body = ''.join(f'<tr><th scope="row">{r[0]}</th>' + ''.join(f'<td data-valor="{v}">{v}</td>' for v in r[1:]) + '</tr>' for r in rows)
    return f'<figure class="ancho" id="g{i}" data-grafica="calor" data-unidad="eventos"><details><summary>Datos</summary><div class="tabla-caja" tabindex="0" role="region" aria-label="t{i}"><table><caption>Calor {i}</caption><thead>{head}</thead><tbody>{body}</tbody></table></div></details></figure>'

def meta(i):
    return (f'<figure class="ancho" id="g{i}" data-grafica="meta" data-unidad="puntos"><details><summary>Datos</summary><div class="tabla-caja" tabindex="0" role="region" aria-label="t{i}"><table><caption>Meta</caption>'
            '<thead><tr><th scope="col">KPI</th><th scope="col">Valor</th><th scope="col">Meta</th></tr></thead><tbody><tr><th scope="row">NPS</th><td data-valor="-12">-12</td><td data-valor="40">40</td></tr></tbody></table></div></details></figure>')

sections = ''.join(f'<section class="seccion" id="s{i}"><h2>Sección {i}</h2>' + '<p>Texto de relleno para que la sección ocupe espacio vertical suficiente.</p>' * 12 + '</section>' for i in range(1, 6))
PAGE = (sections + code(1, escape('const a = 1;\nconst b = 2;\n'))
        + code(2, '<mark>// ver <a href="#s1">enlace</a></mark>\nx = 1;') + code(3, 'const <a href="#s1"><mark>marcado</mark></a> = 3;')
        + heat(1, [['L', 0, 0], ['M', 0, 0]]) + meta(2))

class Defects(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(); path = Path(cls.tmp.name) / 'doc.html'
        path.write_text(build('Defectos', [{'id': 'uno', 'titulo': 'Uno', 'html': PAGE}, {'id': 'dos', 'titulo': 'Dos', 'html': '<section class="seccion" id="z"><h2>Dos</h2><p>x</p></section>'}],
                              description='fixture', document_id='review-defects', format='chapters', theme='editorial', mode='dark', date='2026-10-22'))
        cls.server = serve(path); cls.url = cls.server.__enter__()
        cls.pw = sync_playwright().start(); cls.browser = getattr(cls.pw, ENGINE).launch()
        ctx = cls.browser.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce'); offline(ctx, [])
        cls.page = ctx.new_page(); cls.page.goto(cls.url + '#uno'); cls.page.wait_for_timeout(800)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop(); cls.server.__exit__(None, None, None); cls.tmp.cleanup()

    def test_code_link_inside_mark_survives(self):
        self.assertEqual(self.page.evaluate('[...document.querySelectorAll("#c2 a")].map(a => a.getAttribute("href"))'), ['#s1'])

    def test_code_mark_inside_link_survives(self):
        self.assertEqual(self.page.evaluate('document.querySelectorAll("#c3 mark").length'), 1)

    def test_code_trailing_newline_is_not_a_numbered_line(self):
        self.assertEqual(self.page.evaluate('document.querySelectorAll("#c1 .codigo-linea[data-numero]").length'), 2)

    def test_index_marks_clicked_section_current(self):
        p = self.page; p.set_viewport_size({'width': 1440, 'height': 900}); p.evaluate('scrollTo(0,0)'); p.wait_for_timeout(200)
        link = p.locator('.pagina.viva .indice a[href="#s3"]'); bb = link.bounding_box()
        p.mouse.click(bb['x'] + 10, bb['y'] + bb['height'] / 2); p.wait_for_timeout(500)
        self.assertEqual(p.evaluate('document.querySelector(".pagina.viva .indice a[aria-current]")?.getAttribute("href")'), '#s3')

    def test_index_marks_cold_anchor_current(self):
        p=self.browser.new_page(viewport={'width':1440,'height':900},reduced_motion='reduce');self.addCleanup(p.close)
        p.goto(self.url+'#s3')
        p.wait_for_function("document.querySelector('.pagina.viva .indice a[aria-current]')?.getAttribute('href')==='#s3'",timeout=5000)

    def test_index_marks_clicked_section_current_document(self):
        html=build('Documento',[{'id':'uno','titulo':'Uno','html':sections}],format='document',theme='editorial')
        p=self.browser.new_page(viewport={'width':1440,'height':900},reduced_motion='reduce');self.addCleanup(p.close)
        p.route('https://doc.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=html))
        p.goto('https://doc.test/')
        p.locator('.indice a[href="#s3"]').click()
        p.wait_for_function("document.querySelector('.indice a[aria-current]')?.getAttribute('href')==='#s3'",timeout=5000)

    def test_heatmap_all_zero_is_not_maximum_intensity(self):
        fills = self.page.evaluate('[...document.querySelectorAll("#g1 .mg-calor-celda")].map(r => r.style.fill)')
        self.assertTrue(fills, 'heatmap not drawn')
        self.assertNotIn('var(--calor-4)', fills)

    def test_heatmap_legend_does_not_invent_range(self):
        legend = self.page.evaluate('[...document.querySelectorAll("#g1 .calor-leyenda li")].map(l => l.textContent)')
        self.assertNotIn('0 a 1', legend)

    def test_bullet_negative_value_is_drawn_or_rejected(self):
        state = self.page.evaluate("""() => { const f = document.getElementById('g2'); if (f.querySelector('.grafica-error')) return 'rejected';
            const bar = f.querySelector('svg rect.grafica-barra'); return bar ? +bar.getAttribute('width') : null; }""")
        self.assertTrue(state == 'rejected' or (isinstance(state, (int, float)) and state > 1), f'negative value painted as {state}')

if __name__ == '__main__':
    unittest.main(verbosity=2)
