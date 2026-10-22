"""Body background images must keep reaching the canvas when the bridge backs the root (reviewer repro, adapted).
usage: backing.py REPO OUTDIR LABEL. Disposable store, top-level /render (real CSP sandbox)."""
import json, re, sys, tempfile
from pathlib import Path
REPO, OUT, LABEL = Path(sys.argv[1]).resolve(), Path(sys.argv[2]), sys.argv[3]
sys.path.insert(0, str(REPO))
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
from portal.app import create_app, COOKIE
ORIGIN = 'https://portal.test'
OUT.mkdir(parents=True, exist_ok=True)
tmp = tempfile.TemporaryDirectory()
app = create_app(tmp.name, origin=ORIGIN, issuer='https://identity.test', audience='our-app'); store = app.state.store
owner = TestClient(app, base_url=ORIGIN, headers={'Origin': ORIGIN})
u = store.user('owner@example.com', 'P'); owner.cookies.set(COOKIE, store.session(u['id']))
src = (REPO / 'examples/generated/collaborative.html').read_text()
short = re.sub(r'(<main\b[^>]*>).*?(</main>)', r'\1<h1>Corto</h1><p>Una línea.</p>\2', src, count=1, flags=re.S)
def family(html, fam, mode):
    html = re.sub(r'(<meta name="nota-tema-inicial" content=")[^"]*', r'\g<1>' + fam, html)
    return re.sub(r'(<meta name="nota-modo-inicial" content=")[^"]*', r'\g<1>' + mode, html)
GRAD = '<style>body{background-image:radial-gradient(circle at 50% 100%,#ff0000 0,#ff0000 40px,transparent 41px)}</style></head>'
DOCS = {
    'blueprint-light-short': family(short, 'blueprint', 'light'),
    'margen-custom-body-gradient-short': short.replace('</head>', GRAD, 1),
    'foreign-papel-body-gradient': '<!doctype html><title>F</title><meta name="nota-documento" content="probe-f"><style>:root{--papel:#fafafa}body{margin:0;background:#fafafa radial-gradient(circle at 50% 100%,#ff0000 0,#ff0000 40px,transparent 41px)}</style><p>Ajeno con --papel propio.</p>',
    'foreign-body-image-fixed': '<!doctype html><title>G</title><meta name="nota-documento" content="probe-g"><style>:root{--papel:#ffffff}body{background:#fff linear-gradient(#00f,#00f) no-repeat 0 100%/100% 30px fixed}</style><p>Barra azul fija abajo.</p>',
}
def pub(k,v):
    r=owner.post('/api/artifacts', json={'title': k, 'html': v}); assert r.status_code<300,(k,r.status_code,r.text[:300]); return r.json()['id']
ids = {k: pub(k,v) for k, v in DOCS.items()}
def proxy(route):
    req = route.request; headers = {k: v for k, v in req.headers.items() if k not in {'host', 'cookie', 'accept-encoding'}}
    r = owner.request(req.method, req.url, headers=headers, content=req.post_data_buffer, follow_redirects=False)
    route.fulfill(status=r.status_code, headers={k: v for k, v in r.headers.items() if k not in {'content-encoding', 'content-length'}}, body=r.content)
INNER = "()=>{const r=document.documentElement,b=document.body;return {html:getComputedStyle(r).backgroundColor,body:getComputedStyle(b).backgroundColor,bodyImage:getComputedStyle(b).backgroundImage.slice(0,60),backed:r.hasAttribute('data-margen-surface'),theme:r.dataset.theme||null,family:r.dataset.themeFamily||null,bodyBottom:Math.round(b.getBoundingClientRect().bottom),vh:innerHeight}}"
res = []
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome'); ctx = b.new_context(viewport={'width': 1000, 'height': 800})
    ctx.route(ORIGIN + '/**', proxy); ctx.route('https://fonts.googleapis.com/**', lambda r: r.abort())
    for k, aid in ids.items():
        pg = ctx.new_page(); pg.goto(ORIGIN + '/api/artifacts/' + aid + '/render'); pg.wait_for_timeout(1200)
        shot = Path(tmp.name) / f'{k}.png'; pg.screenshot(path=str(shot))
        px = pg.evaluate("""async u=>{const im=new Image();im.src=u;await im.decode();const c=document.createElement('canvas');c.width=im.width;c.height=im.height;const x=c.getContext('2d');x.drawImage(im,0,0);const g=(X,Y)=>Array.from(x.getImageData(X,Y,1,1).data.slice(0,3));return {bottomCenter:g(500,795),midLeft:g(5,400),bottomLeft:g(5,795)};}""",
                         'data:image/png;base64,' + __import__('base64').b64encode(shot.read_bytes()).decode())
        res.append({'doc': k, 'inner': pg.evaluate(INNER), 'pixels': px}); pg.close()
    b.close()
(OUT / f'{LABEL}-backing.json').write_text(json.dumps(res, indent=1))
for r in res: print(LABEL, r['doc'], json.dumps(r['inner']), r['pixels'])
tmp.cleanup()
