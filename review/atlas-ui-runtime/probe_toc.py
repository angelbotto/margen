#!/usr/bin/env python3
"""Index (TOC) behaviour with physical input. Usage: probe_toc.py atlas.html engine shotsdir"""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from probe_common import serve, offline

STATE = r"""() => { const idx = document.querySelector('.pagina.viva .indice'), page = idx.closest('.pagina');
  const links = [...idx.querySelectorAll('a')];
  return {fixed: getComputedStyle(idx).position, mask: idx.hasAttribute('data-indice-mascara'), fade: idx.style.getPropertyValue('--indice-fade-y'),
    expectFade: Math.round(page.getBoundingClientRect().top - idx.getBoundingClientRect().top), maskImage: getComputedStyle(idx).maskImage || getComputedStyle(idx).webkitMaskImage,
    hash: location.hash, scrollY: Math.round(scrollY), active: document.activeElement?.id || document.activeElement?.tagName,
    items: links.map(a => { const li = a.closest('li'), p = a.querySelector('.indice-tachado path'); const box = a.getBoundingClientRect(), pb = p?.getBoundingClientRect();
      return {t: a.textContent.trim().slice(0, 18), visto: li.classList.contains('visto') || li.classList.contains('aqui-visto'), current: a.hasAttribute('aria-current'),
        paths: a.querySelectorAll('.indice-tachado path').length, off: p ? getComputedStyle(p).strokeDashoffset : null,
        pathInside: pb ? pb.top >= box.top - 2 && pb.bottom <= box.bottom + 2 && pb.width > 4 : null}; }) }; }"""

def main(html, engine, shots):
    shots = Path(shots); shots.mkdir(parents=True, exist_ok=True); rep = {}
    with serve(Path(html)) as url, sync_playwright() as pw:
        b = getattr(pw, engine).launch()
        ctx = b.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce'); offline(ctx, [])
        p = ctx.new_page(); errs = []; p.on('pageerror', lambda e: errs.append(str(e)))
        p.goto(url + '#atlas-lectura'); p.wait_for_timeout(500); p.evaluate('scrollTo(0,0)'); p.wait_for_timeout(200)
        rep['top'] = p.evaluate(STATE); p.screenshot(path=str(shots / f'{engine}-toc-top.png'))
        link = p.locator('.pagina.viva .indice a').nth(3)
        p.evaluate('scrollTo(0, 1600)'); p.wait_for_timeout(300)
        bb = link.bounding_box()
        hit = p.evaluate('([x,y]) => { const e = document.elementFromPoint(x,y); return e?.closest("a")?.getAttribute("href") || e?.tagName }', [bb['x'] + 10, bb['y'] + bb['height'] / 2])
        p.mouse.click(bb['x'] + 10, bb['y'] + bb['height'] / 2); p.wait_for_timeout(500)
        target = link.get_attribute('href')
        rep['click'] = {'hit': hit, 'href': target, 'targetTop': p.evaluate(f'Math.round(document.querySelector("{target}").getBoundingClientRect().top)'), **p.evaluate(STATE)}
        p.screenshot(path=str(shots / f'{engine}-toc-after-click.png'))
        # keyboard: focus index, tab to second link, Enter
        p.evaluate('scrollTo(0, 3000)'); p.wait_for_timeout(200)
        p.locator('.pagina.viva .indice').focus(); p.keyboard.press('Tab'); p.keyboard.press('Tab')
        focused = p.evaluate('document.activeElement.getAttribute("href")')
        masked_focus = p.evaluate('getComputedStyle(document.querySelector(".pagina.viva .indice")).maskImage')
        p.screenshot(path=str(shots / f'{engine}-toc-focus.png'))
        p.keyboard.press('Enter'); p.wait_for_timeout(500)
        rep['keyboard'] = {'focusedHref': focused, 'maskWhileFocused': masked_focus, 'targetTop': p.evaluate(f'Math.round(document.querySelector("{focused}").getBoundingClientRect().top)') if focused else None,
                           'activeAfter': p.evaluate('document.activeElement.id || document.activeElement.tagName'), 'hash': p.evaluate('location.hash')}
        # deep scroll to bottom: all but last struck?
        p.evaluate('scrollTo(0, document.documentElement.scrollHeight)'); p.wait_for_timeout(400)
        rep['bottom'] = p.evaluate(STATE); p.screenshot(path=str(shots / f'{engine}-toc-bottom.png'))
        # 1327: not fixed, no strike shown
        p.set_viewport_size({'width': 1327, 'height': 900}); p.wait_for_timeout(300)
        rep['w1327'] = p.evaluate("() => { const i = document.querySelector('.pagina.viva .indice'); return {pos: getComputedStyle(i).position, svgShown: [...i.querySelectorAll('.indice-tachado')].some(s => getComputedStyle(s).display !== 'none'), mask: i.hasAttribute('data-indice-mascara')}; }")
        rep['errors'] = errs
        b.close()
    print(json.dumps(rep, ensure_ascii=False, indent=1))

if __name__ == '__main__':
    main(*sys.argv[1:4])
