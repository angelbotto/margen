#!/usr/bin/env python3
"""Revisión delta de los arreglos de Guardar / Me gusta sobre la base ae6275f (REPORT.md).

Portal real (harness.Portal) del checkout que indica MARGEN_ROOT, Chromium y WebKit, entrada real de Playwright.
Sondas acotadas y secuenciales:
  dock     presentación y HTML propio: dock de respaldo visible, botón realmente clicable, PUT, toast con enlace
  occ      tabla / galería / priorities a 1280, 1440, 1920 y 390 px: rejilla de puntos sobre cada botón del ancla
  modal    abrir diálogo, redimensionar, cerrar (Escape y botón): ancla vuelve y el foco regresa a quien abrió
  theme    documentos oscuros y claros: contraste botón/fondo del ancla y del dock
  saved    /?view=saved directo: aria-current="page" y lista

Uso: MARGEN_ROOT=/ruta/al/checkout python review/reader-actions-review/check_delta.py --out DIR [--only dock,occ]
Sale con 1 si alguna sonda falla.
"""
import argparse, json, os, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import ROOT, Portal, contract_doc, deck, RAW, GALLERY
from check_reader_actions_portal import open_reader, render_frame, OVERLAY, SLOT, puts
from probe_occlusion import TABLE

MOBILE = {'viewport': {'width': 390, 'height': 844}, 'is_mobile': True, 'has_touch': True, 'device_scale_factor': 2}
RAW_DARK = RAW.replace('<body>', '<body style="background:#101114;color:#eee">')

# Rejilla 5x3 sobre cada botón del ancla, en coordenadas del iframe.
GRID = """()=>{const o=document.querySelector('.reader-actions-anchor');const f=document.querySelector('#artifact-frame').getBoundingClientRect();
 if(!o||o.hidden)return null;const pts=[];for(const b of o.querySelectorAll('button')){const r=b.getBoundingClientRect();
 for(const fx of [.08,.3,.5,.7,.92])for(const fy of [.15,.5,.85])pts.push([r.x+r.width*fx-f.x,r.y+r.height*fy-f.y]);}
 return {pts,scale:f.width/innerWidth}}"""
HITS = """([pts,scale])=>pts.map(([x,y])=>{const e=document.elementFromPoint(x/scale,y/scale);
 if(!e)return 'none';if(e.closest('[data-acciones-lector]'))return 'slot';
 return e.tagName.toLowerCase()+(typeof e.className==='string'&&e.className?'.'+e.className.trim().split(/\\s+/)[0]:'')})"""


def lum(rgb):
    ch = [c / 255 for c in rgb]
    ch = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in ch]
    return .2126 * ch[0] + .7152 * ch[1] + .0722 * ch[2]


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return round((la + .05) / (lb + .05), 2)


def rgb(css):
    import re
    nums = re.findall(r'[\d.]+', css)
    return [round(float(n)) for n in nums[:3]] if len(nums) >= 3 else None


