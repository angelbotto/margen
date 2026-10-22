"""Alternative D2 attack: the artifact asks the portal on the FIRST click of a double click, so the portal dialog opens
under the pointer and the SECOND physical click lands on the portal's own link/play button (isTrusted in the portal).
Real mouse events (Playwright mouse.down/up at fixed coordinates). Synthetic store, stubbed external hosts, no network.
usage: media_doubleclick_browser.py REPO OUTDIR ENGINE"""
import json, sys, tempfile, time
from pathlib import Path
REPO, OUT, ENGINE = Path(sys.argv[1]).resolve(), Path(sys.argv[2]), sys.argv[3]
sys.path.insert(0, str(REPO))
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
from portal.app import create_app, COOKIE

ORIGIN = 'https://portal.test'
OUT.mkdir(parents=True, exist_ok=True)
tmp = tempfile.TemporaryDirectory()
app = create_app(tmp.name, origin=ORIGIN, issuer='https://identity.test', audience='our-app')
store = app.state.store
u = store.user('owner@owner.test', 'Dueña Sintética')
owner = TestClient(app, base_url=ORIGIN, headers={'Origin': ORIGIN}); owner.cookies.set(COOKIE, store.session(u['id']))
# The attacker document: one big "double-click to continue" surface; the first mousedown asks the portal for something.
HTML = """<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="nota-documento" content="dblclick"><title>Doble</title>
<style>#trampa{height:2000px;background:#eee;font:20px sans-serif;padding:20px}</style></head><body><main>
<p id="trampa">Haz doble clic en cualquier parte para continuar.</p></main><script>
const V=document.documentElement.dataset.v;window.mode='external';
document.getElementById('trampa').addEventListener('mousedown',()=>{
 const v=window.__version;if(!v)return;
 const data=window.mode==='external'?{href:'https://attacker.example/phish',version:v}:{provider:'youtube',id:'dQw4w9WgXcQ',version:v};
 parent.postMessage({bottifact:1,id:'dc'+Math.random(),op:window.mode,data},'*');});
</script></body></html>"""
pub = owner.post('/api/artifacts', json={'title': 'Doble', 'html': HTML}); pub.raise_for_status()
AID, V1 = pub.json()['id'], pub.json()['version']
results = {'engine': ENGINE, 'checks': [], 'external_requests': []}
def check(name, ok, detail=None):
    results['checks'].append({'name': name, 'ok': bool(ok), 'detail': detail})
    print(('PASS ' if ok else 'FAIL ') + name, '' if ok else json.dumps(detail, ensure_ascii=False, default=str)[:500], flush=True)

def proxy(route):
    req = route.request
    headers = {k: v for k, v in req.headers.items() if k not in {'host', 'cookie', 'accept-encoding'}}
    r = owner.request(req.method, req.url, headers=headers, content=req.post_data_buffer, follow_redirects=False)
    route.fulfill(status=r.status_code, headers={k: v for k, v in r.headers.items() if k not in {'content-encoding', 'content-length'}}, body=r.content)
def external(route):
    results['external_requests'].append(route.request.url)
    route.fulfill(status=200, content_type='text/html', body='<p>stub</p>')

with sync_playwright() as p:
    browser = getattr(p, ENGINE).launch()
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    ctx.route(ORIGIN + '/**', proxy)
    ctx.route(lambda url: not url.startswith((ORIGIN, 'data:', 'about:', 'blob:')), external)
    popups = []; ctx.on('page', lambda pg: popups.append(pg.url))
    pg = ctx.new_page(); errors = []; pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.goto(ORIGIN + '/a/' + AID)
    fr = None
    for _ in range(150):
        fr = next((f for f in pg.frames if '/render' in f.url), None)
        try:
            if fr and fr.evaluate("()=>!!window.BottifactReviewBridge"): break
        except Exception: pass
        pg.wait_for_timeout(100)
    pg.wait_for_timeout(1500)
    fr.evaluate("(v)=>{window.__version=v}", V1)
    box = pg.locator('#artifact-frame').bounding_box()
    for mode, selector in (('external', '.media-dialog .media-source'), ('embed', '.media-dialog .media-play')):
        fr.evaluate("(m)=>{window.mode=m}", mode)
        # Reconnaissance: one click at the frame centre opens the dialog; the attacker learns where the portal control sits.
        cx, cy = box['x'] + 40, box['y'] + 40
        r0, p0 = len(results['external_requests']), len(popups)
        pg.mouse.click(cx, cy); pg.wait_for_timeout(600)
        opened = pg.evaluate("()=>document.querySelector('.media-dialog')?.open")
        ctl = pg.locator(selector).bounding_box() if opened else None
        check(f'{mode}: single click shows only a preview, no request', opened and not results['external_requests'][r0:] and not popups[p0:], {'opened': opened, 'req': results['external_requests'][r0:], 'popups': popups[p0:]})
        pg.keyboard.press('Escape'); pg.wait_for_timeout(400)
        if not ctl: continue
        x, y = ctl['x'] + ctl['width'] / 2, ctl['y'] + ctl['height'] / 2
        under = pg.evaluate("([x,y])=>document.elementFromPoint(x,y)?.id||document.elementFromPoint(x,y)?.tagName", [x, y])
        for gap in (60, 120, 250):
            n_req, n_pop = len(results['external_requests']), len(popups)
            pg.mouse.move(x, y); pg.mouse.down(); pg.mouse.up(); pg.wait_for_timeout(gap); pg.mouse.down(); pg.mouse.up()
            pg.wait_for_timeout(900)
            leaked = results['external_requests'][n_req:]; tabs = popups[n_pop:]
            check(f'{mode}: double click ({gap} ms) over the frame ({under}) does not reach attacker/provider', not leaked and not tabs,
                  {'requests': leaked, 'tabs': tabs, 'dialog_open': pg.evaluate("()=>document.querySelector('.media-dialog')?.open")})
            pg.keyboard.press('Escape'); pg.wait_for_timeout(400)
            for t in ctx.pages[1:]: t.close()
        # Middle-button double click (auxclick does not go through the portal's click handler).
        n_req, n_pop = len(results['external_requests']), len(popups)
        pg.mouse.move(x, y); pg.mouse.down(button='middle'); pg.mouse.up(button='middle'); pg.wait_for_timeout(120); pg.mouse.down(button='middle'); pg.mouse.up(button='middle')
        pg.wait_for_timeout(900)
        check(f'{mode}: middle-button double click does not reach attacker/provider', not results['external_requests'][n_req:] and not popups[n_pop:],
              {'requests': results['external_requests'][n_req:], 'tabs': popups[n_pop:]})
        pg.keyboard.press('Escape'); pg.wait_for_timeout(400)
        for t in ctx.pages[1:]: t.close()
        # Control: a deliberate click on the portal control after the protection window still works.
        n_req, n_pop = len(results['external_requests']), len(popups)
        pg.mouse.click(cx, cy); pg.wait_for_timeout(1000); pg.mouse.click(x, y); pg.wait_for_timeout(1200)
        check(f'{mode}: deliberate click after the window still acts (control)', results['external_requests'][n_req:] or popups[n_pop:],
              {'requests': results['external_requests'][n_req:], 'tabs': popups[n_pop:]})
        pg.keyboard.press('Escape'); pg.wait_for_timeout(400)
        for t in ctx.pages[1:]: t.close()
    check('no page errors', not errors, errors)
    browser.close()
(OUT / f'doubleclick-{ENGINE}.json').write_text(json.dumps(results, indent=1, ensure_ascii=False, default=str))
sys.exit(0 if all(c['ok'] for c in results['checks']) else 1)
