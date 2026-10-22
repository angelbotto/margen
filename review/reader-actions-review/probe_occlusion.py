#!/usr/bin/env python3
"""Componentes anchos (galería, código, tabla) que cruzan el hueco bajo «En esta página» y contraste host/documento.

Por cada ancho y posición de scroll: si en los puntos donde el portal pinta los botones el documento pone otra cosa
encima del hueco, el ancla (z-index 4 del anfitrión, fuera del iframe) tapa ese contenido. Guarda capturas de cada caso.
Uso: python review/reader-actions-review/probe_occlusion.py --out DIR [--browsers chromium,webkit]
"""
import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import ROOT, Portal, contract_doc, GALLERY
from check_reader_actions_portal import open_reader, render_frame, OVERLAY, SLOT, OCCLUSION

CODE = '<section class="ancho" id="codigo"><pre tabindex="0" aria-label="Código"><code>' + ('const linea_muy_larga = "' + 'x' * 160 + '";\n') * 30 + '</code></pre></section>'
TABLE = '<section class="amplio" id="tabla"><div tabindex="0" role="region" aria-label="Tabla" style="overflow-x:auto"><table><tbody>' + ('<tr>' + '<td>celda ancha de datos</td>' * 12 + '</tr>') * 30 + '</tbody></table></div></section>'
WIDTHS = (1200, 1280, 1440, 1600, 1920)
DARK = ('linear-dark', 'hacker', 'linear-light', 'tikin')


def sweep(p, browser, engine, aid, label, width, out, steps=24):
    ctx = p.context(browser, 'reader', viewport={'width': width, 'height': 900})
    page, _ = open_reader(p, ctx, aid, wait_overlay=False)
    page.wait_for_timeout(2500)
    frame = render_frame(page)
    height = frame.evaluate('document.scrollingElement.scrollHeight')
    cases, shot = [], False
    for i in range(steps + 1):
        frame.evaluate('y=>scrollTo(0,y)', int(height * i / steps))
        page.wait_for_timeout(220)
        ov, sl = page.evaluate(OVERLAY), frame.evaluate(SLOT)
        if not ov['visible'] or not sl:
            continue
        fr = ov['frame']; scale = fr['width'] / sl['innerWidth']
        pts = [[(b['x'] + b['width'] / 2 - fr['x']) / scale, (b['y'] + b['height'] / 2 - fr['y']) / scale] for b in ov['buttons']]
        hits = frame.evaluate(OCCLUSION, pts)
        if any(h != 'slot' for h in hits):
            cases.append({'scrollY': sl['scrollY'], 'hits': hits})
            if not shot:
                page.screenshot(path=str(out / f'occlusion-{engine}-{label}-{width}.png')); shot = True
    ctx.close()
    return {'engine': engine, 'doc': label, 'width': width, 'occluded_positions': len(cases), 'examples': cases[:4]}


def theme_shots(p, browser, engine, docs, out):
    rows = []
    for label in DARK:
        aid = docs.get('ex:' + label)
        if not aid:
            continue
        ctx = p.context(browser, 'reader', viewport={'width': 1280, 'height': 900}, color_scheme='light')
        page, _ = open_reader(p, ctx, aid, wait_overlay=False)
        page.wait_for_timeout(2500)
        ov = page.evaluate(OVERLAY)
        row = {'doc': label, 'overlay': ov['visible']}
        if ov['visible']:
            frame = render_frame(page)
            row['doc_bg'] = frame.evaluate("getComputedStyle(document.body).backgroundColor")
            row['button_bg'] = page.evaluate("getComputedStyle(document.querySelector('.reader-actions-anchor .reader-action')).backgroundColor")
            row['button_color'] = page.evaluate("getComputedStyle(document.querySelector('.reader-actions-anchor .reader-action')).color")
            r = ov['rect']
            page.screenshot(path=str(out / f'theme-{engine}-{label}.png'), clip={'x': max(0, r['x'] - 40), 'y': max(0, r['y'] - 60), 'width': 420, 'height': 160})
        rows.append(row)
        ctx.close()
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--browsers', default='chromium,webkit')
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright
    p = Portal()
    docs = {'gallery': p.publish('Galería', contract_doc('Galería', extra=GALLERY)),
            'code': p.publish('Código', contract_doc('Código', extra=CODE)),
            'table': p.publish('Tabla', contract_doc('Tabla', extra=TABLE))}
    for name in DARK + ('priorities', 'guide'):
        f = ROOT / 'examples/generated' / (name + '.html')
        try:
            docs['ex:' + name] = p.publish(name, f.read_text())
        except AssertionError:
            pass
    result = {'sweeps': [], 'themes': {}}
    try:
        with sync_playwright() as pw:
            for engine in args.browsers.split(','):
                b = getattr(pw, engine).launch()
                for label, aid in docs.items():
                    if label.startswith('ex:') and label[3:] in DARK:
                        continue
                    for w in WIDTHS:
                        row = sweep(p, b, engine, aid, label, w, out)
                        result['sweeps'].append(row)
                        print(engine, label, w, row['occluded_positions'], row['examples'][:1], flush=True)
                result['themes'][engine] = theme_shots(p, b, engine, docs, out)
                b.close()
    finally:
        p.close()
    (out / 'occlusion.json').write_text(json.dumps(result, indent=1, ensure_ascii=False))
    print(json.dumps(result['themes'], indent=1))


if __name__ == '__main__':
    main()
