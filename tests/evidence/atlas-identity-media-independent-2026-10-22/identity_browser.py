"""Independent identity probe in the real reader (portal page + opaque artifact iframe), Chromium or WebKit.
Synthetic store: owner «Propietaria», commenters «Alice Ruiz» and a twin «Alice Ruiz» (other email), a guest whose chosen
name imitates the verified badge, and an owner agent token labelled with a human name. No network, no production.
usage: identity_browser.py REPO OUTDIR SHOTS ENGINE"""
import json, sys, tempfile, uuid
from pathlib import Path
REPO, OUT, SHOTS, ENGINE = Path(sys.argv[1]).resolve(), Path(sys.argv[2]), Path(sys.argv[3]).expanduser(), sys.argv[4]
sys.path.insert(0, str(REPO))
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
from portal.app import create_app, COOKIE

ORIGIN = 'https://portal.test'
OUT.mkdir(parents=True, exist_ok=True); SHOTS.mkdir(parents=True, exist_ok=True)
tmp = tempfile.TemporaryDirectory()
app = create_app(tmp.name, origin=ORIGIN, issuer='https://identity.test', audience='our-app')
store = app.state.store
people = {}
for key, email, name in [('owner', 'owner@owner.test', 'Propietaria'), ('alice', 'alice@team.test', 'Alice Ruiz'), ('twin', 'alice.twin@other.test', 'Alice Ruiz')]:
    u = store.user(email, name); c = TestClient(app, base_url=ORIGIN, headers={'Origin': ORIGIN}); c.cookies.set(COOKIE, store.session(u['id']))
    people[key] = (u, c)
owner = people['owner'][1]
HTML = (REPO / 'examples/generated/collaborative.html').read_text()
pub = owner.post('/api/artifacts', json={'title': 'Identidad', 'html': HTML}); pub.raise_for_status(); AID, VERSION = pub.json()['id'], pub.json()['version']
owner.put('/api/artifacts/' + AID + '/access', json={'visibility': 'unlisted', 'comments': 'readers', 'guests': True, 'grants': [
    {'email': 'alice@team.test', 'role': 'commenter'}, {'email': 'alice.twin@other.test', 'role': 'commenter'}]}).raise_for_status()
guest = TestClient(app, base_url=ORIGIN, headers={'Origin': ORIGIN})
GUEST_NAME = 'Alice Ruiz · correo verificado'
guest.post('/api/guest', json={'artifact': AID, 'name': GUEST_NAME}).raise_for_status()
people['guest'] = (None, guest)
results = {'engine': ENGINE, 'checks': []}
def check(name, ok, detail=None, severity=None):
    results['checks'].append({'name': name, 'ok': bool(ok), 'detail': detail, 'severity_if_fail': severity})
    print(('PASS ' if ok else 'FAIL ') + name, '' if ok else json.dumps(detail, ensure_ascii=False, default=str)[:500], flush=True)

def context(browser, key):
    client = people[key][1]
    ctx = browser.new_context(viewport={'width': 1440, 'height': 900})
    def proxy(route):
        req = route.request
        headers = {k: v for k, v in req.headers.items() if k not in {'host', 'cookie', 'accept-encoding'}}
        r = client.request(req.method, req.url, headers=headers, content=req.post_data_buffer, follow_redirects=False)
        route.fulfill(status=r.status_code, headers={k: v for k, v in r.headers.items() if k not in {'content-encoding', 'content-length'}}, body=r.content)
    ctx.route(ORIGIN + '/**', proxy)
    ctx.route(lambda url: not url.startswith(ORIGIN) and not url.startswith(('data:', 'about:', 'blob:')), lambda r: r.abort())
    pg = ctx.new_page(); pg.errors = []; pg.on('pageerror', lambda e: pg.errors.append(str(e)))
    return ctx, pg

def open_doc(pg):
    pg.goto(ORIGIN + '/a/' + AID)
    for _ in range(150):
        fr = next((f for f in pg.frames if '/render' in f.url), None)
        if fr:
            try:
                if fr.evaluate("()=>!!document.querySelector('.revision-barra')&&!!window.BottifactReviewBridge&&!!document.querySelector('.revision-barra [data-revision-lista]')"):
                    fr.wait_for_timeout(1200); return fr
            except Exception: pass
        pg.wait_for_timeout(120)
    raise RuntimeError('frame not ready')

