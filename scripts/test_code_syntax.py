#!/usr/bin/env python3
"""Per-language highlighting, exact text and deferred work for code.js, offline in a real browser.

MARGEN_BROWSER=webkit runs the same checks in WebKit. MARGEN_CODE_JS=<file> swaps the code.js
module after the contract build, to show which checks fail with another runtime.
"""
from html import escape
import os, sys, unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from contract_artifact import build
from themes import FAMILIES, DATA

ENGINE = os.environ.get('MARGEN_BROWSER', 'chromium')
SAMPLES = {
 'javascript': '/* varias\n   líneas */\nimport { leer } from "./datos.js";\nconst a = `total ${n + 1} filas`;\nconst s = "a\\tb";\nfunction doble(n) { return n * 2; }',
 'tsx': 'type P = { n: number };\nexport const C = ({ n }: P) => <div className="a">{n} filas</div>;',
 'python': 'def f(x):\n    """Documento\n    de dos líneas."""\n    return f"{x!r}\\n"  # comentario',
 'html': '<style>.a { color: red; }</style>\n<script>let x = 1;</script>\n<p class="z">hola</p>',
 'sql': "SELECT equipo, COUNT(*) FROM t\nWHERE estado = 'ok' -- nota\nGROUP BY equipo;",
 'haskell': 'main = putStrLn "hola"',
}
MARKED = 'const total = suma(a, b);\nconst media = total / 2;'
LONG = '\n'.join(f'const registro{n:04d} = {{ numero: {n}, estado: "ejemplo" }};' for n in range(1, 1001))
EXACT = 'línea\tcon tab\n  emoji 🧭 y “comillas”\n\n<final> & fin'


def box(id, lang, source, attrs='', raw=None):
 return (f'<div class="codigo"><pre tabindex="0" aria-label="Código"><code id="{id}" data-lenguaje="{lang}"{attrs}>'
         f'{raw if raw is not None else escape(source)}</code></pre></div>')


def document():
 first = ('<section class="prosa" id="uno"><h2>Lenguajes</h2>' + ''.join(box('c-' + k, k, v) for k, v in SAMPLES.items()) +
          box('marcado', 'javascript', MARKED, ' data-destacar="2"',
              'const total = <mark>suma(a, b)</mark>;\nconst <span class="subra" title="nota">media = total</span> / 2;') +
          box('exacto', 'javascript', EXACT) +
          box('atenuado', 'javascript', MARKED, ' data-destacar="1" data-atenuar') + '</section>')
 second = ('<section class="prosa" id="dos"><h2>Oculto</h2>' + box('oculto', 'python', 'x = 1') +
           '<details id="detalle"><summary>Ver</summary>' + box('en-detalle', 'css', '.a { color: red; }') + '</details>' +
           box('mil', 'javascript', LONG, ' data-destacar="2-5,998-1000"') + '</section>')
 return build('Código', [{'id': 'primera', 'titulo': 'Primera', 'html': first}, {'id': 'segunda', 'titulo': 'Segunda', 'html': second}],
              theme='editorial', mode='dark')


HTML = document()
if os.environ.get('MARGEN_CODE_JS'):
 current = (ROOT / 'packages/core/components/code.js').read_text()
 HTML = HTML.replace(current, Path(os.environ['MARGEN_CODE_JS']).read_text())

CONTRAST = """(sel)=>{const c=document.createElement('canvas').getContext('2d',{willReadFrequently:true});
 const rgb=v=>{c.clearRect(0,0,1,1);c.fillStyle='#000';c.fillStyle=v;c.fillRect(0,0,1,1);return [...c.getImageData(0,0,1,1).data];};
 const lum=([r,g,b])=>[r,g,b].map(v=>{v/=255;return v<=.03928?v/12.92:((v+.055)/1.055)**2.4}).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
 const pre=document.querySelector(sel).closest('pre');
 c.clearRect(0,0,1,1);c.fillStyle=getComputedStyle(document.body).backgroundColor;c.fillRect(0,0,1,1);c.fillStyle=getComputedStyle(pre).backgroundColor;c.fillRect(0,0,1,1);
 const bg=[...c.getImageData(0,0,1,1).data];const L=lum(bg);const out={};
 for(const s of document.querySelectorAll(sel+' span[class]:not(.codigo-linea)')){const k=s.className;if(out[k])continue;const fg=lum(rgb(getComputedStyle(s).color));out[k]=+((Math.max(fg,L)+.05)/(Math.min(fg,L)+.05)).toFixed(2);}
 return out;}"""


