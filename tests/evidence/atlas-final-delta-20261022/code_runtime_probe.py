"""Independent probe of 1a4a2e4/a531697: nested author wrappers stay functional (real click on the link, mark kept),
a trailing newline gives no numbered empty line, and copy (button + full selection) is byte-exact, incl. the final \\n.
Also checks the trailing-newline block is not visibly taller than the same block without it.
usage: MARGEN_BROWSER=chromium|webkit python code_runtime_probe.py REPO OUTDIR"""
import json, os, sys, tempfile
from html import escape
from pathlib import Path
REPO, OUT = Path(sys.argv[1]).resolve(), Path(sys.argv[2]); ENGINE = os.environ.get('MARGEN_BROWSER', 'chromium')
sys.path.insert(0, str(REPO / 'scripts')); sys.path.insert(0, str(REPO / 'review/atlas-ui-runtime'))
from contract_artifact import build
from probe_common import serve, offline
from playwright.sync_api import sync_playwright
SRC = {'c1': 'const a = 1;\nconst b = 2;\n', 'c4': 'const a = 1;\nconst b = 2;', 'c5': 'x\n\n'}
def code(i, body, numbered=True):
    return f'<div class="codigo"><div class="cab"><span>javascript</span></div><pre tabindex="0" aria-label="{i}"><code id="{i}" data-lenguaje="javascript"{" data-lineas" if numbered else ""}>{body}</code></pre></div>'
page = ('<section class="seccion" id="s1"><h2>Uno</h2><p>destino</p></section><section class="seccion" id="s2"><h2>Dos</h2>'
        + code('c1', escape(SRC['c1'])) + code('c4', escape(SRC['c4'])) + code('c5', escape(SRC['c5'])) + code('c6', escape(SRC['c1']), False)
        + code('c2', '<mark>// ver <a href="#s1">enlace</a></mark>\nx = 1;') + code('c3', 'const <a href="#s1"><mark>marcado</mark></a> = 3;') + '<p>' + 'relleno ' * 600 + '</p></section>')
tmp = tempfile.TemporaryDirectory(); path = Path(tmp.name) / 'doc.html'
path.write_text(build('Código', [{'id': 'uno', 'titulo': 'Uno', 'html': page}], description='probe', document_id='code-probe', format='document', theme='editorial', mode='light', date='2026-10-22'))
res = {'engine': ENGINE, 'checks': []}
def check(name, ok, detail=None):
    res['checks'].append({'name': name, 'ok': bool(ok), 'detail': detail}); print(('PASS ' if ok else 'FAIL ') + name, '' if ok else json.dumps(detail, ensure_ascii=False)[:400])
with serve(path) as url, sync_playwright() as p:
    b = getattr(p, ENGINE).launch(); ctx = b.new_context(viewport={'width': 1280, 'height': 900}); blocked = []; offline(ctx, blocked)
    if ENGINE == 'chromium': ctx.grant_permissions(['clipboard-read', 'clipboard-write'], origin=url.split('/doc')[0])
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.goto(url); pg.wait_for_timeout(800)
    pg.wait_for_function("window.NotaCodigo && NotaCodigo.pendientes()===0", timeout=10000)
    for i in ('c1', 'c5', 'c6'):
        info = pg.evaluate("(i)=>{const c=document.getElementById(i);return {text:c.textContent,numbered:c.querySelectorAll('.codigo-linea[data-numero]').length,rows:c.querySelectorAll('.codigo-linea').length}}", i)
        check(f'{i}: textContent byte-exact', info['text'] == SRC.get(i, SRC['c1']), info)
    check('c1: 2 numbered rows for 2 real lines', pg.evaluate("document.querySelectorAll('#c1 .codigo-linea[data-numero]').length") == 2)
    check('c5 (x\\n\\n): blank real line keeps its number (2 numbered)', pg.evaluate("document.querySelectorAll('#c5 .codigo-linea[data-numero]').length") == 2,
          pg.evaluate("[...document.querySelectorAll('#c5 .codigo-linea')].map(l=>[l.dataset.numero||null,l.textContent])"))
    h = pg.evaluate("['c1','c4'].map(i=>document.getElementById(i).closest('pre').getBoundingClientRect().height)")
    check('trailing newline adds no visible extra line (pre height c1 vs c4)', abs(h[0] - h[1]) < 2, h)
    # Full selection copy
    for i in ('c1', 'c6'):
        sel = pg.evaluate("(i)=>{const r=document.createRange();r.selectNodeContents(document.getElementById(i));const s=getSelection();s.removeAllRanges();s.addRange(r);return s.toString()}", i)
        check(f'{i}: selection toString keeps final newline', sel == SRC['c1'], repr(sel))
    pg.evaluate("getSelection().removeAllRanges()")
    if ENGINE == 'chromium':
        btn = pg.locator('#c1').locator('xpath=ancestor::div[contains(@class,"codigo")]').locator('[data-codigo-copiar],[data-copiar]').first
        btn.scroll_into_view_if_needed(); btn.click(); pg.wait_for_timeout(300)
        check('c1: copy button writes byte-exact source to real clipboard', pg.evaluate("navigator.clipboard.readText()") == SRC['c1'])
    link = pg.locator('#c2 a'); check('c2: link kept inside mark', link.count() == 1 and pg.locator('#c2 mark a, #c2 mark .codigo-linea a').count() + pg.locator('#c2 mark').locator('a').count() >= 1,
        pg.evaluate("document.getElementById('c2').innerHTML.slice(0,400)"))
    link.scroll_into_view_if_needed(); link.click(); pg.wait_for_timeout(400)
    check('c2: real click on nested link navigates to #s1', pg.evaluate("location.hash") == '#s1', pg.evaluate("location.hash"))
    check('c3: mark kept inside link', pg.locator('#c3 a mark').count() == 1, pg.evaluate("document.getElementById('c3').innerHTML.slice(0,400)"))
    check('c2/c3 textContent unchanged', pg.evaluate("[document.getElementById('c2').textContent,document.getElementById('c3').textContent]") == ['// ver enlace\nx = 1;', 'const marcado = 3;'])
    check('no page errors / no network', not errs and not blocked, [errs, blocked])
    b.close()
OUT.mkdir(parents=True, exist_ok=True); (OUT / f'code-runtime-{ENGINE}.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
sys.exit(0 if all(c['ok'] for c in res['checks']) else 1)
