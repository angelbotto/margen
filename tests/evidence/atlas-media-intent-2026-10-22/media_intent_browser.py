"""Host-intent probe for D2/D7/D8 in real Chromium and WebKit against the portal shell (create_app behind a Playwright route).
Derived from atlas-identity-media-independent-2026-10-22/media_browser.py. Expected flow is two clicks: the document asks,
the portal shows the destination, and only a click on a portal control opens a tab or connects to a provider.
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
          active:document.activeElement?.className+'|'+document.activeElement?.textContent,intent:d?.dataset.intent,place:d?.querySelector('.media-place')?.textContent,
          tag:d?.querySelector('.media-tag')?.textContent,play:!!d?.querySelector('.media-play')&&!d.querySelector('.media-play').hidden,linkHidden:!!d?.querySelector('.media-source')?.hidden,ua:navigator.userActivation?{a:navigator.userActivation.isActive}:null}}""")
    def close_dialog():
        pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    def popups_since(n):
        pg.wait_for_timeout(700); return popups[n:]

    def ext_since(n): return [x['url'] for x in results['external_requests'][n:]]
    def host_play(): pg.locator('.media-dialog .media-play').click(); pg.wait_for_timeout(1500)
    def frame_intact(): return any('/render' in f.url for f in pg.frames) and not any(f.url.startswith('chrome-error') for f in pg.frames)

    resp = pg.goto(ORIGIN + '/a/' + AID)
    csp = resp.headers.get('content-security-policy', '')
    fr = frame(); pg.wait_for_timeout(2500)
    check('portal reader CSP frame-src exact provider prefixes only',
          "frame-src 'self' https://www.youtube-nocookie.com/embed/ https://www.instagram.com/p/ https://www.instagram.com/reel/;" in csp, csp)
    attrs = pg.evaluate("()=>{const f=document.querySelector('#artifact-frame');return {sandbox:f.getAttribute('sandbox')}}")
    check('artifact iframe sandbox unchanged (allow-scripts allow-downloads)', attrs['sandbox'] == 'allow-scripts allow-downloads', attrs)
    check('artifact stays opaque', fr.evaluate("()=>self.origin") == 'null')
    check('no provider/external request on load', not results['external_requests'], results['external_requests'])
    pg.evaluate("()=>{window.__opens=0;const o=window.open;window.open=(...a)=>{window.__opens++;return o.apply(window,a)}}")

    # 1. Scripted request without any click.
    fr.evaluate("""(v)=>new Promise(res=>{const id='nc'+Math.random();addEventListener('message',e=>{if(e.data?.id===id)res(e.data)});parent.postMessage({bottifact:1,id,op:'embed',data:{provider:'youtube',id:'M7lc1UVf-VE',version:v}},'*');setTimeout(()=>res('timeout'),3000)})""", V1)
    check('scripted embed without user activation opens nothing', not dialog()['open'] and not results['external_requests'], dialog(), 'high')

    # 2. D2 · activation laundering: click on plain text, artifact script asks for an external URL and another player.
    phase['now'] = 'launder'; n_pop = len(popups); n0 = len(results['external_requests'])
    fr.evaluate("""(v)=>document.querySelector('#parrafo').addEventListener('click',()=>parent.postMessage({bottifact:1,id:'lx'+Math.random(),op:'external',data:{href:'https://attacker.example/phish',version:v}},'*'),{once:true})""", V1)
    fr.locator('#parrafo').click(); new = popups_since(n_pop); d = dialog()
    results['launder_external'] = {'popups': [x.url for x in new], 'dialog': d, 'reqs': ext_since(n0)}
    check('D2 laundered external: no tab, no request; at most a portal preview naming the real destination',
          not new and not ext_since(n0) and (not d['open'] or (d['intent'] == 'link' and d['place'] == 'attacker.example')), results['launder_external'], 'medium')
    if d['open']: pg.screenshot(path=str(SHOTS / f'{ENGINE}-launder-preview.png')); close_dialog()
    fr.evaluate("""(v)=>document.querySelector('#parrafo').addEventListener('click',()=>parent.postMessage({bottifact:1,id:'le'+Math.random(),op:'embed',data:{provider:'youtube',id:'dQw4w9WgXcQ',version:v}},'*'),{once:true})""", V1)
    fr.locator('#parrafo').click(); pg.wait_for_timeout(1500); d = dialog()
    results['launder_embed'] = {'dialog': d, 'reqs': ext_since(n0)}
    check('D2 laundered embed: no player and no provider request without the portal button', not d['src'] and d['players'] == 0 and not ext_since(n0), results['launder_embed'], 'medium')
    if d['open']: close_dialog()
    check('host never calls window.open', pg.evaluate('()=>window.__opens') == 0, pg.evaluate('()=>window.__opens'))

    # 3. YouTube: card click shows the portal preview (0 network); the portal button mounts the exact player.
    phase['now'] = 'yt'; n0 = len(results['external_requests'])
    fr.locator('[data-embed="youtube"] [data-embed-load]').click(); pg.wait_for_timeout(1500)
    d = dialog(); results['youtube_preview'] = d
    pg.screenshot(path=str(SHOTS / f'{ENGINE}-youtube-preview.png'))
    check('card click opens portal preview with neutral close focus, no player', d['open'] and d['intent'] == 'confirm' and d['play'] and d['players'] == 0 and 'icon|' in d['active'], d, 'high')
    check('0 provider requests before the portal button', not ext_since(n0), ext_since(n0), 'high')
    check('preview link is the exact source in a new tab', d['link'] == 'https://www.youtube.com/watch?v=M7lc1UVf-VE' and d['linkTarget'] == '_blank' and 'noopener' in d['linkRel'], d)
    host_play(); d = dialog(); results['youtube_dialog'] = d
    exp = 'https://www.youtube-nocookie.com/embed/M7lc1UVf-VE?autoplay=1&mute=1&playsinline=1&rel=0&enablejsapi=1&origin=https%3A%2F%2Fportal.test'
    check('portal button mounts exact player URL', d['open'] and d['src'] == exp and d['intent'] == 'player', d, 'high')
    check('player sandbox/allow/referrer exact', d.get('sandbox') == 'allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox allow-presentation' and d.get('allow') == 'autoplay; encrypted-media; picture-in-picture; fullscreen' and d.get('referrerpolicy') == 'strict-origin', d)
    check('playback liveness from provider postMessage (stub says playing)', 'Reproduciendo' in (d.get('status') or ''), d)
    check('only the exact player URL requested after the portal button', ext_since(n0) == [exp], ext_since(n0))
    pg.screenshot(path=str(SHOTS / f'{ENGINE}-youtube-player.png'))
    fr.evaluate("()=>parent.postMessage(JSON.stringify({event:'onError',info:150}),'*')"); pg.wait_for_timeout(300)
    check('forged provider error from the artifact is ignored', 'insertado' not in (dialog().get('status') or ''), dialog())
    close_dialog(); d = dialog()
    focus = fr.evaluate("()=>document.activeElement?.textContent")
    card = fr.evaluate("()=>document.querySelector('[data-embed=youtube] [data-embed-status]').textContent")
    check('Escape closes and removes the player', not d['open'] and d['players'] == 0, d)
    check('focus returns to the card button inside the artifact', focus == 'Cargar video', focus)
    check('D8 card no longer claims an open player after closing', 'abierto' not in card.lower(), card, 'low')

    # 4. Escape on the preview: nothing loaded, focus back.
    n0 = len(results['external_requests'])
    fr.locator('[data-embed="youtube"] [data-embed-load]').click(); pg.wait_for_timeout(500); close_dialog()
    check('cancelling the preview loads nothing and returns focus', not ext_since(n0) and fr.evaluate("()=>document.activeElement?.textContent") == 'Cargar video', ext_since(n0))

    # 5. Repeated cycles and double messages.
    for i in range(4):
        fr.locator('[data-embed="youtube"] [data-embed-load]').click(); pg.wait_for_timeout(150)
        if i % 2: host_play()
        if i % 3: close_dialog()
        else: pg.locator('.media-dialog .dialog-head button').click(); pg.wait_for_timeout(80)
    fr.locator('[data-embed="youtube"] [data-embed-load]').click(); pg.wait_for_timeout(200); host_play()
    fr.evaluate("(v)=>{for(let i=0;i<3;i++)parent.postMessage({bottifact:1,id:'dbl'+i,op:'embed',data:{provider:'youtube',id:'M7lc1UVf-VE',version:v}},'*')}", V1)
    pg.wait_for_timeout(1000); d = dialog()
    check('repeated opening keeps at most one player and the dialog usable', d['players'] <= 1 and d['open'], d)
    close_dialog(); check('after repeated cycles closing leaves zero players', dialog()['players'] == 0, dialog())

    # 6. Instagram.
    phase['now'] = 'ig'; n0 = len(results['external_requests'])
    fr.locator('[data-embed="instagram"] [data-embed-load]').click(); pg.wait_for_timeout(800)
    check('Instagram preview makes no request', dialog()['intent'] == 'confirm' and not ext_since(n0), {'d': dialog(), 'reqs': ext_since(n0)})
    host_play(); d = dialog()
    check('Instagram portal button mounts exact /embed/ URL with no-referrer', d['open'] and (d['src'] or '').endswith('/embed/') and d['referrerpolicy'] == 'no-referrer', d)
    check('Instagram MEASURE height bounded (5000 ignored, 900 applied)', d.get('height') == '900px', d)
    pg.screenshot(path=str(SHOTS / f'{ENGINE}-instagram.png'))
    close_dialog()

    # 7. popstate and version switch clean an open player.
    fr.locator('[data-embed="youtube"] [data-embed-load]').click(); pg.wait_for_timeout(300); host_play()
    pg.evaluate("()=>{history.pushState({probe:1},'');history.back()}"); pg.wait_for_timeout(800); d = dialog()
    check('popstate closes dialog and removes player', not d['open'] and d['players'] == 0, d)
    fr = frame()
    fr.locator('[data-embed="youtube"] [data-embed-load]').click(); pg.wait_for_timeout(300); host_play()
    cur = pg.evaluate("()=>document.querySelector('#version').value")
    pg.evaluate("(v)=>{const s=document.querySelector('#version');s.value=v;s.dispatchEvent(new Event('change'))}", V1 if cur != V1 else V2); pg.wait_for_timeout(1500)
    d = dialog(); check('switching version closes dialog and removes player', not d['open'] and d['players'] == 0, d)
    fr = frame(); pg.wait_for_timeout(500)
    cur = pg.evaluate("()=>document.querySelector('#version').value")
    fr.locator('#parrafo').click()
    fr.evaluate("(v)=>parent.postMessage({bottifact:1,id:'st',op:'embed',data:{provider:'youtube',id:'M7lc1UVf-VE',version:v}},'*')", V2 if cur == V1 else V1); pg.wait_for_timeout(800)
    check('request carrying another version is refused', not dialog()['open'], dialog())

    # 8. Footer https: first click previews, portal link opens one tab without opener/referrer.
    phase['now'] = 'footer'; n_pop = len(popups); n0 = len(results['external_requests'])
    fr.locator('#l-https').click(); new = popups_since(n_pop); d = dialog(); results['footer_preview'] = d
    pg.screenshot(path=str(SHOTS / f'{ENGINE}-footer-preview.png'))
    check('footer https click shows portal preview, no tab, no request yet', not new and not ext_since(n0) and d['open'] and d['intent'] == 'link' and d['place'] == 'example.org' and d['link'] == 'https://example.org/perfil' and 'media-source' in d['active'], {'d': d, 'new': [x.url for x in new]}, 'high')
    pg.locator('.media-dialog .media-source').click(); new = popups_since(n_pop); info = None
    if new:
        try: new[0].wait_for_load_state(); info = new[0].evaluate('()=>({url:location.href,...window.__info})')
        except Exception as e: info = {'error': str(e)}
    results['footer_open'] = {'popups': [x.url for x in new], 'info': info, 'dialog_open': dialog()['open']}
    check('portal link opens exactly one tab, no opener, no referrer, dialog closes', len(new) == 1 and info and info.get('url') == 'https://example.org/perfil' and info.get('opener') == 'null' and info.get('referrer') == '' and not dialog()['open'], results['footer_open'], 'high')
    for x in new: x.close()

    # 9. X source.
    n_pop = len(popups)
    check('X source href regenerated from ID', fr.evaluate("()=>document.querySelector('#x-real a').href") == 'https://x.com/margen_test/status/1234567890123')
    fr.locator('#x-real a').click(); new = popups_since(n_pop); d = dialog()
    check('X source click previews x.com in the portal, no tab yet', not new and d['open'] and d['link'] == 'https://x.com/margen_test/status/1234567890123', {'d': d, 'new': [x.url for x in new]})
    pg.locator('.media-dialog .media-source').click(); new = popups_since(n_pop)
    check('portal link opens the x.com status', len(new) == 1 and new[0].url.startswith('https://x.com/margen_test/status/'), [x.url for x in new])
    for x in new: x.close()
    pg.wait_for_timeout(300); focus = fr.evaluate("()=>document.activeElement?.textContent")
    check('focus returns to the X source link', focus == 'Ver en X', focus, 'low')

    # 10. D7 · every scheme keeps the document; each gets an honest portal answer.
    expect = {'#l-cred': ('info', None), '#l-http': ('link', 'http://example.org/inseguro'), '#l-rel': ('info', None),
              '#l-tel': ('link', 'tel:+5712345'), '#l-mailto': ('link', 'mailto:autor@example.org')}
    for sel, (intent, link) in expect.items():
        n_pop = len(popups); n0 = len(results['external_requests'])
        fr.locator(sel).click(); pg.wait_for_timeout(700)
        d = dialog(); new = [x.url for x in popups_since(n_pop)]
        row = {'dialog': {k: d[k] for k in ('open', 'intent', 'link', 'linkHidden', 'title', 'tag', 'place', 'status')}, 'popups': new, 'reqs': ext_since(n0), 'frames': [f.url for f in pg.frames]}
        results.setdefault('schemes', {})[sel] = row
        ok = d['open'] and d['intent'] == intent and (d['linkHidden'] if link is None else d['link'] == link) and not new and not row['reqs'] and frame_intact()
        check(f'D7 {sel}: document kept, portal answers ({intent})', ok, row, 'medium')
        if sel in ('#l-http', '#l-rel'): pg.screenshot(path=str(SHOTS / f'{ENGINE}-scheme-{sel[3:]}.png'))
        close_dialog()
    n_pop = len(popups)
    pg.locator('#artifact-frame').focus()
    fr.locator('#l-http').click(); pg.wait_for_timeout(500); pg.locator('.media-dialog .media-source').click(); new = popups_since(n_pop)
    check('http: portal link opens the http destination on explicit click', len(new) == 1 and new[0].url.startswith('http://example.org/inseguro'), [x.url for x in new])
    for x in new: x.close()
    fr.locator('#l-js').click(); pg.wait_for_timeout(500)
    check('javascript: link stays inside the document (no dialog, frame kept)', not dialog()['open'] and frame_intact(), [f.url for f in pg.frames])
    fr.evaluate("()=>document.querySelector('#l-rel').click()"); pg.wait_for_timeout(700)
    check('scripted (untrusted) click on a relative link neither navigates nor asks the portal', not dialog()['open'] and frame_intact(), [f.url for f in pg.frames])
    check('no page errors', not errors, errors)
    results['errors'] = errors; results['console'] = console[-30:]
    browser.close()
(OUT / f'media-{ENGINE}.json').write_text(json.dumps(results, indent=1, ensure_ascii=False, default=str))
print(sum(c['ok'] for c in results['checks']), '/', len(results['checks']))
tmp.cleanup()

raise SystemExit(0 if all(c["ok"] for c in results["checks"]) else 1)
