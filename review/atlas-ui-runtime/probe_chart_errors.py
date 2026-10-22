#!/usr/bin/env python3
"""Count chart figures that fail to draw in a rendered document. Usage: probe_chart_errors.py doc.html engine"""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from probe_common import serve, offline
SEL = '[data-grafica],[data-analitica],[data-reporte],[data-evidencia],[data-atencion]'
with serve(Path(sys.argv[1])) as url, sync_playwright() as pw:
    b = getattr(pw, sys.argv[2]).launch(); ctx = b.new_context(viewport={'width': 1440, 'height': 900}); offline(ctx, [])
    p = ctx.new_page(); errs = []; p.on('pageerror', lambda e: errs.append(str(e)[:160]))
    p.goto(url); p.wait_for_timeout(500)
    res = {}
    for pid in p.eval_on_selector_all('article.pagina[data-pagina]', 'a=>a.map(e=>e.id)') or ['']:
        if pid: p.goto(url + '#' + pid); p.wait_for_timeout(400)
        res[pid] = p.evaluate(f"""() => [...document.querySelectorAll('article.pagina:not([hidden]) :is({SEL})')].map(f => ({{id: f.id || f.closest('[id]')?.id, svg: f.querySelectorAll('svg').length,
            error: (f.querySelector('.grafica-error,.evidencia-error,[data-error-grafica],.analitica-error,.atencion-error')?.textContent || '').slice(0, 90)}}))""")
    print(json.dumps({'G': p.evaluate('typeof MargenGraficas'), 'pageerrors': errs[:5],
                      'summary': {k: {'figures': len(v), 'errors': sum(1 for f in v if f['error']), 'sample': [f for f in v if f['error']][:2]} for k, v in res.items() if v}}, ensure_ascii=False, indent=1))