def comment(fr, text):
    fr.evaluate("""(text)=>{document.querySelector('.revision-barra [data-revision-modo]').click();
      const p=[...document.querySelectorAll('main p')].find(p=>p.getClientRects().length&&p.textContent.trim().length>40);p.click();
      const i=document.querySelector('[data-revision-texto]');i.value=text;i.dispatchEvent(new Event('input',{bubbles:true}));}""", text)
    name = fr.evaluate("()=>document.querySelector('.review-composer-name')?.textContent")
    fr.evaluate("()=>document.querySelector('[data-revision-guardar]').click()"); fr.wait_for_timeout(900)
    return name

LIST = """()=>{document.querySelector('.revision-barra [data-revision-lista]').click();const f=document.querySelector('.revision-utilidades select');f.value='all';f.dispatchEvent(new Event('change'));
  return [...document.querySelectorAll('[data-revision-notas] > li')].map(li=>({meta:li.querySelector('.revision-meta')?.textContent||'',badge:li.querySelector('.revision-meta .revision-identidad')?.textContent,
   person:li.querySelector('.revision-meta bdi')?.textContent,text:li.querySelector(':scope > p:not(.revision-meta)')?.textContent,replies:[...li.querySelectorAll('.revision-respuestas li')].map(x=>x.textContent),
   actions:[...li.querySelectorAll('.acciones button')].map(b=>b.textContent)}));}"""
CLOSE = "()=>document.querySelector('[data-revision-cerrar]')?.click()"
EDIT = """(needle)=>{const li=[...document.querySelectorAll('[data-revision-notas] > li')].find(li=>li.textContent.includes(needle));const b=[...li.querySelectorAll('.acciones button')].find(b=>b.textContent==='Editar');if(!b)return null;b.click();
  return {composerName:document.querySelector('.review-composer-name')?.textContent,text:document.querySelector('[data-revision-texto]')?.value};}"""
def api(key, **kw):
    body = {'id': uuid.uuid4().hex, 'version': VERSION, **kw}
    if kw.get('kind') == 'create':
        body.setdefault('entry_type', 'comment'); body['anchor'] = {'reference': 'documento', 'tag': 'MAIN', 'text': '', 'quote': 'x', 'page': 'Identidad', 'x': .5, 'y': .5}
    return people[key][1].post('/api/artifacts/' + AID + '/review', json=body)

