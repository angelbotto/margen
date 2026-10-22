#!/usr/bin/env python3
"""Footer link detail revealed by real keyboard focus; code block geometry. Usage: probe_footer_code.py atlas.html engine shots"""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from probe_common import serve, offline
html, engine, shots = sys.argv[1:4]
tab = 'Alt+Tab' if engine == 'webkit' else 'Tab'
with serve(Path(html)) as url, sync_playwright() as pw:
    b = getattr(pw, engine).launch(); ctx = b.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce'); offline(ctx, [])
    p = ctx.new_page(); p.goto(url + '#atlas-inicio'); p.wait_for_timeout(500)
    p.evaluate("document.querySelector('.hoja > .pie.pie-documento').scrollIntoView()")
    p.locator('.hoja > .pie.pie-documento').evaluate("f => { const r = f.previousElementSibling; r.tabIndex = -1; r.focus(); }")
    seen = []
    for _ in range(40):
        p.keyboard.press(tab)
        info = p.evaluate("""() => { const a = document.activeElement, f = document.querySelector('.hoja > .pie.pie-documento'); if (!f.contains(a)) return null;
          const d = a.closest('.pie-enlace')?.querySelector('.pie-detalle'); const s = getComputedStyle(a);
          return {text: a.textContent.trim().slice(0, 30), detailFilter: d ? getComputedStyle(d).filter : null, outline: s.outlineStyle + ' ' + s.outlineWidth, focusVisible: a.matches(':focus-visible'),
                  inView: a.getBoundingClientRect().top >= 0 && a.getBoundingClientRect().bottom <= innerHeight}; }""")
        if info: seen.append(info)
        if info and len(seen) >= 6: break
    p.screenshot(path=f'{shots}/{engine}-footer-keyboard.png')
    p.goto(url + '#atlas-configuracion'); p.wait_for_timeout(600)
    code = p.evaluate("""() => [...document.querySelectorAll('.pagina.viva .codigo.codigo-editorial pre')].filter(e => e.getClientRects().length).slice(0, 6).map(pre => {
        const s = getComputedStyle(pre), box = pre.closest('.codigo').getBoundingClientRect();
        return {id: pre.closest('[id]')?.id, w: Math.round(box.width), blur: s.backdropFilter || s.webkitBackdropFilter, bg: s.backgroundColor, inWide: !!pre.closest('.ancho,.amplio')}; })""")
    print(json.dumps({'footer': seen, 'code': code}, ensure_ascii=False, indent=1))
    b.close()
