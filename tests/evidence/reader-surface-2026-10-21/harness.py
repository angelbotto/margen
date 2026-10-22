"""Hosted reader backing-surface harness: real portal shell (create_app + static assets) behind a
Playwright route, real /render CSP and opaque sandbox, CDP screencast of load and remount.
usage: harness.py REPO OUTDIR LABEL [SHOWCASE_HTML]   (CHANNEL env: chrome|chromium, RENDER_DELAY_MS env)
Writes OUTDIR/LABEL.json and the worst offending frames as JPEG. Disposable store; no credentials."""
import base64, json, os, sys, tempfile, time
from pathlib import Path
REPO, OUT, LABEL = Path(sys.argv[1]).resolve(), Path(sys.argv[2]), sys.argv[3]
SHOWCASE = Path(sys.argv[4]) if len(sys.argv) > 4 else None
sys.path.insert(0, str(REPO))
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
from portal.app import create_app, COOKIE

ORIGIN = 'https://portal.test'
DELAY = int(os.environ.get('RENDER_DELAY_MS', '250'))
OUT.mkdir(parents=True, exist_ok=True)
tmp = tempfile.TemporaryDirectory()
app = create_app(tmp.name, origin=ORIGIN, issuer='https://identity.test', audience='our-app')
store = app.state.store
owner = TestClient(app, base_url=ORIGIN, headers={'Origin': ORIGIN})
u = store.user('owner@example.com', 'Propietaria'); owner.cookies.set(COOKIE, store.session(u['id']))

def publish(title, html):
    r = owner.post('/api/artifacts', json={'title': title, 'html': html}); r.raise_for_status(); return r.json()['id']

DOCS = {
    'margen-light-reader': (REPO / 'examples/generated/collaborative.html').read_text(),
    'margen-system-reader': (REPO / 'examples/generated/executive.html').read_text(),
    'foreign-plain': '<!doctype html><title>Plano</title><meta name="nota-documento" content="superficie-plano"><p>Documento sin Margen, sin fondo propio.</p>',
    'foreign-dark': '<!doctype html><title>Oscuro propio</title><meta name="nota-documento" content="superficie-oscuro"><style>body{background:#000;color:#eee}</style><p>Documento oscuro sin Margen.</p>',
}
if SHOWCASE: DOCS = {'showcase-dark-project': SHOWCASE.read_text(), **DOCS}
IDS = {k: publish(k, v) for k, v in DOCS.items()}

SCORE = """async d=>{const im=new Image();im.src='data:image/jpeg;base64,'+d;await im.decode();const c=document.getElementById('c');c.width=im.width;c.height=im.height;const x=c.getContext('2d');x.drawImage(im,0,0);const p=x.getImageData(0,0,c.width,c.height).data;let w=0,b=0,n=p.length/4;for(let i=0;i<p.length;i+=4){if(p[i]>225&&p[i+1]>225&&p[i+2]>225)w++;else if(p[i]<40&&p[i+1]<40&&p[i+2]<40)b++;}return [w/n,b/n];}"""
STATE = """()=>{const f=document.getElementById('artifact-frame');return {frameBg:getComputedStyle(f).backgroundColor,surface:f.dataset.surface||null,inline:f.style.getPropertyValue('--reader-surface')||null,portalDark:document.documentElement.hasAttribute('data-dark'),sandbox:f.getAttribute('sandbox')}}"""
INNER = """()=>{const r=document.documentElement,b=document.body;return {html:getComputedStyle(r).backgroundColor,body:getComputedStyle(b).backgroundColor,mode:r.dataset.colorMode||null,backed:r.hasAttribute('data-margen-surface'),compat:document.compatMode,origin:origin}}"""

def proxy(route):
    req = route.request
    headers = {k: v for k, v in req.headers.items() if k not in {'host', 'cookie', 'accept-encoding'}}
    if '/render' in req.url and DELAY: time.sleep(DELAY / 1000)
    r = owner.request(req.method, req.url, headers=headers, content=req.post_data_buffer, follow_redirects=False)
    h = {k: v for k, v in r.headers.items() if k not in {'content-encoding', 'content-length'}}
    route.fulfill(status=r.status_code, headers=h, body=r.content)

