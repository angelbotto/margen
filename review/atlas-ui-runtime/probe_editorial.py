#!/usr/bin/env python3
"""Editorial metrics vs reference, footer focus, local reactions, print and no-JS. Usage: probe_editorial.py atlas.html engine shots"""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from probe_common import serve, offline

METRICS = r"""() => { const page = document.querySelector('.pagina.viva') || document.querySelector('.hoja');
  const m = el => { if (!el) return null; const s = getComputedStyle(el), r = el.getBoundingClientRect(); return {w: Math.round(r.width), fs: s.fontSize, lh: s.lineHeight, ls: s.letterSpacing, ff: s.fontFamily.split(',')[0]}; };
  const pre = page.querySelector('.codigo.codigo-editorial pre') || document.querySelector('.codigo.codigo-editorial pre');
  return {h1: m(document.querySelector('.hoja .cabecera h1')), h2: m(page.querySelector('.seccion h2')), p: m(page.querySelector('.seccion > p:not(.ceja)')),
          code: pre ? {...m(pre), blur: getComputedStyle(pre).backdropFilter || getComputedStyle(pre).webkitBackdropFilter, code: m(pre.querySelector('code'))} : null,
          date: (() => { const t = document.querySelector('.cabecera-fecha time'); return t ? {text: t.textContent, datetime: t.getAttribute('datetime'), lines: t.getClientRects().length} : null; })(),
          overflow: document.documentElement.scrollWidth > innerWidth + 1}; }"""

def main(html, engine, shots):
    shots = Path(shots); shots.mkdir(parents=True, exist_ok=True); rep = {}
    with serve(Path(html)) as url, sync_playwright() as pw:
        b = getattr(pw, engine).launch()
        for w in (320, 390, 1280, 1328, 1440):
            ctx = b.new_context(viewport={'width': w, 'height': 900}, reduced_motion='reduce'); offline(ctx, [])
            p = ctx.new_page(); p.goto(url + '#atlas-inicio'); p.wait_for_timeout(500)
            rep[f'metrics-{w}'] = p.evaluate(METRICS); ctx.close()
        ctx = b.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce'); offline(ctx, [])
        p = ctx.new_page(); p.goto(url + '#atlas-inicio'); p.wait_for_timeout(500)
        # Footer: link detail blurred until hover/focus; keyboard focus must reveal
        p.evaluate("document.querySelector('.pie-documento').scrollIntoView()"); p.wait_for_timeout(200)
        first = p.locator('.pie-documento .pie-enlaces a').first
        before = first.evaluate("a => getComputedStyle(a.closest('.pie-enlace').querySelector('.pie-detalle')).filter")
        first.focus(); p.wait_for_timeout(400)
        after = first.evaluate("a => [getComputedStyle(a.closest('.pie-enlace').querySelector('.pie-detalle')).filter, getComputedStyle(a).outlineStyle, a.matches(':focus-visible')]")
        p.screenshot(path=str(shots / f'{engine}-footer-focus.png'))
        rep['footer'] = {'blurBefore': before, 'afterFocus': after, 'links': p.eval_on_selector_all('.pie-documento a', 'as => as.map(a => [a.textContent.trim(), a.href, a.target, a.rel])')}
        # Reactions: physical click toggles and persists across reload
        btn = p.locator('.pie-documento .reacciones button[data-reaccion]').first
        btn.scroll_into_view_if_needed(); bb = btn.bounding_box(); p.mouse.click(bb['x'] + bb['width'] / 2, bb['y'] + bb['height'] / 2)
        pressed = btn.get_attribute('aria-pressed'); p.reload(); p.wait_for_timeout(500)
        persisted = p.locator('.pie-documento .reacciones button[data-reaccion]').first.get_attribute('aria-pressed')
        rep['reactions'] = {'count': p.locator('.pie-documento .reacciones button[data-reaccion]').count(), 'pressedAfterClick': pressed, 'afterReload': persisted,
                            'note': p.locator('.reacciones-nota').first.text_content() if p.locator('.reacciones-nota').count() else None,
                            'storageKeys': p.evaluate("Object.keys(localStorage).filter(k => k.startsWith('margen-reacciones'))")}
        # Print media
        p.emulate_media(media='print')
        rep['print'] = p.evaluate("""() => ({reactions: getComputedStyle(document.querySelector('.pie-documento .reacciones')).display, detailFilter: getComputedStyle(document.querySelector('.pie-detalle')).filter,
            bordes: document.querySelector('.lectura-bordes') ? getComputedStyle(document.querySelector('.lectura-bordes')).display : null,
            hiddenPages: [...document.querySelectorAll('article.pagina')].filter(a => getComputedStyle(a).display === 'none').length, pages: document.querySelectorAll('article.pagina').length,
            codeColored: document.querySelectorAll('.codigo [data-codigo-estado=listo]').length, codeBlocks: document.querySelectorAll('.codigo pre code').length})""")
        p.pdf(path=str(shots / 'print.pdf')) if engine == 'chromium' else None
        ctx.close()
        # No JS
        ctx = b.new_context(viewport={'width': 390, 'height': 900}, java_script_enabled=False); offline(ctx, [])
        p = ctx.new_page(); p.goto(url); p.wait_for_timeout(300)
        rep['nojs'] = p.evaluate("""(() => ({pagesVisible: [...document.querySelectorAll('article.pagina')].filter(a => a.getClientRects().length).length, pages: document.querySelectorAll('article.pagina').length,
            overflow: document.documentElement.scrollWidth > innerWidth + 1, tablesVisible: [...document.querySelectorAll('[data-grafica] table')].filter(t => t.getClientRects().length).length,
            charts: document.querySelectorAll('[data-grafica]').length, reactionsVisible: [...document.querySelectorAll('.reacciones')].filter(e => e.getClientRects().length).length}))""") if False else None
        # evaluate needs JS in page; use locator-based checks instead
        rep['nojs'] = {'pagesVisible': sum(1 for i in range(p.locator('article.pagina').count()) if p.locator('article.pagina').nth(i).is_visible()),
                       'pages': p.locator('article.pagina').count(),
                       'reactionsVisible': sum(1 for i in range(p.locator('.reacciones').count()) if p.locator('.reacciones').nth(i).is_visible()),
                       'chartTablesVisible': sum(1 for i in range(p.locator('[data-grafica] table').count()) if p.locator('[data-grafica] table').nth(i).is_visible()),
                       'charts': p.locator('[data-grafica]').count()}
        p.screenshot(path=str(shots / f'{engine}-nojs-390.png'))
        b.close()
    print(json.dumps(rep, ensure_ascii=False, indent=1))

if __name__ == '__main__':
    main(*sys.argv[1:4])
