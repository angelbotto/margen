"""Two (three) real sessions against the portal shell: create_app + static assets behind a Playwright route.
Owner «Ángel Botto», commenters «Alice Ruiz» and «Bob Pérez», plus an agent token of the owner.
usage: harness.py REPO OUTDIR LABEL   Disposable store; nothing touches production."""
import json, os, sys, tempfile, uuid
from pathlib import Path
REPO, OUT, LABEL = Path(sys.argv[1]).resolve(), Path(sys.argv[2]), sys.argv[3]
sys.path.insert(0, str(REPO))
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
from portal.app import create_app, COOKIE

ORIGIN = 'https://portal.test'
OUT.mkdir(parents=True, exist_ok=True)
tmp = tempfile.TemporaryDirectory()
app = create_app(tmp.name, origin=ORIGIN, issuer='https://identity.test', audience='our-app')
store = app.state.store
people = {}
for key, email, name in [('owner', 'angel@owner.test', 'Ángel Botto'), ('alice', 'alice@team.test', 'Alice Ruiz'), ('bob', 'bob@team.test', 'Bob Pérez')]:
    u = store.user(email, name); c = TestClient(app, base_url=ORIGIN, headers={'Origin': ORIGIN}); c.cookies.set(COOKIE, store.session(u['id']))
    people[key] = (u, c)
owner = people['owner'][1]
HTML = (REPO / 'examples/generated/collaborative.html').read_text()
pub = owner.post('/api/artifacts', json={'title': 'Identidad', 'html': HTML}); pub.raise_for_status(); AID, VERSION = pub.json()['id'], pub.json()['version']
owner.put('/api/artifacts/' + AID + '/access', json={'visibility': 'invited', 'grants': [
    {'email': 'alice@team.test', 'role': 'commenter'}, {'email': 'bob@team.test', 'role': 'commenter'}]}).raise_for_status()
results = {'label': LABEL, 'checks': []}
def check(name, ok, detail=None):
    results['checks'].append({'name': name, 'ok': bool(ok), 'detail': detail}); print(('PASS ' if ok else 'FAIL ') + name, '' if ok else json.dumps(detail, ensure_ascii=False)[:400], flush=True)

def context(browser, key):
    client = people[key][1]
    ctx = browser.new_context(viewport={'width': 1440, 'height': 900})
    def proxy(route):
        req = route.request
        headers = {k: v for k, v in req.headers.items() if k not in {'host', 'cookie', 'accept-encoding'}}
        r = client.request(req.method, req.url, headers=headers, content=req.post_data_buffer, follow_redirects=False)
        route.fulfill(status=r.status_code, headers={k: v for k, v in r.headers.items() if k not in {'content-encoding', 'content-length'}}, body=r.content)
    ctx.route(ORIGIN + '/**', proxy)
    ctx.route('https://fonts.googleapis.com/**', lambda r: r.abort())
    pg = ctx.new_page(); pg.errors = []; pg.on('pageerror', lambda e: pg.errors.append(str(e)))
    return ctx, pg

def frame(pg):
    pg.wait_for_function("()=>[...document.querySelectorAll('iframe')].some(f=>f.src.includes('/render'))", timeout=15000)
    for _ in range(100):
        fr = next((f for f in pg.frames if '/render' in f.url), None)
        if fr:
            try:
                if fr.evaluate("()=>!!document.querySelector('.revision-barra')&&!!window.BottifactReviewBridge"):
                    fr.wait_for_timeout(1200); return fr
            except Exception: pass
        pg.wait_for_timeout(150)
    raise RuntimeError('frame not ready')

def open_doc(pg):
    pg.goto(ORIGIN + '/a/' + AID); return frame(pg)

