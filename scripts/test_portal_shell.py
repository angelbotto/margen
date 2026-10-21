"""Real portal shell browser checks through the disposable TestClient bridge."""
import unittest
from unittest.mock import patch
import test_community_marketplace as harness


class PortalShellTests(unittest.TestCase):
    setUp = harness.BrowserTests.setUp
    tearDown = harness.BrowserTests.tearDown
    page = harness.BrowserTests.page
    assert_layout = harness.BrowserTests.assert_layout

    def test_navigation_profile_mobile_focus_and_reader(self):
        page = self.page(self.fixture.owner)
        page.goto('https://portal.test/')
        page.locator('#profile-name', has_text='Propietaria').wait_for(state='attached')
        page.locator('#sidebar-toggle').click()
        self.assertIn('sidebar-collapsed', page.locator('body').get_attribute('class'))
        page.reload()
        page.locator('#profile-name', has_text='Propietaria').wait_for(state='attached')
        self.assertIn('sidebar-collapsed', page.locator('body').get_attribute('class'))
        page.locator('#profile-trigger').click()
        self.assertTrue(page.locator('#theme').evaluate('(e)=>e===document.activeElement'))
        page.keyboard.press('End')
        self.assertTrue(page.locator('#logout').evaluate('(e)=>e===document.activeElement'))
        page.keyboard.press('Escape')
        self.assertTrue(page.locator('#profile-trigger').evaluate('(e)=>e===document.activeElement'))
        page.locator('#sidebar-toggle').click()
        page.locator('[data-view=components]').click()
        page.locator('.component-index').wait_for()
        self.assertEqual(page.locator('#shell-current').inner_text(), 'Componentes')
        self.assert_layout(page)
        page.locator('#sidebar-toggle').click()
        self.assertTrue(page.locator('#main').evaluate('(e)=>e.inert'))
        self.assertEqual(page.locator('#portal-sidebar').get_attribute('aria-modal'), 'true')
        self.assertTrue(page.locator('#sidebar-close').evaluate('(e)=>e===document.activeElement'))
        page.keyboard.press('Shift+Tab')
        self.assertTrue(page.locator('.sidebar-brand .brand').evaluate('(e)=>e===document.activeElement'))
        page.keyboard.press('Shift+Tab')
        self.assertTrue(page.locator('#profile-trigger').evaluate('(e)=>e===document.activeElement'))
        page.keyboard.press('Tab')
        self.assertTrue(page.locator('.sidebar-brand .brand').evaluate('(e)=>e===document.activeElement'))
        page.keyboard.press('Tab')
        self.assertTrue(page.locator('#sidebar-close').evaluate('(e)=>e===document.activeElement'))
        page.locator('#profile-trigger').click()
        page.keyboard.press('Escape')
        self.assertEqual(page.locator('#portal-sidebar').get_attribute('aria-modal'), 'true')
        page.keyboard.press('Escape')
        self.assertFalse(page.locator('#main').evaluate('(e)=>e.inert'))
        self.assertTrue(page.locator('#sidebar-toggle').evaluate('(e)=>e===document.activeElement'))
        page.locator('#sidebar-toggle').click()
        page.locator('[data-view=themes]').click()
        page.locator('.developers-themes').wait_for()
        self.assertFalse(page.locator('#main').evaluate('(e)=>e.inert'))
        page.goto('https://portal.test/a/' + self.fixture.a['id'])
        frame = page.frame_locator('#artifact-frame')
        frame.locator('.bottifact-toolbar').wait_for()
        self.assertFalse(page.locator('#portal-sidebar').is_visible())
        self.assertFalse(page.locator('.shell-topbar').is_visible())
        self.assertEqual(page.locator('#artifact-frame').bounding_box()['width'], 300)
        frame.get_by_label('Compartir', exact=True).click()
        frame.get_by_role('button', name='Gestionar artefacto', exact=True).click()
        page.locator('#owner-panel').wait_for()
        self.assertFalse(self.errors, self.errors)

    def test_anonymous_sections_and_legacy_link(self):
        page = self.page(self.fixture.guest)
        for section in ('themes', 'components', 'developers'):
            self.assertEqual(self.fixture.guest.get('/?view=' + section, follow_redirects=False).status_code, 200)
            page.goto('https://portal.test/?view=' + section)
            page.locator('.developers-' + section).wait_for()
            page.locator('.developers-intro').wait_for()
            self.assert_layout(page)
        page.goto('https://portal.test/?view=developers&item=theme-kaira')
        page.locator('.developer-dialog[open]').wait_for()
        self.assertFalse(self.errors, self.errors)
        self.assertEqual(self.fixture.guest.get('/', follow_redirects=False).status_code, 303)

    def test_admin_summary_lazy_performance_retry_and_logout(self):
        with patch.dict('os.environ', {'BOTTIFACT_ADMIN_EMAILS': 'owner@example.com'}):
            page = self.page(self.fixture.owner)
            calls = []
            page.on('request', lambda request: calls.append(request.url))
            page.route('**/api/admin', lambda route: route.fulfill(status=503, content_type='application/json', body='{"detail":"Unavailable"}'), times=1)
            page.goto('https://portal.test/?view=admin')
            page.get_by_role('button', name='Volver a intentar', exact=True).click()
            page.locator('.admin-metrics').wait_for()
            self.assertEqual(page.locator('.admin-metrics>div').count(), 5)
            self.assertIn('Incluye invitados', page.locator('.admin-metrics').inner_text())
            self.assertIn('No son visitantes únicos', page.locator('.admin-distribution').inner_text())
            self.assertEqual(len([url for url in calls if '/api/operations/performance' in url]), 0)
            self.assert_layout(page)
            page.route('**/api/operations/performance', lambda route: route.fulfill(status=503, content_type='application/json', body='{"detail":"Unavailable"}'), times=1)
            page.locator('.admin-performance summary').click()
            page.locator('.performance-error').wait_for()
            page.locator('.admin-performance summary').click()
            page.locator('.admin-performance summary').click()
            page.locator('.admin-performance table').wait_for()
            self.assertEqual(len([url for url in calls if '/api/operations/performance' in url]), 2)
            self.assert_layout(page)
            page.locator('#sidebar-toggle').click()
            page.locator('#profile-trigger').click()
            page.locator('#logout').click()
            page.wait_for_url('**/login')
            self.assertFalse(self.errors, self.errors)


if __name__ == '__main__':
    unittest.main()