def probe_dock(p, b, engine, docs):
    rows = []
    for label in ('deck', 'raw'):
        for vp_name, vp in (('desktop', {}), ('mobile', MOBILE)):
            aid = docs[label]
            p.act('reader', aid, {'saved': False, 'liked': False})
            ctx = p.context(b, 'reader', **vp)
            page, log = open_reader(p, ctx, aid, wait_overlay=False)
            row = {'engine': engine, 'doc': label, 'vp': vp_name}
            try:
                page.locator('.reader-actions-dock').wait_for(state='visible', timeout=8000)
            except Exception:
                pass
            info = page.evaluate("""()=>{const d=document.querySelector('.reader-actions-dock');if(!d)return null;
             const parent=d.parentElement.id;const btns=[...d.querySelectorAll('button')].map(x=>{const r=x.getBoundingClientRect();
             const top=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return {rect:r.toJSON(),top_is_self:top===x||x.contains(top),top:top?.id||top?.className||top?.tagName}});
             const host=[...document.querySelectorAll('#reader-dock button:not([hidden])')].map(x=>x.getBoundingClientRect().toJSON());
             return {hidden:d.hidden,parent,display:getComputedStyle(d).display,btns,host,overlay_visible:!document.querySelector('.reader-actions-anchor')?.hidden}}""")
            row['info'] = info
            issues = []
            if not info or info['hidden'] or not info['btns'] or not info['btns'][0]['rect']['width']:
                issues.append('dock not visible')
            else:
                if not all(x['top_is_self'] for x in info['btns']):
                    issues.append('dock button covered')
                for bb in info['btns']:
                    r = bb['rect']
                    for h in info['host']:
                        if r['x'] < h['x'] + h['width'] and h['x'] < r['x'] + r['width'] and r['y'] < h['y'] + h['height'] and h['y'] < r['y'] + r['height']:
                            issues.append('dock overlaps host dock')
                # Qué cubre el dock dentro del documento (informativo: controles del documento bajo el dock = problema).
                frame = render_frame(page)
                fr = page.evaluate("document.querySelector('#artifact-frame').getBoundingClientRect().toJSON()")
                under = []
                for bb in info['btns']:
                    r = bb['rect']
                    under.append(frame.evaluate("""([x,y])=>{const e=document.elementFromPoint(x,y);return e?(e.tagName.toLowerCase()+(e.closest('button,a,input,select,[role=button],[tabindex]')?':interactive':'')):'none'}""",
                                                [r['x'] + r['width'] / 2 - fr['x'], r['y'] + r['height'] / 2 - fr['y']]))
                row['doc_under_dock'] = under
                if any(u.endswith(':interactive') for u in under):
                    issues.append('dock covers interactive document control')
                save = page.locator('.reader-actions-dock [data-action=saved]')
                bx = save.bounding_box()
                page.mouse.click(bx['x'] + bx['width'] / 2, bx['y'] + bx['height'] / 2)
                page.wait_for_timeout(900)
                row['puts'] = len(puts(log))
                row['pressed'] = save.get_attribute('aria-pressed')
                row['toast'] = page.evaluate("(()=>{const t=document.querySelector('#toast');return {hidden:t.hidden,text:t.textContent,link:t.querySelector('a')?.getAttribute('href')}})()")
                row['server'] = p.state('reader', aid).json().get('saved')
                if row['puts'] != 1 or row['pressed'] != 'true' or not row['server']:
                    issues.append('dock click did not save')
                if row['toast']['link'] != '/?view=saved':
                    issues.append('toast without saved link')
                if vp_name == 'desktop':
                    page.screenshot(path=str(OUT / f'delta-dock-{engine}-{label}.png'))
            row['issues'] = issues
            rows.append(row)
            print('dock', engine, label, vp_name, issues, flush=True)
            ctx.close()
    return rows


def probe_occ(p, b, engine, docs, steps=20):
    rows = []
    for label in ('table', 'gallery', 'priorities'):
        if label not in docs:
            continue
        for w in (1280, 1440, 1920, 390):
            vp = MOBILE if w == 390 else {'viewport': {'width': w, 'height': 900}}
            ctx = p.context(b, 'reader', **vp)
            page, _ = open_reader(p, ctx, docs[label], wait_overlay=False)
            page.wait_for_timeout(2500)
            frame = render_frame(page)
            height = frame.evaluate('document.scrollingElement.scrollHeight')
            visible, bad, shot = 0, [], False
            for i in range(steps + 1):
                frame.evaluate('y=>scrollTo(0,y)', int(height * i / steps))
                page.wait_for_timeout(240)
                g = page.evaluate(GRID)
                if not g:
                    continue
                visible += 1
                hits = frame.evaluate(HITS, [g['pts'], g['scale']])
                if any(h != 'slot' for h in hits):
                    bad.append({'scrollY': frame.evaluate('scrollY'), 'hits': sorted(set(hits))})
                    if not shot:
                        page.screenshot(path=str(OUT / f'delta-occ-{engine}-{label}-{w}.png')); shot = True
            row = {'engine': engine, 'doc': label, 'width': w, 'visible_positions': visible, 'occluded_positions': len(bad), 'examples': bad[:3]}
            row['issues'] = ['anchor over content at %d positions' % len(bad)] if bad else []
            rows.append(row)
            print('occ', engine, label, w, visible, len(bad), bad[:1], flush=True)
            ctx.close()
    return rows


