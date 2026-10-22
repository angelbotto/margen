"""D6/D1-R final delta: an agent<->human edit of the same account must show the original author AND the last editor,
in the reader list and in the export, with no participant email anywhere. Real clicks for the human edit.
Synthetic store, isolated TestClient, no network. usage: edit_provenance_browser.py REPO OUTDIR ENGINE"""
import json, sys, tempfile, uuid
from pathlib import Path
REPO, OUT, ENGINE = Path(sys.argv[1]).resolve(), Path(sys.argv[2]), sys.argv[3]
sys.path.insert(0, str(REPO))
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
from portal.app import create_app, COOKIE

ORIGIN = 'https://portal.test'
EMAILS = ('owner@owner.test', 'alice@team.test')
OUT.mkdir(parents=True, exist_ok=True)
tmp = tempfile.TemporaryDirectory()
app = create_app(tmp.name, origin=ORIGIN, issuer='https://identity.test', audience='our-app')
store = app.state.store
people = {}
for key, email, name in [('owner', EMAILS[0], 'Propietaria'), ('alice', EMAILS[1], 'Alice Ruiz')]:
    u = store.user(email, name); c = TestClient(app, base_url=ORIGIN, headers={'Origin': ORIGIN}); c.cookies.set(COOKIE, store.session(u['id']))
    people[key] = c
owner, alice = people['owner'], people['alice']
pub = owner.post('/api/artifacts', json={'title': 'Procedencia', 'html': (REPO / 'examples/generated/collaborative.html').read_text()}); pub.raise_for_status()
AID, VERSION = pub.json()['id'], pub.json()['version']
owner.put('/api/artifacts/' + AID + '/access', json={'visibility': 'unlisted', 'comments': 'readers', 'guests': False,
    'grants': [{'email': EMAILS[1], 'role': 'commenter'}]}).raise_for_status()
token = alice.post('/api/tokens', json={'label': 'Codex'}).json()['token']
bot = TestClient(app, base_url=ORIGIN, headers={'Authorization': 'Bearer ' + token})
owner_bot = TestClient(app, base_url=ORIGIN, headers={'Authorization': 'Bearer ' + owner.post('/api/tokens', json={'label': 'Claude'}).json()['token']})

def post(client, **kw):
    body = {'id': uuid.uuid4().hex, 'version': VERSION, **kw}
    if kw.get('kind') == 'create':
        body['entry_type'] = 'comment'; body['anchor'] = {'reference': 'documento', 'tag': 'MAIN', 'text': '', 'quote': 'x', 'page': 'Procedencia', 'x': .5, 'y': .5}
    return client.post('/api/artifacts/' + AID + '/review', json=body)

results = {'engine': ENGINE, 'checks': []}
def check(name, ok, detail=None):
    results['checks'].append({'name': name, 'ok': bool(ok), 'detail': detail})
    print(('PASS ' if ok else 'FAIL ') + name, '' if ok else json.dumps(detail, ensure_ascii=False, default=str)[:600], flush=True)

r = post(alice, kind='create', text='Texto humano de Alice'); check('alice creates', r.status_code == 200, r.status_code)
thread = next(e for e in owner.get('/api/artifacts/' + AID + '/review').json()['snapshot']['events'] if e['kind'] == 'create')['thread']
check('owner agent cannot edit Alice (other actor)', post(owner_bot, kind='edit', thread=thread, text='x').status_code == 403)
check('owner human cannot edit Alice', post(owner, kind='edit', thread=thread, text='x').status_code == 403)
check('forged agent/author in body ignored', post(bot, kind='edit', thread=thread, text='Reescrito por Codex', author='Propietaria', agent='Nadie', verified=False).status_code == 200)

def export():
    return owner.get('/api/review/export?artifact=' + AID).json()['text']

def ctx_page(browser, client):
    ctx = browser.new_context(viewport={'width': 1440, 'height': 900})
    def proxy(route):
        req = route.request
        headers = {k: v for k, v in req.headers.items() if k not in {'host', 'cookie', 'accept-encoding'}}
        resp = client.request(req.method, req.url, headers=headers, content=req.post_data_buffer, follow_redirects=False)
        route.fulfill(status=resp.status_code, headers={k: v for k, v in resp.headers.items() if k not in {'content-encoding', 'content-length'}}, body=resp.content)
    ctx.route(ORIGIN + '/**', proxy)
    ctx.route(lambda url: not url.startswith(ORIGIN) and not url.startswith(('data:', 'about:', 'blob:')), lambda r: r.abort())
    pg = ctx.new_page(); pg.errors = []; pg.on('pageerror', lambda e: pg.errors.append(str(e)))
    return ctx, pg

