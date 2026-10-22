#!/usr/bin/env python3
"""Revisión independiente de Guardar / Me gusta contra el portal real montado completo (no un host simulado).

Levanta portal.app (create_app real, app.js/index.html reales) en HTTPS local con datos temporales y conduce
Chromium y WebKit con entrada real (mouse.click, keyboard). Nunca toca producción.

Uso: python review/reader-actions-review/check_reader_actions_portal.py [--browsers chromium,webkit] [--out DIR]
Escribe summary.json en --out y sale con 1 si algún hallazgo bloqueante se reproduce.
"""
import argparse, json, os, re, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import ROOT, Portal, contract_doc, chapters_doc, deck, RAW, GALLERY

ACT = {'X-Margen-Reader-Action': '1'}
MOBILE = {'viewport': {'width': 390, 'height': 844}, 'is_mobile': True, 'has_touch': True, 'device_scale_factor': 2}
DESKTOP = {'viewport': {'width': 1280, 'height': 900}}


def render_frame(page, timeout=15):
    end = time.time() + timeout
    while time.time() < end:
        for f in page.frames:
            if '/render?version=' in f.url:
                return f
        page.wait_for_timeout(200)
    raise AssertionError('render frame not found')


def puts(log):
    return [u for m, u in log if m == 'PUT' and '/reader-actions' in u]


def open_reader(p, ctx, aid, wait_overlay=True):
    page = ctx.new_page()
    log = []
    page.on('request', lambda r: log.append((r.method, r.url)))
    page.goto(p.origin + '/a/' + aid, wait_until='load')
    if wait_overlay:
        page.locator('.reader-actions-anchor').wait_for(state='visible', timeout=15000)
    return page, log


OVERLAY = """()=>{const o=document.querySelector('.reader-actions-anchor');const fe=document.querySelector('#artifact-frame');if(!fe)return {visible:false,frame:null};const f=fe.getBoundingClientRect();
 if(!o||o.hidden)return {visible:false,frame:f.toJSON()};const r=o.getBoundingClientRect();
 const btns=[...o.querySelectorAll('button')].map(b=>b.getBoundingClientRect().toJSON());
 // Lo que el anfitrión pinta en los puntos de los botones: el botón primero, luego sólo iframe y ancestros.
 const stacks=btns.map(b=>document.elementsFromPoint(b.x+b.width/2,b.y+b.height/2).map(e=>e.id?('#'+e.id):(e.className&&typeof e.className==='string'?'.'+e.className.split(' ')[0]:e.tagName)));
 return {visible:true,rect:r.toJSON(),buttons:btns,stacks,frame:f.toJSON()}}"""

SLOT = """()=>{const s=document.querySelector('[data-acciones-lector]');if(!s)return null;const r=s.getBoundingClientRect();
 const ceja=s.previousElementSibling;const c=ceja?.getBoundingClientRect();
 return {rect:r.toJSON(),afterCeja:!!ceja?.matches('.ceja'),cejaText:ceja?.textContent.trim(),gap:c?Math.round(r.top-c.bottom):null,
  inIndex:!!s.closest('.indice'),reacciones:[...document.querySelectorAll('[data-reacciones]')].map(n=>n.hidden),scrollY,innerWidth,innerHeight}}"""

# Dentro del iframe: ¿qué elemento del documento está encima del hueco en los puntos donde el anfitrión pinta los botones?
OCCLUSION = """pts=>pts.map(([x,y])=>{const e=document.elementFromPoint(x,y);if(!e)return 'none';if(e.closest('[data-acciones-lector]'))return 'slot';
 if(e.closest('.indice'))return 'index';return e.tagName.toLowerCase()+(e.id?'#'+e.id:'')+(typeof e.className==='string'&&e.className?'.'+e.className.trim().split(/\\s+/).slice(0,2).join('.'):'')})"""


