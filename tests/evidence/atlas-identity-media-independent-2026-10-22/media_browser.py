"""Independent media/link probe in real Chromium and WebKit against the portal shell (create_app behind a Playwright route).
Providers and external hosts are stubbed by route: no request leaves the machine. Signals come from stub postMessage, never iframe.onload.
usage: media_browser.py REPO OUTDIR SHOTS ENGINE"""
import json, sys, tempfile, time
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
u = store.user('owner@owner.test', 'Dueña Sintética')
owner = TestClient(app, base_url=ORIGIN, headers={'Origin': ORIGIN}); owner.cookies.set(COOKIE, store.session(u['id']))
core = REPO / 'packages/core'
recipes = ''.join((core / 'recipes' / r / 'example.html').read_text() for r in ('youtube', 'instagram', 'x-post'))
HTML = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="nota-documento" content="medios-independiente"><title>Medios</title><style>{(core/'styles/embeds.css').read_text()}</style></head>
<body><main><h1>Medios</h1><p id="parrafo">Un párrafo cualquiera que el lector puede pulsar para leer, seleccionar o desplazarse sin pedir nada externo.</p>
{recipes}
<figure class="embed embed-x" id="x-real" data-embed="x" data-embed-user="margen_test" data-embed-status="1234567890123"><blockquote class="embed-texto"><p>Texto citado.</p></blockquote>
<img src="https://pbs.twimg.com/media/remota.jpg" alt="remota"><figcaption class="embed-pie"><a data-embed-source href="https://evil.example/robado">Ver en X</a></figcaption></figure>
<footer><p>Autor: <a id="l-https" href="https://example.org/perfil">perfil</a> · <a id="l-mailto" href="mailto:autor@example.org">correo</a>
· <a id="l-http" href="http://example.org/inseguro">http</a> · <a id="l-cred" href="https://usuario:clave@example.org/">cred</a>
· <a id="l-js" href="javascript:void(document.title='js')">js</a> · <a id="l-rel" href="otra.html">relativo</a> · <a id="l-tel" href="tel:+5712345">tel</a></p></footer></main>
<script>{(core/'components/embeds.js').read_text()}</script></body></html>"""
pub = owner.post('/api/artifacts', json={'title': 'Medios', 'html': HTML}); pub.raise_for_status()
AID, V1 = pub.json()['id'], pub.json()['version']
v2 = owner.post('/api/artifacts/' + AID + '/versions', json={'title': 'Medios', 'html': HTML.replace('Medios</h1>', 'Medios v2</h1>')}); v2.raise_for_status()
V2 = v2.json()['version']
results = {'engine': ENGINE, 'checks': [], 'external_requests': []}
def check(name, ok, detail=None, severity=None):
    results['checks'].append({'name': name, 'ok': bool(ok), 'detail': detail, 'severity_if_fail': severity})
    print(('PASS ' if ok else 'FAIL ') + name, '' if ok else json.dumps(detail, ensure_ascii=False, default=str)[:500], flush=True)

YT_STUB = """<!doctype html><script>
addEventListener('message',e=>{if(String(e.data).includes('listening')){parent.postMessage(JSON.stringify({event:'onReady'}),'*');parent.postMessage(JSON.stringify({event:'infoDelivery',info:{playerState:1}}),'*');}});
</script><p>stub youtube</p>"""
IG_STUB = """<!doctype html><script>parent.postMessage(JSON.stringify({type:'MEASURE',details:{height:5000}}),'*');parent.postMessage(JSON.stringify({type:'MEASURE',details:{height:900}}),'*');</script><p>stub instagram</p>"""
EXT_STUB = """<!doctype html><title>externo</title><script>window.__info={opener:window.opener===null?'null':typeof window.opener,referrer:document.referrer}</script><p>externo</p>"""

def proxy(route):
    req = route.request
    headers = {k: v for k, v in req.headers.items() if k not in {'host', 'cookie', 'accept-encoding'}}
    r = owner.request(req.method, req.url, headers=headers, content=req.post_data_buffer, follow_redirects=False)
    route.fulfill(status=r.status_code, headers={k: v for k, v in r.headers.items() if k not in {'content-encoding', 'content-length'}}, body=r.content)

def external(route):
    url = route.request.url
    results['external_requests'].append({'url': url, 't': time.time(), 'phase': phase['now']})
    if url.startswith('https://www.youtube-nocookie.com/embed/'): return route.fulfill(status=200, content_type='text/html', body=YT_STUB)
    if url.startswith('https://www.instagram.com/') and url.endswith('/embed/'): return route.fulfill(status=200, content_type='text/html', body=IG_STUB)
    return route.fulfill(status=200, content_type='text/html', body=EXT_STUB)
phase = {'now': 'load'}

with sync_playwright() as p:
    browser = getattr(p, ENGINE).launch()
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    ctx.route(ORIGIN + '/**', proxy)
    ctx.route(lambda url: not url.startswith(ORIGIN) and not url.startswith('data:') and not url.startswith('about:') and not url.startswith('blob:'), external)
    popups = []
    ctx.on('page', lambda pg: popups.append(pg))
    pg = ctx.new_page(); errors = []; pg.on('pageerror', lambda e: errors.append(str(e)))
    console = []; pg.on('console', lambda m: console.append(m.text) if m.type in ('error', 'warning') else None)

    def frame():
        for _ in range(150):
            fr = next((f for f in pg.frames if '/render' in f.url), None)
            if fr:
                try:
                    if fr.evaluate("()=>!!window.BottifactReviewBridge&&!!document.querySelector('[data-embed-listo]')"): return fr
                except Exception: pass
            pg.wait_for_timeout(100)
        raise RuntimeError('frame not ready')
    def dialog():
        return pg.evaluate("""()=>{const d=document.querySelector('.media-dialog');const f=d?.querySelector('iframe');return {open:!!d?.open,provider:d?.dataset.provider,title:d?.querySelector('h2')?.textContent,
          status:d?.querySelector('.media-status')?.textContent,link:d?.querySelector('.media-source')?.href,linkText:d?.querySelector('.media-source')?.textContent,linkTarget:d?.querySelector('.media-source')?.target,linkRel:d?.querySelector('.media-source')?.rel,
          players:document.querySelectorAll('.media-player').length,src:f?.getAttribute('src'),sandbox:f?.getAttribute('sandbox'),allow:f?.getAttribute('allow'),referrerpolicy:f?.getAttribute('referrerpolicy'),height:f?.style.height,
          active:document.activeElement?.className+'|'+document.activeElement?.textContent,ua:navigator.userActivation?{a:navigator.userActivation.isActive}:null}}""")
    def close_dialog():
        pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    def popups_since(n):
        pg.wait_for_timeout(700); return popups[n:]

    resp = pg.goto(ORIGIN + '/a/' + AID)
    csp = resp.headers.get('content-security-policy', '')
    fr = frame(); pg.wait_for_timeout(2500)
    results['portal_csp'] = csp
    check('portal reader CSP frame-src exact provider prefixes only',
          "frame-src 'self' https://www.youtube-nocookie.com/embed/ https://www.instagram.com/p/ https://www.instagram.com/reel/;" in csp, csp)
    attrs = pg.evaluate("()=>{const f=document.querySelector('#artifact-frame');return {sandbox:f.getAttribute('sandbox'),allow:f.getAttribute('allow')}}")
    check('artifact iframe sandbox unchanged (allow-scripts allow-downloads)', attrs['sandbox'] == 'allow-scripts allow-downloads', attrs)
    origin_in_frame = fr.evaluate("()=>{let p='blocked';try{p=String(parent.document.title)}catch(e){};return {origin:self.origin,parentAccess:p}}")
    check('artifact stays opaque and cannot read the portal', origin_in_frame == {'origin': 'null', 'parentAccess': 'blocked'}, origin_in_frame)
    check('no provider/external request before any click', not results['external_requests'], results['external_requests'])
    btns = fr.evaluate("()=>[...document.querySelectorAll('[data-embed]')].map(e=>({p:e.dataset.embed,btnHidden:e.querySelector('[data-embed-load]')?.hidden,links:[...e.querySelectorAll('a[data-embed-source]')].map(a=>[a.href,a.target,a.rel])}))")
    results['cards'] = btns
    check('YouTube and Instagram cards expose a load button, X does not', [b['btnHidden'] for b in btns] == [False, False, None, None], btns)

    # 1. Scripted request without a click (artifact code) must not open anything.
    r = fr.evaluate("""(v)=>new Promise(res=>{const id='nc'+Math.random();addEventListener('message',e=>{if(e.data?.id===id)res(e.data)});parent.postMessage({bottifact:1,id,op:'embed',data:{provider:'youtube',id:'M7lc1UVf-VE',version:v}},'*');setTimeout(()=>res('timeout'),3000)})""", V1)
    d = dialog()
    check('scripted embed without user activation is refused and opens nothing', not d['open'] and not results['external_requests'], {'reply': r, 'dialog': d}, 'high')

    # 2. Real click on the YouTube load button.
    phase['now'] = 'yt-click'; n0 = len(results['external_requests'])
    fr.locator('[data-embed="youtube"] [data-embed-load]').click(); pg.wait_for_timeout(2500)
    d = dialog(); results['youtube_dialog'] = d
    pg.screenshot(path=str(SHOTS / f'{ENGINE}-youtube.png'))
    exp = 'https://www.youtube-nocookie.com/embed/M7lc1UVf-VE?autoplay=1&mute=1&playsinline=1&rel=0&enablejsapi=1&origin=https%3A%2F%2Fportal.test'
    if d.get('open') and d.get('src') is None:
        check('YouTube click opens the portal dialog with exact player URL', False, d, 'high')
    elif d.get('open') and d['src'] != exp and d['title']:
        check('YouTube click opens the portal dialog with exact player URL', False, d, 'high')
    else:
        check('YouTube click opens the portal dialog with exact player URL', d.get('open') and d.get('src') == exp, d, 'high')
    check('player sandbox/allow/referrer exact', d.get('sandbox') == 'allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox allow-presentation' and d.get('allow') == 'autoplay; encrypted-media; picture-in-picture; fullscreen' and d.get('referrerpolicy') == 'strict-origin', d)
    check('player liveness comes from provider postMessage (stub says playing)', 'Reproduciendo' in (d.get('status') or ''), d)
    card_status = fr.evaluate("()=>document.querySelector('[data-embed=youtube] [data-embed-status]').textContent")
    results['youtube_card_status'] = card_status
    yt_reqs = [x['url'] for x in results['external_requests'][n0:]]
    check('only the exact player URL is requested after the click', yt_reqs == [exp], yt_reqs)
    # forged provider signal from the artifact window must be ignored
    fr.evaluate("()=>parent.postMessage(JSON.stringify({event:'onError',info:150}),'*')"); pg.wait_for_timeout(300)
    check('forged provider error from the artifact is ignored', 'insertado' not in (dialog().get('status') or ''), dialog())
    close_dialog()
    d = dialog(); focus = fr.evaluate("()=>document.activeElement?.textContent")
    check('Escape closes and removes the player', not d['open'] and d['players'] == 0, d)
    check('focus returns to the card button inside the artifact', focus == 'Cargar video', focus)

    # 3. Repeated open/close cycles never stack players or listeners.
    for i in range(4):
        fr.locator('[data-embed="youtube"] [data-embed-load]').click(); pg.wait_for_timeout(120 * (i + 1))
        if i % 2: close_dialog()
        else: pg.locator('.media-dialog .dialog-head button').click(); pg.wait_for_timeout(50)
    fr.locator('[data-embed="youtube"] [data-embed-load]').click()
    # two requests in the same activation (double message) must not stack players
    fr.evaluate("(v)=>{for(let i=0;i<3;i++)parent.postMessage({bottifact:1,id:'dbl'+i,op:'embed',data:{provider:'youtube',id:'M7lc1UVf-VE',version:v}},'*')}", V2 if pg.evaluate("()=>document.querySelector('#version').value") == V2 else V1)
    pg.wait_for_timeout(1200); d = dialog()
    check('repeated opening keeps at most one player and the dialog usable', d['players'] <= 1 and d['open'], d)
    close_dialog(); check('after repeated cycles closing leaves zero players', dialog()['players'] == 0, dialog())

    # 4. Instagram.
    phase['now'] = 'ig-click'; n0 = len(results['external_requests'])
    fr.locator('[data-embed="instagram"] [data-embed-load]').click(); pg.wait_for_timeout(2000)
    d = dialog(); results['instagram_dialog'] = d
    pg.screenshot(path=str(SHOTS / f'{ENGINE}-instagram.png'))
    ig = [x['url'] for x in results['external_requests'][n0:]]
    check('Instagram click mounts exact /embed/ URL with no-referrer', d['open'] and d['src'] and d['src'].startswith('https://www.instagram.com/') and d['src'].endswith('/embed/') and d['referrerpolicy'] == 'no-referrer', {'d': d, 'reqs': ig})
    check('Instagram MEASURE height bounded (5000 ignored, 900 applied)', d.get('height') == '900px', d)
    close_dialog()

    # 5. Version switch / navigation cleans an open player.
    fr.locator('[data-embed="youtube"] [data-embed-load]').click(); pg.wait_for_timeout(800)
    pg.evaluate("()=>{history.pushState({probe:1},'');history.back()}"); pg.wait_for_timeout(800); d = dialog()
    check('history navigation (popstate) closes dialog and removes player', not d['open'] and d['players'] == 0, d)
    try: fr = frame()
    except Exception: pg.goto(ORIGIN + '/a/' + AID); fr = frame()
    fr.locator('[data-embed="youtube"] [data-embed-load]').click(); pg.wait_for_timeout(800)
    target = V1 if pg.evaluate("()=>document.querySelector('#version').value") != V1 else V2
    pg.evaluate("(v)=>{const s=document.querySelector('#version');s.value=v;s.dispatchEvent(new Event('change'))}", target); pg.wait_for_timeout(1500)
    d = dialog()
    check('switching version closes dialog and removes player', not d['open'] and d['players'] == 0, d)
    fr = frame(); pg.wait_for_timeout(500)
    cur = pg.evaluate("()=>document.querySelector('#version').value")
    stale = V2 if cur == V1 else V1
    fr.locator('#parrafo').click()
    r = fr.evaluate("""(v)=>new Promise(res=>{const id='st'+Math.random();addEventListener('message',e=>{if(e.data?.id===id)res(e.data)});parent.postMessage({bottifact:1,id,op:'embed',data:{provider:'youtube',id:'M7lc1UVf-VE',version:v}},'*');setTimeout(()=>res('timeout'),3000)})""", stale)
    check('embed request carrying another version is refused', not dialog()['open'], r)

    # 6. Activation laundering: a click on plain text, then artifact script asks for an external link / player.
    phase['now'] = 'launder'; n_pop = len(popups); n0 = len(results['external_requests'])
    fr.evaluate("""(v)=>document.querySelector('#parrafo').addEventListener('click',()=>parent.postMessage({bottifact:1,id:'lx'+Math.random(),op:'external',data:{href:'https://attacker.example/phish',version:v}},'*'),{once:true})""", cur)
    fr.locator('#parrafo').click(); new = popups_since(n_pop); d = dialog()
    laundered = [x.url for x in new] + ([d['link']] if d['open'] else [])
    results['launder_external'] = {'popups': [x.url for x in new], 'dialog': d}
    check('click on plain text cannot be reused by artifact script to open an arbitrary external URL', not any('attacker.example' in (x or '') for x in laundered), results['launder_external'], 'medium')
    for x in new: x.close()
    if d['open']: close_dialog()
    fr.evaluate("""(v)=>document.querySelector('#parrafo').addEventListener('click',()=>parent.postMessage({bottifact:1,id:'le'+Math.random(),op:'embed',data:{provider:'youtube',id:'dQw4w9WgXcQ',version:v}},'*'),{once:true})""", cur)
    fr.locator('#parrafo').click(); pg.wait_for_timeout(1500); d = dialog()
    results['launder_embed'] = d
    check('click on plain text cannot be reused to load a different provider player', not (d['open'] and d['src']), d, 'medium')
    if d['open']: close_dialog()

    # 7. Footer https link: real click opens one tab, no opener, no referrer.
    phase['now'] = 'footer'; n_pop = len(popups)
    fr.locator('#l-https').click(); new = popups_since(n_pop); d = dialog()
    info = None
    if new:
        try: new[0].wait_for_load_state(); info = new[0].evaluate('()=>({url:location.href,...window.__info})')
        except Exception as e: info = {'error': str(e)}
    results['footer_https'] = {'popups': [x.url for x in new], 'info': info, 'dialog': d}
    check('footer https link opens exactly one tab or a usable fallback', (len(new) == 1 and info and info.get('url') == 'https://example.org/perfil') or (d['open'] and d['link'] == 'https://example.org/perfil'), results['footer_https'], 'high')
    if new: check('opened tab has no opener and no referrer', info and info.get('opener') == 'null' and info.get('referrer') == '', info)
    for x in new: x.close()
    if d['open']:
        pg.screenshot(path=str(SHOTS / f'{ENGINE}-footer-fallback.png')); close_dialog()

    # 8. Forced popup block → fallback dialog with usable link.
    pg.evaluate("()=>{window.__open=window.open;window.open=()=>null}")
    fr.locator('#l-https').click(); pg.wait_for_timeout(700); d = dialog(); results['blocked_fallback'] = d
    pg.screenshot(path=str(SHOTS / f'{ENGINE}-blocked-fallback.png'))
    check('blocked popup shows dialog with the exact link, new tab target and focus on it', d['open'] and d['link'] == 'https://example.org/perfil' and d['linkTarget'] == '_blank' and 'noopener' in d['linkRel'] and 'media-source' in d['active'], d)
    pg.evaluate("()=>{window.open=window.__open}")
    n_pop = len(popups)
    if d['open']:
        pg.locator('.media-dialog .media-source').click(); new = popups_since(n_pop)
        check('fallback link opens the tab on click', len(new) == 1 and new[0].url.startswith('https://example.org/perfil'), [x.url for x in new])
        for x in new: x.close()
        close_dialog()

    # 9. X source link via open-source.
    n_pop = len(popups)
    results['x_href'] = fr.evaluate("()=>document.querySelector('#x-real a').href")
    check('X source href regenerated from ID (authored href ignored)', results['x_href'] == 'https://x.com/margen_test/status/1234567890123', results['x_href'])
    fr.locator('#x-real a').click(); new = popups_since(n_pop); d = dialog()
    results['x_source'] = {'popups': [x.url for x in new], 'dialog': d}
    check('X source link opens x.com status URL (tab or fallback)', any(x.url.startswith('https://x.com/') for x in new) or (d['open'] and (d['link'] or '').startswith('https://x.com/')), results['x_source'])
    for x in new: x.close()
    if d['open']: close_dialog()

    # 10. Rejected / other schemes give visible feedback and never break the reader.
    for sel in ['#l-cred', '#l-http', '#l-rel', '#l-tel', '#l-mailto']:
        n_pop = len(popups); n0 = len(results['external_requests'])
        before = fr.url
        try: fr.locator(sel).click(timeout=3000)
        except Exception as e: pass
        pg.wait_for_timeout(900)
        now_frame = next((f for f in pg.frames if f.name == '' and f.parent_frame == pg.main_frame and 'render' in (f.url or '')), None)
        art_url = pg.evaluate("()=>{try{return document.querySelector('#artifact-frame').src}catch(e){return 'x'}}")
        frames = [f.url for f in pg.frames]
        d = dialog(); new = [x.url for x in popups_since(n_pop)]
        reqs = [x['url'] for x in results['external_requests'][n0:]]
        results.setdefault('schemes', {})[sel] = {'popups': new, 'dialog': {k: d[k] for k in ('open', 'link', 'title')}, 'frames': frames, 'reqs': reqs}
        if d['open']: close_dialog()
        for x in popups[n_pop:]:
            try: x.close()
            except Exception: pass
        try:
            fr = frame()
        except Exception:
            pg.goto(ORIGIN + '/a/' + AID); fr = frame()
    sc = results['schemes']
    check('credentialed https link is not opened', not sc['#l-cred']['popups'] and not sc['#l-cred']['dialog']['open'], sc['#l-cred'])
    check('credentialed https link gives the reader visible feedback', sc['#l-cred']['dialog']['open'], sc['#l-cred'], 'low')
    check('http:// footer link is usable (tab or fallback) or explained', bool(sc['#l-http']['popups']) or sc['#l-http']['dialog']['open'], sc['#l-http'], 'medium')
    check('mailto opens nothing in a new browsing context and stays in the reader', not any('render' not in f and f.startswith('mailto') for f in sc['#l-mailto']['frames']), sc['#l-mailto'])
    results['errors'] = errors; results['console'] = console[-30:]
    browser.close()
(OUT / f'media-{ENGINE}.json').write_text(json.dumps(results, indent=1, ensure_ascii=False, default=str))
print(sum(c['ok'] for c in results['checks']), '/', len(results['checks']))
tmp.cleanup()
