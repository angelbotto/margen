#!/usr/bin/env python3
"""Cold-load measurements of two renders of the same atlas sources (base vs candidate).

Usage: measure_atlas.py --base base/atlas.html --candidate new/atlas.html --output result.json [--runs 3]
Each run is a fresh browser context, served from 127.0.0.1 with every other request aborted.
Chromium also runs with 4x CPU throttling through CDP. Lab automation only: no field or FPS claims.
"""
from __future__ import annotations

import argparse
import gzip
import json
import statistics
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, urlsplit

from playwright.sync_api import sync_playwright


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


INIT = """(()=>{window.__m={listeners:0,tasks:[]};const add=EventTarget.prototype.addEventListener;
EventTarget.prototype.addEventListener=function(...a){window.__m.listeners++;return add.apply(this,a)};
if(PerformanceObserver.supportedEntryTypes.includes('longtask'))new PerformanceObserver(l=>__m.tasks.push(...l.getEntries().map(e=>[Math.round(e.startTime),Math.round(e.duration)]))).observe({type:'longtask',buffered:true});})()"""

SNAPSHOT = """()=>{const n=performance.getEntriesByType('navigation')[0];const t=__m.tasks;
return {nodes:document.querySelectorAll('*').length,codeSpans:document.querySelectorAll('.codigo-linea').length,
 dcl:Math.round(n.domContentLoadedEventEnd),load:Math.round(n.loadEventEnd),listeners:__m.listeners,
 longTasks:t.length,longTaskMs:t.reduce((s,x)=>s+x[1],0),maxTask:t.reduce((m,x)=>Math.max(m,x[1]),0),
 pending:window.NotaCodigo&&NotaCodigo.pendientes?NotaCodigo.pendientes():null,waiting:window.NotaCodigo&&NotaCodigo.esperando?NotaCodigo.esperando():null,
 heap:performance.memory?Math.round(performance.memory.usedJSHeapSize/1024):null}}"""

# Idle = two frames after the code queue is empty (base runtime has no queue: it is synchronous).
IDLE = """()=>new Promise(r=>{const t0=performance.now();const tick=()=>{if(performance.now()-t0>20000)return r(-1);if(window.NotaCodigo&&NotaCodigo.pendientes&&NotaCodigo.pendientes()>0)return setTimeout(tick,4);
requestAnimationFrame(()=>requestAnimationFrame(()=>r(Math.round(performance.now()-t0))));};tick();})"""