def geometry_probe(p, browser, engine, aid, label, viewport, scroll_steps=10):
    ctx = p.context(browser, 'reader', **viewport)
    page, _ = open_reader(p, ctx, aid, wait_overlay=False)
    try:
        page.locator('.reader-actions-anchor').wait_for(state='visible', timeout=6000)
    except Exception:
        pass
    page.wait_for_timeout(1500)
    frame = render_frame(page)
    row = {'engine': engine, 'doc': label, 'viewport': viewport['viewport']['width'], 'slot': frame.evaluate(SLOT),
           'overlay': page.evaluate(OVERLAY), 'dock_hidden': page.evaluate("document.querySelector('.reader-actions-dock')?.hidden")}
    row['has_index'] = frame.evaluate("!!document.querySelector('.lectura-guiada:not([data-presentation]) .indice > .ceja')")
    row['index_visible'] = frame.evaluate("[...document.querySelectorAll('.lectura-guiada:not([data-presentation]) .indice')].some(n=>n.getClientRects().length&&n.querySelector(':scope > .ceja'))")
    issues = []
    if row['overlay']['visible'] and row['slot']:
        o, s = row['overlay']['rect'], row['slot']['rect']
        fr = row['overlay']['frame']
        row['delta'] = [round(o['x'] - (fr['x'] + s['x']), 1), round(o['y'] - (fr['y'] + s['y']), 1)]
        if max(map(abs, row['delta'])) > 2:
            issues.append('overlay misaligned %s' % row['delta'])
    if row['slot'] and not row['slot']['afterCeja']:
        issues.append('slot not after .ceja')
    if row['index_visible'] and not row['overlay']['visible']:
        issues.append('index visible but no overlay')
    # Recorrido de scroll: el ancla nunca debe pintarse sobre contenido que el documento pone encima del hueco
    # (galería ancha, encabezado fijo, etc.) ni sobre controles del anfitrión.
    height = frame.evaluate('document.scrollingElement.scrollHeight')
    occluded, host_cover, stale = [], [], []
    for i in range(scroll_steps + 1):
        y = int(height * i / scroll_steps)
        frame.evaluate('y=>scrollTo(0,y)', y)
        page.wait_for_timeout(260)
        ov = page.evaluate(OVERLAY)
        sl = frame.evaluate(SLOT)
        if not ov['visible']:
            continue
        fr = ov['frame']
        scale = fr['width'] / sl['innerWidth'] if sl else 1
        pts = [[(b['x'] + b['width'] / 2 - fr['x']) / scale, (b['y'] + b['height'] / 2 - fr['y']) / scale] for b in ov['buttons']]
        hits = frame.evaluate(OCCLUSION, pts)
        if any(h not in ('slot',) for h in hits):
            occluded.append({'scrollY': sl['scrollY'] if sl else y, 'hits': hits})
        for st in ov['stacks']:
            # El botón del ancla debe ser lo primero; detrás, el iframe. Cualquier otro control del anfitrión entre medio = tapado.
            under = [e for e in st[1:st.index('#artifact-frame')]] if '#artifact-frame' in st else st[1:]
            if not st or not st[0].startswith('.reader-action') and st[0] != 'BUTTON':
                host_cover.append({'scrollY': y, 'stack': st[:5]})
            elif [e for e in under if e not in ('.reader-actions-anchor',)]:
                host_cover.append({'scrollY': y, 'stack': st[:5], 'covers': under})
        if sl:
            d = abs(ov['rect']['y'] - (fr['y'] + sl['rect']['y'] * scale))
            if d > 2:
                stale.append({'scrollY': sl['scrollY'], 'dy': round(d, 1)})
    row['occluded'] = occluded[:6]
    row['host_overlap'] = host_cover[:6]
    row['stale'] = stale[:6]
    if occluded: issues.append('overlay painted over document content at %d scroll positions' % len(occluded))
    if host_cover: issues.append('overlay overlaps host UI at %d positions' % len(host_cover))
    if stale: issues.append('overlay out of sync with slot at %d positions' % len(stale))
    row['issues'] = issues
    ctx.close()
    return row