def probe_modal(p, b, engine, docs):
    rows = []
    for how in ('Escape', 'button'):
        ctx = p.context(b, 'reader', viewport={'width': 1280, 'height': 900})
        page, _ = open_reader(p, ctx, docs['report'])
        page.wait_for_timeout(800)
        opener = page.locator('.reader-actions-anchor [data-action=liked]')
        bx = opener.bounding_box()
        page.mouse.click(bx['x'] + bx['width'] / 2, bx['y'] + bx['height'] / 2)
        page.locator('.reader-actions-dialog').wait_for(state='visible')
        page.set_viewport_size({'width': 1440, 'height': 900})
        page.wait_for_timeout(700)
        page.set_viewport_size({'width': 1280, 'height': 900})
        page.wait_for_timeout(700)
        if how == 'Escape':
            page.keyboard.press('Escape')
        else:
            c = page.locator('.reader-actions-dialog button[aria-label=Cerrar]').bounding_box()
            page.mouse.click(c['x'] + c['width'] / 2, c['y'] + c['height'] / 2)
        page.wait_for_timeout(500)
        r = page.evaluate("""()=>{const o=document.querySelector('.reader-actions-anchor');const a=document.activeElement;
         return {overlay_hidden:o.hidden,dialog_open:document.querySelector('.reader-actions-dialog').open,
          focus:a?.id||a?.className||a?.tagName,focus_is_like:a?.matches('.reader-actions-anchor [data-action=liked]')}}""")
        row = {'engine': engine, 'close': how, **r}
        row['issues'] = [m for m, bad in (('anchor hidden after close', r['overlay_hidden']), ('focus not on opener', not r['focus_is_like']), ('dialog still open', r['dialog_open'])) if bad]
        rows.append(row)
        print('modal', engine, how, row['issues'], flush=True)
        ctx.close()
    return rows


def probe_theme(p, b, engine, docs):
    rows = []
    for label in ('linear-dark', 'hacker', 'linear-light', 'raw-dark'):
        if label not in docs:
            continue
        for scheme in ('light', 'dark'):
            ctx = p.context(b, 'reader', viewport={'width': 1280, 'height': 900}, color_scheme=scheme)
            page, _ = open_reader(p, ctx, docs[label], wait_overlay=False)
            page.wait_for_timeout(2600)
            sel = '.reader-actions-anchor:not([hidden]) .reader-action, .reader-actions-dock:not([hidden]) .reader-action'
            c = page.evaluate("""s=>{const b=document.querySelector(s);if(!b)return null;const cs=getComputedStyle(b);
             const badge=b.querySelector('.reader-action-count');const bs=badge&&getComputedStyle(badge);
             return {kind:b.closest('.reader-actions-dock')?'dock':'anchor',bg:cs.backgroundColor,color:cs.color,border:cs.borderColor,
              badge:bs?[bs.backgroundColor,bs.color]:null,frame_bg:getComputedStyle(document.querySelector('#artifact-frame')).backgroundColor}}""", sel)
            row = {'engine': engine, 'doc': label, 'scheme': scheme, 'css': c, 'issues': []}
            if not c:
                row['issues'].append('no reader action visible')
            else:
                frame = render_frame(page)
                doc_bg = frame.evaluate("(()=>{for(const n of [document.body,document.documentElement]){const c=getComputedStyle(n).backgroundColor;if(!/rgba\\(0, 0, 0, 0\\)|transparent/.test(c))return c}return 'rgb(255,255,255)'})()")
                row['doc_bg'] = doc_bg
                bg, fg, dbg = rgb(c['bg']), rgb(c['color']), rgb(doc_bg)
                if 'rgba' in c['bg'] and c['bg'].endswith(', 0)'):
                    bg = dbg
                row['text_contrast'] = contrast(fg, bg)
                row['bg_delta_doc'] = round(abs(lum(bg) - lum(dbg)), 3)
                if c['badge']:
                    row['badge_contrast'] = contrast(rgb(c['badge'][0]), rgb(c['badge'][1]))
                if row['text_contrast'] < 4.5:
                    row['issues'].append('text contrast %.2f' % row['text_contrast'])
                if (lum(dbg) < .179) != (lum(bg) < .179):
                    row['issues'].append('button surface does not follow document theme')
                if c['badge'] and row['badge_contrast'] < 4.5:
                    row['issues'].append('badge contrast %.2f' % row['badge_contrast'])
                page.screenshot(path=str(OUT / f'delta-theme-{engine}-{label}-{scheme}.png'))
            rows.append(row)
            print('theme', engine, label, scheme, row.get('text_contrast'), row['issues'], flush=True)
            ctx.close()
    return rows


