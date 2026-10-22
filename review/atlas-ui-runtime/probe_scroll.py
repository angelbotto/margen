#!/usr/bin/env python3
"""Wheel-scroll each page and record long tasks, rAF gaps and running animations. Usage: probe_scroll.py atlas.html engine"""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from probe_common import serve, offline
html, engine = sys.argv[1:3]
INIT = """window.__lt=[];try{new PerformanceObserver(l=>__lt.push(...l.getEntries().map(e=>Math.round(e.duration)))).observe({type:'longtask',buffered:true})}catch{}
window.__gaps=[];let __last=0;const __f=t=>{if(__last&&t-__last>50)__gaps.push(Math.round(t-__last));__last=t;requestAnimationFrame(__f)};requestAnimationFrame(__f);"""
out = {}
with serve(Path(html)) as url, sync_playwright() as pw:
    b = getattr(pw, engine).launch()
    for motion in ('reduce', 'no-preference'):
        ctx = b.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion=motion); offline(ctx, [])
        p = ctx.new_page(); p.add_init_script(INIT); p.goto(url); p.wait_for_timeout(800)
        for pid in ['atlas-graficas', 'atlas-configuracion', 'atlas-pruebas']:
            p.goto(url + '#' + pid); p.wait_for_timeout(600); p.evaluate('scrollTo(0,0); __lt.length=0; __gaps.length=0')
            p.mouse.move(720, 450)
            for _ in range(60): p.mouse.wheel(0, 400); p.wait_for_timeout(30)
            p.wait_for_timeout(300)
            out[f'{motion}:{pid}'] = p.evaluate("""() => ({longtasks: __lt.slice(), gaps: __gaps.slice(), scrollY: Math.round(scrollY),
                animations: document.getAnimations().filter(a => a.playState === 'running').map(a => (a.effect?.target?.className?.baseVal ?? a.effect?.target?.className ?? '') + ':' + (a.animationName || a.transitionProperty || 'waapi')).slice(0, 8),
                runningCount: document.getAnimations().filter(a => a.playState === 'running').length})""")
        ctx.close()
    b.close()
print(json.dumps(out, ensure_ascii=False, indent=1))
