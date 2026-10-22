#!/usr/bin/env python3
"""Prueba de navegador de las gráficas del atlas (sin red).

Uso: check_charts_atlas.py <atlas.html> <salida.json>
Python con Playwright: /Users/angelbotto/orca/workspaces/margen/margen-lector-voz/.venv/bin/python

Comprueba, a 320/390/1440 px y en Editorial, Catabum y Kaira claro/oscuro: sin desbordamiento de página,
desplazamiento solo en calendario/cohortes/gantt, texto SVG legible y sin solapes ni recortes, paleta de 8
distinta con contraste ≥ 3:1, teclado/táctil/tip en el viewport, redibujo idempotente (resize, tema, página),
tablas fuente intactas tras destroy, exportes CSV/SVG exactos y treemap con 26 categorías y cola extrema.
"""
import csv, io, json, pathlib, sys, xml.dom.minidom
from playwright.sync_api import sync_playwright

SEL = '[data-grafica],[data-analitica],[data-reporte="cascada"],[data-reporte="multiples"],[data-evidencia]:not([data-evidencia="imagen"]),[data-atencion]'
SCROLL_OK = {'analitica:calendario', 'evidencia:cohortes', 'evidencia:gantt'}
THEMES = ['light', 'dark', 'catabum-light', 'catabum-dark', 'kaira-light', 'kaira-dark']
PAGES = ['atlas-graficas', 'atlas-reportes']
KIND = "e => ['grafica','analitica','reporte','evidencia','atencion'].filter(k => k in e.dataset).map(k => k + ':' + e.dataset[k])[0]"

GEOMETRY = r"""(sel) => {
  const out = [];
  for (const fig of document.querySelectorAll(sel)) {
    if (!fig.getClientRects().length) continue;
    const kind = ['grafica','analitica','reporte','evidencia','atencion'].filter(k => k in fig.dataset).map(k => k + ':' + fig.dataset[k])[0];
    const svgs = [...fig.querySelectorAll('svg.mg-svg')];
    const boxes = [...fig.querySelectorAll('.grafica-caja,.evidencia-visor,.analitica-caja,.atencion-caja')];
    const scroll = boxes.some(b => b.scrollWidth > b.clientWidth + 1);
    const labelled = boxes.filter(b => b.scrollWidth > b.clientWidth + 1).every(b => b.getAttribute('role') === 'region' && b.tabIndex === 0 && b.getAttribute('aria-label'));
    const problems = [];
    let fmin = 99, fmax = 0;
    for (const svg of svgs) {
      const sr = svg.getBoundingClientRect(), vb = svg.viewBox.baseVal, k = vb && vb.width ? sr.width / vb.width : 1;
      if (Math.abs(k - 1) > .02 && !svg.classList.contains('mg-desplazable')) problems.push('svg escalado ' + k.toFixed(3));
      const texts = [...svg.querySelectorAll('text')].filter(t => t.textContent.trim() && !t.closest('defs'));
      const rects = texts.map(t => ({t: t.textContent.trim().slice(0, 24), r: t.getBoundingClientRect(), fs: parseFloat(getComputedStyle(t).fontSize) * k}));
      for (const {t, r, fs} of rects) {
        fmin = Math.min(fmin, fs); fmax = Math.max(fmax, fs);
        if (r.left < sr.left - 1 || r.right > sr.right + 1 || r.top < sr.top - 2 || r.bottom > sr.bottom + 2) problems.push('fuera: ' + t);
      }
      for (let i = 0; i < rects.length; i++) for (let j = i + 1; j < rects.length; j++) {
        const a = rects[i].r, b = rects[j].r, ox = Math.min(a.right, b.right) - Math.max(a.left, b.left), oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
        if (ox > 1.5 && oy > 1.5) problems.push('solape: ' + rects[i].t + ' / ' + rects[j].t);
      }
      // Treemap: cada rótulo dentro de su celda.
      svg.querySelectorAll('g[data-categoria]').forEach(g => {
        const cell = g.querySelector('rect').getBoundingClientRect();
        g.querySelectorAll('text').forEach(t => { const r = t.getBoundingClientRect(); if (r.left < cell.left - .5 || r.right > cell.right + .5 || r.top < cell.top - .5 || r.bottom > cell.bottom + .5) problems.push('rótulo fuera de celda: ' + t.textContent); });
      });
    }
    out.push({kind, svgs: svgs.length, scroll, labelled, fmin, fmax, problems: problems.slice(0, 6), problemCount: problems.length,
      marks: fig.querySelectorAll('[data-mg-i]').length, error: fig.querySelector('.grafica-error,.evidencia-error')?.textContent || null});
  }
  return {charts: out, pageOverflow: document.documentElement.scrollWidth > innerWidth + 1};
}"""

