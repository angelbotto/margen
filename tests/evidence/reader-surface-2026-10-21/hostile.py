"""Hostile surface messages against the real hosted shell: only an in-range RGB triple from the
sandboxed frame changes the backing; CSS text, out-of-range values and other sources do not.
usage: hostile.py REPO OUTDIR"""
import json, sys, tempfile
from pathlib import Path
REPO, OUT = Path(sys.argv[1]).resolve(), Path(sys.argv[2])
sys.path.insert(0, str(REPO))
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
from portal.app import create_app, COOKIE
ORIGIN = 'https://portal.test'
tmp = tempfile.TemporaryDirectory()
app = create_app(tmp.name, origin=ORIGIN, issuer='https://identity.test', audience='our-app'); store = app.state.store
owner = TestClient(app, base_url=ORIGIN, headers={'Origin': ORIGIN})
u = store.user('owner@example.com', 'Propietaria'); owner.cookies.set(COOKIE, store.session(u['id']))
aid = owner.post('/api/artifacts', json={'title': 'h', 'html': (REPO / 'examples/generated/collaborative.html').read_text()}).json()['id']
def proxy(route):
    req = route.request; headers = {k: v for k, v in req.headers.items() if k not in {'host', 'cookie', 'accept-encoding'}}
    r = owner.request(req.method, req.url, headers=headers, content=req.post_data_buffer, follow_redirects=False)
    route.fulfill(status=r.status_code, headers={k: v for k, v in r.headers.items() if k not in {'content-encoding', 'content-length'}}, body=r.content)
STATE = "()=>{const f=document.getElementById('artifact-frame');return {bg:getComputedStyle(f).backgroundColor,inline:f.getAttribute('style'),sandbox:f.getAttribute('sandbox')}}"
SEND = "c=>new Promise(r=>{const id='h'+Math.random();addEventListener('message',function on(e){if(e.data?.id===id){removeEventListener('message',on);r(e.data);}});parent.postMessage({bottifact:1,id,op:'surface',data:{color:c}},'*');setTimeout(()=>r('no-reply'),1500);})"
results = []
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome'); ctx = b.new_context(viewport={'width': 1200, 'height': 800})
    ctx.route(ORIGIN + '/**', proxy); ctx.route('https://fonts.googleapis.com/**', lambda r: r.abort())
    pg = ctx.new_page(); pg.goto(ORIGIN + '/a/' + aid); pg.wait_for_timeout(2500)
    fr = next(f for f in pg.frames if '/render' in f.url)
    results.append({'case': 'settled', 'state': pg.evaluate(STATE)})
    for color in ([1, 2, 3], 'red;background:url(https://evil.test/x)', [300, 0, 0], [1.5, 2, 3], [1, 2], {'0': 1}, [9, 9, 9, 9]):
        reply = fr.evaluate(SEND, color)
        results.append({'case': 'frame', 'color': color, 'reply': reply.get('data') if isinstance(reply, dict) else reply, 'state': pg.evaluate(STATE)})
    # Same message from the parent's own window (not the frame) is ignored by the source check.
    pg.evaluate("()=>postMessage({bottifact:1,id:'x',op:'surface',data:{color:[200,0,0]}},'*')"); pg.wait_for_timeout(300)
    results.append({'case': 'parent-window-source', 'state': pg.evaluate(STATE)})
    b.close()
(OUT / 'hostile.json').write_text(json.dumps(results, indent=1))
for r in results: print(r['case'], r.get('color'), r.get('reply'), r['state']['bg'], r['state']['sandbox'])
tmp.cleanup()
