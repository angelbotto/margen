"""Editing a comment rewrites its author's voice: only that author may do it; moderation stays separate."""
import json
import unittest
import uuid
from fastapi.testclient import TestClient
from portal import test_app
from portal.test_app import ORIGIN


class EditAuthorshipTests(unittest.TestCase):
    client, access, event, tearDown = test_app.PortalTests.client, test_app.PortalTests.access, test_app.PortalTests.event, test_app.PortalTests.tearDown

    def setUp(self):
        test_app.PortalTests.setUp(self)
        self.editor = self.client('editor@example.com', 'Editora')
        self.access(grants=[{'email': 'other@example.com', 'role': 'commenter'}, {'email': 'editor@example.com', 'role': 'editor'}])

    def post(self, client, **kw):
        return client.post(self.path + '/review', json=self.event(id=uuid.uuid4().hex, **kw))

    def thread(self, client, text):
        self.assertEqual(self.post(client, text=text).status_code, 200)
        return next(e for e in self.events() if e['kind'] == 'create' and e['text'] == text)['thread']

    def events(self):
        return self.owner.get(self.path + '/review').json()['snapshot']['events']

    def projected(self, thread):
        from portal.app import threads
        return next(t for t in threads(self.events()) if t['thread'] == thread)

    def test_owner_and_editor_cannot_rewrite_another_author(self):
        thread = self.thread(self.other, 'Texto de la otra persona')
        for client in (self.owner, self.editor):
            self.assertEqual(self.post(client, kind='edit', thread=thread, text='Reescrito').status_code, 403)
        self.assertEqual(self.projected(thread)['text'], 'Texto de la otra persona')
        exported = self.owner.get('/api/review/export?artifact=' + self.a['id']).json()['text']
        self.assertNotIn('Reescrito', exported)

    def test_author_edits_own_comment_and_moderation_still_works(self):
        thread = self.thread(self.other, 'Primera versión')
        self.assertEqual(self.post(self.other, kind='edit', thread=thread, text='Versión corregida').status_code, 200)
        self.assertEqual(self.projected(thread)['text'], 'Versión corregida')
        own = self.thread(self.editor, 'De la editora')
        self.assertEqual(self.post(self.editor, kind='edit', thread=own, text='Editora corrige lo suyo').status_code, 200)
        for client in (self.owner, self.editor):
            self.assertEqual(self.post(client, kind='resolve', thread=thread, resolved=True).status_code, 200)
            self.assertEqual(self.post(client, kind='resolve', thread=thread, resolved=False).status_code, 200)
        self.assertEqual(self.post(self.other, kind='resolve', thread=thread, resolved=True).status_code, 403)
        self.assertEqual(self.post(self.owner, kind='delete', thread=thread).status_code, 200)

    def test_guests_edit_only_their_own_comments(self):
        self.access(visibility='unlisted', comments='readers', guests=True)
        second = TestClient(self.app, base_url=ORIGIN, headers={'Origin': ORIGIN})
        for client, name in ((self.guest, 'Invitada'), (second, 'Otro invitado')):
            self.assertEqual(client.post('/api/guest', json={'artifact': self.a['id'], 'name': name}).status_code, 200)
        thread = self.thread(self.guest, 'De la invitada')
        self.assertEqual(self.post(second, kind='edit', thread=thread, text='Suplantado').status_code, 403)
        self.assertEqual(self.post(self.owner, kind='edit', thread=thread, text='Suplantado').status_code, 403)
        self.assertEqual(self.post(self.guest, kind='edit', thread=thread, text='Invitada corrige').status_code, 200)
        self.assertEqual(self.projected(thread)['text'], 'Invitada corrige')

    def test_agent_token_of_the_same_account_still_edits_its_human(self):
        token = self.other.post('/api/tokens', json={'label': 'Bot'}).json()['token']
        agent = TestClient(self.app, base_url=ORIGIN, headers={'Authorization': 'Bearer ' + token})
        thread = self.thread(self.other, 'Humano')
        self.assertEqual(self.post(agent, kind='edit', thread=thread, text='Del bot de la misma cuenta').status_code, 200)
        owner_token = self.owner.post('/api/tokens', json={'label': 'Codex'}).json()['token']
        owner_agent = TestClient(self.app, base_url=ORIGIN, headers={'Authorization': 'Bearer ' + owner_token})
        self.assertEqual(self.post(owner_agent, kind='edit', thread=thread, text='Del agente de la dueña').status_code, 403)

    def test_recorded_foreign_edits_are_not_shown_as_the_author(self):
        # Events written before this fix stay in the history, but never replace the author's text.
        thread = self.thread(self.other, 'Original')
        owner = self.owner.get(self.path + '/review').json()['actor']
        with self.store.db() as db:
            event = {'id': 'legacy-edit', 'thread': thread, 'kind': 'edit', 'author': 'Propietaria', 'time': 9999999999999,
                     'version': self.a['version'], 'actor': owner, 'verified': True, 'text': 'Reescrito antes del arreglo'}
            db.execute('INSERT INTO events VALUES(?,?,?,?,?,?,?)', ('legacy-edit', self.a['id'], self.a['version'], owner, 'x', json.dumps(event), event['time']))
        self.assertIn('legacy-edit', [e['id'] for e in self.events()])
        self.assertEqual(self.projected(thread)['text'], 'Original')


if __name__ == '__main__':
    unittest.main()