PALETTE = r"""() => {
  // El color computado puede venir en oklch(); se convierte a sRGB pintándolo en un canvas.
  const probe = document.createElement('span'); document.body.append(probe);
  const ctx = document.createElement('canvas').getContext('2d', {willReadFrequently: true});
  const rgb = v => { probe.style.color = ''; probe.style.color = v; ctx.clearRect(0, 0, 1, 1); ctx.fillStyle = '#000'; ctx.fillStyle = getComputedStyle(probe).color; ctx.fillRect(0, 0, 1, 1); return [...ctx.getImageData(0, 0, 1, 1).data].slice(0, 3); };
  const lum = c => { const [r, g, b] = c.map(v => { v /= 255; return v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }); return .2126 * r + .7152 * g + .0722 * b; };
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); };
  const paper = rgb('var(--grafica-papel)');
  const slots = Array.from({length: 8}, (_, i) => rgb(`var(--grafica-${i + 1})`));
  const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
  // Distancia mínima de cada slot derivado (5–8) a cualquier otro; la de 1–4 entre sí es del tema y se informa aparte.
  let minNew = 999, minBase = 999;
  for (let i = 0; i < 8; i++) for (let j = i + 1; j < 8; j++) { const d = dist(slots[i], slots[j]); if (j >= 4) minNew = Math.min(minNew, d); else minBase = Math.min(minBase, d); }
  probe.remove();
  return {contrast: slots.map(c => +ratio(c, paper).toFixed(2)), minDistance: +minNew.toFixed(1), baseMinDistance: +minBase.toFixed(1), slots: slots.map(c => 'rgb(' + c.join(',') + ')')};
}"""

TREEMAP = r"""(spec) => {
  const fig = document.createElement('figure'); fig.className = 'ancho'; fig.setAttribute('data-atencion', ''); fig.dataset.unidad = 'minutos'; fig.dataset.formato = spec.formato || '';
  const rows = spec.values.map((v, i) => `<tr><th scope="row">${spec.names[i]}</th><td data-valor="${v}">${v}</td></tr>`).join('');
  fig.innerHTML = `<div class="tabla-caja"><table><caption>${spec.title}</caption><thead><tr><th>Aplicación</th><th>Minutos</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  const host = document.querySelector('article.pagina:not([hidden])') || document.body; host.append(fig);
  const map = NotaAtencion.init(fig)[0];
  const svg = fig.querySelector('svg.mg-svg'), W = +svg.getAttribute('width'), H = +svg.getAttribute('height');
  const tiles = [...svg.querySelectorAll('g[data-categoria]')].map(g => { const r = g.querySelector('rect'); return {i: +g.dataset.categoria, v: +r.dataset.valor, a: r.width.baseVal.value * r.height.baseVal.value, w: r.width.baseVal.value, h: r.height.baseVal.value}; });
  const total = spec.values.reduce((a, b) => a + b, 0), area = tiles.reduce((a, t) => a + t.a, 0);
  const proportional = tiles.every(t => Math.abs(t.a / (W * H) - t.v / total) < 1e-6);
  const painted = tiles.reduce((a, t) => a + t.v, 0);
  const others = tiles.find(t => t.i === -1);
  const membersInTip = others ? map.describe(map.tiles.find(t => t.members)).length - 2 : 0;
  const buttons = fig.querySelectorAll('.atencion-leyenda button').length;
  const minSide = Math.min(...tiles.filter(t => t.i !== -1).map(t => Math.min(t.w, t.h)));
  // Ninguna categoría con al menos 1 % del total puede quedar escondida dentro de «Otros».
  const hidden = spec.values.map((v, i) => [v, i]).filter(([v, i]) => v / total >= .01 && !tiles.some(t => t.i === i)).length;
  const result = {W, H, tiles: tiles.length, areaError: Math.abs(area - W * H), proportional, paintedTotal: painted, total, others: !!others, membersInTip, buttons, minSide: +minSide.toFixed(1), hidden, zeroPainted: tiles.some(t => t.v === 0)};
  map.destroy(); fig.remove();
  return result;
}"""


