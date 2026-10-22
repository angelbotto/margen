#!/usr/bin/env python3
"""Hidden chapters stay idle: no Three.js request or 3D work until shown; offline keeps a legible fallback.

MARGEN_BROWSER=webkit runs the same checks in WebKit. Three.js is served from the pinned, SRI-checked
cache of test_developers_runtime_browser.py; that part is skipped when it cannot be obtained.
"""
import os, sys, unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts')); sys.path.insert(0, str(ROOT))
from contract_artifact import build, recipe, THREE
from test_developers_runtime_browser import pinned_three

ENGINE = os.environ.get('MARGEN_BROWSER', 'chromium')
FIRST = '<section class="prosa" id="inicio-texto"><h2>Inicio</h2><p>Sin 3D en esta página.</p></section>'
SECOND = '<section class="prosa" id="espacial"><h2>Espacial</h2></section>' + recipe('xyz')
HTML = build('Diferido', [{'id': 'uno', 'titulo': 'Uno', 'html': FIRST}, {'id': 'dos', 'titulo': 'Dos', 'html': SECOND}])


class DeferredRuntime(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.pw = sync_playwright().start(); cls.browser = getattr(cls.pw, ENGINE).launch(); cls.three = pinned_three()

 @classmethod
 def tearDownClass(cls):
  cls.browser.close(); cls.pw.stop()

 def page(self, online):
  context = self.browser.new_context(viewport={'width': 1280, 'height': 900})
  self.addCleanup(context.close)
  requests, errors = [], []

  def route(r):
   url = r.request.url
   if url.startswith('https://margen.test/'):
    return r.fulfill(status=200, content_type='text/html', body=HTML)
   requests.append(url)
   if online and url == THREE:
    return r.fulfill(status=200, content_type='application/javascript', body=self.three, headers={'access-control-allow-origin': '*'})
   r.abort()
  context.route('**/*', route)
  page = context.new_page()
  page.on('pageerror', lambda e: errors.append(str(e)))
  page.goto('https://margen.test/diferido')
  page.wait_for_timeout(400)
  return page, requests, errors

 def test_offline_hidden_scene_waits_then_falls_back(self):
  page, requests, errors = self.page(False)
  self.assertEqual(requests, [])
  self.assertEqual(page.locator('script[src]').count(), 0)
  page.locator('[data-ir="dos"]').click()
  page.wait_for_function('document.querySelector("[data-escena]") && !document.querySelector("[data-escena]").dataset.tres')
  self.assertEqual(requests, [THREE])
  error = page.locator('[data-escena] .grafica-error, [data-escena] [class*=error]').first
  self.assertIn('no está disponible', error.text_content())
  self.assertTrue(page.locator('[data-escena] table').first.is_visible() or page.locator('[data-escena] details').count() > 0)
  self.assertEqual(errors, [])

 def test_online_scene_loads_three_once_when_shown(self):
  if not self.three:
   self.skipTest('pinned three.js unavailable')
  page, requests, errors = self.page(True)
  self.assertEqual(requests, [])
  page.locator('[data-ir="dos"]').click()
  page.wait_for_function('window.THREE && !document.querySelector("[data-escena]").dataset.tres', timeout=15000)
  self.assertEqual(requests, [THREE])
  self.assertEqual(page.locator('script[src]').evaluate_all('s=>s.map(x=>[x.integrity.slice(0,7),x.crossOrigin])'), [['sha512-', 'anonymous']])
  self.assertGreater(page.locator('[data-escena] canvas').count(), 0)
  page.locator('[data-ir="uno"]').click(); page.locator('[data-ir="dos"]').click()
  self.assertEqual(requests, [THREE])
  self.assertEqual(errors, [])


if __name__ == '__main__':
 unittest.main()
