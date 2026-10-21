#!/usr/bin/env python3
"""Geometry regression: pip install playwright; playwright install chromium.
Run from any directory with Python containing Playwright. No network required.
"""
from pathlib import Path
import unittest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CONTENT = '''<aside id="card" class="pieza"><p>Decision</p><h3 id="card-heading">Evidence</h3></aside>
<section id="prose"><h2 id="heading">Product vision</h2><p id="paragraph">Readable prose.</p><h3 id="subheading">Next steps</h3><p>Supporting evidence.</p></section>
<figure class="ancho" id="wide"><div class="tabla-caja"><table><tr><td>Evidence</td></tr></table></div></figure>
<section class="custom" id="custom"><h2>Custom component</h2><p>Own layout.</p></section>'''

class EditorialFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()
    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def test_geometry(self):
        css = (ROOT/'packages/core/styles/artifact.css').read_text()
        flow = (ROOT/'packages/core/styles/editorial-flow.css').read_text()
        old_css = css.split('/* EDITORIAL FLOW START */')[0] + css.split('/* EDITORIAL FLOW END */')[1]
        for hosted in (False, True):
            # The portal adds the repair BEFORE an older document's stylesheet.
            styles = f'<style>{flow}</style><style>{old_css}</style>' if hosted else f'<style>{css}</style>'
            for wrapper in ('direct','article','page-article'):
                content = CONTENT if wrapper == 'direct' else '<article>'+CONTENT+'</article>'
                if wrapper == 'page-article': content = '<section class="pagina viva">'+content+'</section>'
                for width in (320,390,1024,1440):
                    with self.subTest(hosted=hosted,wrapper=wrapper,width=width):
                        page = self.browser.new_page(viewport={'width':width,'height':900})
                        main_class = 'hoja nota-estandar' + (' multipagina' if wrapper == 'page-article' else '')
                        page.set_content('<meta name="viewport" content="width=device-width">'+styles+'<main class="'+main_class+'">'+content+'</main>')
                        box = lambda selector: page.locator(selector).bounding_box()
                        card,head,para,sub = [box('#'+s) for s in ('card','heading','paragraph','subheading')]
                        self.assertGreaterEqual(head['y']-card['y']-card['height'],23)
                        self.assertGreaterEqual(para['y']-head['y']-head['height'],13)
                        self.assertGreaterEqual(sub['y']-para['y']-para['height'],35)
                        self.assertGreaterEqual(box('#card-heading')['y']-box('#card p')['y']-box('#card p')['height'],27)
                        self.assertGreaterEqual(head['x'],17)
                        self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
                        self.assertEqual(page.locator('#custom p').evaluate('e=>getComputedStyle(e).marginTop'),'0px')
                        if width>=1024: self.assertGreater(box('#wide')['width'],box('#prose')['width'])
                        page.emulate_media(media='print')
                        self.assertTrue(page.locator('#prose').is_visible())
                        page.close()
        page = self.browser.new_page()
        page.set_content(f'<style>{css}</style><main class="hoja nota-estandar" data-presentation><article>{CONTENT}</article></main>')
        self.assertEqual(page.locator('article').evaluate('e=>getComputedStyle(e).display'),'block')
        self.assertEqual(page.locator('#paragraph').evaluate('e=>getComputedStyle(e).marginTop'),'0px')
        page.close()

if __name__ == '__main__': unittest.main()
