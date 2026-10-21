"""Opt-in Chromium regression for bundled map previews and their opaque origins.

Run explicitly with: python scripts/test_developers_runtime_browser.py
Uses disposable FastAPI accounts/content; never contacts a deployed portal.
"""
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from playwright.sync_api import sync_playwright
from portal import test_developers as fixtures


class BundledMapPreviewBrowserTests(unittest.TestCase):
    def test_maps_render_inside_opaque_sandbox(self):
        fixture = fixtures.DevelopersTests()
        fixture.setUp()
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                try:
                    context = browser.new_context()

                    def proxy(route):
                        request = route.request
                        if request.url == 'https://portal.test/preview-harness':
                            route.fulfill(content_type='text/html', body='<html><body><h1>Parent</h1><iframe sandbox="allow-scripts" title="Map preview"></iframe></body></html>')
                            return
                        response = fixture.guest.request(request.method, request.url, follow_redirects=False)
                        headers = {key: value for key, value in response.headers.items()
                                   if key not in {'content-encoding', 'content-length'}}
                        route.fulfill(status=response.status_code, headers=headers, body=response.content)

                    context.route('https://portal.test/**', proxy)
                    page = context.new_page()
                    errors = []
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    page.goto('https://portal.test/preview-harness')
                    for slug, kind in (('route-map', 'rutas'), ('bubble-map', 'burbujas')):
                        with self.subTest(slug=slug):
                            page.locator('iframe').evaluate('(frame, url) => { frame.src = url; }', '/api/developers/items/component-' + slug + '/preview')
                            frame = page.frame_locator('iframe')
                            frame.locator('[data-analitica="' + kind + '"] svg').first.wait_for()
                            self.assertGreater(frame.locator('svg path').count(), 0)
                            self.assertEqual(frame.locator('[data-error-analitica]').count(), 0)
                            self.assertEqual(frame.locator('body').evaluate("() => { try { return parent.document.body.textContent; } catch (error) { return error.name; } }"), 'SecurityError')
                            self.assertEqual(page.locator('iframe').get_attribute('sandbox'), 'allow-scripts')
                    self.assertEqual(errors, [])
                finally:
                    browser.close()
        finally:
            fixture.tearDown()


if __name__ == '__main__':
    unittest.main()
