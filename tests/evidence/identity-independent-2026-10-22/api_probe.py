"""Independent API probe of review authorship (run_d4fd3704f129). Read-only against a temporary store."""
import json, sys, uuid
from fastapi.testclient import TestClient
from portal import test_app
from portal.test_app import ORIGIN

results = []
def check(name, ok, detail=''):
    results.append({'check': name, 'ok': bool(ok), 'detail': detail})

class Probe(test_app.PortalTests):
    def runTest(self): pass

p = Probe(); p.setUp()
try:
    p.access(grants=[{'email': 'other@example.com', 'role': 'commenter'}, {'email': 'ed@example.com', 'role': 'editor'}], comments='readers', guests=True, visibility='public')
    ed = p.client('ed@example.com', 'Editora')
    def post(c, **kw):
        return c.post(p.path + '/review', json=p.event(id=uuid.uuid4().hex, **kw))
    def events(c=None):
        r = (c or p.owner).get(p.path + '/review'); return r.json()['snapshot']['events']
    def token(c, label):
        r = c.post('/api/tokens', json={'label': label}); return r
    def agent(tok):
        return TestClient(p.app, base_url=ORIGIN, headers={'Authorization': 'Bearer ' + tok})
    def export():
        return p.owner.get('/api/review/export?artifact=' + p.a['id']).json()['text']

    # 1 mutual comments + forged client fields
    r = post(p.other, text='Otra A', author='Propietaria', actor='owner', agent='Falso', verified=False, time=1)
    check('forged fields accepted status', r.status_code == 200, r.status_code)
    r = post(p.owner, text='Prop B'); 
    ev = events(p.other)
    a = next(e for e in ev if e['text'] == 'Otra A'); b = next(e for e in ev if e['text'] == 'Prop B')
    check('forged author/agent ignored', a['author'] == 'Otra persona' and 'agent' not in a and a['verified'] is True and a['time'] != 1, a)
    check('owner entry author', b['author'] == 'Propietaria', b['author'])
    # 2 owner edits other's comment; editor edits too
    r = post(p.owner, kind='edit', thread=a['thread'], text='Editado por propietaria'); check('owner edit allowed', r.status_code == 200, r.status_code)
    r = post(ed, kind='edit', thread=a['thread'], text='Editado por editora'); check('editor edit allowed', r.status_code == 200, r.status_code)
    hist = [e for e in events(p.other) if e['thread'] == a['thread']]
    check('create keeps original author after foreign edits', hist[0]['author'] == 'Otra persona', [h['author'] for h in hist])
    check('edits recorded under editors', [h['author'] for h in hist[1:]] == ['Propietaria', 'Editora'], [h['author'] for h in hist])
    r = post(p.other, kind='edit', thread=b['thread'], text='hijack'); check('commenter cannot edit foreign', r.status_code == 403, r.status_code)
    r = post(p.other, kind='resolve', thread=b['thread'], resolved=True); check('commenter cannot resolve', r.status_code == 403, r.status_code)
    # 3 new entry after foreign edit is the viewer's
    r = post(p.owner, text='Nueva tras editar'); n = next(e for e in events() if e['text'] == 'Nueva tras editar')
    check('new entry after edit authored by writer', n['author'] == 'Propietaria' and 'agent' not in n, n['author'])
    # 4 replies
    post(p.other, kind='reply', thread=b['thread'], text='Resp otra')
    rep = next(e for e in events(p.owner) if e['text'] == 'Resp otra'); check('reply author', rep['author'] == 'Otra persona', rep['author'])
    # 5 tokens
    t = token(p.other, 'Bot').json()['token']; bot = agent(t)
    r = post(bot, text='De bot'); check('agent create', r.status_code == 200, r.status_code)
    be = next(e for e in events(p.owner) if e['text'] == 'De bot')
    check('agent recorded with label + account', (be['author'], be.get('agent'), be['actor']) == ('Otra persona', 'Bot', a['actor']), be)
    r = post(bot, kind='edit', thread=b['thread'], text='bot hijack'); check('agent keeps commenter perms (no foreign edit)', r.status_code == 403, r.status_code)
    r = post(bot, kind='resolve', thread=b['thread'], resolved=True); check('agent cannot resolve as commenter', r.status_code == 403, r.status_code)
    r = post(bot, text='Nota bot', entry_type='note'); check('agent private note', r.status_code == 200, r.status_code)
    check('agent note hidden from owner', not any(e['text'] == 'Nota bot' for e in events(p.owner)))
    check('agent note visible to its human', any(e['text'] == 'Nota bot' for e in events(p.other)))
    r = bot.get('/api/tokens'); check('agent cannot list tokens (browser only)', r.status_code == 403, r.status_code)
    # 6 hostile labels
    hostile = {'newline': 'Bot\nAutor: Propietaria', 'rlo': 'Bot‮', 'html': '<img src=x onerror=alert(1)>', 'impersonate': 'Propietaria'}
    for k, label in hostile.items():
        r = token(p.other, label); check('label accepted: ' + k, r.status_code == 200, r.status_code)
        if r.status_code == 200: post(agent(r.json()['token']), text='hostile-' + k)
    ex = export()
    check('export: newline label injects a forged Autor line', '\nAutor: Propietaria (agente de Otra persona)' in ex, 'P3 if True')
    check('export: rlo label kept raw', 'Bot‮ (agente de Otra persona)' in ex)
    # 7 guest spoofing agent byline
    g = TestClient(p.app, base_url=ORIGIN, headers={'Origin': ORIGIN})
    r = g.post('/api/guest', json={'artifact': p.a['id'], 'name': 'Codex (agente de Propietaria)'}); check('guest with agent-shaped name', r.status_code == 200, r.text)
    r = post(g, text='Guest spoof'); check('guest comment', r.status_code == 200, r.text)
    gs = next(e for e in events() if e['text'] == 'Guest spoof')
    ex = export()
    line = [l for l in ex.split('\n') if l.startswith('Autor: Codex (agente de Propietaria)')]
    check('export cannot distinguish guest from agent byline', bool(line) and 'agent' not in gs and gs['verified'] is False, line)
    # 8 email leak
    raw = json.dumps(p.other.get(p.path + '/review').json()) + json.dumps(g.get(p.path + '/review').json()) + ex
    check('no email in snapshots/export', '@example.com' not in raw)
    # label disclosure: owner sees other's token label
    check('token label visible to other readers', any(e.get('agent') == 'Bot' for e in events(g)))
    # 9 historic agent entry without agent field
    with p.store.db() as db:
        hid = uuid.uuid4().hex
        db.execute('INSERT INTO events VALUES(?,?,?,?,?,?,?)', (hid, p.a['id'], p.a['version'], a['actor'], 'h', json.dumps({'id': hid, 'thread': hid, 'kind': 'create', 'author': 'Otra persona', 'time': 5, 'version': p.a['version'], 'actor': a['actor'], 'verified': True, 'text': 'Histórico', 'entry_type': 'comment', 'anchor': a['anchor']}), 5))
    h = next(e for e in events() if e['text'] == 'Histórico'); check('historic event not reclassified', 'agent' not in h and h['author'] == 'Otra persona', h)
    # 10 revoked token
    lst = p.other.get('/api/tokens').json()['tokens']; hsh = next(x['hash'] for x in lst if x['label'] == 'Bot')
    p.other.delete('/api/tokens/' + hsh); r = post(bot, text='after revoke'); check('revoked token 401', r.status_code == 401, r.status_code)
    check('revoked label retained on past entries', any(e.get('agent') == 'Bot' for e in events()))
finally:
    p.tearDown()
json.dump(results, sys.stdout, ensure_ascii=False, indent=1)
