#!/usr/bin/env python3
"""Deferred Three.js: no fetch on hidden pages, one fetch near view, offline fallback, pending interaction.
Three is served from a local copy verified against the pinned SRI (no network). Usage: probe_three.py atlas.html engine three.min.js"""
import json, sys, time
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
from probe_common import serve
html, engine, three = sys.argv[1:4]
body = Path(three).read_bytes()
SEL = '[data-flota],[data-escena],[data-globo]'
def run(mode, delay=0):
    reqs, errs = [], []
    with serve(Path(html)) as url, sync_playwright() as pw:
        b = getattr(pw, engine).launch(); ctx = b.new_context(viewport={'width': 1440, 'height': 900})
        def route(r):
            u = r.request.url
            if urlsplit(u).hostname == '127.0.0.1' or u.startswith('data:'): return r.continue_()
            reqs.append(u)
            if 'three' in u and mode == 'online':
                if delay: time.sleep(delay)
                return r.fulfill(status=200, body=body, headers={'content-type': 'application/javascript', 'access-control-allow-origin': '*'})
            r.abort()
        ctx.route('**/*', route)
        p = ctx.new_page(); p.on('pageerror', lambda e: errs.append(str(e)[:200]))
        p.goto(url + '#atlas-inicio'); p.wait_for_timeout(800)
        before = len(reqs)
        p.goto(url + '#atlas-expresion'); p.wait_for_timeout(400)
        p.evaluate("scrollTo(0,0)"); p.wait_for_timeout(400); at_top = len(reqs)
        states = []
        figs = p.locator(f'article.pagina:not([hidden]) :is({SEL})')
        for i in range(figs.count()):
            f = figs.nth(i); f.scroll_into_view_if_needed(); p.wait_for_timeout(150)
            # interact while possibly pending: click first enabled button inside figure physically
            btn = f.locator('button:visible').first
            if btn.count():
                bb = btn.bounding_box()
                if bb: p.mouse.click(bb['x'] + bb['width'] / 2, bb['y'] + bb['height'] / 2)
            p.wait_for_timeout(1500 if delay else 600)
            states.append(f.evaluate("""f => ({id: f.id, tres: f.dataset.tres || null, canvas: [...f.querySelectorAll('canvas')].filter(c => c.getClientRects().length && c.width > 0).length,
                error: [...f.querySelectorAll('[role=alert],.globo-error,.escena-error,.flota-error,[data-reason]')].filter(e => !e.hidden && e.textContent.trim()).map(e => e.textContent.trim().slice(0, 60))[0] || null})"""))
        b.close()
    return {'mode': mode, 'delay': delay, 'requestsOnInicio': before, 'requestsAtTopOfPage': at_top, 'requestsTotal': len(reqs), 'threeRequests': sum('three' in u for u in reqs), 'states': states, 'errors': errs}
res = [run('online'), run('offline'), run('online', delay=3)]
print(json.dumps({'engine': engine, 'runs': res}, ensure_ascii=False, indent=1))