def run_once(pw, engine, url, width, throttle):
    browser = getattr(pw, engine).launch()
    try:
        context = browser.new_context(viewport={'width': width, 'height': 900}, reduced_motion='reduce')
        blocked = []

        def route(r):
            if urlsplit(r.request.url).hostname == '127.0.0.1':
                r.continue_()
            else:
                blocked.append(r.request.url)
                r.abort()
        context.route('**/*', route)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.add_init_script(INIT)
        cdp = None
        if engine == 'chromium':
            cdp = context.new_cdp_session(page)
            cdp.send('Performance.enable')
            if throttle:
                cdp.send('Emulation.setCPUThrottlingRate', {'rate': 4})
        page.goto(url, wait_until='load')
        settle = page.evaluate(IDLE)
        result = {'initial': page.evaluate(SNAPSHOT), 'settleAfterLoad': settle}
        if cdp:
            metrics = {m['name']: m['value'] for m in cdp.send('Performance.getMetrics')['metrics']}
            result['cdp'] = {k: round(metrics[k], 1) for k in ('Nodes', 'JSEventListeners', 'JSHeapUsedSize', 'ScriptDuration', 'LayoutDuration', 'RecalcStyleDuration', 'TaskDuration') if k in metrics}
        chapters = page.locator('.barra [data-ir]').evaluate_all('els=>els.map(e=>e.dataset.ir)')
        navs = []
        for target in chapters[1:] + chapters[:1]:
            ms = page.evaluate("""async(id)=>{const t0=performance.now();document.querySelector(`[data-ir="${id}"]`).click();
              await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));const idle=await (%s)();return [Math.round(performance.now()-t0),idle]}""" % IDLE, target)
            navs.append({'page': target, 'ms': ms[0], 'idleMs': ms[1]})
        result['navigation'] = navs
        # Reopen: visit the 1000-line details page and open every closed details element there.
        page.evaluate("()=>{document.querySelector('[data-ir=\"atlas-pruebas\"]').click()}")
        page.evaluate(IDLE)
        result['openDetails'] = page.evaluate("""async()=>{const ds=[...document.querySelectorAll('.pagina.viva details:not([open])')];const t0=performance.now();
          ds.forEach(d=>d.open=true);await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));const idle=await (%s)();
          return {count:ds.length,ms:Math.round(performance.now()-t0),idleMs:idle,lines:document.querySelectorAll('.pagina.viva .codigo-linea').length}}""" % IDLE)
        result['final'] = page.evaluate(SNAPSHOT)
        if cdp:
            metrics = {m['name']: m['value'] for m in cdp.send('Performance.getMetrics')['metrics']}
            result['cdpFinal'] = {k: round(metrics[k], 1) for k in ('Nodes', 'JSEventListeners', 'JSHeapUsedSize') if k in metrics}
        result['blocked'] = sorted(set(blocked))
        result['errors'] = errors
        return result
    finally:
        browser.close()


def summarize(runs):
    def med(path):
        values = []
        for r in runs:
            v = r
            for k in path:
                v = v.get(k) if isinstance(v, dict) else None
            if isinstance(v, (int, float)):
                values.append(v)
        return statistics.median(values) if values else None
    return {'loadMs': med(['initial', 'load']), 'dclMs': med(['initial', 'dcl']), 'settleMs': med(['settleAfterLoad']),
            'nodesInitial': med(['initial', 'nodes']), 'codeLinesInitial': med(['initial', 'codeSpans']),
            'longTasks': med(['initial', 'longTasks']), 'longTaskMs': med(['initial', 'longTaskMs']), 'maxTaskMs': med(['initial', 'maxTask']),
            'listenersInitial': med(['initial', 'listeners']), 'heapKbInitial': med(['initial', 'heap']),
            'cdpScriptMs': med(['cdp', 'ScriptDuration']), 'cdpTaskMs': med(['cdp', 'TaskDuration']),
            'openDetailsMs': med(['openDetails', 'idleMs']), 'nodesFinal': med(['final', 'nodes'])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', type=Path, required=True)
    ap.add_argument('--candidate', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--runs', type=int, default=3)
    args = ap.parse_args()
    report = {'note': 'Lab automation on one machine; medians of cold loads. Not field data and not FPS.', 'files': {}, 'results': []}
    servers = {}
    for name, path in (('base', args.base), ('candidate', args.candidate)):
        data = path.read_bytes()
        report['files'][name] = {'bytes': len(data), 'gzip': len(gzip.compress(data, 9))}
        server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(path.parent)))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers[name] = f'http://127.0.0.1:{server.server_port}/{quote(path.name)}'
    configs = [('chromium', w, False) for w in (1440, 390, 320)] + [('chromium', 1440, True), ('chromium', 390, True), ('webkit', 1440, False), ('webkit', 390, False), ('webkit', 320, False)]
    with sync_playwright() as pw:
        for engine, width, throttle in configs:
            for name in ('base', 'candidate'):
                runs = [run_once(pw, engine, servers[name], width, throttle) for _ in range(args.runs)]
                report['results'].append({'engine': engine, 'width': width, 'cpuThrottle': 4 if throttle else 1, 'build': name,
                                          'summary': summarize(runs), 'runs': runs})
                print(engine, width, throttle, name, json.dumps(report['results'][-1]['summary']), flush=True)
    args.output.write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
