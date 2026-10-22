#!/usr/bin/env python3
"""Token colour contrast against the code surface in each theme family/mode. Usage: probe_code_contrast.py doc.html engine"""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from probe_common import serve, offline
JS = r"""() => {
  const canvas = document.createElement('canvas'); canvas.width = canvas.height = 1; const ctx = canvas.getContext('2d', {willReadFrequently: true});
  const rgba = c => { ctx.clearRect(0, 0, 1, 1); ctx.fillStyle = '#000'; ctx.fillStyle = c; ctx.fillRect(0, 0, 1, 1); return [...ctx.getImageData(0, 0, 1, 1).data]; };
  const over = (top, bottom) => { const a = top[3] / 255; return [0, 1, 2].map(i => Math.round(top[i] * a + bottom[i] * (1 - a))).concat(255); };
  const lum = c => { const [r, g, b] = c.slice(0, 3).map(v => { v /= 255; return v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }); return .2126 * r + .7152 * g + .0722 * b; };
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return +((Math.max(x, y) + .05) / (Math.min(x, y) + .05)).toFixed(2); };
  const codes = [...document.querySelectorAll('.pagina.viva .codigo.codigo-editorial pre code[data-codigo-estado=listo]')].filter(c => c.getClientRects().length);
  if (!codes.length) return null; const agg = {n: codes.length, out: {}};
  for (const code of codes) {
  // effective background: walk up and composite
  let bg = [0, 0, 0, 0], chain = [];
  for (let n = code; n; n = n.parentElement) { const c = rgba(getComputedStyle(n).backgroundColor); if (c[3]) chain.push(c); }
  bg = chain.reverse().reduce((acc, c) => over(c, acc), [255, 255, 255, 255]);
  const out = {};
  for (const cls of ['com', 'str', 'kw', 'codigo-atributo', 'codigo-funcion', 'codigo-numero', 'codigo-etiqueta', 'codigo-puntuacion', 'codigo-escape', 'codigo-regex']) {
    const el = code.querySelector('.' + cls); if (!el) continue; out[cls] = ratio(over(rgba(getComputedStyle(el).color), bg), bg);
  }
  const line = code.querySelector('.codigo-linea'); if (line) out['linea-numero'] = ratio(over(rgba(getComputedStyle(line, '::before').color), bg), bg);
  out.plain = ratio(over(rgba(getComputedStyle(code).color), bg), bg);
  for (const [k, v] of Object.entries(out)) agg.out[k] = Math.min(agg.out[k] ?? 99, v);
  }
  return agg;
}"""
html, engine = sys.argv[1:3]; res = {}
with serve(Path(html)) as url, sync_playwright() as pw:
    b = getattr(pw, engine).launch(); ctx = b.new_context(viewport={'width': 1440, 'height': 900}); offline(ctx, [])
    p = ctx.new_page(); p.goto(url + '#receta-codigo-poliglota'); p.wait_for_timeout(1500)
    for fam in ('editorial', 'catabum', 'kaira'):
        for mode in ('light', 'dark'):
            p.evaluate(f"""() => {{ document.querySelector('[data-elegir-tema][value="{fam}"]')?.click(); document.querySelector('[data-elegir-modo][value="{mode}"]')?.click(); }}""")
            p.wait_for_timeout(250)
            res[f'{fam}-{mode}'] = {'theme': p.evaluate('document.documentElement.dataset.theme'), **(p.evaluate(JS) or {})}
    b.close()
for k, v in res.items():
    low = {c: r for c, r in v.get('out', {}).items() if r < 4.5}
    print(k, v.get('theme'), 'blocks', v.get('n'), 'min ratios', v.get('out'))
