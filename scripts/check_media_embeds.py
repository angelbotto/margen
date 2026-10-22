#!/usr/bin/env python3
"""Comprueba X, YouTube e Instagram en el portal real local y fuera de él, en Chromium y WebKit.

Levanta portal.app con datos temporales sobre HTTPS local (https://localhost, certificado
autofirmado; WebKit no admite reglas de resolución), crea dos cuentas temporales y un artefacto «unlisted» con las tres recetas,
el pie con enlaces y el runtime de embeds cableado como lo hará el contrato. Nunca usa producción.

Comprueba: nada del proveedor antes del clic en el botón del portal (la tarjeta sólo abre la vista previa);
diálogo del portal con URL, sandbox y referrer exactos;
reproducción real (un <video> que avanza, no iframe.onload); Escape/cierre/reapertura con foco de vuelta;
navegación por hash; mensajes sin clic del lector o de otra ventana ignorados; fuente y pie abiertos sólo
con clic; red de proveedores bloqueada; HTML portátil por HTTPS, file:// y sin JavaScript.

El resumen (sin texto de proveedores, cookies ni tokens) va a --summary; capturas y detalle a --out.
Uso: python scripts/check_media_embeds.py [--browsers chromium,webkit] [--offline-only]
"""
import argparse, json, re, ssl, subprocess, sys, tempfile, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]
HOST = 'localhost'
YT, IG = 'M7lc1UVf-VE', 'fA9uwTtkSN'  # ejemplos de la documentación oficial de cada proveedor
PROVIDERS = re.compile(r'https://([a-z0-9-]+\.)*(youtube(-nocookie)?\.com|ytimg\.com|googlevideo\.com|google\.com|gstatic\.com|doubleclick\.net|instagram\.com|cdninstagram\.com|fbcdn\.net|facebook\.com|x\.com)/')
RECIPES = ROOT / 'packages/core/recipes'
# X y los enlaces del pie nunca se contactan: una página mínima conserva la URL exacta y registra el Referer.
STUBS = re.compile(r'https://([a-z0-9-]+\.)?(x\.com|example\.org)/.*')
STUB_REFERERS = []


def stub(route):
    STUB_REFERERS.append(route.request.headers.get('referer'))
    route.fulfill(status=200, content_type='text/html', body='<title>stub</title>')


def artifact_html():
    """Documento del contrato con embeds.js y embeds.css cableados como en el parche de wiring."""
    import contract_artifact as c
    module = 'packages/core/components/embeds.js'
    if module not in c.ORDER:
        c.ORDER.insert(c.ORDER.index('packages/core/components/editorial-pieces.js') + 1, module)
    c.ATTRS.setdefault('data-embed', [module])
    pages = [{'id': 'publicaciones', 'titulo': 'Publicaciones', 'html': '<section class="seccion" id="tres"><h2>Tres proveedores</h2>'
              + ''.join((RECIPES / r / 'example.html').read_text() for r in ('x-post', 'youtube', 'instagram'))
              + '<figure class="embed embed-x" id="x-real" data-embed="x" data-embed-user="XDevelopers"><blockquote class="embed-texto"><p>Tarjeta con fuente real para probar la apertura.</p></blockquote>'
              + '<figcaption class="embed-pie"><a data-embed-source href="https://evil.example/">Ver en X</a></figcaption></figure></section>'}]
    footer = {'author': 'Autora de prueba', 'links': [{'label': 'Sitio', 'href': 'https://example.org/perfil'}, {'label': 'Correo', 'href': 'mailto:autora@example.org'}]}
    html = c.build('Embeds de prueba', pages, document_id='embeds-prueba', footer=footer)
    css = (ROOT / 'packages/core/styles/embeds.css').read_text()
    marker = '<style data-nota-fuente="packages/core/styles/artifact.css">\n'
    assert marker in html
    return html.replace(marker, marker + css + '\n', 1)


def certificate(tmp):
    cert, key = tmp / 'c.pem', tmp / 'k.pem'
    subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1', '-subj', '/CN=' + HOST,
                    '-addext', 'subjectAltName=DNS:' + HOST, '-keyout', key, '-out', cert], check=True, capture_output=True)
    return cert, key


