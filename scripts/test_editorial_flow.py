#!/usr/bin/env python3
"""Geometry regression: pip install playwright; playwright install chromium.
Run from any directory with Python containing Playwright. No network required.
"""
from pathlib import Path
import unittest
import json
import sys
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
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


    def test_all_recipes_have_heading_separation(self):
        css = (ROOT/'packages/core/styles/artifact.css').read_text()
        flow = (ROOT/'packages/core/styles/editorial-flow.css').read_text()
        old = css.split('/* EDITORIAL FLOW START */')[0] + css.split('/* EDITORIAL FLOW END */')[1]
        page = self.browser.new_page()
        page.route('http**/*', lambda route: route.abort())
        scan = """()=>[...document.querySelectorAll('main h2,main h3,main h4')].flatMap(h=>{
          const r=h.getBoundingClientRect(); if(!r.height)return [];
          return [h.previousElementSibling,h.nextElementSibling].flatMap((n,i)=>{
            if(!n)return [];const q=n.getBoundingClientRect();if(!q.height)return [];
            const gap=i?q.top-r.bottom:r.top-q.bottom;
            return gap>=-0.5&&gap<1?[{heading:h.textContent.slice(0,60),gap,boundary:i?'after':'before'}]:[];
          });
        })"""
        for hosted in (False,True):
            styles = f'<style>{flow}</style><style>{old}</style>' if hosted else f'<style>{css}</style>'
            for width in (320,390,1440):
                page.set_viewport_size({'width':width,'height':900})
                for path in sorted((ROOT/'packages/core/recipes').glob('*/example.html')):
                    with self.subTest(hosted=hosted,width=width,recipe=path.parent.name):
                        # Legacy roots are intentionally included: theme/format must not gate rhythm.
                        page.set_content(styles+'<main class="hoja">'+path.read_text()+'</main>')
                        self.assertEqual(page.evaluate(scan),[])
        page.close()

    def test_nested_prose_themes_and_protected_components(self):
        css = (ROOT/'packages/core/styles/artifact.css').read_text()
        page = self.browser.new_page()
        prose = '<p class="ceja">Context</p><h3>Heading</h3><p>Evidence.</p><p>Details.</p><h4>Next step</h4><p>Action.</p>'
        content = ('<section class="ancho"><h3>Overview</h3><p>Introduction.</p></section>'
                   '<section><div>'+prose+'</div></section><section class="prosa custom"><div>'+prose+'</div></section>'
                   '<aside class="pieza"><div>'+prose+'</div></aside><section><ol><li>'+prose+'</li></ol></section>')
        families=json.loads((ROOT/'VERSION.json').read_text())['temas']
        for family in families:
            for mode in ('light','dark'):
                for width in (320,390,1440):
                    with self.subTest(family=family,mode=mode,width=width):
                        page.set_viewport_size({'width':width,'height':900})
                        page.set_content(f'<style>{css}</style><main class="hoja">{content}</main>')
                        page.evaluate('([family,mode])=>{document.documentElement.dataset.theme=mode==="light"?family+"-light":family;document.documentElement.dataset.colorMode=mode}',[family,mode])
                        gaps=page.evaluate("""()=>[...document.querySelectorAll('h3+p,h4+p')].map(p=>p.getBoundingClientRect().top-p.previousElementSibling.getBoundingClientRect().bottom)""")
                        self.assertTrue(all(gap>=13 for gap in gaps),gaps)
                        self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
        # Preserve intentional custom flow and exclude data/UI canvases.
        protected = ['<section class="prosa" data-ritmo="propio"><div>'+prose+'</div></section>',
                     '<section data-explorador><div>'+prose+'</div></section>',
                     '<section data-visor><div>'+prose+'</div></section>',
                     '<nav><div>'+prose+'</div></nav>']
        flow=(ROOT/'packages/core/styles/editorial-flow.css').read_text()
        old=css.split('/* EDITORIAL FLOW START */')[0]+css.split('/* EDITORIAL FLOW END */')[1]
        for content in protected:
            measures=[]
            for style in (old,css):
                page.set_content(f'<style>{style}</style><main class="hoja">{content}</main>')
                measures.append(page.locator('h3+p').evaluate('e=>getComputedStyle(e).marginTop'))
            self.assertEqual(measures[0],measures[1])
        for recipe in ('outlined-cards','before-after'):
            path=ROOT/'packages/core/recipes'/recipe/'example.html'
            if not path.exists():continue
            measures=[]
            for style in (old,css):
                page.set_content(f'<style>{style}</style><main class="hoja">'+path.read_text()+'</main>')
                measures.append(page.evaluate("""()=>[...document.querySelectorAll('.card-editorial,.cards-trazadas>a,.antes-despues>div')].map(e=>({gap:getComputedStyle(e).gap,margins:[...e.children].map(c=>getComputedStyle(c).marginTop)}))"""))
            self.assertEqual(measures[0],measures[1])
        page.close()


    def test_review_regressions(self):
        css=(ROOT/'packages/core/styles/artifact.css').read_text()
        page=self.browser.new_page(viewport={'width':320,'height':900})
        def load(content):page.set_content(f'<style>{css}</style><main class="hoja nota-estandar">{content}</main>')
        load('<section><h2>Evidence</h2><p>'+'X'*100+'</p></section>')
        self.assertEqual(page.evaluate('document.documentElement.scrollWidth'),320)
        load('<article class="prosa"><h2>Evidence</h2><p>Text</p></article>')
        self.assertEqual(page.locator('h2+p').evaluate('e=>getComputedStyle(e).marginTop'),'14px')
        load('<section class="kept"><article><h3>Evidence</h3><p>Text</p></article></section>')
        self.assertEqual(page.locator('h3+p').evaluate('e=>getComputedStyle(e).marginTop'),'0px')
        self.assertEqual(page.locator('article').evaluate('e=>getComputedStyle(e).rowGap'),'12px')
        load('<section><div style="display:grid;gap:12px"><h3>Evidence</h3><p>Text</p></div></section>')
        self.assertEqual(page.locator('h3+p').evaluate('e=>getComputedStyle(e).marginTop'),'0px')
        load('<article data-ritmo="propio"><section class="prosa"><h2>Evidence</h2><p>Text</p></section></article>')
        for selector in ('article','section'):
            self.assertEqual(page.locator(selector).evaluate('e=>getComputedStyle(e).display'),'block')
        self.assertEqual(page.locator('h2+p').evaluate('e=>getComputedStyle(e).marginTop'),'0px')
        page.close()


    def test_hosted_upgrade_replaces_old_flow(self):
        from portal.reader_style import without_embedded_flow
        css=(ROOT/'packages/core/styles/artifact.css').read_text()
        old=css.split('/* EDITORIAL FLOW START */')[0]+'/* EDITORIAL FLOW START */'+(ROOT/'tests/fixtures/editorial-flow-v1.css').read_text()+'/* EDITORIAL FLOW END */'+css.split('/* EDITORIAL FLOW END */')[1]
        content='<main class="hoja nota-estandar"><article data-ritmo="propio"><section class="prosa"><h3>Own layout</h3><p>Text</p></section></article><section style="display:grid;gap:12px"><h3>Own grid</h3><p>Text</p></section></main>'
        page=self.browser.new_page()
        page.set_content('<style>'+(ROOT/'portal/static/review-additions.css').read_text()+'</style>'+without_embedded_flow('<style>'+old+'</style>'+content))
        self.assertEqual(page.locator('article').evaluate('e=>getComputedStyle(e).display'),'block')
        self.assertEqual(page.locator('.prosa').evaluate('e=>getComputedStyle(e).display'),'block')
        self.assertEqual(page.locator('h3+p').evaluate_all('es=>es.map(e=>getComputedStyle(e).marginTop)'),['0px','0px'])
        page.close()

if __name__ == '__main__': unittest.main()