with sync_playwright() as p:
    browser = getattr(p, ENGINE).launch()
    actx, alice = context(browser, 'alice'); tctx, twin = context(browser, 'twin'); octx, own = context(browser, 'owner'); gctx, gst = context(browser, 'guest')
    fa = open_doc(alice)
    check('Alice composer shows Alice', comment(fa, 'Comentario original de Alice.') == 'Alice Ruiz')
    ft = open_doc(twin)
    check('twin composer shows her own name', comment(ft, 'Comentario de la gemela.') == 'Alice Ruiz')
    rows = ft.evaluate(LIST); ft.evaluate(CLOSE)
    a_row = next(r for r in rows if 'original de Alice' in (r['text'] or ''))
    t_row = next(r for r in rows if 'gemela' in (r['text'] or ''))
    check('twin cannot edit Alice comment (no Editar)', 'Editar' not in a_row['actions'], a_row)
    check('twin can edit her own', 'Editar' in t_row['actions'], t_row)
    results['twin_rows'] = [a_row, t_row]
    check('two accounts with the same name are distinguishable in the reader', a_row['meta'].split(' · ')[:2] != t_row['meta'].split(' · ')[:2], [a_row['meta'], t_row['meta']], 'low')
    fg = open_doc(gst)
    check('guest composer shows chosen name', comment(fg, 'Comentario de la invitada.') == GUEST_NAME)
    token = store.token(people['owner'][0]['id'], 'Alice Ruiz')
    agent = TestClient(app, base_url=ORIGIN, headers={'Authorization': 'Bearer ' + token})
    r = agent.post('/api/artifacts/' + AID + '/review', json={'id': uuid.uuid4().hex, 'kind': 'create', 'version': VERSION, 'text': 'Comentario del agente.', 'entry_type': 'comment',
        'anchor': {'reference': 'documento', 'tag': 'MAIN', 'text': '', 'quote': 'x', 'page': 'Identidad', 'x': .5, 'y': .5}})
    check('agent token comment accepted', r.status_code == 200)
    fo = open_doc(own)
    rows = fo.evaluate(LIST)
    results['owner_rows'] = rows
    g_row = next(r for r in rows if 'invitada' in (r['text'] or ''))
    ag_row = next(r for r in rows if 'agente.' in (r['text'] or ''))
    a_row = next(r for r in rows if 'original de Alice' in (r['text'] or ''))
    check('guest badge says invitado', g_row['badge'] == 'invitado', g_row)
    check('guest chosen name cannot contain the verified badge wording', 'correo verificado' not in (g_row['person'] or ''), g_row, 'low')
    check('agent badge says conexión de agente and byline names the account', ag_row['badge'] == 'conexión de agente' and ag_row['person'] == 'Alice Ruiz (agente de Propietaria)', ag_row)
    check('agent label cannot be another person name', not (ag_row['person'] or '').startswith('Alice Ruiz'), ag_row, 'low')
    pg_shot = SHOTS / f'{ENGINE}-identity-owner-list.png'
    fo.locator('[data-revision-panel]').screenshot(path=str(pg_shot))
    check('owner has no Editar on Alice comment (owner edits only own)', 'Editar' not in a_row['actions'], a_row, 'high')
    e = fo.evaluate(EDIT, 'original de Alice')
    results['owner_edit_alice'] = e
    if e:
        check('owner editing Alice comment does not write under Alice name', e['composerName'] != 'Alice Ruiz', e, 'high')
        fo.evaluate("()=>{const i=document.querySelector('[data-revision-texto]');i.value='Texto puesto por la propietaria.';i.dispatchEvent(new Event('input',{bubbles:true}));document.querySelector('[data-revision-guardar]').click()}")
        fo.wait_for_timeout(900)
    fa = open_doc(alice)
    rows = fa.evaluate(LIST)
    a_row = next((r for r in rows if r['person'] == 'Alice Ruiz' and r['badge'] == 'correo verificado' and 'gemela' not in (r['text'] or '')), None)
    results['alice_after_owner_edit'] = a_row
    fa.locator('[data-revision-panel]').screenshot(path=str(SHOTS / f'{ENGINE}-identity-alice-after-owner-edit.png'))
    check('after reload Alice never sees owner words under her own byline', not (a_row and a_row['text'] == 'Texto puesto por la propietaria.'), a_row, 'high')
    fa.evaluate(CLOSE)
    # Reply flow + reload persistence
    fa.evaluate("""()=>{document.querySelector('.revision-barra [data-revision-lista]').click();const i=document.querySelector('.revision-responder input');i.value='Respuesta de Alice.';document.querySelector('.revision-responder button').click();}""")
    fa.wait_for_timeout(900)
    ft = open_doc(twin); rows = ft.evaluate(LIST)
    replies = [x for r in rows for x in r['replies']]
    check('reply after reload attributed to its writer with badge', any(x.startswith('Alice Ruiz · correo verificado: Respuesta de Alice.') for x in replies), replies)
    # Bidi/control label at token creation (UI path) and portal side panel
    r = owner.post('/api/tokens', json={'label': '‮etnemirep‬ Bot\n'}).json()
    check('token label creation strips bidi/newline (stored label)', all('‮' not in t['label'] and '\n' not in t['label'] for t in owner.get('/api/tokens').json()['tokens']), owner.get('/api/tokens').json()['tokens'])
    exported = owner.get('/api/review/export?artifact=' + AID).json()
    results['export_authors'] = [l for l in exported['text'].splitlines() if l.startswith(('Autor', 'Identidad'))]
    check('export never contains participant emails', not any(x in json.dumps(exported) for x in ('alice@team.test', 'alice.twin@other.test', 'owner@owner.test')))
    results['errors'] = {k: v.errors for k, v in [('alice', alice), ('twin', twin), ('owner', own), ('guest', gst)]}
    check('no page errors', not any(results['errors'].values()), results['errors'])
    browser.close()
(OUT / f'identity-{ENGINE}.json').write_text(json.dumps(results, indent=1, ensure_ascii=False, default=str))
print(sum(c['ok'] for c in results['checks']), '/', len(results['checks']))
tmp.cleanup()
