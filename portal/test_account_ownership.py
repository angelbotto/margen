"""Regression coverage for personal ownership versus administrator access."""
import tempfile
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from portal.app import COOKIE, create_app

ORIGIN = 'https://portal.test'
HTML = '<meta name="nota-documento" content="team-guide"><p>Team guide</p>'


class AccountOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        env = patch.dict('os.environ', {'BOTTIFACT_ADMIN_EMAILS': 'admin@example.com', 'BOTTIFACT_OWNER_ALIASES': 'admin@example.com,alias@example.com'})
        env.start()
        self.addCleanup(env.stop)
        self.app = create_app(self.tmp.name, origin=ORIGIN)
        self.store = self.app.state.store
        self.admin = self.client('admin@example.com')
        self.author = self.client('author@example.com')
        self.third = self.client('third@other.com')
        self.own = self.publish(self.admin, 'Admin document')
        self.other = self.publish(self.author, 'Team document')
        self.secret = self.publish(self.third, 'Private document')

    def client(self, email):
        user = self.store.user(email, email.split('@')[0])
        client = TestClient(self.app, base_url=ORIGIN, headers={'Origin': ORIGIN})
        client.cookies.set(COOKIE, self.store.session(user['id']))
        return client

    def publish(self, client, title):
        result = client.post('/api/artifacts', json={'title': title, 'html': HTML})
        self.assertEqual(result.status_code, 200, result.text)
        return result.json()['id']

    def ids(self, client, view):
        result = client.get('/api/artifacts?view=' + view).json()
        return {a['id'] for a in result['artifacts']}

    def test_admin_is_not_owner_in_personal_views_in_both_query_paths(self):
        for legacy in (False, True):
            with self.subTest(legacy_bookmarks=legacy):
                self.assertEqual(self.ids(self.admin, 'mine') & {self.own, self.other, self.secret}, {self.own})
                self.assertEqual(self.ids(self.admin, 'shared'), set())
                self.assertTrue({self.own, self.other, self.secret}.issubset(self.ids(self.admin, 'all')))
                self.assertEqual(self.ids(self.author, 'mine') & {self.own, self.other, self.secret}, {self.other})
                self.assertNotIn(self.secret, self.ids(self.author, 'all'))
                self.assertEqual(self.ids(self.client('alias@example.com'), 'mine'), self.ids(self.admin, 'mine'))
                # An unmigrated bookmark switches the server to its legacy query path.
                self.admin.post('/api/bookmarks', json={'title': 'Old link', 'url': 'https://example.com/old'})
                response = self.author.post('/api/bookmarks', json={'title': 'Other link', 'url': 'https://example.com/other'})
                self.assertEqual(response.status_code, 200)
                self.assertFalse(any(a['title'] == 'Other link' for a in self.admin.get('/api/artifacts?view=mine').json()['artifacts']))

    def test_domain_sharing_does_not_change_ownership_for_admin(self):
        response = self.author.put('/api/artifacts/' + self.other + '/access', json={'visibility': 'invited', 'domain_grants': [{'domain': 'example.com', 'role': 'commenter'}]})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.ids(self.admin, 'shared'), {self.other})
        self.assertEqual(self.ids(self.admin, 'mine'), {self.own})
        self.assertEqual(self.ids(self.third, 'shared'), set())
        result = self.admin.get('/api/artifacts?view=shared').json()['artifacts'][0]
        self.assertEqual(result['owner_email'], 'author@example.com')
        self.author.patch('/api/artifacts/' + self.other + '/organization', json={'archived': True})
        self.assertNotIn(self.other, self.ids(self.admin, 'archived'))
        self.assertIn(self.other, self.ids(self.author, 'archived'))

    def test_personal_token_cannot_choose_another_creator(self):
        token = self.author.post('/api/tokens', json={'label': 'My agent'}).json()['token']
        agent = TestClient(self.app, base_url=ORIGIN, headers={'Authorization': 'Bearer ' + token})
        author = self.author.get('/api/session').json()['user']
        admin = self.admin.get('/api/session').json()['user']
        created = agent.post('/api/artifacts', json={'title': 'Agent document', 'html': HTML, 'owner': admin['id'], 'email': admin['email']}).json()
        actual = agent.get('/api/artifacts/' + created['id']).json()
        self.assertEqual(actual['owner'], author['id'])
        self.assertNotIn(created['id'], self.ids(self.admin, 'mine'))
        self.assertEqual(agent.get('/api/artifacts/' + self.own).status_code, 404)
        self.assertEqual(author['emails'], ['author@example.com'])
        self.assertEqual(admin['emails'], ['admin@example.com', 'alias@example.com'])
        self.assertEqual(agent.post('/api/tokens', json={}).status_code, 403)
