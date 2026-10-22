#!/usr/bin/env python3
"""Chart exports with physical clicks, standalone SVG rendering, and edge-case data.
Usage: probe_charts.py atlas.html chromium|webkit outdir"""
import json, re, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from probe_common import serve

EDGE = r"""(spec) => {
  const host = document.querySelector('article.pagina:not([hidden])');
  const f = document.createElement('figure'); f.className = 'ancho'; f.dataset.grafica = spec.type; Object.assign(f.dataset, spec.data || {});
  const head = '<tr>' + spec.heads.map(h => `<th scope="col">${h}</th>`).join('') + '</tr>';
  const body = spec.rows.map(r => `<tr><th scope="row">${r[0]}</th>` + r.slice(1).map(v => `<td data-valor="${v ?? ''}">${v ?? 'Sin dato'}</td>`).join('') + '</tr>').join('');
  f.innerHTML = `<details><summary>Datos</summary><div class="tabla-caja" tabindex="0" role="region" aria-label="t"><table><caption>${spec.title}</caption><thead>${head}</thead><tbody>${body}</tbody></table></div></details>`;
  host.append(f); NotaGraficas.init(f);
  const svg = f.querySelector('svg.mg-svg');
  const out = {title: spec.title, error: f.querySelector('.grafica-error')?.textContent || null};
  if (svg) {
    const sr = svg.getBoundingClientRect();
    out.width = Math.round(sr.width); out.figure = Math.round(f.getBoundingClientRect().width);
    out.yTicks = [...svg.querySelectorAll('[data-tick-y]')].map(l => +l.dataset.tickY);
    out.xTicks = [...svg.querySelectorAll('[data-tick-x]')].map(l => +l.dataset.tickX);
    out.cells = [...svg.querySelectorAll('.mg-calor-celda')].slice(0, 3).map(r => r.style.fill);
    out.legend = [...f.querySelectorAll('.calor-leyenda li')].map(l => l.textContent);
    out.bars = [...svg.querySelectorAll('rect.grafica-barra')].map(r => ({v: r.dataset.value, w: +(+r.getAttribute('width')).toFixed(1), h: +(+r.getAttribute('height')).toFixed(1)})).slice(0, 6);
    out.labels = [...svg.querySelectorAll('text[data-label-index]')].map(t => t.textContent);
    out.marks = svg.querySelectorAll('[data-mg-i]').length;
    out.describe0 = svg.querySelector('[data-mg-i]')?.getAttribute('aria-label');
    out.outside = [...svg.querySelectorAll('rect,text')].filter(n => { const r = n.getBoundingClientRect(); return r.width && (r.right > sr.right + 1 || r.left < sr.left - 1); }).length;
  }
  if (!spec.keep) { NotaGraficas.get(f)?.destroy(); f.remove(); }
  return out;
}"""

CASES = [
  {'title': 'Calor todo cero', 'type': 'calor', 'heads': ['Día', 'A', 'B', 'C'], 'rows': [['L', 0, 0, 0], ['M', 0, 0, 0]], 'data': {'unidad': 'eventos'}},
  {'title': 'Calor constante 5', 'type': 'calor', 'heads': ['Día', 'A', 'B'], 'rows': [['L', 5, 5], ['M', 5, 5]], 'data': {'unidad': 'eventos'}},
  {'title': 'Líneas todo cero', 'type': 'lineas', 'heads': ['Mes', 'Altas'], 'rows': [['Ene', 0], ['Feb', 0], ['Mar', 0]], 'data': {'unidad': 'altas'}},
  {'title': 'Barras negativas', 'type': 'barras', 'heads': ['Unidad', 'Margen'], 'rows': [['Norte', -120], ['Sur', 80], ['Este', None], ['Oeste', 0]], 'data': {'unidad': 'millones'}},
  {'title': 'Meta con valor negativo', 'type': 'meta', 'heads': ['KPI', 'Valor', 'Meta'], 'rows': [['NPS', -12, 40], ['CSAT', 30, 40]], 'data': {'unidad': 'puntos'}},
  {'title': 'Columnas agrupadas con negativos', 'type': 'columnas', 'heads': ['T', 'A', 'B'], 'rows': [['T1', -5, 10], ['T2', 3, None], ['T3', 0, -2]], 'data': {'unidad': 'u'}},
  {'title': 'Columnas 26 categorías', 'type': 'columnas', 'heads': ['Letra', 'Valor'], 'rows': [[chr(65 + i) + ' categoría larga', (i * 37) % 50] for i in range(26)], 'data': {'unidad': 'u'}},
  {'title': 'Barras 26 categorías', 'type': 'barras', 'heads': ['Letra', 'Valor'], 'rows': [[chr(65 + i), i] for i in range(26)], 'data': {'unidad': 'u'}},
  {'title': 'Calor 26 columnas', 'type': 'calor', 'heads': ['Fila'] + [chr(65 + i) for i in range(26)], 'rows': [['Una fila con rótulo largo'] + list(range(26))], 'data': {'unidad': 'u'}},
]

