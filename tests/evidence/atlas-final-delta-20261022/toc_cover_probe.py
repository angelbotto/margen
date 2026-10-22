"""Hit-test: with #apuntes-ejemplo in view (scrolled there via its own TOC entry), which TOC links of the live page are
covered by content? Reports elementFromPoint at each link centre. usage: ENGINE ATLAS_HTML WIDTH [SHOT]"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'review/atlas-ui-runtime'))
from probe_common import serve, offline
from playwright.sync_api import sync_playwright
ENGINE, HTML, W = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3])
with serve(HTML) as url, sync_playwright() as p:
    b = getattr(p, ENGINE).launch(); ctx = b.new_context(viewport={'width': W, 'height': 900}); offline(ctx, [])
    pg = ctx.new_page(); pg.goto(url + '#apuntes-ejemplo'); pg.wait_for_timeout(1200)
    r = pg.evaluate("""()=>{const out=[];for(const a of document.querySelectorAll('.pagina.viva .indice a[href^="#"]')){const b=a.getBoundingClientRect();if(!b.width||b.bottom<0||b.top>innerHeight)continue;
      const e=document.elementFromPoint(b.left+b.width/2,b.top+b.height/2);if(!a.contains(e)&&e!==a)out.push({href:a.getAttribute('href'),covered_by:(e?.closest('[id]')?.id||e?.tagName)+'.'+(e?.className||'')})}
      const ap=document.getElementById('apuntes-ejemplo').getBoundingClientRect(),ix=document.querySelector('.pagina.viva .indice').getBoundingClientRect();
      return {covered:out,apuntes:[ap.left,ap.right],indice:[ix.left,ix.right],pos:getComputedStyle(document.querySelector('.pagina.viva .indice')).position}}""")
    print(json.dumps(r, ensure_ascii=False))
    if len(sys.argv) > 4: pg.screenshot(path=sys.argv[4])
    b.close()