def comment(fr, text, note=False):
    fr.evaluate("""([text,note])=>{const bar=document.querySelector('.revision-barra');(note?bar.querySelector('button[aria-label="Añadir nota privada"]'):bar.querySelector('[data-revision-modo]')).click();
      const p=[...document.querySelectorAll('main p')].find(p=>p.getClientRects().length&&p.textContent.trim().length>40);p.click();
      const i=document.querySelector('[data-revision-texto]');i.value=text;i.dispatchEvent(new Event('input',{bubbles:true}));}""", [text, note])
    composer = fr.evaluate("()=>({name:document.querySelector('.review-composer-name')?.textContent,avatar:document.querySelector('.review-composer-avatar')?.textContent})")
    fr.evaluate("()=>document.querySelector('[data-revision-guardar]').click()"); fr.wait_for_timeout(900)
    return composer

LIST = """()=>{document.querySelector('.revision-barra [data-revision-lista]').click();const f=document.querySelector('.revision-utilidades select');f.value='all';f.dispatchEvent(new Event('change'));
  const rows=[...document.querySelectorAll('[data-revision-notas] > li')].map(li=>({text:li.querySelector('.revision-hilo, p:not(.revision-meta)')?.textContent||'',meta:li.querySelector('.revision-meta')?.textContent||'',replies:[...li.querySelectorAll('.revision-respuestas li')].map(x=>x.textContent),actions:[...li.querySelectorAll('button')].map(b=>b.textContent),all:li.textContent}));
  document.querySelector('[data-revision-cerrar]')?.click();return rows;}"""
PIN = """(needle)=>{const markers=[...document.querySelectorAll('.revision-marca')];const panel=document.querySelector('[data-revision-panel]');const editor=document.querySelector('[data-revision-editor]');
  for(const m of markers){if(!(m.getAttribute('aria-label')||'').includes(needle)&&m.hidden)continue;}
  const rev=NotaRevision?.get?.(document.querySelector('[data-revision]'));
  const m=markers.find(m=>!m.hidden)||markers[0];if(!m)return null;m.click();
  const out={editorOpen:editor.open,panelOpen:panel.open,composerName:document.querySelector('.review-composer-name')?.textContent,composerAvatar:document.querySelector('.review-composer-avatar')?.textContent,composerText:document.querySelector('[data-revision-texto]')?.value,composerTitle:editor.querySelector('h2')?.textContent};
  editor.open&&editor.close();panel.open&&panel.close();return out;}"""
EDIT = """(needle)=>{document.querySelector('.revision-barra [data-revision-lista]').click();const f=document.querySelector('.revision-utilidades select');f.value='all';f.dispatchEvent(new Event('change'));
  const li=[...document.querySelectorAll('[data-revision-notas] > li')].find(li=>li.textContent.includes(needle));const b=[...li.querySelectorAll('button')].find(b=>b.textContent==='Editar');if(!b)return null;b.click();
  const editor=document.querySelector('[data-revision-editor]');const out={editorOpen:editor.open,composerName:document.querySelector('.review-composer-name')?.textContent,composerAvatar:document.querySelector('.review-composer-avatar')?.textContent,composerText:document.querySelector('[data-revision-texto]')?.value};editor.close();return out;}"""
REPLY = """(text)=>{document.querySelector('.revision-barra [data-revision-lista]').click();const f=document.querySelector('.revision-utilidades select');f.value='all';f.dispatchEvent(new Event('change'));const i=document.querySelector('.revision-responder input');i.value=text;document.querySelector('.revision-responder button').click();return true;}"""

