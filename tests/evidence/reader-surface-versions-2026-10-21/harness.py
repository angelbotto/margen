"""Version-aware backing surface: real portal shell (create_app + static assets) behind a Playwright
route, real /render CSP and opaque sandbox, render latency, CDP screencast and a 16 ms log of the
iframe's computed background in the parent.
usage: harness.py REPO OUTDIR LABEL   (CHANNEL env: chrome|chromium, RENDER_DELAY_MS env)
Public examples only (linear-light / linear-dark share one documento-id). Disposable store."""
import base64, json, os, sys, tempfile, time
from pathlib import Path
REPO, OUT, LABEL = Path(sys.argv[1]).resolve(), Path(sys.argv[2]), sys.argv[3]
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
LIGHT = (REPO / 'examples/generated/linear-light.html').read_text()
DARK = (REPO / 'examples/generated/linear-dark.html').read_text()

def post(path, body):
    r = owner.post(path, json=body); r.raise_for_status(); return r.json()

pub = post('/api/artifacts', {'title': 'Versiones', 'html': LIGHT})
AID, PUBLISHED = pub['id'], pub['version']
DRAFT = post('/api/artifacts/' + AID + '/versions', {'title': 'Versiones', 'html': DARK, 'mode': 'draft'})['version']
# Doctype preceded by a comment and no <head>: the served copy must stay in standards mode.
COMMENTED = post('/api/artifacts', {'title': 'Comentario', 'html': '<!-- exportado -->\n<!DOCTYPE html>\n' + DARK.replace('nota-laboratorio-colaborativo', 'nota-doctype-comentado')})['id']

LOG = """if(window.top===window){window.__bg=[];const t0=performance.now();const tick=()=>{const f=document.getElementById('artifact-frame');if(f&&document.body?.classList.contains('reading'))window.__bg.push([Math.round(performance.now()-t0),getComputedStyle(f).backgroundColor,f.dataset.surface||null]);requestAnimationFrame(tick);};requestAnimationFrame(tick);}"""
SCORE = """async d=>{const im=new Image();im.src='data:image/jpeg;base64,'+d;await im.decode();const c=document.getElementById('c');c.width=im.width;c.height=im.height;const x=c.getContext('2d');x.drawImage(im,0,0);const p=x.getImageData(0,0,c.width,c.height).data;let w=0,b=0,n=p.length/4;for(let i=0;i<p.length;i+=4){if(p[i]>225&&p[i+1]>225&&p[i+2]>225)w++;else if(p[i]<40&&p[i+1]<40&&p[i+2]<40)b++;}return [w/n,b/n];}"""
INNER = """()=>({compat:document.compatMode,theme:document.documentElement.dataset.theme||null,first:document.documentElement.firstChild?.nodeName||null,body:getComputedStyle(document.body).backgroundColor,version:new URLSearchParams(location.search).get('version')})"""

def lum(css):
    import re
    m = re.match(r'rgba?\((\d+), (\d+), (\d+)', css or '')
    return None if not m else .2126 * int(m[1]) + .7152 * int(m[2]) + .0722 * int(m[3])