def run(browser, doc, parent_dark, W=1440, H=900):
    ctx = browser.new_context(viewport={'width': W, 'height': H}, color_scheme='dark' if parent_dark else 'light')
    ctx.add_init_script("try{localStorage.setItem('bottifact-portal-dark','%s')}catch{}" % ('true' if parent_dark else 'false'))
    ctx.route(ORIGIN + '/**', proxy)
    ctx.route('https://fonts.googleapis.com/**', lambda r: r.abort())
    pg = ctx.new_page(); errors = []; pg.on('pageerror', lambda e: errors.append(str(e)))
    cdp = ctx.new_cdp_session(pg); frames = []; phase = {'v': 'load'}
    def onf(ev):
        frames.append({'phase': phase['v'], 't': ev['metadata']['timestamp'], 'data': ev['data']})
        cdp.send('Page.screencastFrameAck', {'sessionId': ev['sessionId']})
    cdp.on('Page.screencastFrame', onf)
    pg.goto('about:blank'); cdp.send('Page.startScreencast', {'format': 'jpeg', 'quality': 60})
    pg.goto(ORIGIN + '/a/' + IDS[doc], wait_until='commit'); pg.wait_for_timeout(3500)
    state = {'afterLoad': pg.evaluate(STATE)}
    inner = lambda: next(f for f in pg.frames if '/render' in f.url).evaluate(INNER)
    state['innerAfterLoad'] = inner()
    phase['v'] = 'remount'; pg.evaluate("()=>{const f=document.getElementById('artifact-frame');f.src=f.src;}"); pg.wait_for_timeout(3000)
    state['afterRemount'] = pg.evaluate(STATE)
    # Document preference switch from inside the document (reader controls / appearance menu).
    switches = []
    fr = next(f for f in pg.frames if '/render' in f.url)
    for mode in ('light', 'dark'):
        phase['v'] = 'switch-' + mode
        ok = fr.evaluate("m=>{const i=document.querySelector('[data-elegir-modo][value='+m+']');if(!i)return false;i.checked=true;i.dispatchEvent(new Event('change',{bubbles:true}));return true;}", mode)
        pg.wait_for_timeout(600)
        switches.append({'mode': mode, 'control': ok, 'inner': inner(), 'parent': pg.evaluate(STATE)})
    # Revisit: the first-paint surface remembered from the first visit backs the frame before the API answers.
    phase['v'] = 'revisit'; pg.goto(ORIGIN + '/a/' + IDS[doc], wait_until='commit'); pg.wait_for_timeout(3000)
    state['afterRevisit'] = pg.evaluate(STATE)
    cdp.send('Page.stopScreencast')
    sc = ctx.new_page(); sc.set_content('<canvas id=c></canvas>')
    t0 = frames[0]['t'] if frames else 0; rows = []
    for i, f in enumerate(frames):
        w, b = sc.evaluate(SCORE, f['data'])
        rows.append({'i': i, 'phase': f['phase'], 't': round(f['t'] - t0, 3), 'white': round(w, 4), 'black': round(b, 4)})
        f['w'], f['b'] = w, b
    summary = {}
    for ph in sorted({r['phase'] for r in rows}):
        rs = [r for r in rows if r['phase'] == ph]
        summary[ph] = {'frames': len(rs), 'whiteOver50': sum(r['white'] > .5 for r in rs), 'blackOver50': sum(r['black'] > .5 for r in rs),
                       'final': {'white': rs[-1]['white'], 'black': rs[-1]['black']}}
    # Save the first frames of load and anything that disagrees with the settled frame.
    for f, r in zip(frames, rows):
        if r['phase'] in ('load', 'remount', 'revisit') and (r['white'] > .5) != (summary[r['phase']]['final']['white'] > .5) or ((r['black'] > .5) != (summary[r['phase']]['final']['black'] > .5) and r['phase'] in ('load', 'remount', 'revisit')):
            (OUT / f'{LABEL}-{doc}-{"dark" if parent_dark else "light"}-{r["i"]:03d}-{r["phase"]}.jpg').write_bytes(base64.b64decode(f['data']))
    ctx.close()
    return {'doc': doc, 'parentDark': parent_dark, 'summary': summary, 'state': state, 'switches': switches, 'errors': errors, 'rows': rows}

with sync_playwright() as p:
    browser = p.chromium.launch(channel=os.environ.get('CHANNEL', 'chrome'))
    results = [run(browser, d, dark) for d in DOCS for dark in (False, True)]
    browser.close()
(OUT / f'{LABEL}.json').write_text(json.dumps({'label': LABEL, 'channel': os.environ.get('CHANNEL', 'chrome'), 'renderDelayMs': DELAY, 'results': results}, indent=1))
for r in results:
    print(r['doc'], 'parentDark' if r['parentDark'] else 'parentLight', json.dumps({k: (v['frames'], v['whiteOver50'], v['blackOver50']) for k, v in r['summary'].items()}), r['state']['afterLoad']['frameBg'], r['state']['innerAfterLoad']['html'], r['state']['innerAfterLoad']['body'], 'switch', [(s['mode'], s['control'], s['inner']['body'], s['parent']['frameBg']) for s in r['switches']], 'errors', len(r['errors']))
tmp.cleanup()
