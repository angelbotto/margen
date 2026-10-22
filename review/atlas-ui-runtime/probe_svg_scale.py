#!/usr/bin/env python3
"""Per page and width: chart SVGs drawn, scaled (viewBox vs rendered) or wider than their figure. Usage: probe_svg_scale.py doc.html engine"""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from probe_common import serve, offline
with serve(Path(sys.argv[1])) as url, sync_playwright() as pw:
    b = getattr(pw, sys.argv[2]).launch(); out = {}
    for w in (320, 390, 1440):
        ctx = b.new_context(viewport={'width': w, 'height': 860}); offline(ctx, []); p = ctx.new_page(); p.goto(url); p.wait_for_timeout(400)
        for pid in p.eval_on_selector_all('article.pagina[data-pagina]', 'a=>a.map(e=>e.id)'):
            p.goto(url + '#' + pid); p.wait_for_timeout(500)
            r = p.evaluate("""() => { const svgs = [...document.querySelectorAll('article.pagina:not([hidden]) svg.mg-svg')].filter(s => s.getClientRects().length);
              const bad = svgs.map(s => { const r = s.getBoundingClientRect(), vb = s.viewBox.baseVal, k = vb && vb.width ? r.width / vb.width : 1;
                return {id: s.closest('[id]')?.id, k: +k.toFixed(2), scroll: s.classList.contains('mg-desplazable')}; }).filter(x => Math.abs(x.k - 1) > .02 && !x.scroll);
              return {svgs: svgs.length, scaled: bad, overflow: document.documentElement.scrollWidth > innerWidth + 1}; }""")
            if r['svgs']: out[f'{w}:{pid}'] = r
        ctx.close()
    b.close()
print(json.dumps(out, ensure_ascii=False))
