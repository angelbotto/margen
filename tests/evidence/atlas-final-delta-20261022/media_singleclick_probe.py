"""Follow-up to media_doubleclick_browser.py: does ONE physical click (attacker asks on mousedown) already reach the
portal control under the pointer? Fresh page per trial, final URL of every tab after 2 s. usage: REPO OUTDIR ENGINE"""
import json, sys, runpy
from pathlib import Path
REPO, OUT, ENGINE = Path(sys.argv[1]).resolve(), Path(sys.argv[2]), sys.argv[3]
sys.argv = [sys.argv[0], str(REPO), str(OUT / 'unused'), ENGINE]
g = {}
src = (Path(__file__).parent / 'media_doubleclick_browser.py').read_text().split('with sync_playwright() as p:')[0]
exec(compile(src, 'setup', 'exec'), g)
from playwright.sync_api import sync_playwright
out = {'engine': ENGINE, 'trials': []}
with sync_playwright() as p:
    browser = getattr(p, ENGINE).launch()
    for mode, selector in (('external', '.media-dialog .media-source'), ('embed', '.media-dialog .media-play')):
        for trial in ('recon', 'single', 'single-other-place'):
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
            box = pg.locator('#artifact-frame').bounding_box()
            if trial == 'recon':
                pg.evaluate("()=>0"); fr.evaluate("()=>document.getElementById('trampa').dispatchEvent(new MouseEvent('mousedown'))")
            # scripted mousedown has no activation; open via a real click far from any control instead
            pg.mouse.click(box['x'] + 40, box['y'] + 40); pg.wait_for_timeout(600)
            ctl = pg.locator(selector).bounding_box() if pg.evaluate("()=>document.querySelector('.media-dialog')?.open") else None
            pg.keyboard.press('Escape'); pg.wait_for_timeout(400)
            reqs.clear(); n = len(ctx.pages)
            if trial != 'recon' and ctl:
                x, y = (ctl['x'] + ctl['width'] / 2, ctl['y'] + ctl['height'] / 2) if trial == 'single' else (box['x'] + 40, box['y'] + 40)
                pg.mouse.click(x, y); pg.wait_for_timeout(2000)
            out['trials'].append({'mode': mode, 'trial': trial, 'control': ctl, 'requests': list(reqs), 'tabs': [t.url for t in ctx.pages[n:]],
                                  'dialog_open': pg.evaluate("()=>document.querySelector('.media-dialog')?.open"),
                                  'players': pg.evaluate("()=>document.querySelectorAll('.media-player').length")})
            print(json.dumps(out['trials'][-1]))
            ctx.close()
    browser.close()
(OUT / f'singleclick-{ENGINE}.json').write_text(json.dumps(out, indent=1))
