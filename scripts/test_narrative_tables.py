"""Narrative fields remain readable in typed tables and mobile record cards."""
import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from contract_artifact import build
from portal.reader_style import refresh_editorial_reference
TEXT='A definition includes its source, eligible population, measurement window and limitations. '*3
CONTENT='''<section class="pieza amplio" id="records" data-explorador><h2>Measurement definitions</h2>
<form><input name="buscar" type="search" aria-label="Search records"></form><p data-explorador-estado role="status"></p>
<div class="tabla-caja" tabindex="0" role="region" aria-label="Records"><table><caption>Illustrative definitions</caption>
<thead><tr><th data-tipo="texto" scope="col">Name</th><th data-tipo="texto" scope="col">Category</th><th data-tipo="numero" scope="col">Count</th><th data-tipo="texto" scope="col">Definition</th></tr></thead>
<tbody><tr><th scope="row">Coverage</th><td>Operations</td><td data-valor="12">12</td><td id="definition">TEXT</td></tr></tbody></table></div></section>'''.replace('TEXT',TEXT)
class NarrativeTables(unittest.TestCase):
 def test_types_mobile_width_and_hosted_refresh_preserve_values(self):
  from playwright.sync_api import sync_playwright
  source=build('Definitions',[{'id':'report','titulo':'Report','html':CONTENT}])
  # The hosted stylesheet must override an older document's last-column numeric rule.
  old=source.replace('</style>','\n[data-explorador] td:last-child{font:13px var(--mono);text-align:right}\n</style>',1)
  runtime=json.loads((ROOT/'portal/static/runtime-refresh.json').read_text())
  hosted=refresh_editorial_reference(old,(ROOT/'portal/static/editorial-reference.css').read_text(),(ROOT/'portal/static/editorial-code.js').read_text(),(ROOT/'portal/static/editorial-pieces.js').read_text(),runtime)
  with tempfile.TemporaryDirectory() as tmp,sync_playwright() as p:
   for label,html in [('standalone',source),('hosted',hosted)]:
    path=Path(tmp)/(label+'.html');path.write_text(html)
    for engine in ['chromium','webkit']:
     browser=getattr(p,engine).launch()
     for width in [1440,390]:
      with self.subTest(mode=label,engine=engine,width=width):
       page=browser.new_page(viewport={'width':width,'height':900});page.goto(path.as_uri());page.locator('.explorer-ready').wait_for()
       c=page.locator('#definition');style=c.evaluate('e=>({align:getComputedStyle(e).textAlign,font:getComputedStyle(e).fontFamily,width:e.getBoundingClientRect().width,row:e.parentElement.getBoundingClientRect().width})')
       self.assertEqual(style['align'],'left');self.assertNotIn('Mono',style['font'])
       if width==390:self.assertGreater(style['width'],style['row']*.85)
       else:self.assertEqual(page.locator('[data-value-type=numero]').evaluate('e=>getComputedStyle(e).textAlign'),'right')
       self.assertEqual(c.text_content(),TEXT)
       self.assertIn(TEXT.strip(),page.locator('[data-explorador]').evaluate('e=>NotaExplorador.get(e).exportCSV()'))
       self.assertTrue(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
       page.close()
     browser.close()
if __name__=='__main__':unittest.main()