def main(html, engine, outdir):
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    rep = {'engine': engine, 'exports': [], 'edge': {}}
    with serve(Path(html)) as url, sync_playwright() as pw:
        b = getattr(pw, engine).launch()
        ctx = b.new_context(viewport={'width': 1440, 'height': 900}, accept_downloads=True, reduced_motion='reduce')
        p = ctx.new_page(); errors = []; p.on('pageerror', lambda e: errors.append(str(e)))
        p.goto(url + '#atlas-graficas'); p.wait_for_timeout(800)
        figs = p.locator('article.pagina:not([hidden]) .mg-exportar')
        for i in range(figs.count()):
            box = figs.nth(i)
            fig_id = box.evaluate("b => b.closest('[id]')?.id")
            for k, ext in ((0, 'csv'), (1, 'svg')):
                btn = box.locator('button').nth(k)
                if not btn.count(): continue
                btn.scroll_into_view_if_needed(); bb = btn.bounding_box()
                try:
                    with p.expect_download(timeout=6000) as d:
                        p.mouse.click(bb['x'] + bb['width'] / 2, bb['y'] + bb['height'] / 2)
                    target = outdir / f'{engine}-{fig_id}.{ext}'
                    d.value.save_as(target)
                    rep['exports'].append({'fig': fig_id, 'ext': ext, 'file': target.name, 'bytes': target.stat().st_size})
                except Exception as e:
                    hit = p.evaluate('([x,y]) => { const e = document.elementFromPoint(x,y); return e && (e.closest("[id]")?.id + " " + e.tagName + "." + e.className); }', [bb['x'] + bb['width'] / 2, bb['y'] + bb['height'] / 2])
                    rep['exports'].append({'fig': fig_id, 'ext': ext, 'error': str(e)[:120], 'hit': hit})
        # Standalone rendering of every exported SVG in a blank page (no stylesheet, file origin)
        viewer = ctx.new_page()
        for svgfile in sorted(outdir.glob(f'{engine}-*.svg')):
            text = svgfile.read_text()
            viewer.goto(svgfile.as_uri()); viewer.wait_for_timeout(50)
            info = viewer.evaluate("""() => { const s = document.documentElement; const shapes = [...s.querySelectorAll('rect,path,circle')].filter(n => !n.closest('defs'));
              const fills = shapes.map(n => getComputedStyle(n).fill); const strokes = shapes.map(n => getComputedStyle(n).stroke);
              const unresolved = fills.filter(f => /url\\(/.test(f)).filter(f => { const id = f.match(/#([^"')]+)/)?.[1]; return !id || !document.getElementById(id); }).length;
              return {tag: s.tagName, shapes: shapes.length, painted: fills.filter(f => f !== 'none').length + strokes.filter(x => x !== 'none').length, unresolved,
                      texts: s.querySelectorAll('text').length, w: s.getAttribute('width'), h: s.getAttribute('height')}; }""")
            info['external_url'] = bool(re.search(r'url\(["\']?https?://', text))
            info['modern_color_fns'] = sorted(set(re.findall(r'\b(oklch|oklab|color-mix|color|lab|lch|light-dark)\(', text)))
            info['file'] = svgfile.name
            viewer.screenshot(path=str(outdir / (svgfile.stem + '.png')))
            rep['exports'].append({'standalone': info})
        # Edge cases at 320 and 1440
        for width in (320, 1440):
            p.set_viewport_size({'width': width, 'height': 860}); p.wait_for_timeout(200)
            rep['edge'][width] = [p.evaluate(EDGE, c) for c in CASES]
        rep['errors'] = errors
        b.close()
    (outdir / f'charts-{engine}.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
    print(json.dumps(rep, ensure_ascii=False)[:200])

if __name__ == '__main__':
    main(*sys.argv[1:4])
