#!/usr/bin/env python3
"""Hit-test every interactive element and every index label against the fixed index.

For each atlas page at widths where the index is fixed, scroll the page in steps and:
 * for each focusable/clickable element that overlaps the index box, ask the engine what is
   on top at the overlap centre (same hit test a physical click uses);
 * for each visible index label, report content that paints *below* the label (index above content).
Usage: probe_layering.py atlas.html chromium|webkit out.json
"""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from probe_common import serve, offline

JS = r"""() => {
 const page = document.querySelector('.pagina.viva') || document.querySelector('.hoja');
 const idx = page.querySelector('.indice'); if (!idx || getComputedStyle(idx).position !== 'fixed') return {fixed:false};
 const ib = idx.getBoundingClientRect(); const out = {fixed:true, blocked:[], over:[]};
 const id = el => { const s = el.closest('[id]'); return (s ? '#' + s.id + ' ' : '') + el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/).slice(0,2).join('.') : ''); };
 const q = 'a[href],button,summary,input,select,textarea,[tabindex]:not([tabindex="-1"]),[role=button],[role=slider],[role=tab]';
 for (const el of page.querySelectorAll(q)) {
  if (idx.contains(el) || !el.checkVisibility({visibilityProperty:true, opacityProperty:true})) continue;
  for (const r of el.getClientRects()) {
   const l = Math.max(r.left, ib.left), t = Math.max(r.top, ib.top, 0), rr = Math.min(r.right, ib.right), b = Math.min(r.bottom, ib.bottom, innerHeight);
   if (rr - l < 2 || b - t < 2) continue;
   const x = (l + rr) / 2, y = (t + b) / 2, hit = document.elementFromPoint(x, y);
   if (hit && idx.contains(hit)) out.blocked.push({el: id(el), x: Math.round(x), y: Math.round(y), hit: id(hit)});
  }
 }
 for (const a of idx.querySelectorAll('a')) {
  const r = a.getBoundingClientRect(); if (!r.width || r.bottom < 0 || r.top > innerHeight) continue;
  const x = r.left + Math.min(r.width/2, 40), y = r.top + r.height/2;
  const stack = document.elementsFromPoint(x, y); const i = stack.findIndex(e => idx.contains(e));
  if (i < 0) continue;
  const below = stack.slice(i + 1).find(e => !idx.contains(e) && page.contains(e) && e !== page && !e.matches('.pagina,.hoja,body,html') && (e.textContent.trim() || e.matches('img,svg,canvas,video,iframe')));
  if (below) out.over.push({label: a.textContent.trim().slice(0,40), below: id(below), x: Math.round(x), y: Math.round(y)});
 }
 return out;
}"""

def main(html, engine, out):
    report = {'engine': engine, 'results': [], 'blocked_requests': []}
    with serve(Path(html)) as url, sync_playwright() as pw:
        browser = getattr(pw, engine).launch()
        for width, opened in ((1328, False), (1440, False), (1440, True)):
            ctx = browser.new_context(viewport={'width': width, 'height': 900}, reduced_motion='reduce')
            offline(ctx, report['blocked_requests'])
            page = ctx.new_page()
            page.goto(url, wait_until='load'); page.evaluate('document.fonts.ready')
            ids = page.eval_on_selector_all('article.pagina[data-pagina]', 'a=>a.map(e=>e.id)')
            for pid in ids:
                page.goto(url + '#' + pid); page.wait_for_timeout(300)
                if opened: page.evaluate("document.querySelectorAll('.pagina.viva details').forEach(d=>d.open=true)"); page.wait_for_timeout(200)
                page.evaluate('window.scrollTo(0,0)')
                height = page.evaluate('document.documentElement.scrollHeight')
                y = 0
                while y < height:
                    page.evaluate(f'window.scrollTo(0,{y})'); page.wait_for_timeout(60)
                    r = page.evaluate(JS)
                    if r.get('blocked') or r.get('over'):
                        report['results'].append({'width': width, 'details_open': opened, 'page': pid, 'scrollY': y, **r})
                    y += 450
            ctx.close()
        browser.close()
    Path(out).write_text(json.dumps(report, ensure_ascii=False, indent=1))
    agg = {}
    for r in report['results']:
        for b in r['blocked']: agg.setdefault(('blocked', r['width'], r['details_open'], r['page'], b['el']), b)
        for o in r['over']: agg.setdefault(('over', r['width'], r['details_open'], r['page'], o['below']), o)
    for k in sorted(agg, key=str): print(k)
    print('unique issues', len(agg))

if __name__ == '__main__':
    main(*sys.argv[1:4])