class CodeSyntax(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.pw = sync_playwright().start(); cls.browser = getattr(cls.pw, ENGINE).launch()

 @classmethod
 def tearDownClass(cls):
  cls.browser.close(); cls.pw.stop()

 def page(self, width=1440, hash=''):
  perms = ['clipboard-read', 'clipboard-write'] if ENGINE == 'chromium' else []
  context = self.browser.new_context(viewport={'width': width, 'height': 900}, permissions=perms)
  self.addCleanup(context.close)
  page = context.new_page(); errors = []
  page.on('pageerror', lambda e: errors.append(str(e)))
  self.addCleanup(lambda: self.assertEqual(errors, []))
  if ENGINE != 'chromium':
   page.add_init_script("Object.defineProperty(navigator,'clipboard',{value:{writeText:async t=>{window.copiado=t},readText:async()=>window.copiado}})")
  context.route('**/*', lambda r: r.fulfill(status=200, content_type='text/html', body=HTML) if r.request.url.startswith('https://margen.test/') else r.abort())
  page.goto('https://margen.test/codigo' + hash)
  return page

 def kinds(self, page, id):
  return page.evaluate('(id)=>[...document.getElementById(id).querySelectorAll("span[class]:not(.codigo-linea)")].map(s=>[s.className,s.textContent])', id)

 def test_grammars_by_language(self):
  page = self.page()
  js = self.kinds(page, 'c-javascript')
  self.assertIn(['com', '/* varias'], js); self.assertIn(['com', '   líneas */'], js)
  self.assertIn(['kw', 'import'], js); self.assertIn(['str', '"./datos.js"'], js)
  self.assertIn(['kw', '${'], js); self.assertNotIn(['str', 'n'], js)
  self.assertIn(['codigo-escape', '\\t'], js); self.assertIn(['codigo-funcion', 'doble'], js)
  tsx = self.kinds(page, 'c-tsx')
  self.assertIn(['codigo-atributo', 'className'], tsx); self.assertIn(['kw', 'type'], tsx)
  self.assertTrue(any(k == 'codigo-etiqueta' and t.strip() == 'div' for k, t in tsx), tsx)
  py = self.kinds(page, 'c-python')
  self.assertIn(['str', '    de dos líneas."""'], py); self.assertIn(['codigo-escape', '\\n'], py); self.assertIn(['com', '# comentario'], py)
  html = self.kinds(page, 'c-html')
  self.assertIn(['codigo-atributo', 'color'], html); self.assertIn(['kw', 'let'], html); self.assertIn(['codigo-atributo', 'class'], html)
  sql = self.kinds(page, 'c-sql')
  self.assertIn(['kw', 'SELECT'], sql); self.assertIn(['str', "'ok'"], sql); self.assertIn(['com', '-- nota'], sql)
  unknown = page.locator('#c-haskell')
  self.assertEqual(self.kinds(page, 'c-haskell'), [])
  self.assertEqual(page.locator('#c-haskell').evaluate('e=>e.closest(".codigo").querySelector(".cab span").textContent'), 'haskell')
  self.assertEqual(unknown.text_content(), SAMPLES['haskell'])
  for key, source in SAMPLES.items():
   self.assertEqual(page.locator('#c-' + key).text_content(), source, key)

 def test_marks_exact_text_copy_and_idempotence(self):
  page = self.page()
  marked = page.locator('#marcado')
  self.assertEqual(marked.text_content(), MARKED)
  self.assertEqual(marked.locator('mark').evaluate_all('ms=>ms.map(m=>m.textContent).join("")'), 'suma(a, b)')
  self.assertGreater(marked.locator('mark span[class]').count(), 1)
  self.assertEqual(marked.locator('.subra').evaluate_all('ms=>ms.map(m=>[m.tagName,m.title,m.textContent])'), [['SPAN', 'nota', 'media = total']])
  self.assertEqual(marked.locator('.codigo-linea.destacada').evaluate_all('ls=>ls.map(l=>l.dataset.numero)'), ['2'])
  self.assertEqual(page.locator('#exacto').text_content(), EXACT)
  dynamic = page.evaluate("""()=>{const s='a\\r\\nb\\tc\\u{1F9ED}\\n';const box=document.createElement('div');box.className='codigo';
   box.innerHTML='<pre tabindex="0" aria-label="x"><code data-lenguaje="js"></code></pre>';const code=box.querySelector('code');code.textContent=s;
   document.querySelector('#uno').append(box);NotaCodigo.init(box,{inmediato:true});return [code.textContent===s,code.querySelectorAll('.codigo-linea').length];}""")
  self.assertEqual(dynamic, [True, 3])
  before = marked.evaluate('e=>e.innerHTML')
  page.evaluate('NotaCodigo.init();NotaCodigo.init(document.getElementById("marcado"))')
  self.assertEqual(marked.evaluate('e=>e.innerHTML'), before)
  self.assertEqual(page.locator('style[data-margen-codigo]').count(), 1)
  button = page.locator('#marcado').locator('xpath=ancestor::div[contains(@class,"codigo")]').locator('[data-codigo-copiar]')
  button.click()
  self.assertEqual(page.evaluate('navigator.clipboard.readText()'), MARKED)

 def test_theme_switch_keeps_tokens_and_contrast_in_every_palette(self):
  page = self.page()
  node = page.evaluate_handle('document.querySelector("#c-javascript .kw")')
  low = []
  for family in FAMILIES:
   for mode in ('light', 'dark'):
    page.evaluate('([f,m])=>{document.querySelector(`[data-elegir-tema][value="${f}"]`).click();document.querySelector(`[data-elegir-modo][value="${m}"]`).click()}', [family, mode])
    for id in ('c-javascript', 'c-tsx', 'c-python', 'c-html'):
     for kind, ratio in page.evaluate(CONTRAST, '#' + id).items():
      if ratio < 4.5: low.append((family, mode, kind, ratio))
  self.assertTrue(node.evaluate('n=>n.isConnected'))
  self.assertEqual(low, [])

 def test_dimmed_rest_stays_legible(self):
  page = self.page()
  dim = page.locator('#atenuado .codigo-linea:not(.destacada) .kw').first.evaluate('e=>getComputedStyle(e).color')
  lit = page.locator('#atenuado .codigo-linea.destacada .kw').first.evaluate('e=>getComputedStyle(e).color')
  self.assertNotEqual(dim, lit)
  self.assertTrue(all(r >= 4.5 for r in page.evaluate(CONTRAST, '#atenuado').values()))

 def test_hidden_pages_and_closed_details_wait(self):
  page = self.page()
  page.wait_for_timeout(300)
  self.assertEqual(page.locator('#oculto .codigo-linea, #en-detalle .codigo-linea, #mil .codigo-linea').count(), 0)
  self.assertEqual(page.locator('#mil').text_content(), LONG)
  page.locator('[data-ir="segunda"]').click()
  page.wait_for_function('document.querySelectorAll("#oculto .codigo-linea").length===1')
  self.assertEqual(page.locator('#en-detalle .codigo-linea').count(), 0)
  page.locator('#detalle > summary').click()
  page.wait_for_function('document.querySelectorAll("#en-detalle .codigo-linea").length===1')
  page.locator('#mil').scroll_into_view_if_needed()
  page.wait_for_function('document.querySelectorAll("#mil .codigo-linea").length===1000', timeout=10000)
  code = page.locator('#mil')
  self.assertEqual(code.text_content(), LONG)
  self.assertEqual(code.evaluate('e=>[e.lastElementChild.dataset.numero,getComputedStyle(e).getPropertyValue("--codigo-cifras")]'), ['1000', '4'])
  self.assertEqual(code.locator('.destacada').evaluate_all('ls=>ls.map(l=>l.dataset.numero)'), ['2', '3', '4', '5', '998', '999', '1000'])
  gutter = code.evaluate('e=>{const l=e.lastElementChild,b=getComputedStyle(l,"::before");return [parseFloat(b.width),parseFloat(getComputedStyle(l).fontSize)]}')
  self.assertGreaterEqual(gutter[0], gutter[1] * 4 * .55)

 def test_deep_link_into_unvisited_page(self):
  page = self.page(hash='#en-detalle')
  page.wait_for_function('document.querySelectorAll("#en-detalle .codigo-linea").length===1')
  self.assertTrue(page.locator('#en-detalle').is_visible())

 def test_horizontal_fade_follows_scroll(self):
  page = self.page(width=390)
  page.locator('[data-ir="segunda"]').click()
  page.locator('#mil').scroll_into_view_if_needed()
  page.wait_for_function('document.querySelector("#mil").closest("pre").dataset.desborde==="fin"', timeout=10000)
  page.locator('#mil').evaluate('e=>{const p=e.closest("pre");p.scrollLeft=p.scrollWidth}')
  page.wait_for_function('document.querySelector("#mil").closest("pre").dataset.desborde==="inicio"')
  self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), 390)


if __name__ == '__main__':
 unittest.main()
