"""Alt attack on 63bb3b2 printReady: many deferred blocks, blocks in HIDDEN chapters, one block mid-colouring when print
starts, and Chromium page.pdf(). Every block must end 'listo' with numbered lines == real lines and exact text, no dupes.
usage: MARGEN_BROWSER=chromium|webkit python print_probe.py REPO OUTDIR"""
import json, os, sys, tempfile
from html import escape
from pathlib import Path
REPO, OUT = Path(sys.argv[1]).resolve(), Path(sys.argv[2]); ENGINE = os.environ.get('MARGEN_BROWSER', 'chromium')
sys.path.insert(0, str(REPO / 'scripts')); sys.path.insert(0, str(REPO / 'review/atlas-ui-runtime'))
from contract_artifact import build
from probe_common import serve, offline
from playwright.sync_api import sync_playwright
def src(n, k): return ''.join(f'const v{k}_{i} = {i}; // línea {i}\n' for i in range(n)).rstrip('\n')
blocks = {}
def box(i, n):
    blocks[i] = src(n, i)
    return f'<div class="codigo"><div class="cab"><span>javascript</span></div><pre tabindex="0" aria-label="{i}"><code id="{i}" data-lenguaje="javascript" data-lineas>{escape(blocks[i])}</code></pre></div>'
chapters = []
for c in range(3):
    html = f'<section class="seccion" id="s{c}"><h2>Capítulo {c}</h2>' + ''.join('<p>' + 'relleno ' * 200 + '</p>' + box(f'k{c}_{j}', 3000 if j == 0 else 60) for j in range(12)) + '</section>'
    chapters.append({'id': f'cap{c}', 'titulo': f'Cap {c}', 'html': html})
tmp = tempfile.TemporaryDirectory(); path = Path(tmp.name) / 'doc.html'
path.write_text(build('Impresión', chapters, description='probe', document_id='print-probe', format='chapters', theme='editorial', mode='light', date='2026-10-22'))
STATE = """(ids)=>ids.map(i=>{const c=document.getElementById(i);return {i,estado:c.dataset.codigoEstado||null,num:c.querySelectorAll('.codigo-linea[data-numero]').length,
  tokens:c.querySelectorAll('[class*=codigo-]').length,text:c.textContent}})"""
res = {'engine': ENGINE, 'checks': []}
def check(name, ok, detail=None):
    res['checks'].append({'name': name, 'ok': bool(ok), 'detail': detail}); print(('PASS ' if ok else 'FAIL ') + name, '' if ok else json.dumps(detail, ensure_ascii=False)[:500])
with serve(path) as url, sync_playwright() as p:
    b = getattr(p, ENGINE).launch()
    for trigger in ('media', 'beforeprint') + (('pdf',) if ENGINE == 'chromium' else ()):
        ctx = b.new_context(viewport={'width': 1280, 'height': 900}); blocked = []; offline(ctx, blocked)
        pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        pg.goto(url + '#cap0'); pg.wait_for_timeout(50)
        # Start colouring the 3000-line block now so print begins while it is mid-way (running generator).
        pg.evaluate("()=>document.getElementById('k0_0').scrollIntoView()"); pg.wait_for_timeout(30)
        before = pg.evaluate(STATE, list(blocks))
        hidden = sum(1 for s in before if s['estado'] is None)
        if trigger == 'media': pg.emulate_media(media='print')
        elif trigger == 'beforeprint': pg.evaluate("dispatchEvent(new Event('beforeprint'))")
        else: pg.pdf(path=str(Path(tmp.name) / 'out.pdf'))
        pg.wait_for_timeout(300)
        after = pg.evaluate(STATE, list(blocks))
        bad = [{'i': s['i'], 'estado': s['estado'], 'num': s['num']} for s in after if s['estado'] != 'listo' or s['num'] != blocks[s['i']].count('\n') + 1 or s['text'] != blocks[s['i']]]
        check(f'{trigger}: {len(blocks)} blocks ({hidden} untouched before, incl. hidden chapters) all listo/exact after print', not bad, bad[:6])
        pg.emulate_media(media='screen'); pg.evaluate("()=>{for(const id of ['cap1','cap2'])document.querySelector('[data-ir=\"'+id+'\"]')?.click()}"); pg.wait_for_timeout(400)
        again = pg.evaluate(STATE, list(blocks))
        dup = [s['i'] for s in again if s['num'] != blocks[s['i']].count('\n') + 1]
        check(f'{trigger}: no duplicated lines after returning to screen and opening chapters', not dup, dup[:6])
        check(f'{trigger}: no errors/network', not errs and not blocked, [errs[:3], blocked[:3]])
        ctx.close()
    b.close()
OUT.mkdir(parents=True, exist_ok=True); (OUT / f'print-{ENGINE}.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
sys.exit(0 if all(c['ok'] for c in res['checks']) else 1)
