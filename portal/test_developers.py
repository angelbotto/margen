import copy
import json
import unittest
from unittest.mock import patch

from portal import test_app as fixtures
from portal.developers import bundled, COLORS


class DevelopersTests(unittest.TestCase):
    setUp = fixtures.PortalTests.setUp
    tearDown = fixtures.PortalTests.tearDown
    client = fixtures.PortalTests.client

    def package(self, kind='theme'):
        item = copy.deepcopy(bundled()['theme-kaira' if kind == 'theme' else 'component-bar-chart'])
        return {key: value for key, value in dict(item, schema=1, slug='sample-piece', version='1.0.0').items()
                if key in {'schema', 'slug', 'version', 'kind', 'title', 'description', 'license', 'source_url', 'content'}}

    def submit(self, package=None, publication='private', client=None):
        response = (client or self.owner).post('/api/developers/submissions', json={
            'package': package or self.package(), 'publication': publication,
            'rights_accepted': True, 'public_listing_accepted': True})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()['id']

    def publication(self, key, action, revision=1, client=None):
        return (client or self.owner).put('/api/developers/submissions/' + key + '/publication', json={
            'publication': action, 'revision': revision, 'rights_accepted': True, 'public_listing_accepted': True})

    def test_private_to_shared_to_catalog_and_revocation(self):
        key = self.submit()
        path = '/api/developers/items/' + key
        for suffix in ('', '/download', '/preview'):
            self.assertEqual(self.other.get(path + suffix).status_code, 404)
            self.assertEqual(self.guest.get(path + suffix).status_code, 404)
            self.assertEqual(self.owner.get(path + suffix).status_code, 200)
        self.assertEqual(self.publication(key, 'shared', client=self.other).status_code, 404)
        self.assertEqual(self.publication(key, 'shared').status_code, 200)
        self.assertEqual(self.guest.get(path).status_code, 200)
        self.assertNotIn(key, [i['id'] for i in self.guest.get('/api/developers/catalog').json()['items']])
        self.assertEqual(self.publication(key, 'review', revision=1).status_code, 409)
        self.assertEqual(self.publication(key, 'review', revision=2).status_code, 200)
        review = {'status': 'approved', 'revision': 3, 'note': ''}
        route = '/api/developers/submissions/' + key + '/review'
        self.assertEqual(self.other.put(route, json=review).status_code, 403)
        with patch.dict('os.environ', {'BOTTIFACT_ADMIN_EMAILS': 'other@example.com'}):
            self.assertEqual(self.other.put(route, json=review).status_code, 200)
            self.assertEqual(self.other.put(route, json=review).status_code, 409)
        item = next(i for i in self.guest.get('/api/developers/catalog').json()['items'] if i['id'] == key)
        self.assertEqual(item['author'], 'Propietaria')
        self.assertNotIn('content', item)
        self.assertNotIn('owner', item)
        self.assertEqual(self.publication(key, 'private', revision=4).status_code, 200)
        self.assertEqual(self.guest.get(path).status_code, 404)
        with patch.dict('os.environ', {'BOTTIFACT_ADMIN_EMAILS': 'other@example.com'}):
            self.assertEqual(self.other.put(route, json={**review, 'revision': 5}).status_code, 409)

    def test_catalog_favorites_and_anonymous_write_guards(self):
        response = self.guest.get('/api/developers/catalog').json()
        self.assertEqual(len(response['items']), len(bundled()))
        self.assertFalse(response['admin'])
        self.assertFalse(response['can_submit'])
        url = '/api/developers/items/theme-kaira/favorite'
        self.assertEqual(self.guest.put(url, json={'favorite': True}).status_code, 401)
        for _ in range(2):
            item = self.owner.put(url, json={'favorite': True}).json()
            self.assertEqual(item['favorites'], 1)
            self.assertTrue(item['favorite'])
        other = self.other.get('/api/developers/items/theme-kaira').json()
        self.assertFalse(other['favorite'])
        self.assertEqual(other['favorites'], 1)
        self.assertEqual(self.owner.put(url, json={'favorite': False}).json()['favorites'], 0)
        self.assertEqual(self.other.get('/api/developers/submissions?scope=review').status_code, 403)

    def test_validation_and_immutable_versions(self):
        self.submit()
        body = {'package': self.package(), 'publication': 'shared', 'rights_accepted': True, 'public_listing_accepted': True}
        self.assertEqual(self.owner.post('/api/developers/submissions', json=body).status_code, 409)
        self.assertEqual(self.owner.post('/api/developers/submissions', json={**body, 'rights_accepted': False}).status_code, 422)
        for key, bad in [('kind', 'javascript'), ('slug', '../escape'), ('version', True), ('source_url', 'javascript:alert(1)'),
                         ('license', 'invented'), ('typography', {'heading': 'url(https://example.com)', 'body': 'geist'}), ('status', 'approved')]:
            with self.subTest(key=key):
                self.assertEqual(self.owner.post('/api/developers/submissions', json={**body, 'package': {**self.package(), key: bad}}).status_code, 422)
        package = self.package(); package['content']['light']['papel'] = 'red; background:url(https://example.com)'
        self.assertEqual(self.owner.post('/api/developers/submissions', json={**body, 'package': package}).status_code, 422)
        package = self.package('component'); package['content'] = 'x' * 160000
        self.assertEqual(self.owner.post('/api/developers/submissions', json={**body, 'package': package}).status_code, 413)

    def test_preview_cannot_execute_or_contact_network(self):
        package = self.package('component')
        package['content'] = '<svg onload="alert(1)"><rect width="4"/></svg><script>alert(2)</script><iframe src="https://bad.test"></iframe><a href="https://bad.test">link</a>'
        key = self.submit(package)
        response = self.owner.get('/api/developers/items/' + key + '/preview')
        self.assertEqual(response.status_code, 200)
        self.assertIn("script-src 'none'", response.headers['content-security-policy'])
        self.assertIn("default-src 'none'", response.headers['content-security-policy'])
        self.assertNotIn('<script', response.text)
        self.assertNotIn('<iframe', response.text)
        self.assertNotIn('onload=', response.text)
        download = self.owner.get('/api/developers/items/' + key + '/download')
        self.assertIn('attachment', download.headers['content-disposition'])
        self.assertIn('<script>', download.json()['content'])

    def test_bundled_runtime_is_hashed_and_community_cannot_opt_in(self):
        import base64
        import hashlib
        import re
        response = self.guest.get('/api/developers/items/component-line-chart/preview')
        policy = response.headers['content-security-policy']
        self.assertIn('sandbox allow-scripts;', policy)
        self.assertNotIn('allow-same-origin', policy)
        self.assertNotIn("script-src 'unsafe-inline'", policy)
        self.assertIn("default-src 'none'", policy)
        self.assertIn('data-grafica="lineas"', response.text)
        scripts = re.findall(r'<script>(.*?)</script>', response.text, re.S)
        self.assertEqual(len(scripts), 1)
        self.assertIn('window.NotaGraficas', scripts[0])
        digest = base64.b64encode(hashlib.sha256(scripts[0].encode()).digest()).decode()
        self.assertIn("'sha256-" + digest + "'", policy)
        package = self.package('component')
        package['content'] = bundled()['component-line-chart']['content']
        key = self.submit(package)
        community = self.owner.get('/api/developers/items/' + key + '/preview')
        self.assertIn("script-src 'none'", community.headers['content-security-policy'])
        self.assertNotIn('<script>', community.text)
        package['preview_runtime'] = ['charts.js']
        self.assertEqual(self.owner.post('/api/developers/submissions', json={'package': package}).status_code, 422)

    def test_bundled_map_previews_load_geography_before_analytics(self):
        import re
        for slug in ('route-map', 'bubble-map'):
            with self.subTest(slug=slug):
                item = bundled()['component-' + slug]
                self.assertEqual(item['preview_runtime'], ['geography.js', 'analytics.js'])
                response = self.guest.get('/api/developers/items/' + item['id'] + '/preview')
                scripts = re.findall(r'<script>(.*?)</script>', response.text, re.S)
                self.assertEqual(len(scripts), 2)
                self.assertIn('window.NotaGeografia=', scripts[0])
                self.assertIn('window.NotaAnalitica=', scripts[1])
                self.assertNotIn('allow-same-origin', response.headers['content-security-policy'])
        for item in bundled().values():
            if item['kind'] == 'component' and 'packages/core/components/analytics.js' not in item.get('dependencies', []):
                self.assertNotIn('geography.js', item['preview_runtime'])

    def test_theme_applies_as_draft_preserving_identity_and_access(self):
        key = self.submit()
        url = '/api/developers/items/' + key + '/use'
        before = self.owner.get(self.path).json()
        body = {'artifact': self.a['id'], 'expected_current': before['current_version']}
        self.assertEqual(self.other.post(url, json=body).status_code, 404)
        result = self.owner.post(url, json=body)
        self.assertEqual(result.status_code, 200, result.text)
        result = result.json()
        self.assertEqual(result['id'], self.a['id'])
        self.assertEqual(result['state'], 'draft')
        after = self.owner.get(self.path).json()
        self.assertEqual(after['current_version'], before['current_version'])
        self.assertEqual(after['visibility'], before['visibility'])
        self.assertEqual(after['document_id'], before['document_id'])
        rendered = self.owner.get(self.path + '/render?version=' + result['version']).text
        self.assertIn('data-margen-community-attachment', rendered)
        self.assertIn('data-margen-community-theme', rendered)
        self.assertIn('#fbf4e9', rendered)
        self.assertEqual(self.owner.post(url, json={**body, 'expected_current': 'stale'}).status_code, 409)
        self.assertEqual(self.other.get(self.path + '/render?version=' + result['version']).status_code, 404)

    def test_no_code_component_becomes_private_artifact_without_pr(self):
        result = self.owner.post('/api/developers/visual-component', json={'kind': 'diagram', 'title': 'Proceso', 'text': 'Investigar\nProbar\nDecidir <script>alert(1)</script>'})
        self.assertEqual(result.status_code, 200, result.text)
        package = self.package('component'); package['content'] = result.json()['content']
        self.assertNotIn('<script>', package['content'])
        key = self.submit(package, 'shared')
        result = self.other.post('/api/developers/items/' + key + '/use', json={})
        self.assertEqual(result.status_code, 200, result.text)
        data = result.json()
        self.assertEqual(data['visibility'], 'private')
        rendered = self.other.get('/api/artifacts/' + data['id'] + '/render').text
        self.assertIn('Investigar', rendered)
        self.assertIn('viewBox=', rendered)
        self.assertNotIn('id="community-slot"', rendered)
        self.assertEqual(self.owner.get('/api/artifacts/' + data['id']).status_code, 404)

    def test_visual_preview_fonts_and_contrast_palettes(self):
        package = self.package()
        package['typography'] = {'heading': 'source-serif', 'body': 'manrope'}
        result = self.owner.post('/api/developers/preview?mode=dark', json={'package': package})
        self.assertEqual(result.status_code, 200, result.text)
        preview = self.owner.get(result.json()['url'])
        self.assertEqual(preview.status_code, 200)
        self.assertEqual(self.other.get(result.json()['url']).status_code, 404)
        self.assertEqual(self.guest.get(result.json()['url']).status_code, 401)
        self.assertIn('Source Serif 4', preview.text)
        self.assertIn('Manrope', preview.text)
        self.assertIn('data-color-mode="dark"', preview.text)
        self.assertIn('Content-Security-Policy', preview.text)
        self.assertEqual(self.guest.post('/api/developers/preview', json={'package': package}).status_code, 401)

    def test_unsaved_preview_bound_expiry_and_public_shell(self):
        urls = [self.owner.post('/api/developers/preview', json={'package': self.package()}).json()['url'] for _ in range(5)]
        self.assertEqual(self.owner.get(urls[0]).status_code, 404)
        self.assertEqual(self.owner.get(urls[-1]).status_code, 200)
        from portal import developers
        now = developers.time.monotonic()
        with patch.object(developers.time, 'monotonic', return_value=now + 301):
            self.assertEqual(self.owner.get(urls[-1]).status_code, 404)
        self.assertEqual(self.guest.get('/?view=developers', follow_redirects=False).status_code, 200)
        self.assertEqual(self.guest.get('/', follow_redirects=False).status_code, 303)
        self.assertEqual(self.guest.get('/api/artifacts').status_code, 401)

    def test_download_roundtrip_and_all_builtin_theme_palettes(self):
        for item in bundled().values():
            if item['kind'] != 'theme':
                continue
            with self.subTest(theme=item['id']):
                package = self.guest.get('/api/developers/items/' + item['id'] + '/download').json()
                preview = self.owner.post('/api/developers/preview', json={'package': package})
                self.assertEqual(preview.status_code, 200, preview.text)
                self.assertIn(item['author'], package['credits'])
        key = self.submit(publication='shared')
        package = self.guest.get('/api/developers/items/' + key + '/download').json()
        self.assertIn('Propietaria', package['credits'])
        clone = self.submit(package, client=self.other)
        self.assertEqual(self.other.get('/api/developers/items/' + clone).json()['content'], package['content'])

    def test_visual_design_is_retained_and_server_generated(self):
        package = self.package('component')
        package.update(design={'kind': 'diagram', 'text': 'First step\nSecond step'},
                       content='<script>arbitrary()</script>', credits='Original author', license='Apache-2.0')
        key = self.submit(package)
        stored = self.owner.get('/api/developers/items/' + key).json()
        self.assertEqual(stored['design'], package['design'])
        self.assertEqual(stored['license'], 'Apache-2.0')
        self.assertEqual(stored['credits'], 'Original author')
        self.assertIn('First step', stored['content'])
        self.assertNotIn('<script>', stored['content'])

    def test_svg_mutation_is_removed_when_component_becomes_artifact(self):
        package = self.package('component')
        package['content'] = '<svg><style><img src=x onerror="window.reviewExecuted=1"></style></svg><p>Retained content</p>'
        key = self.submit(package, 'shared')
        created = self.other.post('/api/developers/items/' + key + '/use', json={}).json()
        rendered = self.other.get('/api/artifacts/' + created['id'] + '/render').text
        self.assertNotIn('reviewExecuted', rendered)
        self.assertIn('Retained content', rendered)


if __name__ == '__main__':
    unittest.main()