def flows_probe(p, browsers, docs, out):
    """Entrada real: intención, doble clic, tecla sostenida, mensajes forjados, persistencia multiusuario, revocación, guardados."""
    chromium, webkit = browsers.get('chromium'), browsers.get('webkit')
    doc = docs['doc']
    r = {}
    b1 = chromium or webkit
    ctx = p.context(b1, 'reader')
    page, log = open_reader(p, ctx, doc)
    anchor_save = page.locator('.reader-actions-anchor [data-action=saved]')
    dialog = page.locator('dialog.reader-actions-dialog')

    # 1. Forjados: desde el documento (script del autor), desde la ventana del portal y con claves extra.
    frame = render_frame(page)
    frame.evaluate("""()=>{const send=(op,data)=>parent.postMessage({bottifact:1,id:'f'+Math.random(),op,data},'*');
      send('reader-actions-anchor',{saved:true});send('reader-actions-anchor',{visible:true,x:0,y:0,width:300,height:44,vw:innerWidth,vh:innerHeight,liked:true});
      for(const op of ['reader-actions','save','like','action'])send(op,{saved:true,liked:true,key:'saved',value:true});
      document.querySelector('[data-reacciones] button')?.click();}""")
    page.evaluate("""()=>{for(const op of ['reader-actions-anchor','action'])postMessage({bottifact:1,id:'x',op,data:{saved:true,liked:true}},'*');
      document.querySelector('.reader-actions-anchor [data-action=saved]').dispatchEvent(new MouseEvent('click',{bubbles:true}));}""")
    page.wait_for_timeout(500)
    r['forged_messages_put'] = len(puts(log))
    r['forged_synthetic_click_opens_dialog'] = dialog.evaluate('d=>d.open')
    # El documento puede mover el ancla a cualquier punto de su propio viewport (no hay atadura al hueco real).
    frame.evaluate("()=>parent.postMessage({bottifact:1,id:'g',op:'reader-actions-anchor',data:{visible:true,x:40,y:600,width:300,height:44,vw:innerWidth,vh:innerHeight}},'*')")
    page.wait_for_timeout(300)
    moved = page.evaluate(OVERLAY)
    r['document_can_relocate_overlay'] = bool(moved['visible'] and abs(moved['rect']['y'] - 600) < 2)
    frame.evaluate('()=>scrollTo(0,1)')
    frame.evaluate('()=>scrollTo(0,0)')
    page.wait_for_timeout(400)

    # 2. Intención: clic real en el ancla y clic inmediato sobre «Guardar» del diálogo.
    anchor_save.click()
    dialog.locator('[data-action=saved]').wait_for(state='visible')
    box = dialog.locator('[data-action=saved]').bounding_box()
    t0 = time.time()
    page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
    r['early_click_ms'] = round((time.time() - t0) * 1000)
    page.wait_for_timeout(250)
    r['early_click_put'] = len(puts(log))
    page.wait_for_timeout(700)
    # Doble clic real tras el retardo: exactamente una mutación.
    page.mouse.dblclick(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
    page.wait_for_timeout(600)
    r['dblclick_puts'] = len(puts(log))
    r['saved_after_dblclick'] = p.state('reader', doc).json()['saved']
    page.keyboard.press('Escape')
    page.wait_for_timeout(300)
    r['overlay_after_close'] = page.evaluate(OVERLAY)['visible']
    r['focus_after_close'] = page.evaluate("document.activeElement?.dataset?.action||document.activeElement?.id||document.activeElement?.tagName")

    # 3. Tecla sostenida: Enter mantenido sobre el ancla «Me gusta».
    base = len(puts(log))
    page.locator('.reader-actions-anchor [data-action=liked]').focus()
    page.keyboard.down('Enter')
    for _ in range(6):
        page.wait_for_timeout(120)
        page.keyboard.down('Enter')  # Playwright marca repeat=true
    page.wait_for_timeout(800)
    for _ in range(4):
        page.keyboard.down('Enter')
        page.wait_for_timeout(60)
    page.keyboard.up('Enter')
    page.wait_for_timeout(400)
    r['held_enter_puts'] = len(puts(log)) - base
    r['held_enter_dialog_open'] = dialog.evaluate('d=>d.open')
    r['held_enter_focus'] = page.evaluate("document.activeElement?.getAttribute('aria-label')||document.activeElement?.tagName")
    if dialog.evaluate('d=>d.open'):
        page.keyboard.press('Escape')
    # Espacio sostenido
    base = len(puts(log))
    page.locator('.reader-actions-anchor [data-action=liked]').focus()
    page.keyboard.down(' ')
    for _ in range(10):
        page.wait_for_timeout(100)
        page.keyboard.down(' ')
    page.keyboard.up(' ')
    page.wait_for_timeout(400)
    r['held_space_puts'] = len(puts(log)) - base
    r['held_space_dialog_open'] = dialog.evaluate('d=>d.open')
    if dialog.evaluate('d=>d.open'):
        page.keyboard.press('Escape')

    # 4. Me gusta con clic real (tras retardo) para reader.
    page.locator('.reader-actions-anchor [data-action=liked]').click()
    page.wait_for_timeout(750)
    dialog.locator('[data-action=liked]').click()
    page.locator('dialog.reader-actions-dialog [data-action=liked][aria-pressed=true]').wait_for()
    page.keyboard.press('Escape')

    # 5. Cerrar con resize mientras el diálogo está abierto: el ancla debe volver.
    page.locator('.reader-actions-anchor [data-action=saved]').click()
    page.set_viewport_size({'width': 1240, 'height': 900})
    page.wait_for_timeout(500)
    page.keyboard.press('Escape')
    page.wait_for_timeout(600)
    r['overlay_after_resize_while_open'] = page.evaluate(OVERLAY)['visible']
    r['focus_after_resize_close'] = page.evaluate("document.activeElement?.dataset?.action||document.activeElement?.id||document.activeElement?.tagName")
    page.set_viewport_size({'width': 1280, 'height': 900})
    page.close()

    # 6. Segunda cuenta en el otro motor: estado independiente, total compartido.
    b2 = webkit or chromium
    ctx2 = p.context(b2, 'second')
    page2, log2 = open_reader(p, ctx2, doc)
    r['second_initial'] = {k: v for k, v in p.state('second', doc).json().items() if k in ('saved', 'liked', 'likes')}
    r['second_anchor_like_text'] = page2.locator('.reader-actions-anchor [data-action=liked]').text_content()
    page2.locator('.reader-actions-anchor [data-action=liked]').click()
    page2.wait_for_timeout(800)
    page2.locator('dialog.reader-actions-dialog [data-action=liked]').click()
    page2.locator('dialog.reader-actions-dialog [data-action=liked][aria-pressed=true]').wait_for()
    page2.close()
    r['after_both'] = {w: {k: v for k, v in p.state(w, doc).json().items() if k in ('saved', 'liked', 'likes')} for w in ('reader', 'second', 'author')}
    # Persistencia: reabrir en contexto nuevo.
    ctx.close()
    ctx = p.context(b1, 'reader')
    page, log = open_reader(p, ctx, doc)
    r['reload_anchor'] = [page.locator('.reader-actions-anchor [data-action=%s]' % k).text_content() for k in ('saved', 'liked')]

    # 7. Guardados: pestaña real del portal y navegación de vuelta.
    page.goto(p.origin + '/?view=saved')
    page.locator('.reader-saved-list a').first.wait_for(timeout=10000)
    r['saved_list'] = page.locator('.reader-saved-list a').evaluate_all('l=>l.map(a=>[a.textContent,a.getAttribute("href")])')
    r['saved_tab_active'] = page.evaluate("document.querySelector('[data-view=saved]')?.classList.contains('active')||document.querySelector('[data-view=saved]')?.getAttribute('aria-current')")
    page.goto(p.origin + '/')
    page.wait_for_timeout(1200)
    tab = page.locator('[data-view=saved]')
    r['saved_tab_visible'] = tab.is_visible()
    if tab.is_visible():
        tab.click()
        page.locator('.reader-saved-list a, .reader-saved-empty').first.wait_for(timeout=10000)
        r['saved_tab_url'] = page.url.replace(p.origin, '')
    page.locator('.reader-saved-list a').first.click()
    page.wait_for_url(re.compile('/a/' + doc))
    r['saved_link_navigates'] = True
    page.screenshot(path=str(out / 'reader-after-nav.png'))
    page.close()

    # 8. Revocación: se oculta de guardados y del total, se conserva la fila; re-concesión la devuelve.
    p.share(doc, 'invited', ('second@example.com',))
    r['revoked_state_status'] = p.state('reader', doc).status_code
    r['revoked_put_status'] = p.act('reader', doc, {'liked': True}).status_code
    r['revoked_saved_list'] = [a['id'] for a in p.clients['reader'].get('/api/reader/saved').json()['artifacts']]
    r['revoked_likes_seen_by_second'] = p.state('second', doc).json()['likes']
    page, _ = open_reader(p, ctx, doc, wait_overlay=False)
    page.wait_for_timeout(2500)
    r['revoked_overlay'] = page.evaluate(OVERLAY)['visible']
    page.close()
    p.share(doc)
    r['regrant_saved_list'] = [a['id'] for a in p.clients['reader'].get('/api/reader/saved').json()['artifacts']]
    r['regrant_likes'] = p.state('second', doc).json()['likes']
    ctx.close()
    return r


def fallback_probe(p, browser, engine, docs):
    out = {}
    for label in ('deck', 'raw'):
        ctx = p.context(browser, 'reader')
        page, log = open_reader(p, ctx, docs[label], wait_overlay=False)
        dock = page.locator('.reader-actions-dock')
        t0 = time.time()
        try:
            dock.wait_for(state='visible', timeout=8000)
            visible_after = round(time.time() - t0, 2)
        except Exception:
            visible_after = None
        row = {'dock_visible_after_s': visible_after, 'overlay': page.evaluate(OVERLAY)['visible'],
               'dock_attr_hidden': page.evaluate("document.querySelector('.reader-actions-dock')?.hidden"),
               'host_reader_dock_hidden': page.evaluate("document.querySelector('#reader-dock')?.hidden"),
               'dock_box': page.evaluate("document.querySelector('.reader-actions-dock')?.getBoundingClientRect().toJSON()")}
        if visible_after is not None:
            like = dock.locator('[data-action=liked]')
            row['dock_box'] = like.bounding_box()
            like.click()
            page.locator('.reader-actions-dock [data-action=liked][aria-pressed=true]').wait_for(timeout=5000)
            row['after_click'] = p.state('reader', docs[label]).json()['liked']
            # Doble clic real en el dock: detail>1 ignorado → un solo PUT
            n = len(puts(log))
            dock.locator('[data-action=saved]').dblclick()
            page.wait_for_timeout(600)
            row['dock_dblclick_puts'] = len(puts(log)) - n
            frame = render_frame(page)
            frame.evaluate("()=>parent.postMessage({bottifact:1,id:'h',op:'reader-actions-anchor',data:{visible:true,x:10,y:10,width:200,height:44,vw:innerWidth,vh:innerHeight}},'*')")
            page.wait_for_timeout(300)
            row['doc_can_force_anchor_and_hide_dock'] = page.evaluate(OVERLAY)['visible'] and page.evaluate("document.querySelector('.reader-actions-dock').hidden")
            p.act('reader', docs[label], {'liked': False, 'saved': False})
        ctx.close()
        out[label] = row
    # Anónimo en un documento público sin índice: el dock explica cómo entrar, no muta.
    ctx = p.context(browser, None)
    page, log = open_reader(p, ctx, docs['public_raw'], wait_overlay=False)
    try:
        page.locator('.reader-actions-dock').wait_for(state='visible', timeout=8000)
        page.locator('.reader-actions-dock [data-action=saved]').click()
        page.wait_for_timeout(400)
        out['anonymous'] = {'dialog_open': page.locator('dialog.reader-actions-dialog').evaluate('d=>d.open'),
                            'login_href': page.locator('.reader-actions-login').get_attribute('href'), 'puts': len(puts(log))}
    except Exception as e:
        out['anonymous'] = {'error': type(e).__name__, 'dock_hidden': page.evaluate("document.querySelector('.reader-actions-dock')?.hidden")}
    ctx.close()
    return out


def version_probe(p, browser, docs):
    """Cambio de versión en el selector real: reset+load, el ancla vuelve."""
    aid = docs['doc']
    ctx = p.context(browser, 'author')
    page, log = open_reader(p, ctx, aid)
    opts = page.locator('#version option').count()
    res = {'versions': opts}
    if opts > 1:
        # El selector vive en un menú plegado; se dispara el mismo handler «change» del portal.
        page.evaluate("()=>{const s=document.querySelector('#version');s.selectedIndex=1;s.dispatchEvent(new Event('change'))}")
        page.wait_for_timeout(300)
        res['overlay_hidden_during_switch'] = not page.evaluate(OVERLAY)['visible']
        try:
            page.locator('.reader-actions-anchor').wait_for(state='visible', timeout=8000)
            res['overlay_after_switch'] = True
        except Exception:
            res['overlay_after_switch'] = False
    ctx.close()
    return res


def alias_merge_probe():
    """Dos alias del administrador con «me gusta» en el mismo artefacto: tras la unión, ¿cuenta 1 o 2?"""
    import tempfile
    from unittest.mock import patch
    from fastapi.testclient import TestClient
    from portal.app import COOKIE, create_app
    out = {}
    with tempfile.TemporaryDirectory() as tmp:
        with patch.dict(os.environ, {'BOTTIFACT_OWNER_ALIASES': '', 'BOTTIFACT_ADMIN_EMAILS': ''}):
            app = create_app(tmp, origin='https://portal.test')
            s = app.state.store
            ids = {}
            for e in ('main@example.com', 'old@example.com', 'author@example.com'):
                ids[e] = s.user(e, e[:3])['id']
            def client(e):
                c = TestClient(app, base_url='https://portal.test', headers={'Origin': 'https://portal.test'})
                c.cookies.set(COOKIE, s.session(ids[e]))
                return c
            a = client('author@example.com')
            aid = a.post('/api/artifacts', json={'title': 'T', 'html': '<meta name="nota-documento" content="t"><p>x</p>'}).json()['id']
            a.put('/api/artifacts/' + aid + '/access', json={'visibility': 'invited', 'grants': [{'email': 'main@example.com', 'role': 'viewer'}, {'email': 'old@example.com', 'role': 'viewer'}]})
            for e in ('main@example.com', 'old@example.com'):
                client(e).put('/api/artifacts/' + aid + '/reader-actions', json={'liked': True, 'saved': True}, headers=ACT)
            out['before'] = a.get('/api/artifacts/' + aid + '/reader-actions').json()['likes']
        with patch.dict(os.environ, {'BOTTIFACT_OWNER_ALIASES': 'main@example.com,old@example.com', 'BOTTIFACT_ADMIN_EMAILS': ''}):
            app = create_app(tmp, origin='https://portal.test')
            s = app.state.store
            with s.db() as db:
                out['rows_after'] = {t: db.execute(f'SELECT user FROM {t} WHERE artifact=?', (aid,)).fetchall().__len__() for t in ('reader_saves', 'reader_likes')}
                out['old_user_left_rows'] = db.execute('SELECT count(*) FROM reader_likes WHERE user=?', (ids['old@example.com'],)).fetchone()[0]
            a = TestClient(app, base_url='https://portal.test', headers={'Origin': 'https://portal.test'})
            a.cookies.set(COOKIE, s.session(ids['author@example.com']))
            out['after'] = a.get('/api/artifacts/' + aid + '/reader-actions').json()['likes']
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--browsers', default='chromium,webkit')
    ap.add_argument('--out', default=str(Path(os.environ.get('TMPDIR', '/tmp')) / 'reader-actions-review'))
    ap.add_argument('--examples', default='all')
    ap.add_argument('--skip-geometry', action='store_true')
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright
    p = Portal()
    docs = {
        'doc': p.publish('Informe trimestral', contract_doc('Informe trimestral', reactions=True, footer={'author': 'Autora'})),
        'chapters': p.publish('Capítulos', chapters_doc('Capítulos')),
        'gallery': p.publish('Galería ancha', contract_doc('Galería ancha', extra=GALLERY)),
        'deck': p.publish('Presentación', deck('Presentación')),
        'raw': p.publish('HTML propio', RAW),
        'public_raw': p.publish('HTML público', RAW, visibility='public', grants=()),
    }
    # Segunda versión para el selector.
    v2 = p.clients['author'].post('/api/artifacts/' + docs['doc'] + '/versions', json={'title': 'Informe trimestral', 'html': contract_doc('Informe trimestral', reactions=True)})
    assert v2.status_code == 200, v2.text
    examples = sorted((ROOT / 'examples/generated').glob('*.html'))
    if args.examples != 'all':
        examples = [e for e in examples if e.stem in args.examples.split(',')]
    unpublishable = []
    for e in examples:
        try:
            docs['ex:' + e.stem] = p.publish(e.stem, e.read_text())
        except AssertionError as error:
            unpublishable.append([e.stem, str(error)[:120]])
    summary = {'unpublishable_examples': unpublishable, 'commit': os.popen('git -C %s rev-parse --short HEAD' % ROOT).read().strip(), 'geometry': [], 'flows': None, 'fallback': {}, 'version': None}
    try:
        with sync_playwright() as pw:
            browsers = {}
            for name in args.browsers.split(','):
                browsers[name] = getattr(pw, name).launch()
            summary['flows'] = flows_probe(p, browsers, docs, out)
            for name, b in browsers.items():
                summary['fallback'][name] = fallback_probe(p, b, name, docs)
            summary['version'] = version_probe(p, next(iter(browsers.values())), docs)
            if not args.skip_geometry:
                for name, b in browsers.items():
                    for vp_name, vp in (('desktop', DESKTOP), ('mobile', MOBILE)):
                        for label, aid in docs.items():
                            if label in ('deck', 'raw', 'public_raw'):
                                continue
                            try:
                                row = geometry_probe(p, b, name, aid, label, vp)
                            except Exception as e:
                                row = {'engine': name, 'doc': label, 'viewport': vp['viewport']['width'], 'error': repr(e)[:200], 'issues': ['probe error']}
                            summary['geometry'].append(row)
                            print(name, vp_name, label, row.get('issues'), flush=True)
            for b in browsers.values():
                b.close()
        summary['alias_merge'] = alias_merge_probe()
    finally:
        p.close()
    (out / 'summary.json').write_text(json.dumps(summary, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in summary.items() if k != 'geometry'}, indent=1, ensure_ascii=False))
    print('summary:', out / 'summary.json')


if __name__ == '__main__':
    main()
