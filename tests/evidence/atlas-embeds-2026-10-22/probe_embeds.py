"""Sonda de compatibilidad de embeds (X, YouTube, Instagram) bajo los headers reales del portal.

Lee las CSP exactas de portal/app.py, levanta un servidor local HTTP y HTTPS (certificado
autofirmado) y ensaya cada proveedor con Playwright en varios marcos:

  file          archivo local abierto con file://
  http-top      render con headers exactos abierto como documento superior (http://127.0.0.1)
  portal-nested shell con CSP del portal -> iframe sandbox del artefacto -> iframe del proveedor
  portal-host   shell con CSP del portal + frame-src exacto; el artefacto pide por postMessage
                y el portal monta el reproductor en su propio <dialog>
  static-host   HTML portátil servido sin cabeceras desde un host https cualquiera

Solo carga embeds tras un clic simulado, siempre en silencio (mute=1). No inicia sesión, no
interactúa con el contenido ni guarda credenciales. La evidencia completa (consola, red,
capturas) va a OUT; el resumen comprometido no lleva texto del proveedor.

Uso: python probe_embeds.py [--out DIR] [--offline-only]
"""
import argparse, json, os, re, ssl, subprocess, sys, tempfile, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[3]
APP = (ROOT / 'portal/app.py').read_text()
PORTAL_CSP = re.search(r"Content-Security-Policy'\] = \"(default-src 'self'[^\"]+)\"", APP).group(1)
RENDER_CSP = re.search(r"'Content-Security-Policy':\"(sandbox allow-scripts[^\"]+)\"", APP).group(1)
YT_ID, IG_ID = 'M7lc1UVf-VE', 'fA9uwTtkSN'  # ejemplos de la documentación oficial de cada proveedor
PROVIDER_FRAMES = 'https://www.youtube-nocookie.com/embed/ https://www.instagram.com/p/'
HOST = 'artifacts.margen.test'      # equivalente local de artifacts.botto.is
ECHO = 'echo.margen.test'           # proveedor simulado: mide Referer/Origin/sandbox heredado
HEADERS_SEEN = []

def frame_src(extra):
    return extra and "frame-src " + extra + ";"

def render_csp(frames):
    if not frames: return RENDER_CSP
    return RENDER_CSP.replace("connect-src 'none';", "connect-src 'none'; " + frame_src(frames))

def portal_csp(frames):
    return PORTAL_CSP if not frames else PORTAL_CSP.replace("frame-src 'self';", "frame-src 'self' " + frames + ";")