def serve_portal(tmp, cert, key):
    import uvicorn
    from portal.app import create_app
    origin_holder = {}
    sock_port = free_port()
    origin = 'https://' + HOST + ':' + str(sock_port)
    app = create_app(str(tmp / 'data'), origin=origin, issuer='https://identity.test', audience='margen-check')
    config = uvicorn.Config(app, host='127.0.0.1', port=sock_port, ssl_certfile=str(cert), ssl_keyfile=str(key), log_level='warning')
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(100):
        if server.started: break
        time.sleep(.1)
    return app, origin, server


def serve_static(html, cert, key):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_GET(self):
            body = html.encode()
            self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.end_headers(); self.wfile.write(body)
    srv = ThreadingHTTPServer(('127.0.0.1', 0), H)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.load_cert_chain(cert, key)
    srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return 'https://' + HOST + ':' + str(srv.server_address[1]) + '/'


def free_port():
    import socket
    s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close(); return port


def find_frame(page, pattern, timeout=15):
    end = time.time() + timeout
    while time.time() < end:
        for f in page.frames:
            if re.search(pattern, f.url): return f
        page.wait_for_timeout(250)
    return None


def youtube_playback(frame):
    """Reproducción real: un <video> silenciado cuyo tiempo avanza. Que el iframe cargue no cuenta."""
    try:
        return frame.evaluate("""async()=>{const v=()=>document.querySelector('video');let a=null;for(let i=0;i<40&&!v();i++)await new Promise(r=>setTimeout(r,250));
          if(!v())return {video:false,error153:/Error 153/.test(document.body.innerText||'')};a=v().currentTime;await new Promise(r=>setTimeout(r,4000));
          const x=v();return {video:true,advanced:x.currentTime>a,currentTime:Math.round(x.currentTime*10)/10,muted:x.muted,paused:x.paused,error153:/Error 153/.test(document.body.innerText||'')}}""")
    except Exception as error:
        return {'video': False, 'evaluate_error': type(error).__name__}


def instagram_view(frame):
    try:
        return frame.evaluate("""async()=>{await new Promise(r=>setTimeout(r,4000));const t=document.body.innerText||'';
          return {media:!!document.querySelector('.EmbeddedMedia,.EmbeddedMediaImage,video,img'),login:/log in|inicia sesi/i.test(t)&&!document.querySelector('.EmbeddedMedia'),chars:t.length}}""")
    except Exception as error:
        return {'media': False, 'evaluate_error': type(error).__name__}