def run(src, out):
    report = {'geometry': [], 'palette': {}, 'interaction': [], 'idempotence': [], 'tables': [], 'exports': [], 'treemap': [], 'errors': []}
    failures = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        def open_page(width, theme='light', touch=False, offline=True):
            ctx = browser.new_context(viewport={'width': width, 'height': 860}, has_touch=touch, is_mobile=touch, accept_downloads=True,
                                      color_scheme='dark' if 'dark' in theme else 'light')
            page = ctx.new_page()
            if offline:
                page.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
            page.on('pageerror', lambda e: report['errors'].append(f'{width} {theme}: {e}'))
            page.goto(src.as_uri()); page.wait_for_timeout(300)
            page.evaluate("t => { document.documentElement.setAttribute('data-theme', t); document.dispatchEvent(new CustomEvent('nota:tema')); }", theme)
            return ctx, page

        def go(page, target):
            page.evaluate("id => document.querySelector(`[data-ir='${id}']`)?.click()", target)
            page.wait_for_timeout(350)

        # 1. Geometría por ancho y tema.
        for width in [320, 390, 1440]:
            for theme in THEMES:
                ctx, page = open_page(width, theme)
                if theme == THEMES[0] or width == 390:
                    report['palette'][theme] = page.evaluate(PALETTE)
                for target in PAGES:
                    go(page, target)
                    g = page.evaluate(GEOMETRY, SEL)
                    for c in g['charts']:
                        bad = []
                        if c['scroll'] and c['kind'] not in SCROLL_OK: bad.append('scroll no declarado')
                        if c['scroll'] and not c['labelled']: bad.append('scroll sin región etiquetada')
                        if c['problemCount']: bad.append(c['problems'])
                        if c['error']: bad.append(c['error'])
                        if c['svgs'] and (c['fmin'] < 11 or c['fmax'] > 18.5): bad.append(f"texto {c['fmin']:.1f}–{c['fmax']:.1f}px")
                        if not c['marks']: bad.append('sin marcas navegables')
                        report['geometry'].append({'width': width, 'theme': theme, **c})
                        if bad: failures.append(f'{width} {theme} {c["kind"]}: {bad}')
                    if g['pageOverflow']: failures.append(f'{width} {theme} {target}: desbordamiento horizontal de página')
                ctx.close()
        for theme, p in report['palette'].items():
            low = [i + 1 for i, c in enumerate(p['contrast']) if c < 3]
            if low: failures.append(f'paleta {theme}: slots con contraste < 3:1 → {low} {p["contrast"]}')
            if p['minDistance'] < 20: failures.append(f'paleta {theme}: un slot derivado casi igual a otro (distancia RGB {p["minDistance"]})')

        # 2. Teclado, tip, táctil y cambio de página.
        for width, touch in [(1440, False), (390, True)]:
            ctx, page = open_page(width, 'light', touch)
            for target in PAGES:
                go(page, target)
                figs = page.locator(SEL)
                for i in range(figs.count()):
                    f = figs.nth(i)
                    if not f.is_visible(): continue
                    kind = f.evaluate(KIND)
                    first = f.locator('[data-mg-i="0"]').first
                    if not first.count(): continue
                    first.scroll_into_view_if_needed(); first.focus()
                    total = first.evaluate("m => m.closest('svg').querySelectorAll('[data-mg-i]').length")
                    page.keyboard.press('ArrowRight')
                    state = page.evaluate("""() => { const t = document.querySelector('.mg-tip'), r = t.getBoundingClientRect();
                      return {focus: document.activeElement?.dataset?.mgI, tip: !t.hidden && t.textContent.length > 0, inside: r.left >= 0 && r.top >= 0 && r.right <= innerWidth && r.bottom <= innerHeight,
                              described: document.activeElement?.getAttribute('aria-describedby') === t.id}; }""")
                    page.keyboard.press('End')
                    end = page.evaluate("() => document.activeElement?.dataset?.mgI")
                    page.keyboard.press('Enter')
                    pinned = f.evaluate("e => [...e.querySelectorAll('[role=status]')].some(s => s.textContent.trim().length > 0)")
                    page.keyboard.press('Escape')
                    hidden = page.evaluate("() => document.querySelector('.mg-tip').hidden")
                    tap = None
                    if touch:
                        mark = f.locator('[data-mg-i="0"]').first
                        mark.evaluate("m => m.scrollIntoView({block: 'center'})")
                        box = mark.evaluate("""m => { const s = m.matches('path,rect,circle,line') ? m : m.querySelector('path,rect,circle,line'); if (!s) return null;
                          let p; if (s.getTotalLength && s.tagName !== 'rect' && s.tagName !== 'circle') p = s.getPointAtLength(s.getTotalLength() / 2); else { const b = s.getBBox(); p = {x: b.x + b.width / 2, y: b.y + b.height / 2}; }
                          const q = new DOMPoint(p.x, p.y).matrixTransform(s.getScreenCTM()); return {x: q.x, y: q.y}; }""")
                        if box:
                            page.touchscreen.tap(box['x'], box['y'])
                            page.wait_for_timeout(60)
                            tap = page.evaluate("() => { const t = document.querySelector('.mg-tip'), r = t.getBoundingClientRect(); return !t.hidden && r.left >= 0 && r.right <= innerWidth && r.top >= 0 && r.bottom <= innerHeight; }")
                    rec = {'width': width, 'kind': kind, **state, 'end': end, 'expectedEnd': str(total - 1), 'pinned': pinned, 'escHides': hidden, 'tap': tap}
                    report['interaction'].append(rec)
                    if not (state['focus'] == '1' or total == 1) or not state['tip'] or not state['inside'] or not state['described'] or end != str(total - 1) or not pinned or not hidden or tap is False:
                        failures.append(f'interacción {width} {kind}: {rec}')
                # El tip se oculta al cambiar de página.
                page.evaluate("() => [...document.querySelectorAll('[data-mg-i=\"0\"]')].find(m => m.getClientRects().length)?.focus()")
            go(page, 'atlas-inicio')
            if not page.evaluate("() => document.querySelector('.mg-tip')?.hidden !== false"):
                failures.append(f'{width}: el tip sigue visible tras cambiar de página')
            ctx.close()

        # 3. Idempotencia: resize, tema y páginas sin duplicar ni redibujar de más; listeners estables.
        # Sin interceptar red: Playwright no entrega descargas blob: con rutas activas.
        ctx, page = open_page(1440, offline=False)
        go(page, 'atlas-graficas')
        cdp = ctx.new_cdp_session(page)
        def listeners():
            doc = cdp.send('Runtime.evaluate', {'expression': 'document'})['result']['objectId']
            win = cdp.send('Runtime.evaluate', {'expression': 'window'})['result']['objectId']
            return len(cdp.send('DOMDebugger.getEventListeners', {'objectId': doc})['listeners']) + len(cdp.send('DOMDebugger.getEventListeners', {'objectId': win})['listeners'])
        # Calentamiento: las figuras de páginas ocultas se dibujan (y registran sus marcas) al primer acceso.
        go(page, 'atlas-reportes'); go(page, 'atlas-graficas')
        before = listeners()
        page.evaluate("() => document.querySelectorAll('svg.mg-svg').forEach(s => s.dataset.marca = '1')")
        page.evaluate("() => { document.documentElement.setAttribute('data-theme', 'catabum-dark'); document.dispatchEvent(new CustomEvent('nota:tema')); }")
        page.wait_for_timeout(200)
        same_after_theme = page.evaluate("() => [...document.querySelectorAll('article:not([hidden]) svg.mg-svg')].every(s => s.dataset.marca === '1')")
        for w in [390, 1024, 320, 1440]:
            page.set_viewport_size({'width': w, 'height': 860}); page.wait_for_timeout(250)
        for _ in range(5):
            go(page, 'atlas-reportes'); go(page, 'atlas-graficas')
        after = listeners()
        dup = page.evaluate(f"""() => [...document.querySelectorAll('{SEL}')].filter(f => f.getClientRects().length && !f.matches('[data-reporte=multiples]')).map(f => [f.querySelectorAll('svg.mg-svg').length, f.querySelectorAll('.mg-exportar').length]).filter(([s, e]) => s > 1 || e > 1).length""")
        widths_ok = page.evaluate("""() => [...document.querySelectorAll('article:not([hidden]) svg.mg-svg:not(.mg-desplazable)')].every(s => Math.abs(s.getBoundingClientRect().width - +s.getAttribute('width')) <= 1)""")
        report['idempotence'] = {'sameSvgAfterTheme': same_after_theme, 'listenersBefore': before, 'listenersAfter': after, 'duplicates': dup, 'widthsMatch': widths_ok}
        if not same_after_theme: failures.append('el cambio de tema sin cambio de fuente redibujó gráficas')
        if after > before: failures.append(f'listeners crecieron con resize/páginas: {before} → {after}')
        if dup: failures.append(f'{dup} figuras con SVG o exportación duplicados')
        if not widths_ok: failures.append('algún SVG no coincide con el ancho de su caja tras resize')

        # 4. Tablas intactas tras destroy (contra el HTML original) y reinicio.
        original = src.read_text()
        result = page.evaluate("""(html) => {
          const doc = new DOMParser().parseFromString(html, 'text/html'), sel = '""" + SEL + """';
          const source = [...doc.querySelectorAll(sel)], live = [...document.querySelectorAll(sel)], out = [];
          live.forEach((f, i) => {
            const api = f.matches('[data-grafica]') ? NotaGraficas : f.matches('[data-analitica]') ? NotaAnalitica : f.matches('[data-reporte]') ? NotaReportes : f.matches('[data-evidencia]') ? NotaEvidencia : NotaAtencion;
            api.get(f)?.destroy();
            const a = f.querySelector('table')?.outerHTML, b = source[i]?.querySelector('table')?.outerHTML;
            out.push({id: f.id, same: a === b, leftovers: f.querySelectorAll('.mg-svg,.mg-exportar,.mg-leyenda').length});
            api.init(f);
          });
          return out;
        }""", original)
        report['tables'] = result
        for r in result:
            if not r['same'] or r['leftovers']: failures.append(f"tabla/restos tras destroy: {r}")

        # 5. Exportes exactos: el contenido se genera con las mismas funciones que usan los botones;
        #    además se comprueba una descarga real por tipo de botón.
        go(page, 'atlas-graficas')
        bar = page.locator('[data-grafica="barras"] .mg-exportar button')
        for k, ext in [(0, '.csv'), (1, '.svg')]:
            try:
                with page.expect_download(timeout=8000) as d: bar.nth(k).evaluate('b => b.click()')
                if not d.value.suggested_filename.endswith(ext): failures.append('descarga con extensión inesperada: ' + d.value.suggested_filename)
            except Exception as e:  # noqa: BLE001
                failures.append(f'descarga real {ext} falló: {str(e)[:80]}')
        for target in PAGES:
            go(page, target)
            items = page.evaluate("""(sel) => [...document.querySelectorAll(sel)].filter(f => f.getClientRects().length).map(f => {
              const kind = ['grafica','analitica','reporte','evidencia','atencion'].filter(k => k in f.dataset).map(k => k + ':' + f.dataset[k])[0];
              const table = f.querySelector('table'), svgs = [...f.querySelectorAll('svg.mg-svg')], title = table?.caption?.textContent || kind;
              const expected = [...table.querySelectorAll(':scope > thead > tr, :scope > tbody > tr, :scope > tfoot > tr')].map(r => [...r.cells].map(c => c.hasAttribute('data-valor') ? c.getAttribute('data-valor').trim() : ((c.querySelector('time[datetime]')?.getAttribute('datetime')) || c.textContent).trim().replace(/\\s+/g, ' ')));
              return {kind, buttons: f.querySelectorAll('.mg-exportar button').length, csv: MargenGraficas.tableCsv(table), expected, svg: svgs.length ? MargenGraficas.standaloneSvg(svgs.length > 1 ? svgs : svgs[0], {title, source: 'prueba', unit: f.dataset.unidad || ''}) : ''};
            })""", SEL)
            for it in items:
                kind = it['kind']
                if it['buttons'] < 2: failures.append(f'{kind}: faltan botones de exportar'); continue
                rows = list(csv.reader(io.StringIO(it['csv'])))
                csv_ok = rows == [[("'" + v) if v[:1] and v[:1] in '=+-@' and not _num(v) else v for v in r] for r in it['expected']]
                svg_text = it['svg']
                try:
                    dom = xml.dom.minidom.parseString(svg_text.encode()); root = dom.documentElement
                    svg_ok = root.tagName == 'svg' and bool(root.getElementsByTagName('title')) and bool(root.getElementsByTagName('desc')) and 'var(' not in svg_text and 'currentColor' not in svg_text and 'http' not in svg_text.replace('http://www.w3.org', '')
                except Exception:  # noqa: BLE001
                    svg_ok = False
                report['exports'].append({'kind': kind, 'csv': csv_ok, 'svg': bool(svg_ok), 'csvRows': len(rows)})
                if not csv_ok or not svg_ok: failures.append(f'export {kind}: csv={csv_ok} svg={bool(svg_ok)} {rows[:2]} {it["expected"][:2]}')
        ctx.close()

        # 6. Treemap: 26 categorías, distribución extrema y ceros, a varios anchos.
        names = ['Arc', 'ChatGPT', 'Slack', 'Tuple', 'Spotify', 'Figma', 'Linear', 'Notion', 'Mail', 'Calendar', 'Terminal', 'Xcode', 'Safari', 'Messages', 'Zoom',
                 'Photos', 'Music', 'Notes', 'Finder', 'Preview', 'Orca', 'GitHub Desktop', 'Raycast', 'Obsidian', 'WhatsApp', 'Telegram']
        cases = {
            '26 categorías': [5541, 4956, 605, 164, 83, 61, 55, 40, 33, 29, 22, 19, 15, 14, 12, 11, 9, 8, 7, 6, 5, 4, 3, 2, 2, 1],
            'extrema con ceros': [1000000, 0, 120000, 0, 3, 2, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            'uniforme': [10] * 26,
        }
        for width in [320, 390, 1440]:
            ctx, page = open_page(width, 'dark')
            go(page, 'atlas-graficas')
            for title, values in cases.items():
                r = page.evaluate(TREEMAP, {'title': title, 'names': names, 'values': values, 'formato': 'duration_min'})
                r.update({'width': width, 'case': title})
                report['treemap'].append(r)
                ok = r['areaError'] < 1 and r['proportional'] and r['paintedTotal'] == r['total'] and r['buttons'] == 26 and not r['zeroPainted'] and r['minSide'] >= 9.9 and not r['hidden'] and (not r['others'] or r['membersInTip'] >= 2)
                if not ok: failures.append(f'treemap {width} {title}: {r}')
            # Mapa de calor 31 × 31 sin umbrales (cuantiles), con huecos: sin desplazamiento ni solapes.
            heat = page.evaluate("""(sel) => {
              const f = document.createElement('figure'); f.className = 'ancho'; f.dataset.grafica = 'calor'; f.dataset.unidad = 'eventos';
              const head = '<tr><th>Día</th>' + Array.from({length: 31}, (_, i) => `<th>H${i + 1}</th>`).join('') + '</tr>';
              const body = Array.from({length: 31}, (_, r) => `<tr><th>Fila ${r + 1}</th>` + Array.from({length: 31}, (_, c) => (r * c) % 17 === 5 ? '<td data-valor="">Sin dato</td>' : `<td data-valor="${(r * 7 + c * 3) % 50}">x</td>`).join('') + '</tr>').join('');
              f.innerHTML = `<details><summary>Datos</summary><div class="tabla-caja"><table><caption>Calor 31 × 31</caption><thead>${head}</thead><tbody>${body}</tbody></table></div></details>`;
              (document.querySelector('article.pagina:not([hidden])') || document.body).append(f);
              NotaGraficas.init(f);
              const svg = f.querySelector('svg.mg-svg'), box = f.querySelector('.grafica-caja'), texts = [...svg.querySelectorAll('text')].map(t => t.getBoundingClientRect()), sr = svg.getBoundingClientRect();
              let overlaps = 0; for (let i = 0; i < texts.length; i++) for (let j = i + 1; j < texts.length; j++) { const a = texts[i], b = texts[j]; if (Math.min(a.right, b.right) - Math.max(a.left, b.left) > 1.5 && Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 1.5) overlaps++; }
              const outside = texts.filter(r => r.left < sr.left - 1 || r.right > sr.right + 1).length;
              const r = {cells: svg.querySelectorAll('[data-mg-i]').length, scroll: box.scrollWidth > box.clientWidth + 1, overlaps, outside, legend: f.querySelector('.calor-leyenda').getAttribute('aria-label')};
              NotaGraficas.get(f).destroy(); f.remove(); return r;
            }""", SEL)
            heat.update({'width': width}); report['heatmap'] = report.get('heatmap', []) + [heat]
            if heat['cells'] != 961 or heat['scroll'] or heat['overlaps'] or heat['outside'] or 'cuantiles' not in heat['legend']: failures.append(f'calor 31×31 {width}: {heat}')
            ctx.close()
        browser.close()
    report['errors'] and failures.extend(report['errors'])
    report['failures'] = failures
    pathlib.Path(out).write_text(json.dumps(report, indent=1, ensure_ascii=False))
    print(json.dumps({'geometry': len(report['geometry']), 'interaction': len(report['interaction']), 'exports': len(report['exports']),
                      'tables': len(report['tables']), 'treemap': len(report['treemap']), 'idempotence': report['idempotence'], 'failures': len(failures)}, ensure_ascii=False))
    for f in failures[:40]: print('FALLA', str(f)[:400])
    return 1 if failures else 0


def _num(v):
    try:
        float(v); return v.strip() != ''
    except ValueError:
        return False


if __name__ == '__main__':
    sys.exit(run(pathlib.Path(sys.argv[1]).resolve(), sys.argv[2]))