with sync_playwright() as p:
    browser = p.chromium.launch(channel=os.environ.get('CHANNEL', 'chrome'))
    actx, alice = context(browser, 'alice'); bctx, bob = context(browser, 'bob'); octx, angel = context(browser, 'owner')
    fa = open_doc(alice)
    composer = comment(fa, 'Comentario de Alice sobre el alcance.')
    check('composer of a new comment names its writer (Alice)', composer['name'] == 'Alice Ruiz', composer)
    comment(fa, 'Nota privada de Alice.', note=True)
    fb = open_doc(bob)
    rows = fb.evaluate(LIST)
    alice_row = next((r for r in rows if 'Comentario de Alice' in r['all']), None)
    check('Bob sees Alice comment attributed to Alice', alice_row and 'Alice Ruiz' in alice_row['meta'] and 'Bob' not in alice_row['meta'], rows)
    check('Bob does not see Alice private note', not any('Nota privada de Alice' in r['all'] for r in rows), rows)
    pin = fb.evaluate(PIN, 'Alice')
    check('Bob opening Alice pin does not present it as Bob', pin and pin['composerName'] != 'Bob Pérez', pin)
    results['bob_pin'] = pin
    fb.evaluate(REPLY, 'Respuesta de Bob.'); fb.wait_for_timeout(900)
    fa = open_doc(alice)
    rows = fa.evaluate(LIST)
    alice_row = next((r for r in rows if 'Comentario de Alice' in r['all']), None)
    check('Alice sees Bob reply attributed to Bob after reload', alice_row and any(x.startswith('Bob Pérez:') for x in alice_row['replies']), rows)
    check('Alice still sees her own private note after reload', any('Nota privada de Alice' in r['all'] for r in rows), rows)
    fo = open_doc(angel)
    rows = fo.evaluate(LIST)
    alice_row = next((r for r in rows if 'Comentario de Alice' in r['all']), None)
    check('Owner sees Alice comment attributed to Alice', alice_row and 'Alice Ruiz' in alice_row['meta'], rows)
    check('Owner does not see Alice private note', not any('Nota privada de Alice' in r['all'] for r in rows), rows)
    pin = fo.evaluate(PIN, 'Alice')
    results['owner_pin'] = pin
    check('Owner opening Alice pin does not present it as Ángel', pin and not (pin['editorOpen'] and pin['composerName'] == 'Ángel Botto'), pin)
    check('Owner opening Alice pin shows her thread instead of an editor in his name', pin and pin['panelOpen'] and not pin['editorOpen'], pin)
    edit = fo.evaluate(EDIT, 'Comentario de Alice')
    results['owner_edit'] = edit
    check('Owner editing Alice comment explicitly keeps Alice as the composer author', edit and edit['composerName'] == 'Alice Ruiz', edit)
    own = comment(fo, 'Comentario propio de Ángel.')
    check('Owner new comment composer names Ángel', own['name'] == 'Ángel Botto', own)
    # Agent token of the owner comments through the public API.
    token = store.token(people['owner'][0]['id'], 'Codex')
    agent = TestClient(app, base_url=ORIGIN, headers={'Authorization': 'Bearer ' + token})
    a = agent.post('/api/artifacts/' + AID + '/review', json={'id': uuid.uuid4().hex, 'kind': 'create', 'version': VERSION, 'text': 'Sugerencia del agente.', 'entry_type': 'comment',
        'anchor': {'reference': 'documento', 'tag': 'MAIN', 'text': '', 'quote': 'x', 'page': 'Identidad', 'x': .5, 'y': .5}})
    check('agent comment accepted', a.status_code == 200, a.text[:200])
    snap = owner.get('/api/artifacts/' + AID + '/review').json()['snapshot']['events']
    ev = next(e for e in snap if e.get('text') == 'Sugerencia del agente.')
    results['agent_event'] = {k: ev.get(k) for k in ('author', 'verified', 'agent', 'kind', 'source')}
    check('agent comment carries agent provenance, not only the reader name', ev.get('agent'), results['agent_event'])
    fo = open_doc(angel)
    rows = fo.evaluate(LIST)
    agent_row = next((r for r in rows if 'Sugerencia del agente' in r['all']), None)
    check('Owner sees agent comment marked as agent', agent_row and 'agente' in agent_row['meta'].lower(), agent_row)
    fb = open_doc(bob); rows = fb.evaluate(LIST)
    agent_row = next((r for r in rows if 'Sugerencia del agente' in r['all']), None)
    check('Bob sees agent comment marked as agent', agent_row and 'agente' in agent_row['meta'].lower(), agent_row)
    events = owner.get('/api/artifacts/' + AID + '/review').json()['snapshot']['events']
    alice_thread = next(e for e in events if e.get('text') == 'Comentario de Alice sobre el alcance.')['thread']
    human_thread = next(e for e in events if e.get('text') == 'Comentario propio de Ángel.')['thread']
    agent_thread = next(e for e in events if e.get('text') == 'Sugerencia del agente.')['thread']
    edit = lambda c, t: c.post('/api/artifacts/' + AID + '/review', json={'id': uuid.uuid4().hex, 'kind': 'edit', 'thread': t, 'version': VERSION, 'text': 'Reescrito.'}).status_code
    check('Bob cannot edit Alice comment (API)', edit(people['bob'][1], alice_thread) == 403)
    owner_user = people['owner'][0]; bob_token = store.token(people['bob'][0]['id'], 'Bot de Bob')
    bob_agent = TestClient(app, base_url=ORIGIN, headers={'Authorization': 'Bearer ' + bob_token})
    r = bob_agent.post('/api/artifacts/' + AID + '/review', json={'id': uuid.uuid4().hex, 'kind': 'reply', 'thread': alice_thread, 'version': VERSION, 'text': 'Respuesta del bot de Bob.'})
    check('agent reply of a commenter accepted', r.status_code == 200, r.text[:200])
    bob_human = next(e for e in events if e.get('text') == 'Respuesta de Bob.')
    bob_create = people['bob'][1].post('/api/artifacts/' + AID + '/review', json={'id': uuid.uuid4().hex, 'kind': 'create', 'version': VERSION, 'text': 'Comentario humano de Bob.', 'entry_type': 'comment',
        'anchor': {'reference': 'documento', 'tag': 'MAIN', 'text': '', 'quote': 'x', 'page': 'Identidad', 'x': .5, 'y': .5}}).json()['snapshot']['events']
    bob_thread = next(e for e in bob_create if e.get('text') == 'Comentario humano de Bob.')['thread']
    check('Bob can still edit his own human comment', edit(people['bob'][1], bob_thread) == 200)
    after = owner.get('/api/artifacts/' + AID + '/review').json()['snapshot']['events']
    check('history keeps immutable authors (create events unchanged)', all(e['author'] == {'owner': 'Ángel Botto', 'alice': 'Alice Ruiz', 'bob': 'Bob Pérez'}[k] for k, uid in [(k, people[k][0]['id']) for k in people] for e in after if e['actor'] == uid and not e.get('agent')))
    fa = open_doc(alice); rows = fa.evaluate(LIST)
    alice_row = next((r for r in rows if 'Comentario de Alice' in r['all']), None)
    check('Alice sees the bot reply named as Bob agent, not as Bob', alice_row and any(x.startswith('Bot de Bob (agente de Bob Pérez):') for x in alice_row['replies']), alice_row and alice_row['replies'])
    exported = owner.get('/api/review/export?artifact=' + AID).json()
    text = exported['text']; results['export_excerpt'] = text[:2000]
    check('export keeps Alice as author of her comment', 'Autor: Alice Ruiz' in text)
    check('export keeps Bob reply author', 'autor="Bob Pérez"' in text)
    check('export marks agent comment as agent', any(l.startswith('Autor: ') and 'agente' in l.lower() for l in text.splitlines()), [l for l in text.splitlines() if l.startswith('Autor')])
    check('owner export omits Alice private note', 'Nota privada de Alice' not in text)
    check('no participant email leaks to commenters', '@team.test' not in json.dumps(people['bob'][1].get('/api/artifacts/' + AID + '/review').json()) and '@owner.test' not in json.dumps(people['bob'][1].get('/api/artifacts/' + AID + '/review').json()))
    results['errors'] = {'alice': alice.errors, 'bob': bob.errors, 'owner': angel.errors}
    browser.close()
(OUT / f'{LABEL}.json').write_text(json.dumps(results, indent=1, ensure_ascii=False))
print(sum(c['ok'] for c in results['checks']), '/', len(results['checks']))
tmp.cleanup()