ARTIFACT = r"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Fixture embeds</title>
<style>
body{font:16px/1.5 system-ui;margin:24px;max-width:40rem;background:#fbfaf7;color:#1b1b1b}
.tarjeta{border:1px solid #d8d3c8;border-radius:12px;padding:16px;margin:0 0 20px;background:#fff}
.poster{aspect-ratio:16/9;min-width:200px;min-height:200px;display:grid;place-items:center;background:#ece8df;border-radius:8px}
.poster iframe{width:100%;height:100%;border:0;border-radius:8px}
.ig .poster{aspect-ratio:auto;height:640px}
.tweet header{display:flex;gap:10px;align-items:center}.avatar{width:40px;height:40px;border-radius:50%;background:#c9c2b4}
.ejemplo{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:#7a6f5c}
</style></head><body>
<article class="tarjeta tweet" data-blog-tweet data-x-card>
 <p class="ejemplo">Ejemplo sintético · no es una publicación real</p>
 <header><span class="avatar" aria-hidden="true"></span><div><strong>Autora de ejemplo</strong><br><small>@ejemplo · 22 oct 2026</small></div></header>
 <p>Texto inventado para probar la tarjeta portátil: sin script de X, sin métricas ni verificación.</p>
 <p><a data-x-source data-provider="x" data-path="/XDevelopers" href="https://x.com/XDevelopers" target="_blank" rel="noopener noreferrer">Ver fuente original en X</a></p>
</article>
<article class="tarjeta yt" data-embed="youtube" data-id="__YT__">
 <div class="poster"><button type="button" data-load>Cargar video de YouTube (sin sonido)</button></div>
 <p><a data-source href="https://www.youtube.com/watch?v=__YT__" target="_blank" rel="noopener noreferrer">Abrir en YouTube</a></p>
</article>
<article class="tarjeta ig" data-embed="instagram" data-id="__IG__">
 <div class="poster"><button type="button" data-load>Cargar publicación de Instagram</button></div>
 <p><a data-source href="https://www.instagram.com/p/__IG__/" target="_blank" rel="noopener noreferrer">Abrir en Instagram</a></p>
</article>
<article class="tarjeta echo" data-embed="echo" data-id="medir">
 <div class="poster"><button type="button" data-load>Cargar proveedor simulado</button></div>
</article>
<script>
(()=>{
 const mode="__MODE__",ref="__REF__";
 const url={youtube:id=>"https://www.youtube-nocookie.com/embed/"+id+"?autoplay=1&mute=1&playsinline=1&rel=0",
  instagram:id=>"https://www.instagram.com/p/"+id+"/embed/",echo:id=>"__ECHO__/echo?k="+mode+"-"+id};
 const state={origin:self.origin,cookie:(()=>{try{document.cookie="a=1";return "ok"}catch(e){return e.name}})(),
  storage:(()=>{try{localStorage.setItem("a","1");return "ok"}catch(e){return e.name}})(),
  fetch:"pending"};
 fetch("__ECHO__/echo?k=connect").then(()=>state.fetch="ok",e=>state.fetch="blocked");
 window.__fixture=state;
 if(mode==="host")document.addEventListener("click",e=>{const a=e.target.closest("a[data-x-source],a[data-source]");if(!a)return;
  const c=a.closest("[data-embed]");e.preventDefault();
  parent.postMessage({margenOpen:1,provider:a.dataset.provider||c.dataset.embed,id:a.dataset.path||c.dataset.id},"*")});
 document.querySelectorAll("[data-load]").forEach(b=>b.addEventListener("click",()=>{
  const card=b.closest("[data-embed]"),p=card.dataset.embed,id=card.dataset.id;
  if(mode==="host"){parent.postMessage({margenEmbed:1,provider:p,id},"*");return}
  const f=document.createElement("iframe");f.src=url[p](id);f.title="Contenido de "+p;
  if(ref)f.referrerPolicy=ref;f.allow="autoplay; encrypted-media; picture-in-picture; fullscreen";
  b.replaceWith(f);
 }));
})();
</script></body></html>"""

SHELL = """<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Shell portal</title>
<script src="/shell.js?__Q__" defer></script>
<link rel="stylesheet" href="/shell.css"></head><body>
<iframe id="artifact-frame" title="Artefacto" sandbox="allow-scripts allow-downloads" allow="clipboard-write" src="__SRC__"></iframe>
<dialog id="embed-dialog"><div class="embed-head"><span id="embed-title"></span><a id="embed-source" target="_blank" rel="noopener noreferrer">Abrir en el proveedor</a><button id="embed-close" type="button">Cerrar</button></div>
<div id="embed-slot"></div><p id="embed-status" role="status"></p></dialog>
</body></html>"""

SHELL_CSS = """body{margin:0;font:15px system-ui}#artifact-frame{width:100%;height:100vh;border:0}
dialog{width:min(92vw,860px);border:0;border-radius:12px;padding:12px}dialog::backdrop{background:rgb(0 0 0/.55)}
.embed-head{display:flex;gap:12px;align-items:center;margin-bottom:8px}.embed-head span{flex:1}
#embed-slot iframe{width:100%;border:0;display:block}#embed-slot .yt{aspect-ratio:16/9;min-height:200px}"""

# Montaje por el host: el portal es la única capa que construye URLs de proveedor.
SHELL_JS = r"""(()=>{
 const q=new URLSearchParams(document.currentScript.src.split("?")[1]||"");
 const frame=document.getElementById("artifact-frame"),dialog=document.getElementById("embed-dialog");
 const slot=document.getElementById("embed-slot"),status=document.getElementById("embed-status");
 const providers={
  youtube:{name:"YouTube",id:/^[A-Za-z0-9_-]{11}$/,origin:"https://www.youtube-nocookie.com",
   src:id=>"https://www.youtube-nocookie.com/embed/"+id+"?autoplay=1&mute=1&playsinline=1&rel=0&enablejsapi=1&origin="+encodeURIComponent(location.origin),
   page:id=>"https://www.youtube.com/watch?v="+id,cls:"yt"},
  instagram:{name:"Instagram",id:/^[A-Za-z0-9_-]{5,40}$/,origin:"https://www.instagram.com",
   src:id=>"https://www.instagram.com/p/"+id+"/embed/",page:id=>"https://www.instagram.com/p/"+id+"/",cls:"ig",height:640},
  echo:{name:"Eco",id:/^[a-z]{1,20}$/,origin:"__ECHO__",src:id=>"__ECHO__/echo?k=host-"+id,page:id=>"__ECHO__/",cls:"echo",height:240}};
 const sources={x:/^\/[A-Za-z0-9_]{1,15}(?:\/status\/[0-9]{1,20})?$/};
 let live=null,timer=null,listen=null;
 window.__embedLog=[];
 addEventListener("message",e=>{
  if(e.source===frame.contentWindow&&e.origin==="null"&&e.data?.margenEmbed===1){open(e.data);return}
  if(e.source===frame.contentWindow&&e.origin==="null"&&e.data?.margenOpen===1){openSource(e.data);return}
  if(live&&e.source===live.frame.contentWindow&&e.origin===live.p.origin){
   window.__embedLog.push(String(e.data).slice(0,160));
   if(!live.alive){live.alive=true;clearTimeout(timer);clearInterval(listen);status.textContent="";}
   if(live.p===providers.instagram){try{const m=JSON.parse(e.data);if(m.type==="MEASURE"&&m.details.height>0&&m.details.height<4000)live.frame.style.height=Math.round(m.details.height)+"px"}catch{}}
  }
 });
 function openSource({provider,id}){
  let url=null;
  if(provider==="x"&&typeof id==="string"&&sources.x.test(id))url="https://x.com"+id;
  else if(Object.hasOwn(providers,provider)&&typeof id==="string"&&providers[provider].id.test(id))url=providers[provider].page(id);
  if(url)window.open(url,"_blank","noopener,noreferrer");
 }
 function open({provider,id}){
  const p=Object.hasOwn(providers,provider)&&providers[provider];
  if(!p||typeof id!=="string"||!p.id.test(id))return;
  slot.replaceChildren();const f=document.createElement("iframe");
  f.className=p.cls;if(p.height)f.style.height=p.height+"px";
  f.title="Contenido de "+p.name;f.allow="autoplay; encrypted-media; picture-in-picture; fullscreen";
  f.referrerPolicy=q.get("ref")||"strict-origin";
  if(q.get("psb")!=="0")f.setAttribute("sandbox","allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox allow-presentation");
  f.src=p.src(id);slot.append(f);live={p,frame:f,alive:false};
  document.getElementById("embed-title").textContent=p.name;
  const a=document.getElementById("embed-source");a.href=p.page(id);a.textContent="Abrir en "+p.name;
  status.textContent="Cargando…";dialog.showModal();
  if(p===providers.youtube){f.addEventListener("load",()=>{listen=setInterval(()=>f.contentWindow?.postMessage('{"event":"listening","id":1,"channel":"widget"}',p.origin),400)})}
  timer=setTimeout(()=>{if(!live.alive)status.textContent=p.name+" no respondió. El enlace de arriba abre la fuente original.";clearInterval(listen)},Number(q.get("timeout")||9000));
 }
 document.getElementById("embed-close").addEventListener("click",()=>{dialog.close();slot.replaceChildren();live=null});
})();"""

ECHO_PAGE = """<!doctype html><meta charset="utf-8"><title>eco</title><body style="font:13px monospace">
<script>window.__echo={origin:self.origin,referrer:document.referrer,
cookie:(()=>{try{document.cookie="b=1";return "ok"}catch(e){return e.name}})(),
storage:(()=>{try{localStorage.setItem("b","1");return "ok"}catch(e){return e.name}})(),
popup:(()=>{try{return window.open("about:blank")?"opened":"null"}catch(e){return e.name}})()};
document.body.textContent=JSON.stringify(window.__echo)</script>"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def send(self, body, ctype='text/html; charset=utf-8', csp=None, extra=None):
        data = body.encode()
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Cache-Control', 'private, no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        if csp: self.send_header('Content-Security-Policy', csp)
        for k, v in (extra or {}).items(): self.send_header(k, v)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        u = urlparse(self.path); q = {k: v[0] for k, v in parse_qs(u.query).items()}
        echo = 'https://' + ECHO + ':' + str(self.server.https_port)
        if u.path == '/echo':
            HEADERS_SEEN.append({'k': q.get('k'), 'host': self.headers.get('Host'), 'referer': self.headers.get('Referer'),
                                 'origin': self.headers.get('Origin'), 'sec-fetch-dest': self.headers.get('Sec-Fetch-Dest'),
                                 'sec-fetch-site': self.headers.get('Sec-Fetch-Site')})
            return self.send(ECHO_PAGE, extra={'Access-Control-Allow-Origin': '*'})
        if u.path == '/artifact':
            frames = PROVIDER_FRAMES + ' ' + echo + '/echo' if q.get('csp') == 'frames' else ''
            body = artifact(q.get('mode', 'nested'), q.get('ref', ''), echo)
            return self.send(body, csp=None if q.get('csp') == 'none' else render_csp(frames))
        if u.path == '/shell':
            frames = PROVIDER_FRAMES + ' ' + echo + '/echo' if q.get('csp') == 'frames' else ''
            src = '/artifact?mode=' + q.get('mode', 'host') + '&csp=' + q.get('acsp', 'exact') + '&ref=' + q.get('aref', '')
            return self.send(SHELL.replace('__SRC__', src).replace('__Q__', u.query), csp=portal_csp(frames))
        if u.path == '/shell.js': return self.send(SHELL_JS.replace('__ECHO__', echo), 'text/javascript', csp=portal_csp(''))
        if u.path == '/shell.css': return self.send(SHELL_CSS, 'text/css', csp=portal_csp(''))
        self.send_error(404)

def artifact(mode, ref, echo):
    return (ARTIFACT.replace('__YT__', YT_ID).replace('__IG__', IG_ID).replace('__MODE__', mode)
            .replace('__REF__', ref).replace('__ECHO__', echo))

def serve(tmp):
    http = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    https = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    cert, key = tmp / 'c.pem', tmp / 'k.pem'
    subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1', '-subj', '/CN=' + HOST,
                    '-addext', 'subjectAltName=DNS:' + HOST + ',DNS:' + ECHO, '-keyout', key, '-out', cert],
                   check=True, capture_output=True)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.load_cert_chain(cert, key)
    https.socket = ctx.wrap_socket(https.socket, server_side=True)
    for s in (http, https):
        s.https_port = https.server_address[1]
        threading.Thread(target=s.serve_forever, daemon=True).start()
    return http.server_address[1], https.server_address[1]

PROVIDER_HOSTS = re.compile(r'https://([a-z0-9-]+\.)*(youtube(-nocookie)?\.com|ytimg\.com|googlevideo\.com|google\.com|gstatic\.com|doubleclick\.net|instagram\.com|cdninstagram\.com|fbcdn\.net|facebook\.com|x\.com)/')

def inspect_youtube(frame):
    return frame.evaluate("""async()=>{await new Promise(r=>setTimeout(r,7000));const v=document.querySelector('video');
     const err=document.querySelector('.ytp-error');const t=(err?.innerText||'').replace(/\\s+/g,' ').slice(0,200);
     const all=document.body.innerText||'';
     return {video:!!v,currentTime:v?Math.round(v.currentTime*10)/10:null,muted:v?v.muted:null,paused:v?v.paused:null,
      error:!!err&&getComputedStyle(err).display!=='none',error153:/Error 153/.test(all),errorText:t||all.slice(0,160),
      bot:/not a bot|no eres un bot|inicia sesi|sign in/i.test(all)}}""")

def inspect_instagram(frame):
    return frame.evaluate("""async()=>{await new Promise(r=>setTimeout(r,5000));const t=document.body.innerText||'';
     return {images:document.querySelectorAll('img').length,media:!!document.querySelector('.EmbeddedMedia,.EmbeddedMediaImage,video'),
      login:/log in|iniciar sesi|inicia sesi/i.test(t)&&!document.querySelector('.EmbeddedMedia'),
      unavailable:/unavailable|no está disponible|isn.t available/i.test(t),chars:t.length,textSample:t.slice(0,160)}}""")

def find_frame(page, pattern, timeout=15):
    end = time.time() + timeout
    while time.time() < end:
        for f in page.frames:
            if re.search(pattern, f.url): return f
        page.wait_for_timeout(250)
    return None

def run(out, offline_only):
    from playwright.sync_api import sync_playwright
    tmp = Path(tempfile.mkdtemp(prefix='margen-embeds-'))
    http_port, https_port = serve(tmp)
    H = 'https://' + HOST + ':' + str(https_port)
    L = 'http://127.0.0.1:' + str(http_port)
    file_path = tmp / 'artefacto.html'
    file_path.write_text(artifact('nested', 'strict-origin', 'https://' + ECHO + ':' + str(https_port)))
    scenarios = [
        # (id, entorno, url, modo de carga, bloquear red)
        ('file', 'archivo local', file_path.as_uri(), 'nested', False),
        ('http-top-exact', 'http local · headers exactos', L + '/artifact?mode=nested&csp=exact&ref=strict-origin', 'nested', False),
        ('http-top-frames', 'http local · headers exactos + frame-src', L + '/artifact?mode=nested&csp=frames&ref=strict-origin', 'nested', False),
        ('portal-nested-exact', 'host https · portal → artefacto (CSP actual)', H + '/shell?mode=nested&acsp=exact&aref=strict-origin', 'nested', False),
        ('portal-nested-frames', 'host https · portal → artefacto + frame-src', H + '/shell?mode=nested&acsp=frames&aref=strict-origin', 'nested', False),
        ('portal-host', 'host https · portal monta el iframe', H + '/shell?mode=host&csp=frames', 'host', False),
        ('portal-host-noref', 'host https · portal monta, no-referrer', H + '/shell?mode=host&csp=frames&ref=no-referrer', 'host', False),
        ('portal-host-csp-exact', 'host https · portal monta sin ampliar frame-src', H + '/shell?mode=host&csp=exact', 'host', False),
        ('portal-host-offline', 'host https · portal monta, red de proveedores bloqueada', H + '/shell?mode=host&csp=frames&timeout=6000', 'host', True),
        ('static-host', 'host https sin cabeceras (HTML portátil)', H + '/artifact?mode=nested&csp=none&ref=strict-origin', 'nested', False),
    ]
    results, private = [], []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='chromium', headless=True,
                                     args=['--host-resolver-rules=MAP *.margen.test 127.0.0.1', '--autoplay-policy=no-user-gesture-required'])
        for sid, env, url, mode, offline in scenarios:
            ctx = browser.new_context(ignore_https_errors=True, viewport={'width': 1100, 'height': 900}, locale='es-ES')
            ctx.route(re.compile(r'https://([a-z0-9-]+\.)?x\.com/.*'), lambda r: r.abort())  # nunca contactar X
            if offline or offline_only:
                ctx.route(PROVIDER_HOSTS, lambda r: r.abort())
            page = ctx.new_page()
            console, net, popups = [], [], []
            page.on('console', lambda m: console.append(m.type + ': ' + m.text[:300]))
            def on_req(r):
                if PROVIDER_HOSTS.match(r.url) or ECHO in r.url:
                    net.append({'url': r.url.split('?')[0][:160], 'type': r.resource_type, 'req': r})
            page.on('request', on_req)
            ctx.on('page', lambda p: popups.append(p))
            row = {'id': sid, 'entorno': env, 'modo': mode}
            try:
                page.goto(url, wait_until='load')
                art = page if mode == 'nested' and '/shell' not in url else page.frame_locator('#artifact-frame')
                artf = page.main_frame if art is page else find_frame(page, r':\d+/artifact\?')
                for _ in range(40):
                    if (artf.evaluate('window.__fixture && window.__fixture.fetch') or 'pending') != 'pending': break
                    page.wait_for_timeout(200)
                row['artefacto'] = artf.evaluate('window.__fixture')
                row['x_card'] = artf.evaluate("!!document.querySelector('[data-x-card] [data-x-source]')")
                # Enlace de fuente con target=_blank dentro del artefacto (popup)
                n0 = len(popups)
                art.locator('[data-x-source]').click(); page.wait_for_timeout(700)
                row['x_link_popup'] = len(popups) > n0
                for p in popups[n0:]: p.close()
                for prov, pat in (('echo', r'/echo\?k=(nested|host)-'), ('youtube', r'youtube-nocookie\.com/embed/'), ('instagram', r'instagram\.com/p/' + IG_ID + '/embed')):
                    if mode == 'host' and page.locator('dialog[open]').count():
                        page.locator('#embed-close').click()
                    start = len(HEADERS_SEEN)
                    art.locator(f'[data-embed="{prov}"] [data-load]').click()
                    f = find_frame(page, pat, timeout=10)
                    r = {'frame': bool(f)}
                    if f:
                        page.wait_for_timeout(1500)
                        try:
                            if prov == 'echo':
                                r['frame_view'] = f.evaluate('window.__echo || null')
                                r['server_saw'] = HEADERS_SEEN[start:] and HEADERS_SEEN[-1]
                            elif prov == 'youtube':
                                r.update(inspect_youtube(f))
                            else:
                                r.update(inspect_instagram(f))
                        except Exception as e:
                            r['frame_error'] = str(e).splitlines()[0][:200]
                        r['frame_url_error'] = f.url.startswith('chrome-error')
                    if mode == 'host':
                        r['host_status'] = page.locator('#embed-status').inner_text() if page.locator('dialog[open]').count() else None
                        r['host_messages'] = len(page.evaluate('window.__embedLog'))
                        r['source_link_visible'] = page.locator('#embed-source').is_visible()
                    else:
                        r['source_link_visible'] = prov == 'echo' or art.locator(f'[data-embed="{prov}"] [data-source]').is_visible()
                    page.screenshot(path=str(out / f'{sid}-{prov}.png'))
                    row[prov] = r
            except Exception as e:
                row['error'] = str(e).splitlines()[0][:300]
            reqs = []
            for n in net:
                rq = n['req']
                try: h = rq.all_headers()
                except Exception: h = {}
                resp = None
                try: resp = rq.response()
                except Exception: pass
                reqs.append({'url': n['url'], 'type': n['type'], 'referer': h.get('referer'), 'origin': h.get('origin'),
                             'status': resp.status if resp else None, 'failure': rq.failure})
            row['provider_requests'] = len(reqs)
            row['provider_documents'] = [r for r in reqs if r['type'] == 'document']
            row['csp_violations'] = [c for c in console if 'Content Security Policy' in c or 'Refused to frame' in c][:6]
            private.append({**row, 'console': console[:80], 'requests': reqs})
            results.append({k: v for k, v in row.items()})
            ctx.close()
        browser.close()
    def scrub(o):
        if isinstance(o, dict): return {k: scrub(v) for k, v in o.items() if k not in ('textSample', 'errorText')}
        if isinstance(o, list): return [scrub(v) for v in o]
        return o
    (out / 'private-results.json').write_text(json.dumps(private, indent=1, ensure_ascii=False, default=str))
    summary = {'portal_csp': PORTAL_CSP, 'render_csp': RENDER_CSP, 'chromium': None, 'results': scrub(results)}
    return summary

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.expanduser('~/.local/share/margen-review/atlas-embeds-20261022'))
    ap.add_argument('--summary', default=str(Path(__file__).with_name('results.json')))
    ap.add_argument('--offline-only', action='store_true')
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    s = run(out, a.offline_only)
    s['ran_at'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')
    Path(a.summary).write_text(json.dumps(s, indent=1, ensure_ascii=False, default=str) + '\n')
    print(json.dumps(s['results'], indent=1, ensure_ascii=False, default=str))
