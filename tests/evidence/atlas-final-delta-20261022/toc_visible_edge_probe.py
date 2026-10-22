"""TOC current-section via the visible left edge on the REAL atlas (original repro: Lectura → «Glosario editorial»): physical click, cold deep link,
and every TOC link of the live chapter, at 1440/1328 and 390 (no fixed TOC → skipped). usage: ENGINE ATLAS_HTML OUTDIR"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'review/atlas-ui-runtime'))
from probe_common import serve, offline
from playwright.sync_api import sync_playwright
ENGINE, HTML, OUT = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
res = {'engine': ENGINE, 'checks': []}
def check(name, ok, detail=None):
    res['checks'].append({'name': name, 'ok': bool(ok), 'detail': detail}); print(('PASS ' if ok else 'FAIL ') + name, '' if ok else json.dumps(detail, ensure_ascii=False)[:400])
CUR = "document.querySelector('.pagina.viva .indice a[aria-current]')?.getAttribute('href')"
with serve(HTML) as url, sync_playwright() as p:
    b = getattr(p, ENGINE).launch()
    for w in (1440, 1328):
        ctx = b.new_context(viewport={'width': w, 'height': 900}); offline(ctx, [])
        pg = ctx.new_page(); pg.goto(url + '#receta-glosario'); pg.wait_for_timeout(1200)
        check(f'{w}: cold deep link #receta-glosario is current', pg.evaluate(CUR) == '#receta-glosario', pg.evaluate(CUR))
        pg.goto(url + '#atlas-lectura'); pg.wait_for_timeout(800)
        hrefs = pg.evaluate("[...document.querySelectorAll('.pagina.viva .indice a[href^=\"#\"]')].map(a=>a.getAttribute('href'))")
        wrong = []
        for h in hrefs:
            a = pg.locator(f'.pagina.viva .indice a[href="{h}"]').first
            if not a.is_visible(): continue
            try: a.click(position={'x': 10, 'y': a.bounding_box()['height'] / 2}, timeout=4000)
            except Exception as e: wrong.append({'href': h, 'unclickable': str(e).split('Call log')[-1][-300:]}); continue
            pg.wait_for_timeout(700)
            cur = pg.evaluate(CUR); top = pg.evaluate(f"document.getElementById('{h[1:]}')?.getBoundingClientRect().top")
            at_bottom = pg.evaluate("innerHeight + scrollY >= document.documentElement.scrollHeight - 2")
            if cur != h and not at_bottom: wrong.append({'href': h, 'current': cur, 'top': top})
        check(f'{w}: physical click on each of {len(hrefs)} Lectura TOC links marks it current (unless page bottom)', not wrong, wrong)
        ctx.close()
    b.close()
OUT.mkdir(parents=True, exist_ok=True); (OUT / f'toc-visible-edge-{ENGINE}.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))

assert all(c["ok"] for c in res["checks"]), res
