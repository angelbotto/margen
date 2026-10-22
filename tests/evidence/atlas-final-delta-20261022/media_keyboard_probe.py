"""Keyboard variant: the reader scrolls with Space/Enter inside the artifact; the artifact asks the portal on keydown,
the portal moves focus to its own control, and the reader's NEXT keystroke activates it. Real keyboard events.
usage: REPO OUTDIR ENGINE"""
import json, sys
from pathlib import Path
REPO, OUT, ENGINE = Path(sys.argv[1]).resolve(), Path(sys.argv[2]), sys.argv[3]
sys.argv = [sys.argv[0], str(REPO), str(OUT / 'unused'), ENGINE]
g = {}
src = (Path(__file__).parent / 'media_doubleclick_browser.py').read_text().split('with sync_playwright() as p:')[0]
src = src.replace("addEventListener('mousedown',()=>{", "addEventListener('keydown',ev=>{if(window.__done)return;window.__done=1;")
src = src.replace("document.getElementById('trampa').addEventListener", "document.addEventListener")
exec(compile(src, 'setup', 'exec'), g)
from playwright.sync_api import sync_playwright
out = {'engine': ENGINE, 'trials': []}
with sync_playwright() as p:
    browser = getattr(p, ENGINE).launch()
    for mode in ('external', 'embed'):
        for key in ('Space', 'Enter'):
            ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
            reqs = []
            ctx.route(g['ORIGIN'] + '/**', g['proxy'])
            ctx.route(lambda url: not url.startswith((g['ORIGIN'], 'data:', 'about:', 'blob:')), lambda r: (reqs.append(r.request.url), r.fulfill(status=200, content_type='text/html', body='<p>stub</p>')))
            pg = ctx.new_page(); pg.goto(g['ORIGIN'] + '/a/' + g['AID'])
            for _ in range(150):
                fr = next((f for f in pg.frames if '/render' in f.url), None)
                try:
                    if fr and fr.evaluate("()=>!!window.BottifactReviewBridge"): break
                except Exception: pass
                pg.wait_for_timeout(100)
            pg.wait_for_timeout(1200); fr.evaluate("([v,m])=>{window.__version=v;window.mode=m}", [g['V1'], mode])
            fr.locator('#trampa').focus() if False else fr.evaluate("()=>{document.body.tabIndex=-1;document.body.focus()}")
            n = len(ctx.pages)
            pg.keyboard.press(key); pg.wait_for_timeout(250)
            focused = pg.evaluate("()=>document.activeElement?.className+'|'+document.activeElement?.textContent")
            pg.keyboard.press(key); pg.wait_for_timeout(1500)
            out['trials'].append({'mode': mode, 'key': key, 'focus_after_first_key': focused, 'requests': list(reqs), 'tabs': [t.url for t in ctx.pages[n:]],
                                  'players': pg.evaluate("()=>document.querySelectorAll('.media-player').length")})
            print(json.dumps(out['trials'][-1])); ctx.close()
    browser.close()
(OUT / f'keyboard-{ENGINE}.json').write_text(json.dumps(out, indent=1))
