#!/usr/bin/env python3
"""Mide cada gráfica del atlas: desbordamiento, tamaño real del texto SVG, solapes de rótulos,
rótulos literales X/Y, marcas enfocables y errores. Sin red.

Uso: measure_charts.py <atlas.html> <salida.json> [--shots DIR]
Python con Playwright: /Users/angelbotto/orca/workspaces/margen/margen-lector-voz/.venv/bin/python
"""
import json, sys, pathlib
from playwright.sync_api import sync_playwright

SELECTOR = '[data-grafica],[data-analitica],[data-reporte="cascada"],[data-reporte="multiples"],[data-evidencia]:not([data-evidencia="imagen"]),[data-atencion]'
PROBE = r"""(sel) => {
  const out = [];
  for (const fig of document.querySelectorAll(sel)) {
    if (!fig.offsetParent && getComputedStyle(fig).position !== 'fixed') continue;
    const kind = ['grafica','analitica','reporte','evidencia','atencion'].filter(k => k in fig.dataset).map(k => k + ':' + fig.dataset[k])[0];
    const svgs = [...fig.querySelectorAll('svg')].filter(s => !s.closest('.mg-tip') && s.getBoundingClientRect().width > 40);
    const boxes = [...fig.querySelectorAll('.grafica-caja,.evidencia-visor,.analitica-caja,.atencion-caja')];
    const scroll = boxes.filter(b => b.scrollWidth > b.clientWidth + 1).map(b => ({sw: b.scrollWidth, cw: b.clientWidth, declared: b.classList.contains('mg-desplazable-caja') || !!b.querySelector('svg.mg-desplazable')}));
    const sizes = [], overlaps = [], literal = [], outside = [];
    for (const svg of svgs) {
      const sr = svg.getBoundingClientRect();
      const texts = [...svg.querySelectorAll('text')].filter(t => t.textContent.trim() && t.getBBox().width > 0 && !t.closest('defs'));
      const rects = texts.map(t => { const r = t.getBoundingClientRect(); return {t: t.textContent.trim().slice(0, 30), x: r.x, y: r.y, w: r.width, h: r.height, fs: parseFloat(getComputedStyle(t).fontSize) * (sr.width / (svg.viewBox.baseVal?.width || sr.width))}; });
      rects.forEach(r => sizes.push(r.fs));
      texts.forEach(t => { if (/^[XY]$/.test(t.textContent.trim()) && !t.classList.contains('mg-dia')) literal.push(t.textContent.trim()); });
      // Rótulos que salen del recuadro visible del SVG (recorte o desborde).
      const box = svg.closest('.grafica-caja,.evidencia-visor,.analitica-caja,.atencion-caja')?.getBoundingClientRect() || sr;
      rects.forEach(r => { if (r.x < Math.min(sr.x, box.x) - 1 || r.x + r.w > Math.max(sr.right, box.right) + 1) outside.push(r.t); });
      for (let i = 0; i < rects.length; i++) for (let j = i + 1; j < rects.length; j++) {
        const a = rects[i], b = rects[j];
        const ox = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x), oy = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
        if (ox > 1.5 && oy > 1.5) overlaps.push(a.t + ' ⟂ ' + b.t);
      }
    }
    const focusable = fig.querySelectorAll('svg [tabindex]').length;
    out.push({kind, svgs: svgs.length, scroll, fontMin: sizes.length ? Math.min(...sizes) : null, fontMax: sizes.length ? Math.max(...sizes) : null,
      overlaps: overlaps.slice(0, 8), overlapCount: overlaps.length, literalXY: literal, outside: outside.slice(0, 6), focusableMarks: focusable,
      error: fig.querySelector('.grafica-error,[data-error-grafica],[data-error-analitica],[data-error-reporte],[data-error-atencion],.evidencia-error')?.textContent.trim() || null,
      pageOverflow: document.documentElement.scrollWidth > innerWidth + 1});
  }
  return out;
}"""


def measure(page, width):
    result = {}
    for target in ['atlas-graficas', 'atlas-reportes']:
        page.evaluate("id => document.querySelector(`[data-ir='${id}']`)?.click()", target)
        page.wait_for_timeout(500)
        result[target] = page.evaluate(PROBE, SELECTOR)
    return result


def main():
    src, out = pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2])
    shots = pathlib.Path(sys.argv[sys.argv.index('--shots') + 1]) if '--shots' in sys.argv else None
    data = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for width, height in [(390, 844), (1440, 900)]:
            page = browser.new_page(viewport={'width': width, 'height': height})
            page.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(src.as_uri())
            page.wait_for_timeout(600)
            data[width] = {'charts': measure(page, width), 'errors': errors}
            if shots:
                shots.mkdir(parents=True, exist_ok=True)
                page.evaluate("document.querySelector(`[data-ir='atlas-graficas']`)?.click()")
                page.wait_for_timeout(300)
                page.screenshot(path=str(shots / f'graficas-{width}.png'), full_page=True)
            page.close()
        browser.close()
    out.write_text(json.dumps(data, indent=1, ensure_ascii=False))
    for width, d in data.items():
        rows = [c for v in d['charts'].values() for c in v]
        scroll = [c['kind'] for c in rows if c['scroll']]
        fonts = [c['fontMax'] for c in rows if c['fontMax']]
        print(width, 'charts', len(rows), 'scroll', len(scroll), scroll, 'font', round(min(f for c in rows if (f := c['fontMin'])), 1) if fonts else None, '–', round(max(fonts), 1) if fonts else None,
              'overlaps', sum(c['overlapCount'] for c in rows), 'XY', sum(len(c['literalXY']) for c in rows), 'focusable', sum(c['focusableMarks'] for c in rows), 'errors', d['errors'][:3],
              'chart errors', [c['kind'] for c in rows if c['error']])


if __name__ == '__main__':
    main()
