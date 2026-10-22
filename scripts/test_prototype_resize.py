#!/usr/bin/env python3
"""Exercise hidden-to-visible prototype sizing in Chromium and WebKit, offline."""
from pathlib import Path
import unittest

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'packages/core/components/prototype.js').read_text()
RECIPE = (ROOT / 'packages/core/recipes/prototype/example.html').read_text()
CSS = """+:root { --sans: sans-serif; --serif: serif; }
* { box-sizing: border-box; }
[hidden] { display: none !important; }
body { margin: 24px; }
figure { margin: 0; min-width: 0; }
.visor-caja { width: 100%; overflow: auto; }
.visor-lienzo { border: 1px solid; }
.visor-fuente[data-oculta] { display: none; }
"""


class PrototypeResize(unittest.TestCase):
    def test_reveal_resize_controls_and_destroy(self):
        with sync_playwright() as pw:
            for engine in ('chromium', 'webkit'):
                with self.subTest(engine=engine):
                    browser = getattr(pw, engine).launch()
                    try:
                        page = browser.new_page(viewport={'width': 1440, 'height': 900})
                        page.route('**/*', lambda r: r.abort())
                        errors = []
                        page.on('pageerror', lambda e: errors.append(str(e)))
                        page.set_content('<style>' + CSS + '</style><section hidden id="page">' + RECIPE + '</section>')
                        page.add_script_tag(content=SOURCE)
                        for width in (1440, 390, 320):
                            page.set_viewport_size({'width': width, 'height': 900})
                            page.evaluate('document.querySelector("#page").hidden=false')
                            page.wait_for_function('document.querySelector(".visor-marco").offsetHeight > 100')
                            page.evaluate("window.v=NotaVisores.get(document.querySelector('[data-visor]'));v.setWidth('390');v.setAspect('9/16')")
                            self.assertAlmostEqual(page.locator('.visor-lienzo').evaluate('e=>parseFloat(e.style.height)'), 390 * 16 / 9, delta=.1)
                            page.locator('[data-girar-visor]').click()
                            self.assertAlmostEqual(page.locator('.visor-lienzo').evaluate('e=>parseFloat(e.style.height)'), 390, delta=.1)
                            page.locator('[data-ajustar-visor]').click()
                            self.assertTrue(page.evaluate('v.host.getBoundingClientRect().width<=v.box.clientWidth+.1'))
                            page.evaluate("v.setAspect('auto');v.setWidth('390');v.fit=false;v.layout()")
                            page.evaluate('document.querySelector("#page").hidden=true')
                            page.wait_for_timeout(40)
                        page.evaluate('document.querySelector("#page").hidden=false')
                        page.wait_for_timeout(80)
                        # Destroy immediately after geometry changes, while a resize
                        # delivery or scheduled layout may still be queued.
                        page.evaluate("v.box.style.width='280px';v.destroy()")
                        page.wait_for_timeout(80)
                        self.assertEqual(page.locator('.visor-lienzo').count(), 0)
                        self.assertTrue(page.locator('.visor-fuente').is_visible())
                        self.assertEqual(errors, [])
                    finally:
                        browser.close()


if __name__ == '__main__':
    unittest.main()
