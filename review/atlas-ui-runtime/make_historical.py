#!/usr/bin/env python3
"""Historical-refresh fixture: render every chart/report/expression recipe with the production contract
(a d61743a tree), then apply the portal refresh from a newer tree. Usage: make_historical.py BASE_TREE NEW_TREE OUTDIR"""
import json, sys, importlib
from pathlib import Path
base, new, out = map(Path, sys.argv[1:4]); out.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(base / 'scripts'))
import contract_artifact as old
recipes = json.loads((base / 'packages/core/registry/registry.json').read_text())['componentes']
pages, n = [], 0
for cap in ('graficas', 'reportes', 'expresion', 'lectura'):
    items = [r for r in recipes if r['capitulo'] == cap]
    html = ''.join(f'<section class="seccion" id="h-{r["id"]}"><h2>{r["nombre"]}</h2><p>Receta histórica.</p></section>' + r['html'] for r in items)
    pages.append({'id': 'h-' + cap, 'titulo': cap, 'html': html}); n += len(items)
try:
    doc = old.build('Histórico', pages, description='fixture', document_id='review-historical', format='chapters', theme='editorial', mode='dark')
except ValueError as e:
    # keep going: record validation messages, build without validation
    print('base validation:', str(e)[:300]); old.validate = lambda html: []; doc = old.build('Histórico', pages, description='fixture', document_id='review-historical', format='chapters', theme='editorial', mode='dark')
(out / 'historical-base.html').write_text(doc)
sys.path.insert(0, str(new))
from portal.reader_style import without_embedded_flow, refresh_editorial_reference, with_initial_theme
P = new / 'portal'
refreshed = refresh_editorial_reference(with_initial_theme(without_embedded_flow(doc)), (P / 'static/editorial-reference.css').read_text(),
    (P / 'static/editorial-code.js').read_text(), (P / 'static/editorial-pieces.js').read_text(), json.loads((P / 'static/runtime-refresh.json').read_text()))
(out / 'historical-refreshed.html').write_text(refreshed)
print(json.dumps({'recipes': n, 'base_bytes': len(doc), 'refreshed_bytes': len(refreshed), 'chart_core_inserted': refreshed.count('data-nota-modulo="packages/core/components/chart-core.js"')}))
