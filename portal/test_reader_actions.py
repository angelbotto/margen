"""Guardar y «me gusta»: persistencia por cuenta, idempotencia, revocación, CSRF e invitados."""
import inspect
import tempfile
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from portal.app import COOKIE, create_app, permissions, artifact_for, payload
from portal import reader_actions

ORIGIN = 'https://portal.test'
HTML = '<meta name="nota-documento" content="lectura"><p>Lectura</p>'
ACT = {'X-Margen-Reader-Action': '1'}


def closure(app, path, name):
    route = next(r for r in app.routes if getattr(r, 'path', '') == path)
    return inspect.getclosurevars(route.endpoint).nonlocals[name]


def mounted(data):
    app = create_app(data, origin=ORIGIN)
    # Mientras la raíz no lo monte en create_app, la prueba lo monta con los mismos who/account.
    if not any(getattr(r, 'path', '') == '/api/reader/saved' for r in app.routes):
        reader_actions.mount(app, app.state.store, closure(app, '/api/session', 'who'),
                             closure(app, '/api/tokens', 'account'), payload, artifact_for, permissions)
    return app


class ReaderActionsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        env = patch.dict('os.environ', {'BOTTIFACT_ADMIN_EMAILS': 'admin@example.com', 'BOTTIFACT_OWNER_ALIASES': ''})
        env.start()
        self.addCleanup(env.stop)
        self.app = mounted(self.tmp.name)
        self.store = self.app.state.store
        self.author = self.client('author@example.com')
        self.reader = self.client('reader@example.com')
        self.second = self.client('second@example.com')
        self.doc = self.publish(self.author, 'Informe')
        self.share(['reader@example.com', 'second@example.com'])

    def client(self, email):
        user = self.store.user(email, email.split('@')[0])
        client = TestClient(self.app, base_url=ORIGIN, headers={'Origin': ORIGIN})
        client.cookies.set(COOKIE, self.store.session(user['id']))
        return client

    def publish(self, client, title):
        result = client.post('/api/artifacts', json={'title': title, 'html': HTML})
        self.assertEqual(result.status_code, 200, result.text)
        return result.json()['id']

    def share(self, emails, visibility='invited'):
        grants = [{'email': e, 'role': 'viewer'} for e in emails]
        response = self.author.put('/api/artifacts/' + self.doc + '/access', json={'visibility': visibility, 'grants': grants})
        self.assertEqual(response.status_code, 200, response.text)

    def act(self, client, body, aid=None, headers=ACT):
        return client.put('/api/artifacts/' + (aid or self.doc) + '/reader-actions', json=body, headers=headers)

    def state(self, client, aid=None):
        return client.get('/api/artifacts/' + (aid or self.doc) + '/reader-actions')

    def saved_ids(self, client):
        return [a['id'] for a in client.get('/api/reader/saved').json()['artifacts']]

    def test_save_and_like_persist_per_account_and_survive_a_new_app(self):
        self.assertEqual(self.act(self.reader, {'saved': True, 'liked': True}).status_code, 200)
        self.assertEqual(self.act(self.second, {'liked': True}).status_code, 200)
        restarted = mounted(self.tmp.name)
        reader = TestClient(restarted, base_url=ORIGIN, headers={'Origin': ORIGIN})
        reader.cookies.set(COOKIE, self.reader.cookies.get(COOKIE))
        second = TestClient(restarted, base_url=ORIGIN, headers={'Origin': ORIGIN})
        second.cookies.set(COOKIE, self.second.cookies.get(COOKIE))
        mine = reader.get('/api/artifacts/' + self.doc + '/reader-actions').json()
        theirs = second.get('/api/artifacts/' + self.doc + '/reader-actions').json()
        self.assertEqual((mine['saved'], mine['liked'], mine['likes']), (True, True, 2))
        self.assertEqual((theirs['saved'], theirs['liked'], theirs['likes']), (False, True, 2))
        self.assertEqual(self.saved_ids(reader), [self.doc])
        self.assertEqual(self.saved_ids(second), [])

    def test_desired_state_is_idempotent(self):
        for _ in range(3):
            response = self.act(self.reader, {'saved': True, 'liked': True})
            self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['likes'], 1)
        self.assertEqual(self.saved_ids(self.reader), [self.doc])
        for _ in range(2):
            response = self.act(self.reader, {'liked': False})
        self.assertEqual((response.json()['liked'], response.json()['saved'], response.json()['likes']), (False, True, 0))
        self.assertEqual(self.act(self.reader, {'saved': False}).json()['saved'], False)
        self.assertEqual(self.saved_ids(self.reader), [])

    def test_revoked_access_hides_saved_count_and_blocks_actions(self):
        self.act(self.reader, {'saved': True, 'liked': True})
        self.act(self.second, {'liked': True})
        self.share(['second@example.com'])
        self.assertEqual(self.saved_ids(self.reader), [])
        self.assertEqual(self.state(self.reader).status_code, 404)
        self.assertEqual(self.act(self.reader, {'liked': True}).status_code, 404)
        # El conteo sólo incluye cuentas que todavía pueden leer.
        self.assertEqual(self.state(self.second).json()['likes'], 1)
        # Restaurar el acceso devuelve el guardado sin pedirlo de nuevo.
        self.share(['reader@example.com', 'second@example.com'])
        self.assertEqual(self.saved_ids(self.reader), [self.doc])
        self.assertEqual(self.state(self.second).json()['likes'], 2)

    def test_mutations_require_portal_origin_header_and_browser_session(self):
        self.assertEqual(self.act(self.reader, {'saved': True}, headers={}).status_code, 403)
        forged = TestClient(self.app, base_url=ORIGIN, headers={'Origin': 'https://evil.test'})
        forged.cookies.set(COOKIE, self.reader.cookies.get(COOKIE))
        self.assertEqual(self.act(forged, {'saved': True}).status_code, 403)
        opaque = TestClient(self.app, base_url=ORIGIN, headers={'Origin': 'null'})
        opaque.cookies.set(COOKIE, self.reader.cookies.get(COOKIE))
        self.assertEqual(self.act(opaque, {'liked': True}).status_code, 403)
        token = self.reader.post('/api/tokens', json={'label': 'Agente'}).json()['token']
        agent = TestClient(self.app, base_url=ORIGIN)
        self.assertEqual(self.act(agent, {'saved': True}, headers={**ACT, 'Authorization': 'Bearer ' + token}).status_code, 403)
        self.assertEqual(self.saved_ids(self.reader), [])
        self.assertEqual(self.state(self.reader).json()['likes'], 0)

    def test_body_cannot_choose_another_account_or_unknown_fields(self):
        for body in ({'saved': True, 'user': 'x'}, {'saved': True, 'account': 'second@example.com'}, {'saved': 'yes'}, {}, []):
            self.assertEqual(self.act(self.reader, body).status_code, 422, body)
        self.assertEqual(self.saved_ids(self.reader), [])
        self.assertEqual(self.saved_ids(self.second), [])

    def test_guest_and_anonymous_read_counts_without_acting(self):
        self.share([], visibility='unlisted')
        self.author.put('/api/artifacts/' + self.doc + '/access', json={'visibility': 'unlisted', 'comments': 'readers', 'guests': True, 'grants': []})
        self.act(self.reader, {'liked': True})
        anonymous = TestClient(self.app, base_url=ORIGIN, headers={'Origin': ORIGIN})
        state = self.state(anonymous).json()
        self.assertEqual({k: state[k] for k in ('saved', 'liked', 'likes', 'signed_in', 'can_act')},
                         {'saved': False, 'liked': False, 'likes': 1, 'signed_in': False, 'can_act': False})
        self.assertEqual(self.act(anonymous, {'saved': True}).status_code, 401)
        guest = TestClient(self.app, base_url=ORIGIN, headers={'Origin': ORIGIN})
        self.assertEqual(guest.post('/api/guest', json={'artifact': self.doc, 'name': 'Visita'}).status_code, 200)
        self.assertFalse(self.state(guest).json()['can_act'])
        self.assertEqual(self.act(guest, {'liked': True}).status_code, 401)
        self.assertEqual(guest.get('/api/reader/saved').status_code, 401)
        self.assertEqual(self.state(anonymous).json()['likes'], 1)

    def test_state_never_lists_who_liked_and_private_documents_stay_hidden(self):
        self.act(self.reader, {'liked': True, 'saved': True})
        state = self.state(self.author).json()
        self.assertEqual(set(state), {'artifact', 'saved', 'liked', 'likes', 'signed_in', 'can_act', 'saved_path'})
        self.assertNotIn('reader@example.com', str(state))
        outsider = self.client('outsider@other.test')
        self.assertEqual(self.state(outsider).status_code, 404)
        self.assertEqual(self.act(outsider, {'liked': True}).status_code, 404)
        self.assertEqual(self.state(TestClient(self.app, base_url=ORIGIN)).status_code, 404)

    def test_alias_merge_counts_one_person_and_preserves_distinct_saves(self):
        self.act(self.reader, {'saved': True, 'liked': True})
        self.act(self.second, {'saved': True, 'liked': True})
        later = self.publish(self.author, 'Otro informe')
        self.author.put('/api/artifacts/' + later + '/access', json={'visibility': 'public'})
        self.act(self.second, {'saved': True, 'liked': True}, aid=later)
        with patch.dict('os.environ', {'BOTTIFACT_OWNER_ALIASES': 'reader@example.com,second@example.com'}):
            self.store.merge_admin_aliases()
            self.store.merge_admin_aliases()  # migration is idempotent
            self.assertEqual(self.reader.get('/api/artifacts/' + self.doc + '/reader-actions').json()['likes'], 1)
            self.assertEqual(set(self.saved_ids(self.reader)), {self.doc, later})
            self.assertEqual(self.second.get('/api/artifacts/' + later + '/reader-actions').json()['liked'], True)
            self.act(self.reader, {'liked': False})
            self.assertEqual(self.reader.get('/api/artifacts/' + self.doc + '/reader-actions').json()['likes'], 0)

    def test_saved_list_is_recent_first_and_offers_a_return_path(self):
        later = self.publish(self.author, 'Segundo')
        self.author.put('/api/artifacts/' + later + '/access', json={'visibility': 'invited', 'grants': [{'email': 'reader@example.com', 'role': 'viewer'}]})
        self.act(self.reader, {'saved': True})
        response = self.act(self.reader, {'saved': True}, aid=later)
        with self.store.db() as db:
            db.execute('UPDATE reader_saves SET created=created-60 WHERE artifact=?', (self.doc,))
        self.assertEqual(response.json()['saved_path'], '/?view=saved')
        listed = self.reader.get('/api/reader/saved').json()
        self.assertEqual([a['id'] for a in listed['artifacts']], [later, self.doc])
        self.assertEqual(listed['artifacts'][0]['url'], '/a/' + later)
        self.assertEqual(listed['artifacts'][0]['title'], 'Segundo')


if __name__ == '__main__':
    unittest.main()