def frame(pg):
    pg.goto(ORIGIN + '/a/' + AID)
    for _ in range(150):
        fr = next((f for f in pg.frames if '/render' in f.url), None)
        try:
            if fr and fr.evaluate("()=>!!window.BottifactReviewBridge&&!!document.querySelector('.revision-barra [data-revision-lista]')"):
                fr.wait_for_timeout(1200); return fr
        except Exception: pass
        pg.wait_for_timeout(120)
    raise RuntimeError('frame not ready')

ROWS = """()=>{const f=document.querySelector('.revision-utilidades select');if(f){f.value='all';f.dispatchEvent(new Event('change'));}
 return [...document.querySelectorAll('[data-revision-notas] > li')].map(li=>({meta:li.querySelector('.revision-meta')?.innerText||'',
  text:li.querySelector(':scope > p:not(.revision-meta)')?.textContent,actions:[...li.querySelectorAll('.acciones button')].map(b=>b.textContent)}));}"""

with sync_playwright() as p:
    browser = getattr(p, ENGINE).launch()
    for who in ('owner', 'alice'):
        ctx, pg = ctx_page(browser, people[who]); fr = frame(pg)
        fr.evaluate("()=>document.querySelector('.revision-barra [data-revision-lista]').click()"); fr.wait_for_timeout(300)
        rows = fr.evaluate(ROWS); row = next((x for x in rows if 'Reescrito por Codex' in (x['text'] or '')), None)
        meta = (row or {}).get('meta', '')
        check(f'{who}: reader shows original author Alice', row and meta.startswith('Alice Ruiz'), rows)
        check(f'{who}: reader shows last edit by Codex (agente de Alice Ruiz)', 'Última edición' in meta and 'Codex (agente de Alice Ruiz)' in meta, meta)
        check(f'{who}: forged author/agent not shown', 'Nadie' not in meta and 'Propietaria' not in meta.split('Última edición')[-1], meta)
        check(f'{who}: Editar only for the author', ('Editar' in row['actions']) == (who == 'alice'), row and row['actions'])
        check(f'{who}: no emails in reader frame', not any(e in fr.content() for e in EMAILS))
        if who == 'alice':
            # Real human edit through the UI: composer must show the session's own name.
            fr.locator('[data-revision-notas] > li', has_text='Reescrito por Codex').locator('.acciones button', has_text='Editar').click()
            fr.wait_for_timeout(300)
            name = fr.evaluate("()=>document.querySelector('.review-composer-name')?.textContent")
            check('alice editing composer shows Alice', name == 'Alice Ruiz', name)
            box = fr.locator('[data-revision-texto]'); box.fill('Alice vuelve a escribir'); fr.locator('[data-revision-guardar]').click(); fr.wait_for_timeout(1200)
            pg.reload(); fr = frame(pg); fr.evaluate("()=>document.querySelector('.revision-barra [data-revision-lista]').click()"); fr.wait_for_timeout(300)
            rows = fr.evaluate(ROWS); row = next((x for x in rows if 'Alice vuelve a escribir' in (x['text'] or '')), None)
            meta = (row or {}).get('meta', '')
            check('after human edit: last edit is Alice, agent label gone', row and 'Última edición' in meta and 'Codex' not in meta, rows)
        check(f'{who}: no page errors', not pg.errors, pg.errors)
        ctx.close()
    browser.close()

text = export()
block = text.split('### Comentario')[1]
check('export: Autor is last editor (human)', 'Autor: Alice Ruiz ·' in block, block[:400])
check('export: Autor original + Última edición present', 'Autor original: Alice Ruiz' in block and 'Última edición: Alice Ruiz' in block, block[:600])
check('export: no participant emails', not any(e in text for e in EMAILS))
post(bot, kind='edit', thread=thread, text='Codex de nuevo')
block = export().split('### Comentario')[1]
check('export after agent edit: Autor Codex (agente de Alice Ruiz) + original Alice', 'Autor: Codex (agente de Alice Ruiz)' in block and 'Autor original: Alice Ruiz' in block and '"tipo": "agente"' in block, block[:700])
(OUT / f'edit-provenance-{ENGINE}.json').write_text(json.dumps(results, indent=1, ensure_ascii=False, default=str))
sys.exit(0 if all(c['ok'] for c in results['checks']) else 1)