def portal_checks(pw, engine, origin, aid, version, session, label, shots, offline):
    browser = getattr(pw, engine).launch(**launch_args(engine))
    ctx = browser.new_context(ignore_https_errors=True, viewport={'width': 1280, 'height': 900}, locale='es-ES')
    ctx.add_cookies([{'name': '__Host-bottifact', 'value': session, 'url': origin + '/', 'secure': True, 'httpOnly': True, 'sameSite': 'Lax'}])
    ctx.route(STUBS, stub)
    if offline: ctx.route(PROVIDERS, lambda r: r.abort())
    page = ctx.new_page()
    provider_requests, popups, frame_requests = [], [], []
    def on_request(r):
        if PROVIDERS.match(r.url):
            provider_requests.append(r.url)
            if r.resource_type == 'document' and ('/embed' in r.url):
                frame_requests.append({'url': r.url.split('?')[0], 'referer': r.headers.get('referer')})
    page.on('request', on_request)
    ctx.on('page', lambda p: popups.append(p))
    row = {'browser': engine, 'user': label, 'offline': offline}
    page.goto(origin + '/a/' + aid, wait_until='load')
    art = page.frame_locator('#artifact-frame')
    art.locator('#youtube-ejemplo [data-embed-load]').wait_for(state='visible', timeout=15000)
    page.wait_for_timeout(800)
    artf = find_frame(page, r'/render\?version=')
    row['artifact_sandbox'] = page.get_attribute('#artifact-frame', 'sandbox')
    row['artifact_origin'] = artf.evaluate('self.origin')
    row['no_provider_before_click'] = not provider_requests
    row['links'] = artf.evaluate("[...document.querySelectorAll('a[data-embed-source]')].map(a=>a.getAttribute('href'))")
    row['synthetic_without_link'] = artf.evaluate("!document.querySelector('#x-ejemplo a') && /Ejemplo sintético/.test(document.querySelector('#x-ejemplo').textContent)")
    # Mensajes sin clic del lector: no abren diálogo ni pestaña, ni con URL arbitraria.
    n = len(popups)
    # evaluate() de Playwright lleva gesto de usuario: el envío se programa después de que la activación transitoria (~5 s) caduque.
    artf.evaluate("""v=>{setTimeout(()=>{if(navigator.userActivation?.isActive)return;for(const [op,data] of [['embed',{provider:'youtube',id:'M7lc1UVf-VE',version:v}],['open-source',{provider:'x',user:'XDevelopers',version:v}],
       ['external',{href:'https://example.org/spam',version:v}],['external',{href:'javascript:alert(1)',version:v}],['embed',{provider:'youtube',id:'M7lc1UVf-VE',version:v,url:'https://evil.example'}]])
       parent.postMessage({bottifact:1,id:crypto.randomUUID(),op,data},'*');window.__forged=true},6500)}""", version)
    page.evaluate("window.postMessage({bottifact:1,id:'x',op:'embed',data:{provider:'youtube',id:'M7lc1UVf-VE',version:%s}},'*')" % json.dumps(version))
    page.wait_for_timeout(8000)
    row['unactivated_messages_sent'] = artf.evaluate('window.__forged===true')
    row['unactivated_messages_ignored'] = row['unactivated_messages_sent'] and page.locator('dialog.media-dialog[open]').count() == 0 and len(popups) == n and not provider_requests
    # YouTube: clic real en la tarjeta → vista previa del portal sin red; sólo su botón «Reproducir aquí» monta el reproductor.
    art.locator('#youtube-ejemplo [data-embed-load]').click()
    page.locator('dialog.media-dialog[open] .media-play').wait_for(timeout=10000)
    page.wait_for_timeout(600)
    row['preview_without_provider'] = not provider_requests and page.locator('iframe.media-player').count() == 0
    row['preview_focus_on_portal_button'] = page.evaluate("document.activeElement?.classList.contains('media-play')")
    page.locator('dialog.media-dialog .media-play').click()
    page.locator('dialog.media-dialog[open] iframe.media-player').wait_for(timeout=10000)
    player = page.locator('dialog.media-dialog[open] iframe.media-player')
    row['youtube_dialog'] = {k: player.get_attribute(k) for k in ('src', 'sandbox', 'referrerpolicy', 'allow')}
    row['youtube_notice'] = page.locator('dialog.media-dialog .media-notice').text_content()
    row['youtube_source_link'] = page.locator('dialog.media-dialog a.media-source').get_attribute('href')
    if not offline:
        f = find_frame(page, r'youtube-nocookie\.com/embed/' + YT)
        row['youtube_playback'] = youtube_playback(f) if f else {'video': False, 'frame': False}
    else:
        page.wait_for_timeout(8800)
    row['youtube_status'] = page.locator('dialog.media-dialog .media-status').text_content()
    page.screenshot(path=str(shots / f'{engine}-{label}{"-offline" if offline else ""}-youtube-dialog.png'))
    page.keyboard.press('Escape')
    page.wait_for_timeout(500)
    row['escape_closes'] = page.locator('dialog.media-dialog[open]').count() == 0 and page.locator('iframe.media-player').count() == 0
    row['focus_returns'] = artf.evaluate("document.activeElement && document.activeElement.matches('#youtube-ejemplo [data-embed-load]')")
    art.locator('#youtube-ejemplo [data-embed-load]').click()
    page.locator('dialog.media-dialog .media-play').click()
    page.locator('dialog.media-dialog[open] iframe.media-player').wait_for(timeout=10000)
    page.locator('dialog.media-dialog .dialog-head button').click()
    page.wait_for_timeout(400)
    row['reopen_and_close_button'] = page.locator('iframe.media-player').count() == 0
    # Instagram: no-referrer, sin rd/rp, altura medida.
    art.locator('#instagram-ejemplo [data-embed-load]').click()
    page.locator('dialog.media-dialog .media-play').click()
    page.locator('dialog.media-dialog[open] iframe.media-player').wait_for(timeout=10000)
    ig = page.locator('dialog.media-dialog[open] iframe.media-player')
    row['instagram_dialog'] = {k: ig.get_attribute(k) for k in ('src', 'sandbox', 'referrerpolicy')}
    if not offline:
        f = find_frame(page, r'instagram\.com/p/' + IG + '/embed')
        row['instagram_view'] = instagram_view(f) if f else {'media': False, 'frame': False}
        row['instagram_height'] = ig.evaluate('e=>e.style.height||null')
    else:
        page.wait_for_timeout(8800)
    row['instagram_status'] = page.locator('dialog.media-dialog .media-status').text_content()
    page.screenshot(path=str(shots / f'{engine}-{label}{"-offline" if offline else ""}-instagram-dialog.png'))
    # Navegación por hash con el diálogo abierto: se cierra y no queda reproductor.
    page.evaluate("location.hash='#tres'")
    page.wait_for_timeout(600)
    row['hash_navigation_closes'] = page.locator('dialog.media-dialog[open]').count() == 0 and page.locator('iframe.media-player').count() == 0
    row['frame_requests'] = frame_requests
    # Fuente y pie: el clic del documento sólo muestra el destino; la pestaña la abre el enlace del portal, sin opener.
    for key, selector in (('x_source', '#x-real a[data-embed-source]'), ('youtube_source', '#youtube-ejemplo a[data-embed-source]'), ('footer_link', '.pie-enlaces a[href^="https:"]')):
        n = len(popups)
        art.locator(selector).click()
        page.wait_for_timeout(800)
        dialog = page.locator('dialog.media-dialog[open] a.media-source')
        preview = {'popups_before_portal_click': len(popups) - n, 'portal_link': dialog.get_attribute('href') if dialog.count() else None}
        if dialog.count(): dialog.click()
        page.wait_for_timeout(1200)
        opened = popups[n:]
        if opened: opened[0].wait_for_load_state()
        row[key] = {**preview, 'popups': len(opened), 'url': opened[0].url if opened else None,
                    'opener_null': opened[0].evaluate('window.opener===null') if opened else None,
                    'dialog_closed': page.locator('dialog.media-dialog[open]').count() == 0}
        for p in opened: p.close()
        if page.locator('dialog.media-dialog[open]').count(): page.keyboard.press('Escape')
    row['provider_requests'] = len(provider_requests)
    row['stub_referers'] = sorted({str(r) for r in STUB_REFERERS}); STUB_REFERERS.clear()
    ctx.close(); browser.close()
    return row


