#!/usr/bin/env python3
"""Exercise an actual atlas in Chromium, including offline deep links and copy.

Run with the Playwright Python environment. Does not publish or contact providers.
The JSON records performance observations; it does not infer field performance.
"""
from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from urllib.parse import quote, urlsplit

from playwright.sync_api import sync_playwright


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def check(html: Path, coverage: Path, output: Path, full: bool) -> dict:
    expected = json.loads(coverage.read_text())
    ids = [r['id'] for r in expected['components']]
    assert len(set(ids)) == expected['registry_count'] == len(ids)
    output.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(html.parent)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}/{quote(html.name)}'
    report = {'source': str(html), 'registry_count': len(ids), 'checks': [], 'errors': [], 'network_blocked': []}

    def record(name, passed, details=None):
        report['checks'].append({'name': name, 'passed': bool(passed), 'details': details})

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            context = browser.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce', permissions=['clipboard-read', 'clipboard-write'])

            def route(request):
                if urlsplit(request.request.url).hostname == '127.0.0.1':
                    request.continue_()
                else:
                    report['network_blocked'].append(request.request.url)
                    request.abort()

            context.route('**/*', route)
            page = context.new_page()
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            page.add_init_script("""window.atlasTasks=[];
                new PerformanceObserver(l=>atlasTasks.push(...l.getEntries().map(e=>({start:e.startTime,duration:e.duration})))).observe({type:'longtask',buffered:true});""")
            page.goto(url, wait_until='load')
            page.evaluate('document.fonts.ready')
            page.wait_for_timeout(100)
            report['initial'] = page.evaluate("""()=>({nodes:document.querySelectorAll('*').length,longTasks:atlasTasks,
                navigation:performance.getEntriesByType('navigation')[0].toJSON(),
                livePages:document.querySelectorAll('.pagina:not([hidden])').length})""")
            record('one visible chapter', report['initial']['livePages'] == 1)
            # Exercise the public hash route, not a private helper that bypasses navigation.
            for component in expected['components']:
                page.evaluate('(id)=>{location.hash=id}', component['anchor'])
                page.wait_for_function('(id)=>document.getElementById(id)?.closest(".pagina")?.hidden===false', arg=component['anchor'])
                visible = page.locator('#' + component['anchor']).is_visible()
                actual = page.locator('.pagina.viva').get_attribute('id')
                record('deep link ' + component['id'], visible and actual == component['page'], actual)

            configurations = [(1440, 'editorial', 'dark'), (390, 'catabum', 'light'), (320, 'kaira', 'dark')]
            if full:
                configurations = [(w, t, m) for w in (1440, 1328, 1280, 390, 320) for t in ('editorial', 'catabum', 'kaira') for m in ('light', 'dark')]
            chapters = page.locator('.barra [data-ir]').evaluate_all('(els)=>els.map(e=>e.dataset.ir)')
            for width, family, mode in configurations:
                page.set_viewport_size({'width': width, 'height': 900})
                for attr, value in [('data-elegir-tema', family), ('data-elegir-modo', mode)]:
                    page.locator(f'[{attr}][value="{value}"]').first.evaluate("e=>{e.checked=true;e.dispatchEvent(new Event('change',{bubbles:true}))}")
                for chapter in chapters:
                    page.evaluate('(id)=>{location.hash=id}', chapter)
                    page.wait_for_function('(id)=>document.querySelector(".pagina.viva")?.id===id', arg=chapter)
                    page.wait_for_timeout(40)
                    metrics = page.evaluate("""()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,
                        family:document.documentElement.dataset.themeFamily,mode:document.documentElement.dataset.colorMode,
                        h1:document.querySelector('.pagina.viva h1')?.getBoundingClientRect().toJSON()})""")
                    record(f'layout {chapter} {width}/{family}/{mode}', metrics['scroll'] <= width + 1 and metrics['family'] == family and metrics['mode'] == mode, metrics)

            page.set_viewport_size({'width': 1440, 'height': 900})
            page.evaluate("location.hash='prueba-mil-lineas'")
            page.wait_for_function("document.querySelector('#prueba-mil-lineas')?.closest('.pagina')?.hidden===false")
            summary = page.locator('#prueba-mil-lineas > summary')
            if page.locator('#prueba-mil-lineas').get_attribute('open') is not None:
                summary.click()
            summary.focus()
            page.keyboard.press('Enter')
            page.wait_for_function("document.querySelector('#prueba-mil-lineas').open")
            code = page.locator('#prueba-mil-lineas code')
            page.wait_for_function("document.querySelectorAll('#prueba-mil-lineas .codigo-linea').length===1000")
            source = '\n'.join(f'const registro{n:04d} = {{ numero: {n}, estado: "ejemplo" }};' for n in range(1, 1001))
            record('code source remains exact', code.text_content() == source)
            numbers = code.locator('.codigo-linea').evaluate_all('(els)=>els.map(e=>e.dataset.numero)')
            record('1000 sequential line numbers', numbers == [str(n) for n in range(1, 1001)])
            page.locator('#prueba-mil-lineas .cab button').first.click()
            copied = page.evaluate('navigator.clipboard.readText()')
            record('clipboard excludes line numbers', copied == source)
            code.evaluate('e=>{const p=e.closest("pre");p.scrollTop=p.scrollHeight;}')
            page.screenshot(path=str(output / 'thousand-lines.png'))

            # New document navigation must resolve an anchor on a never-opened page.
            last = expected['components'][-1]
            page.goto(url + '#' + last['anchor'], wait_until='load')
            page.wait_for_function('(id)=>document.getElementById(id)?.closest(".pagina")?.hidden===false', arg=last['anchor'])
            record('cold deep link', page.locator('#' + last['anchor']).is_visible())
            record('no JavaScript exceptions', not report['errors'], report['errors'])
            context.close()

            plain = browser.new_context(java_script_enabled=False, viewport={'width': 390, 'height': 844})
            plain.route('**/*', route)
            nojs = plain.new_page()
            nojs.goto(url, wait_until='load')
            visible = nojs.locator('.pagina').evaluate_all('(els)=>els.filter(e=>getComputedStyle(e).display!=="none").length')
            record('all chapters readable without JavaScript', visible == len(chapters), {'visible': visible, 'expected': len(chapters)})
            record('all component headings available without JavaScript', nojs.locator('[data-atlas-componente]').count() == len(ids))
            plain.close()
            browser.close()
    except Exception as error:
        record('probe completed', False, str(error))
    finally:
        server.shutdown()
        server.server_close()
    report['passed'] = all(item['passed'] for item in report['checks'])
    (output / 'atlas-check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', type=Path, required=True)
    parser.add_argument('--coverage', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--full', action='store_true', help='Run all five widths, three families and both modes.')
    args = parser.parse_args()
    result = check(args.html.resolve(), args.coverage.resolve(), args.output.resolve(), args.full)
    print(json.dumps({'passed': result['passed'], 'checks': len(result['checks']), 'failed': [r for r in result['checks'] if not r['passed']], 'report': str(args.output / 'atlas-check.json')}, ensure_ascii=False))
    raise SystemExit(0 if result['passed'] else 1)
