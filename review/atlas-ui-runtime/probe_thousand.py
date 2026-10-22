#!/usr/bin/env python3
"""1..1000 numbered block: open with a physical click, numbering, gutter fit, highlighted ranges, exact copy. Usage: probe_thousand.py atlas.html engine"""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from probe_common import serve, offline
html, engine = sys.argv[1:3]
with serve(Path(html)) as url, sync_playwright() as pw:
    b = getattr(pw, engine).launch(); ctx = b.new_context(viewport={'width': 390, 'height': 844}, permissions=['clipboard-read', 'clipboard-write'] if engine == 'chromium' else []); offline(ctx, [])
    p = ctx.new_page()
    if engine == 'webkit': p.add_init_script("Object.defineProperty(navigator,'clipboard',{value:{writeText:async t=>{window.__copied=t}}})")
    p.goto(url + '#prueba-mil-lineas'); p.wait_for_timeout(600)
    s = p.locator('#prueba-mil-lineas > summary'); bb = s.bounding_box(); p.mouse.click(bb['x'] + 20, bb['y'] + bb['height'] / 2); p.wait_for_timeout(1500)
    code = p.locator('#prueba-mil-lineas code')
    info = code.evaluate("""c => { const lines = c.querySelectorAll('.codigo-linea'), last = lines[lines.length - 1];
      const before = getComputedStyle(last, '::before'), ctx = document.createElement('canvas').getContext('2d'); ctx.font = before.font || (before.fontSize + ' ' + before.fontFamily);
      const need = ctx.measureText('1000').width, have = parseFloat(before.width);
      const firstText = last.firstChild?.nodeType === 1 ? last.firstChild : last; const range = document.createRange(); range.selectNodeContents(last); const textLeft = range.getClientRects()[0]?.left - last.getBoundingClientRect().left;
      return {estado: c.dataset.codigoEstado, lines: lines.length, lastNumber: last.dataset.numero, digits: c.style.getPropertyValue('--codigo-cifras'),
              gutterNeed: +need.toFixed(1), gutterHave: have, numberRight: 16 + have, textLeft: +textLeft.toFixed(1),
              highlighted: [...c.querySelectorAll('.codigo-linea.destacada')].map(l => +l.dataset.numero)}; }""")
    btn = p.locator('#prueba-mil-lineas .cab button').first
    btn.scroll_into_view_if_needed(); p.wait_for_timeout(200); bb = btn.bounding_box(); p.mouse.click(bb['x'] + bb['width'] / 2, bb['y'] + bb['height'] / 2); p.wait_for_timeout(300)
    copied = p.evaluate('navigator.clipboard.readText()') if engine == 'chromium' else p.evaluate('window.__copied')
    src = code.evaluate('c => c.textContent')
    info.update({'copyExact': copied == src, 'copiedLines': copied.count('\n') + 1 if copied else 0, 'status': p.locator('#prueba-mil-lineas .copia-estado').first.text_content()})
    print(json.dumps(info, ensure_ascii=False)); b.close()