def launch_args(engine):
    return {'args': ['--autoplay-policy=user-gesture-required']} if engine == 'chromium' else {}


def standalone_checks(pw, engine, url, file_url, shots):
    rows = []
    browser = getattr(pw, engine).launch(**launch_args(engine))
    for name, target, js in (('https', url, True), ('file', file_url, True), ('no-js', url, False)):
        ctx = browser.new_context(ignore_https_errors=True, java_script_enabled=js, viewport={'width': 390, 'height': 900}, locale='es-ES')
        ctx.route(STUBS, stub)
        page = ctx.new_page()
        provider, frames = [], []
        page.on('request', lambda r: (provider.append(r.url), r.resource_type == 'document' and '/embed' in r.url and frames.append({'url': r.url.split('?')[0], 'referer': r.headers.get('referer')})) if PROVIDERS.match(r.url) else None)
        page.goto(target, wait_until='load')
        page.wait_for_timeout(600)
        row = {'browser': engine, 'mode': name, 'no_provider_before_click': not provider,
               'cards': page.locator('figure[data-embed]').count(),
               'links': page.eval_on_selector_all('a[data-embed-source]', 'l=>l.map(a=>a.getAttribute("href"))'),
               'youtube_button_visible': page.locator('#youtube-ejemplo [data-embed-load]').is_visible(),
               'youtube_status': page.locator('#youtube-ejemplo [data-embed-status]').text_content()}
        if js and name == 'https':
            page.locator('#youtube-ejemplo [data-embed-load]').click()
            f = find_frame(page, r'youtube-nocookie\.com/embed/' + YT)
            row['youtube_iframe'] = page.locator('#youtube-ejemplo iframe').evaluate('e=>({sandbox:e.getAttribute("sandbox"),referrerpolicy:e.getAttribute("referrerpolicy"),src:e.src.split("?")[0]})')
            row['youtube_playback'] = youtube_playback(f) if f else {'video': False, 'frame': False}
            row['youtube_status'] = page.locator('#youtube-ejemplo [data-embed-status]').text_content()
            page.locator('#youtube-ejemplo .embed-quitar').click()
            row['youtube_removed'] = page.locator('#youtube-ejemplo iframe').count() == 0
        if js:
            if page.locator('#instagram-ejemplo [data-embed-load]').is_visible():
                page.locator('#instagram-ejemplo [data-embed-load]').click()
                f = find_frame(page, r'instagram\.com/p/' + IG + '/embed')
                row['instagram_view'] = instagram_view(f) if f else {'media': False, 'frame': False}
                row['instagram_height'] = page.locator('#instagram-ejemplo iframe').evaluate('e=>e.style.height||null') if page.locator('#instagram-ejemplo iframe').count() else None
        row['frame_requests'] = frames
        page.screenshot(path=str(shots / f'{engine}-standalone-{name}.png'), full_page=True)
        rows.append(row)
        ctx.close()
    # Anchos, temas, impresión y movimiento reducido en el HTML portátil.
    ctx = browser.new_context(ignore_https_errors=True, locale='es-ES', reduced_motion='reduce')
    page = ctx.new_page()
    layout = {}
    for width in (320, 390, 1440):
        page.set_viewport_size({'width': width, 'height': 900})
        page.goto(url, wait_until='load')
        for mode in ('light', 'dark'):
            page.evaluate("m=>{document.documentElement.dataset.modo=m;document.dispatchEvent(new Event('nota:tema'))}", mode)
            page.emulate_media(color_scheme=mode)
            page.wait_for_timeout(150)
            layout[f'{width}-{mode}'] = page.evaluate("""()=>({overflow:document.documentElement.scrollWidth>innerWidth,
              cards:[...document.querySelectorAll('figure[data-embed]')].map(f=>{const r=f.getBoundingClientRect();return {w:Math.round(r.width),fits:r.right<=innerWidth+.5}})})""")
            page.locator('#tres').screenshot(path=str(shots / f'{engine}-cards-{width}-{mode}.png'))
    page.emulate_media(media='print')
    layout['print'] = page.evaluate("""()=>({buttons_hidden:[...document.querySelectorAll('[data-embed-load]')].every(b=>getComputedStyle(b).display==='none'),
      link_url_printed:getComputedStyle(document.querySelector('#youtube-ejemplo a[data-embed-source]'),'::after').content.includes('youtube.com')})""")
    ctx.close(); browser.close()
    rows.append({'browser': engine, 'mode': 'layout', **layout})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browsers', default='chromium,webkit')
    parser.add_argument('--out', default=str(Path.home() / '.local/share/margen-review/atlas-embeds-impl-20261022'))
    parser.add_argument('--summary', default=str(ROOT / 'tests/evidence/atlas-embeds-impl-2026-10-22/results.json'))
    args = parser.parse_args()
    from playwright.sync_api import sync_playwright
    out = Path(args.out); shots = out / 'shots'; shots.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix='margen-embeds-check-'))
    cert, key = certificate(tmp)
    html = artifact_html()
    app, origin, server = serve_portal(tmp, cert, key)
    store = app.state.store
    owner, reader = store.user('autora@example.test', 'Autora temporal'), store.user('lectora@example.test', 'Lectora temporal')
    sessions = {'owner': store.session(owner['id']), 'reader': store.session(reader['id'])}
    from fastapi.testclient import TestClient
    client = TestClient(app, base_url=origin, headers={'Origin': origin})
    client.cookies.set('__Host-bottifact', sessions['owner'])
    created = client.post('/api/artifacts', json={'title': 'Embeds de prueba', 'html': html, 'visibility': 'unlisted'}).json()
    aid, version = created['id'], created['version']
    static_url = serve_static(html, cert, key)
    file_path = tmp / 'embeds.html'; file_path.write_text(html)
    results = {'origin': 'https://' + HOST + ':<puerto>', 'artifact_visibility': 'unlisted', 'portal': [], 'standalone': []}
    with sync_playwright() as pw:
        for engine in args.browsers.split(','):
            results['versions'] = {**results.get('versions', {}), engine: getattr(pw, engine).launch(**launch_args(engine)).version}
            for label in ('owner', 'reader'):
                results['portal'].append(portal_checks(pw, engine, origin, aid, version, sessions[label], label, shots, False))
            results['portal'].append(portal_checks(pw, engine, origin, aid, version, sessions['reader'], 'reader', shots, True))
            results['standalone'] += standalone_checks(pw, engine, static_url, file_path.as_uri(), shots)
    server.should_exit = True
    text = json.dumps(results, ensure_ascii=False, indent=1)
    text = text.replace(origin, 'https://' + HOST + ':<puerto>').replace(static_url.rstrip('/'), 'https://' + HOST + ':<puerto-estatico>')
    for value in sessions.values(): assert value not in text
    Path(args.summary).parent.mkdir(parents=True, exist_ok=True)
    Path(args.summary).write_text(text + '\n')
    (out / 'results.json').write_text(text + '\n')
    print(text)


if __name__ == '__main__':
    main()
