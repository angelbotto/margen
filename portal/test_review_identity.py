"""Review authorship is the server-recorded account, and an agent token never passes as its human."""
import unittest
import uuid
from fastapi.testclient import TestClient
from portal import test_app
from portal.test_app import ORIGIN


class ReviewIdentityTests(unittest.TestCase):
    client, access, event, tearDown = test_app.PortalTests.client, test_app.PortalTests.access, test_app.PortalTests.event, test_app.PortalTests.tearDown

    def setUp(self):
        test_app.PortalTests.setUp(self)
        self.access()
        token = self.owner.post('/api/tokens', json={'label': 'Codex'}).json()['token']
        self.agent = TestClient(self.app, base_url=ORIGIN, headers={'Authorization': 'Bearer ' + token})

    def post(self, client, **kw):
        return client.post(self.path + '/review', json=self.event(id=uuid.uuid4().hex, **kw))

    def events(self, client=None):
        return (client or self.owner).get(self.path + '/review').json()['snapshot']['events']

    def test_author_is_the_writer_for_every_viewer_and_ignores_client_fields(self):
        self.assertEqual(self.post(self.other, text='De la otra persona', author='Propietaria', actor='x', agent='Falso').status_code, 200)
        thread = self.events()[0]['thread']
        self.assertEqual(self.post(self.owner, kind='reply', thread=thread, text='Respuesta').status_code, 200)
        for viewer in (self.owner, self.other):
            create, reply = self.events(viewer)
            self.assertEqual((create['author'], reply['author']), ('Otra persona', 'Propietaria'))
            self.assertNotIn('agent', create)
        exported = self.owner.get('/api/review/export?artifact=' + self.a['id']).json()['text']
        self.assertIn('Autor: Otra persona', exported)
        self.assertIn('<respuesta autor="Propietaria">', exported)

    def test_agent_token_is_recorded_as_agent_with_its_account_permissions(self):
        self.assertEqual(self.post(self.agent, text='Del agente').status_code, 200)
        self.assertEqual(self.post(self.other, text='Humano').status_code, 200)
        agent_entry = next(e for e in self.events(self.other) if e['text'] == 'Del agente')
        self.assertEqual((agent_entry['author'], agent_entry['agent']), ('Propietaria', 'Codex'))
        exported = self.owner.get('/api/review/export?artifact=' + self.a['id']).json()['text']
        self.assertIn('Autor: Codex (agente de Propietaria)', exported)
        other_token = self.other.post('/api/tokens', json={'label': 'Bot'}).json()['token']
        other_agent = TestClient(self.app, base_url=ORIGIN, headers={'Authorization': 'Bearer ' + other_token})
        human = next(e for e in self.events() if e['text'] == 'Humano')['thread']
        # Delegated tokens share the account: attribution differs, permissions do not.
        self.assertEqual(self.post(other_agent, kind='edit', thread=human, text='Reescrito por el bot').status_code, 200)
        edit = next(e for e in self.events() if e['kind'] == 'edit')
        self.assertEqual((edit['author'], edit['agent']), ('Otra persona', 'Bot'))
        self.assertEqual(next(e for e in self.events() if e['thread'] == human and e['kind'] == 'create')['author'], 'Otra persona')

    def test_private_note_stays_with_its_author(self):
        self.assertEqual(self.post(self.other, text='Nota mía', entry_type='note').status_code, 200)
        self.assertEqual([e['text'] for e in self.events(self.other)], ['Nota mía'])
        self.assertEqual(self.events(self.owner), [])
        self.assertNotIn('Nota mía', self.owner.get('/api/review/export?artifact=' + self.a['id']).json()['text'])