def run(browser, parent_dark):
    ctx = browser.new_context(viewport={'width': 1440, 'height': 900}, color_scheme='dark' if parent_dark else 'light')
    ctx.add_init_script("try{localStorage.setItem('bottifact-portal-dark','%s')}catch{}" % ('true' if parent_dark else 'false'))
    ctx.add_init_script(LOG)
    def proxy(route):
        req = route.request
        headers = {k: v for k, v in req.headers.items() if k not in {'host', 'cookie', 'accept-encoding'}}
        if '/render' in req.url and DELAY: time.sleep(DELAY / 1000)
        r = owner.request(req.method, req.url, headers=headers, content=req.post_data_buffer, follow_redirects=False)
        route.fulfill(status=r.status_code, headers={k: v for k, v in r.headers.items() if k not in {'content-encoding', 'content-length'}}, body=r.content)
    ctx.route(ORIGIN + '/**', proxy)
    ctx.route('https://fonts.googleapis.com/**', lambda r: r.abort())
    pg = ctx.new_page(); errors = []; pg.on('pageerror', lambda e: errors.append(str(e)))
    cdp = ctx.new_cdp_session(pg); frames = []; phase = {'v': 'load-published'}
    def onf(ev):
        frames.append({'phase': phase['v'], 't': ev['metadata']['timestamp'], 'data': ev['data']})
        cdp.send('Page.screencastFrameAck', {'sessionId': ev['sessionId']})
    cdp.on('Page.screencastFrame', onf)
    pg.goto('about:blank'); cdp.send('Page.startScreencast', {'format': 'jpeg', 'quality': 60})
    inner = lambda: next(f for f in pg.frames if '/render' in f.url).evaluate(INNER)
    logs, states = {}, {}
    # The selector lives in the owner popover; choose a version the way its change handler sees it.
    choose = lambda vid: pg.evaluate("v=>{window.__bg=[];const s=document.getElementById('version');s.value=v;s.dispatchEvent(new Event('change'))}", vid)
    # target: the mode of the version the phase opens.
    steps = [('load-published', 'light', lambda: pg.goto(ORIGIN + '/a/' + AID, wait_until='commit')),
             ('select-draft', 'dark', lambda: choose(DRAFT)),
             ('select-published', 'light', lambda: choose(PUBLISHED)),
             ('url-draft', 'dark', lambda: pg.goto(ORIGIN + '/a/' + AID + '?version=' + DRAFT, wait_until='commit')),
             ('revisit-published', 'light', lambda: pg.goto(ORIGIN + '/a/' + AID, wait_until='commit')),
             ('commented-doctype', 'dark', lambda: pg.goto(ORIGIN + '/a/' + COMMENTED, wait_until='commit'))]
    for name, target, act in steps:
        phase['v'] = name
        act(); pg.wait_for_timeout(2500)
        log = pg.evaluate('()=>window.__bg')
        # Samples whose backing contradicts the version being opened (the parent shell before the API is excluded:
        # until the reader knows the version, data-surface is unset).
        wrong = [s for s in log if lum(s[1]) is not None and (lum(s[1]) < 128) != (target == 'dark')]
        logs[name] = log
        states[name] = {'target': target, 'samples': len(log), 'contradicting': len(wrong), 'firstWrong': wrong[:3], 'lastWrongMs': wrong[-1][0] if wrong else None,
                        'final': log[-1] if log else None, 'inner': inner()}
    # A report naming another version (a document being replaced) never paints; hostile payloads with the right one neither.
    fr = next(f for f in pg.frames if '/render' in f.url)
    bg = lambda: pg.evaluate("()=>getComputedStyle(document.getElementById('artifact-frame')).backgroundColor")
    send = "([color,version])=>new Promise(r=>{const id=crypto.randomUUID();addEventListener('message',e=>{if(e.data?.id===id)r(e.data)});parent.postMessage({bottifact:1,id,op:'surface',data:{color,version}},'*')})"
    mine = fr.evaluate("()=>new URLSearchParams(location.search).get('version')")
    probes = []
    for color, version in (([250, 0, 0], PUBLISHED), ('red;background:url(https://evil.test/x)', mine), ([300, 0, 0], mine), ([1, 2, 3], mine)):
        reply = fr.evaluate(send, [color, version])
        probes.append({'color': color, 'ownVersion': version == mine, 'reply': {k: reply.get(k) for k in ('data', 'error')}, 'frameBg': bg()})
    states['probes'] = probes
    cdp.send('Page.stopScreencast')
    sc = ctx.new_page(); sc.set_content('<canvas id=c></canvas>')
    t0 = frames[0]['t'] if frames else 0; rows = []
    for i, f in enumerate(frames):
        w, b = sc.evaluate(SCORE, f['data'])
        rows.append({'i': i, 'phase': f['phase'], 't': round(f['t'] - t0, 3), 'white': round(w, 4), 'black': round(b, 4)})
    summary = {}
    for name, target, _ in steps:
        rs = [r for r in rows if r['phase'] == name]
        summary[name] = {'target': target, 'frames': len(rs), 'whiteOver50': sum(r['white'] > .5 for r in rs), 'blackOver50': sum(r['black'] > .5 for r in rs),
                         'timeline': ''.join('W' if r['white'] > .5 else 'B' if r['black'] > .5 else '.' for r in rs)}
    ctx.close()
    return {'parentDark': parent_dark, 'summary': summary, 'states': states, 'errors': errors, 'rows': rows}

with sync_playwright() as p:
    browser = p.chromium.launch(channel=os.environ.get('CHANNEL', 'chrome'))
    results = [run(browser, dark) for dark in (False, True)]
    browser.close()
(OUT / f'{LABEL}.json').write_text(json.dumps({'label': LABEL, 'channel': os.environ.get('CHANNEL', 'chrome'), 'renderDelayMs': DELAY, 'results': results}, indent=1))
for r in results:
    print('parentDark' if r['parentDark'] else 'parentLight', 'errors', len(r['errors']))
    for name, s in r['summary'].items():
        st = r['states'][name]
        print(f"  {name:18} target={s['target']:5} screencast={s['timeline']:24} backing contradicts={st['contradicting']}/{st['samples']} final={st['final'] and st['final'][1:]} inner={st['inner']}")
    for probe in r['states']['probes']: print('  probe', json.dumps(probe))
tmp.cleanup()