def probe_saved(p, b, engine, docs):
    p.act('reader', docs['report'], {'saved': True})
    ctx = p.context(b, 'reader', viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    page.goto(p.origin + '/?view=saved', wait_until='load')
    try:
        page.locator('.reader-saved-list a, .reader-saved-empty').first.wait_for(timeout=8000)
    except Exception:
        pass
    page.wait_for_timeout(600)
    r = page.evaluate("""()=>({tabs:[...document.querySelectorAll('button[data-view]')].filter(b=>b.getAttribute('aria-current')==='page').map(b=>b.dataset.view),
     saved_current:document.querySelector('button[data-view=saved]')?.getAttribute('aria-current'),saved_hidden:document.querySelector('button[data-view=saved]')?.hidden,
     items:[...document.querySelectorAll('.reader-saved-list a')].map(a=>a.getAttribute('href')),url:location.pathname+location.search})""")
    row = {'engine': engine, **r}
    row['issues'] = [m for m, bad in (('saved tab not aria-current=page', r['saved_current'] != 'page'), ('other tab marked current', [t for t in r['tabs'] if t != 'saved']),
                                       ('saved list empty', '/a/' + docs['report'] not in r['items'])) if bad]
    print('saved', engine, row, flush=True)
    ctx.close()
    return [row]


def main():
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--browsers', default='chromium,webkit')
    ap.add_argument('--only', default='dock,occ,modal,theme,saved')
    args = ap.parse_args()
    OUT = Path(args.out); OUT.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright
    import portal
    p = Portal()
    docs = {'deck': p.publish('Deck', deck('Deck')), 'raw': p.publish('Raw', RAW), 'raw-dark': p.publish('Raw oscuro', RAW_DARK),
            'report': p.publish('Informe', contract_doc('Informe')),
            'table': p.publish('Tabla', contract_doc('Tabla', extra=TABLE)), 'gallery': p.publish('Galería', contract_doc('Galería', extra=GALLERY))}
    for name in ('priorities', 'linear-dark', 'hacker', 'linear-light'):
        docs[name] = p.publish(name, (ROOT / 'examples/generated' / (name + '.html')).read_text())
    p.act('second', docs['report'], {'liked': True})
    summary = {'root': str(ROOT), 'portal_module': portal.__file__, 'commit': os.popen('git -C %s rev-parse --short HEAD' % ROOT).read().strip(), 'probes': {}}
    print('root', summary['root'], summary['commit'], summary['portal_module'], flush=True)
    probes = {'dock': probe_dock, 'occ': probe_occ, 'modal': probe_modal, 'theme': probe_theme, 'saved': probe_saved}
    started = time.time()
    try:
        with sync_playwright() as pw:
            for engine in args.browsers.split(','):
                b = getattr(pw, engine).launch()
                for name in args.only.split(','):
                    summary['probes'].setdefault(name, []).extend(probes[name](p, b, engine, docs))
                b.close()
    finally:
        p.close()
    summary['seconds'] = round(time.time() - started)
    failed = {k: [r for r in v if r['issues']] for k, v in summary['probes'].items()}
    summary['failed'] = {k: len(v) for k, v in failed.items()}
    (OUT / 'delta-summary.json').write_text(json.dumps(summary, indent=1, ensure_ascii=False))
    print(json.dumps(summary['failed']), flush=True)
    sys.exit(1 if any(failed.values()) else 0)


if __name__ == '__main__':
    main()
