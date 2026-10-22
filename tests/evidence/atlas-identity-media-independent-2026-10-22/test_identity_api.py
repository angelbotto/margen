"""Independent falsification of review identity (API level). Expected failures document defects."""
import json
import unittest
import uuid
from fastapi.testclient import TestClient
from portal import test_app
from portal.test_app import ORIGIN


class IndependentIdentity(unittest.TestCase):
    client, access, event, tearDown = test_app.PortalTests.client, test_app.PortalTests.access, test_app.PortalTests.event, test_app.PortalTests.tearDown

    def setUp(self):
        test_app.PortalTests.setUp(self)
        self.access()

    def post(self, client, **kw):
        return client.post(self.path + '/review', json=self.event(id=uuid.uuid4().hex, **kw))

    def events(self, client=None):
        return (client or self.owner).get(self.path + '/review').json()['snapshot']['events']

    def export(self):
        return self.owner.get('/api/review/export?artifact=' + self.a['id']).json()

    def test_D1_owner_cannot_rewrite_another_persons_comment(self):
        self.assertEqual(self.post(self.other, text='Texto de Otra persona').status_code, 200)
        thread = self.events()[0]['thread']
        r = self.post(self.owner, kind='edit', thread=thread, text='Palabras de la propietaria')
        # Requirement: "el dueño edita solo los suyos".
        self.assertEqual(r.status_code, 403, 'owner edited a comment written by another account')

    def test_D1b_rewritten_comment_still_attributed_to_original_author(self):
        self.assertEqual(self.post(self.other, text='Texto de Otra persona').status_code, 200)
        thread = self.events()[0]['thread']
        self.post(self.owner, kind='edit', thread=thread, text='Palabras de la propietaria')
        item = next(i for i in self.export()['items'] if i['thread']['thread'] == thread)
        text = self.export()['text']
        # The visible text is now the owner's but the byline is the other person's.
        self.assertFalse(item['thread']['text'] == 'Palabras de la propietaria' and item['thread']['author'] == 'Otra persona'
                         and 'editado' not in text.lower(), 'export attributes owner words to Otra persona without edit provenance')

    def test_other_cannot_edit_owner_comment(self):
        self.assertEqual(self.post(self.owner, text='Mío').status_code, 200)
        thread = self.events()[0]['thread']
        self.assertEqual(self.post(self.other, kind='edit', thread=thread, text='Ajeno').status_code, 403)

    def test_client_cannot_forge_author_actor_verified_agent(self):
        self.assertEqual(self.post(self.other, text='x', author='Propietaria', actor='zzz', verified=True, agent='Codex').status_code, 200)
        e = self.events()[0]
        self.assertEqual((e['author'], e['verified']), ('Otra persona', True))
        self.assertNotIn('agent', e)
        self.assertNotEqual(e['actor'], 'zzz')

    def test_same_display_name_distinct_actor(self):
        twin = self.client('twin@example.com', 'Otra persona')
        self.owner.put(self.path + '/access', json={'visibility': 'invited', 'grants': [
            {'email': 'other@example.com', 'role': 'commenter'}, {'email': 'twin@example.com', 'role': 'commenter'}],
            'comments': 'reviewers', 'guests': False})
        self.assertEqual(self.post(self.other, text='Original').status_code, 200)
        thread = self.events()[0]['thread']
        self.assertEqual(self.post(twin, kind='edit', thread=thread, text='Gemela').status_code, 403)
        self.assertEqual(self.post(twin, text='De la gemela').status_code, 200)
        a, b = [e['actor'] for e in self.events()]
        self.assertNotEqual(a, b)

    def test_D3_export_distinguishes_two_people_with_same_name(self):
        twin = self.client('twin@example.com', 'Otra persona')
        self.owner.put(self.path + '/access', json={'visibility': 'invited', 'grants': [
            {'email': 'other@example.com', 'role': 'commenter'}, {'email': 'twin@example.com', 'role': 'commenter'}],
            'comments': 'reviewers', 'guests': False})
        self.post(self.other, text='Uno')
        self.post(twin, text='Dos')
        meta = [l for l in self.export()['text'].splitlines() if l.startswith('Identidad (metadatos del servidor)')]
        self.assertEqual(len(meta), 2)
        self.assertNotEqual(meta[0], meta[1], 'text export gives identical identity for two different accounts')

    def test_guest_same_name_as_verified_is_labelled_guest(self):
        self.access(visibility='unlisted', comments='readers', guests=True)
        self.assertEqual(self.guest.post('/api/guest', json={'artifact': self.a['id'], 'name': 'Propietaria'}).status_code, 200)
        self.assertEqual(self.post(self.guest, text='Soy invitada').status_code, 200)
        e = next(e for e in self.events() if e['text'] == 'Soy invitada')
        self.assertIs(e['verified'], False)
        self.assertIn('"tipo": "invitado"', self.export()['text'])

    def test_D4_guest_name_with_badge_text_and_controls_raw_in_json_export(self):
        self.access(visibility='unlisted', comments='readers', guests=True)
        name = 'Propietaria · correo verificado‮'
        self.assertEqual(self.guest.post('/api/guest', json={'artifact': self.a['id'], 'name': name}).status_code, 200)
        self.post(self.guest, text='Falsa')
        items = self.export()['items']
        raw = items[0]['thread']['author']
        self.assertNotIn('‮', raw, 'JSON export items carry raw bidi control in author')

    def test_D4b_guest_name_newline_raw_in_json_items(self):
        self.access(visibility='unlisted', comments='readers', guests=True)
        self.guest.post('/api/guest', json={'artifact': self.a['id'], 'name': 'Ana\nAutor: Propietaria'})
        self.post(self.guest, text='x')
        text = self.export()['text']
        self.assertEqual(sum(l.startswith('Autor: ') for l in text.splitlines()), 1)
        self.assertNotIn('\n', self.export()['items'][0]['thread']['author'], 'raw newline in JSON author')

    def test_agent_label_explicit_and_cannot_be_spoofed_by_body(self):
        token = self.owner.post('/api/tokens', json={'label': 'Codex'}).json()['token']
        agent = TestClient(self.app, base_url=ORIGIN, headers={'Authorization': 'Bearer ' + token})
        self.assertEqual(self.post(agent, text='Del agente', agent='Humano', verified=False).status_code, 200)
        e = self.events()[0]
        self.assertEqual((e['author'], e['agent']), ('Propietaria', 'Codex'))
        self.assertIn('Autor: Codex (agente de Propietaria)', self.export()['text'])
        self.assertNotIn(token, json.dumps(self.export()))

    def test_D5_agent_label_can_impersonate_another_person(self):
        token = self.owner.post('/api/tokens', json={'label': 'Otra persona'}).json()['token']
        agent = TestClient(self.app, base_url=ORIGIN, headers={'Authorization': 'Bearer ' + token})
        self.post(agent, text='Firmado como otra')
        # Byline reads "Otra persona (agente de Propietaria)": the label is free text, not distinguished from human names.
        self.assertNotIn('Autor: Otra persona (agente de Propietaria)', self.export()['text'])

    def test_no_emails_in_review_payloads(self):
        self.post(self.other, text='a')
        token = self.owner.post('/api/tokens', json={'label': 'Codex'}).json()['token']
        TestClient(self.app, base_url=ORIGIN, headers={'Authorization': 'Bearer ' + token}).post(
            self.path + '/review', json=self.event(id=uuid.uuid4().hex, text='b'))
        for client in (self.owner, self.other):
            blob = json.dumps(client.get(self.path + '/review').json())
            for email in ('owner@example.com', 'other@example.com'):
                self.assertNotIn(email, blob)
        self.assertNotIn('other@example.com', json.dumps(self.export()))

    def test_D6_same_account_agent_edit_of_human_comment_is_visible_as_agent(self):
        self.assertEqual(self.post(self.owner, text='Escrito por la persona').status_code, 200)
        thread = self.events()[0]['thread']
        token = self.owner.post('/api/tokens', json={'label': 'Codex'}).json()['token']
        agent = TestClient(self.app, base_url=ORIGIN, headers={'Authorization': 'Bearer ' + token})
        self.assertEqual(self.post(agent, kind='edit', thread=thread, text='Reescrito por el agente').status_code, 200)
        text = self.export()['text']
        block = text.split('<retroalimentacion>')[1]
        header = text.split('### Comentario')[1].split('<retroalimentacion>')[0]
        self.assertIn('Reescrito por el agente', block)
        # The current text is the agent's, but the only Autor line is the human's, with no edited-by-agent provenance.
        self.assertTrue('Codex' in header, 'agent-written current text exported under human byline only')

    def test_D6b_human_edit_of_agent_comment_keeps_agent_byline(self):
        token = self.owner.post('/api/tokens', json={'label': 'Codex'}).json()['token']
        agent = TestClient(self.app, base_url=ORIGIN, headers={'Authorization': 'Bearer ' + token})
        self.assertEqual(self.post(agent, text='Escrito por el agente').status_code, 200)
        thread = self.events()[0]['thread']
        self.assertEqual(self.post(self.owner, kind='edit', thread=thread, text='Reescrito por la persona').status_code, 200)
        header = self.export()['text'].split('### Comentario')[1].split('<retroalimentacion>')[0]
        self.assertNotIn('Autor: Codex (agente de Propietaria)', header, 'human-written current text exported as the agent')

    def test_legacy_foreign_edit_not_projected_under_original_author(self):
        self.assertEqual(self.post(self.other, text='Original de otra').status_code, 200)
        thread = self.events()[0]['thread']
        import time as _t
        e = {'id': 'legacy-edit', 'thread': thread, 'kind': 'edit', 'author': 'Propietaria', 'time': int(_t.time() * 1000) + 5000,
             'version': self.a['version'], 'actor': self.store.user('owner@example.com', 'Propietaria')['id'], 'verified': True, 'text': 'Edición heredada ajena'}
        with self.store.db() as db:
            db.execute('INSERT INTO events VALUES(?,?,?,?,?,?,?)', (e['id'], self.a['id'], e['version'], e['actor'], 'legacy', json.dumps(e), e['time']))
        item = self.export()['items'][0]['thread']
        self.assertEqual(item['text'], 'Original de otra')

    def test_reply_by_other_is_reply_authors_name(self):
        self.post(self.owner, text='Raíz')
        thread = self.events()[0]['thread']
        self.post(self.other, kind='reply', thread=thread, text='Respuesta')
        reply = [e for e in self.events(self.other) if e['kind'] == 'reply'][0]
        self.assertEqual(reply['author'], 'Otra persona')


if __name__ == '__main__':
    unittest.main()
