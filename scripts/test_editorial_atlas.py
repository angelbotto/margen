#!/usr/bin/env python3
"""Index layering, reading edges, dated headers and author footers in real Chromium; offline.

Regression seen on 2026-10-22: the fixed index (z 2) painted over transparent wide
surfaces (z auto) such as photo galleries and open details, and the gallery's edge
fade revealed index text. Hit testing and decoded screenshots are the evidence;
computed styles alone are not.
"""
import base64,html as html_lib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from contract_artifact import build,document_dates,footer_options
RECIPES={r['id']:r['html'] for r in json.loads((ROOT/'packages/core/registry/registry.json').read_text())['componentes']}
FILLER='<p>Un párrafo suficiente para desplazar la lectura y cruzar el índice marginal con cada superficie ancha.</p>'*6
def lines(n):return '\n'.join(f'const registro{i:04d} = {{ numero: {i}, estado: "ejemplo" }};' for i in range(1,n+1))
def code(id,n):return (f'<div class="codigo"><div class="cab"><span>registros.js · JavaScript</span><button type="button" data-copiar="{id}">Copiar código</button><span class="copia-estado" role="status"></span></div>'
 f'<pre tabindex="0" aria-label="{n} líneas de código"><code id="{id}" data-lenguaje="javascript" data-lineas data-destacar="2-5">{html_lib.escape(lines(n))}</code></pre></div>')
# Long entries so index text reaches the 1024 px surfaces at x=208 (1440) and x=128 (1280).
TITLES=['Abrir la galería y recorrer cada fotografía','Recorrer las fotos sin perder el contexto','Abrir el detalle y leer su explicación','Leer el código con números y rangos','Comparar la tabla con sus valores','Cerrar la lectura con autoría y fecha']
SECTIONS=''.join(f'<section class="prosa" id="s{i}"><h2>{t}</h2>{FILLER}</section>' for i,t in enumerate(TITLES))
CONTENT=(SECTIONS.replace('</section><section class="prosa" id="s1">','</section>'+RECIPES['galeria']+'<section class="prosa" id="s1">',1)
 .replace('</section><section class="prosa" id="s3">','</section><details class="ancho" id="detalle"><summary>Ciento veinte líneas</summary><p>Una explicación que cruza el índice cuando el detalle está abierto.</p>'+code('cien',120)+'</details><section class="prosa" id="s3">',1)
 .replace('</section><section class="prosa" id="s4">','</section><figure class="ancho" id="tabla"><div class="tabla-caja" tabindex="0" aria-label="Tabla de ejemplo"><table><thead><tr><th>Mes</th><th>Valor</th></tr></thead><tbody>'+''.join(f'<tr><td>Mes {i}</td><td>{i*7}</td></tr>' for i in range(1,9))+'</tbody></table></div><figcaption>Datos ilustrativos.</figcaption></figure><section class="prosa" id="s4">',1))
# Author-owned layouts and data views marked data-presentation="auto" at runtime
# (the data explorer) are scope boundaries for geometry, but still cross the index.
CONTENT=CONTENT.replace('</section><section class="prosa" id="s5">','</section><section class="ancho" id="propio" data-ritmo="propio"><p>Composición propia del autor que también cruza el índice marginal de lectura.</p>'+FILLER+'</section><section class="ancho" id="datos"><p>Una vista de datos con su propia presentación, que cruza el índice.</p>'+FILLER+'</section><section class="prosa" id="s5">',1)
SURFACES={'galeria':'#galeria-ejemplo','detalle':'#detalle','tabla':'#tabla','propio':'#propio','datos':'#datos'}
DIFF='''async([a,b])=>{const px=async s=>{const i=await createImageBitmap(await (await fetch('data:image/png;base64,'+s)).blob()),c=new OffscreenCanvas(i.width,i.height),x=c.getContext('2d');x.drawImage(i,0,0);return x.getImageData(0,0,i.width,i.height).data};
 const [p,q]=await Promise.all([px(a),px(b)]);let n=0;for(let i=0;i<p.length;i+=4)if(Math.max(Math.abs(p[i]-q[i]),Math.abs(p[i+1]-q[i+1]),Math.abs(p[i+2]-q[i+2]))>8)n++;return n/(p.length/4)}'''
# Index text points inside a surface: how many hit the index, and the overlap clip.
HIT='''sel=>{const idx=[...document.querySelectorAll('.indice')].find(e=>e.offsetParent!==null||getComputedStyle(e).position==='fixed'),s=document.querySelector(sel);const ir=idx.getBoundingClientRect(),sr=s.getBoundingClientRect();
 let points=0,index=0;for(const a of idx.querySelectorAll('a')){const range=document.createRange();range.selectNodeContents(a);for(const r of range.getClientRects())for(const fx of [.2,.5,.8]){
  const x=r.left+r.width*fx,y=r.top+r.height/2;if(!r.width||x<sr.left||x>sr.right||y<sr.top||y>sr.bottom||y>ir.bottom||y>innerHeight-170||y<170)continue;points++;if(idx.contains(document.elementFromPoint(x,y)))index++;}}
 const clip={x:Math.max(ir.left,sr.left),y:Math.max(ir.top,sr.top,170)};clip.width=Math.min(ir.right,sr.right)-clip.x;clip.height=Math.min(ir.bottom,sr.bottom,innerHeight-170)-clip.y;return {points,index,clip}}'''

class EditorialAtlas(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch()
  cls.html=build('La forma de leer',[{'id':'content','titulo':'La forma de leer','html':CONTENT}],theme='editorial',mode='dark',date={'published':'2026-10-01','updated':'2026-10-22'},
   footer={'author':'Ana Autora','note':'Notas de campo.','links':[{'label':'Sitio','href':'https://ana.example/','detail':'proyectos y notas'},{'label':'Correo','href':'mailto:ana@ana.example'}]},reactions=True)
  cls.html=cls.html.replace('id="datos"','id="datos" data-presentation="auto"')
  long=CONTENT.replace(code('cien',120),code('mil',1000))
  cls.chapters=build('Atlas de prueba',[{'id':'uno','titulo':'Uno','html':long},{'id':'dos','titulo':'Dos','html':'<section class="prosa" id="d1"><h2>Dos</h2><p>Otra página.</p></section>'}],theme='editorial',mode='dark',format='chapters')
 @classmethod
 def tearDownClass(cls):cls.browser.close();cls.pw.stop()
 def page(self,width=1440,html=None,scheme='dark',motion='no-preference',touch=False,js=True):
  context=self.browser.new_context(viewport={'width':width,'height':1000},color_scheme=scheme,reduced_motion=motion,has_touch=touch,java_script_enabled=js,permissions=['clipboard-read','clipboard-write'])
  self.addCleanup(context.close);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  context.route('https://margen.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body='<!doctype html>'+(html or self.html)))
  page.goto('https://margen.test/atlas')
  if js:page.evaluate('document.fonts.ready')
  return page,errors
 def bring(self,page,selector,offset=330):
  page.evaluate('([s,o])=>{const e=document.querySelector(s);scrollTo({top:scrollY+e.getBoundingClientRect().top-o,behavior:"instant"})}',[selector,offset]);page.mouse.move(5,995);page.wait_for_timeout(400)
 def index_pixels(self,page,clip):
  shown=page.screenshot(clip=clip);page.evaluate('document.querySelectorAll(".indice").forEach(e=>e.style.visibility="hidden")')
  hidden=page.screenshot(clip=clip);page.evaluate('document.querySelectorAll(".indice").forEach(e=>e.style.visibility="")')
  return page.evaluate(DIFF,[base64.b64encode(shown).decode(),base64.b64encode(hidden).decode()])

 def test_wide_surfaces_cover_the_index(self):
  for width in (1440,1280):
   for scheme,family in (('dark','editorial'),('light','editorial'),('dark','catabum'),('light','kaira')):
    page,errors=self.page(width,scheme=scheme);page.evaluate('([f,m])=>NotaTemas.set({family:f,mode:m})',[family,scheme])
    page.locator('#detalle summary').focus();page.keyboard.press('Enter');page.locator('#detalle summary').blur()
    self.assertTrue(page.locator('#detalle').evaluate('e=>e.open'))
    for name,selector in SURFACES.items():
     with self.subTest(width=width,theme=family,scheme=scheme,surface=name):
      self.bring(page,selector,200 if name=='detalle' else 330);hit=page.evaluate(HIT,selector)
      self.assertGreater(hit['points'],0,'the fixture must cross the index');self.assertEqual(hit['index'],0)
      self.assertLess(self.index_pixels(page,hit['clip']),.01)
    self.assertEqual(errors,[]);page.close()

 def test_gallery_fade_reveals_paper_not_index(self):
  page,_=self.page();self.bring(page,'#galeria-ejemplo')
  track=page.locator('#galeria-ejemplo [data-galeria-pista]')
  track.evaluate('e=>{e.scrollLeft=120}');page.evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
  # The fade follows the scroll within a frame, not after the 90 ms status debounce.
  self.assertEqual(track.evaluate('e=>e.style.getPropertyValue("--galeria-fade-inicio")'),'40px')
  index=page.locator('.indice').bounding_box();box=page.locator('#galeria-ejemplo').bounding_box();rect=track.bounding_box()
  clip={'x':rect['x'],'y':rect['y'],'width':40,'height':rect['height']}
  self.assertLess(clip['x'],index['x']+index['width'])
  self.assertLess(self.index_pixels(page,clip),.01)
  self.assertEqual(page.locator('#galeria-ejemplo').evaluate('e=>getComputedStyle(e).backgroundColor'),page.evaluate('getComputedStyle(document.body).backgroundColor'))
  self.assertGreater(box['width'],1000)

 def test_focus_restores_index_and_tab_order(self):
  page,_=self.page();self.bring(page,'#galeria-ejemplo');hit=page.evaluate(HIT,'#galeria-ejemplo')
  order=page.locator('.indice a').evaluate_all('as=>as.map(a=>a.hash)')
  page.locator('.indice').focus()
  visited=[]
  for _ in order:page.keyboard.press('Tab');visited.append(page.evaluate('document.activeElement.hash'))
  self.assertEqual(visited,order)
  self.assertEqual(page.locator('.indice').evaluate('e=>getComputedStyle(e).zIndex'),'4')
  point=[hit['clip']['x']+hit['clip']['width']/2,hit['clip']['y']+hit['clip']['height']/2]
  self.assertTrue(page.evaluate('([x,y])=>!!document.elementFromPoint(x,y)?.closest(".indice")',point))
  page.keyboard.press('Tab');self.assertFalse(page.evaluate('([x,y])=>!!document.elementFromPoint(x,y)?.closest(".indice")',point))

 def test_code_still_blurs_and_is_not_nested_twice(self):
  page,_=self.page()
  self.assertEqual(page.locator('#detalle pre').evaluate('e=>getComputedStyle(e).backdropFilter'),'none')
  self.assertEqual(page.locator('#detalle').evaluate('e=>getComputedStyle(e).zIndex'),'3')
  page.locator('#detalle summary').click();page.locator('#detalle button[data-copiar]').click()
  self.assertEqual(page.evaluate('navigator.clipboard.readText()'),lines(120))
  numbers=page.locator('#cien .codigo-linea').evaluate_all('es=>es.map(e=>getComputedStyle(e,"::before").content)')
  self.assertEqual(len(numbers),120)

 def test_thousand_lines_numbers_and_copy(self):
  page,errors=self.page(html=self.chapters);page.locator('#detalle summary').click()
  rows=page.locator('#mil .codigo-linea');self.assertEqual(rows.count(),1000)
  tops=rows.evaluate_all('es=>[es[0],es[998],es[999]].map(e=>e.getBoundingClientRect().top)')
  self.assertAlmostEqual(tops[2]-tops[1],22,delta=.1)
  last=rows.nth(999).evaluate('e=>{const b=getComputedStyle(e,"::before");return [b.whiteSpace,parseFloat(b.width)]}')
  self.assertEqual(last[0],'nowrap');self.assertGreaterEqual(last[1],3*7)
  page.locator('#detalle button[data-copiar]').click();self.assertEqual(page.evaluate('navigator.clipboard.readText()'),lines(1000))
  self.assertEqual(errors,[])

 def test_toc_strike_in_documents_and_chapters(self):
  for html,cls in ((None,'visto'),(self.chapters,'aqui-visto')):
   with self.subTest(item=cls):
    page,_=self.page(html=html);self.bring(page,'#s4',100)
    seen=page.locator('.indice li.'+cls+' a').first
    self.assertGreater(page.locator('.indice li.'+cls).count(),2)
    style=seen.evaluate('a=>{const s=getComputedStyle(a);return [s.textDecorationLine,s.textDecorationThickness,s.color,s.textDecorationColor]}')
    self.assertEqual(style[:2],['line-through','2px'])
    self.assertNotIn('rgba(0, 0, 0, 0)',style[3]);self.assertRegex(style[2],r'oklab|color-mix|rgba|/ 0\.5')
    unread=page.locator('.indice li:not(.'+cls+') a').last.evaluate('a=>getComputedStyle(a).textDecorationColor')
    self.assertEqual(unread,'rgba(0, 0, 0, 0)')
  page,_=self.page(motion='reduce');self.assertEqual(page.locator('.indice a').first.evaluate('a=>getComputedStyle(a).transitionDuration'),'0s')

 def test_reading_edges_are_decorative(self):
  page,_=self.page()
  layers=page.locator('.lectura-bordes > span');self.assertEqual(layers.count(),8)
  self.assertEqual(page.locator('.lectura-bordes').get_attribute('aria-hidden'),'true')
  info=layers.evaluate_all('es=>es.map(e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return [s.backdropFilter,s.pointerEvents,Math.round(r.top),Math.round(r.height)]})')
  self.assertEqual([i[0] for i in info],['blur(1px)','blur(2px)','blur(4px)','blur(8px)']*2)
  self.assertTrue(all(i[1]=='none' and i[3]==100 for i in info));self.assertEqual({i[2] for i in info},{0,900})
  # Text under the bottom band stays selectable and clickable.
  self.bring(page,'#s2',700);point=page.evaluate('()=>[document.querySelector("#s2 p").getBoundingClientRect().left+20,innerHeight-30]')
  self.assertTrue(page.evaluate('([x,y])=>!!document.elementFromPoint(x,y).closest("#s2")',point))
  cdp=page.context.new_cdp_session(page);cdp.send('Emulation.setEmulatedMedia',{'features':[{'name':'prefers-reduced-transparency','value':'reduce'}]})
  self.assertEqual(page.locator('.lectura-bordes').evaluate('e=>getComputedStyle(e).display'),'none')
  page.emulate_media(media='print');self.assertEqual(page.locator('.lectura-bordes').evaluate('e=>getComputedStyle(e).display'),'none')
  self.assertEqual(page.locator('#detalle').evaluate('e=>getComputedStyle(e).zIndex'),'auto')
  pres=build('Diapositivas',[{'id':'a','titulo':'A','html':'<section id="x"><h2>X</h2><p>y</p></section>'},{'id':'b','titulo':'B','html':'<p>z</p>'}],format='presentation')
  page,_=self.page(html=pres);self.assertEqual(page.locator('.lectura-bordes').count(),0)

 def test_mobile_and_touch(self):
  for width in (390,320):
   with self.subTest(width=width):
    page,errors=self.page(width,touch=True)
    self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
    self.assertEqual(page.locator('.indice').evaluate('e=>getComputedStyle(e).position'),'static')
    page.locator('.indice a').nth(2).tap();page.wait_for_timeout(100);self.assertEqual(page.evaluate('location.hash'),'#s2')
    self.assertEqual(errors,[])
  page,_=self.page(touch=True);self.bring(page,'#galeria-ejemplo');hit=page.evaluate(HIT,'#galeria-ejemplo')
  page.touchscreen.tap(hit['clip']['x']+hit['clip']['width']/2,hit['clip']['y']+hit['clip']['height']/2);page.wait_for_timeout(100)
  self.assertEqual(page.evaluate('location.hash'),'')

 def test_hover_goes_to_the_surface(self):
  page,_=self.page();self.bring(page,'#galeria-ejemplo');hit=page.evaluate(HIT,'#galeria-ejemplo')
  page.mouse.move(hit['clip']['x']+hit['clip']['width']/2,hit['clip']['y']+hit['clip']['height']/2)
  self.assertEqual(page.locator('.indice a:hover').count(),0)

 def test_header_date_and_author_footer(self):
  page,errors=self.page()
  date=page.locator('.cabecera-fecha')
  self.assertEqual(date.text_content(),'Publicado 1 oct 2026 · Actualizado 22 oct 2026')
  self.assertEqual(date.locator('time').evaluate_all('ts=>ts.map(t=>t.getAttribute("datetime"))'),['2026-10-01','2026-10-22'])
  self.assertEqual(date.evaluate('e=>[getComputedStyle(e).fontSize,getComputedStyle(e).fontFamily.includes("Mono")]'),['13.7px',True])
  footer=page.locator('footer.pie-documento')
  self.assertEqual(footer.locator('.pie-autor').text_content(),'Ana Autora')
  self.assertEqual(footer.locator('.pie-enlaces a').evaluate_all('as=>as.map(a=>[a.href,a.rel])'),[['https://ana.example/','noopener noreferrer'],['mailto:ana@ana.example','noopener noreferrer']])
  self.assertEqual(footer.locator('.pie-plataforma').text_content(),'Hecho con Margen')
  detail=footer.locator('.pie-detalle')
  self.assertEqual(detail.evaluate('e=>getComputedStyle(e).filter'),'blur(4px)')
  footer.locator('.pie-enlaces a').first.focus();page.wait_for_timeout(350);self.assertEqual(detail.evaluate('e=>getComputedStyle(e).filter'),'none')
  self.assertEqual(errors,[])
  plain=build('Sin pie',[{'id':'a','titulo':'Sin pie','html':'<p>texto</p>'}])
  self.assertNotIn('class="cabecera-fecha"',plain);self.assertNotIn('class="pie pie-documento"',plain);self.assertIn('<footer class="pie"><p>Margen · Sin pie</p></footer>',plain)

 def test_reactions_are_local_and_uncounted(self):
  page,_=self.page()
  group=page.locator('[data-reacciones]');buttons=group.locator('[data-reaccion]')
  self.assertEqual(buttons.count(),3);self.assertIn('solo en este navegador',group.text_content())
  self.assertNotRegex(group.text_content(),r'\d')
  buttons.nth(1).click();self.assertEqual(buttons.nth(1).get_attribute('aria-pressed'),'true')
  page.reload();page.wait_for_timeout(100)
  self.assertEqual(page.locator('[data-reaccion]').evaluate_all('bs=>bs.map(b=>b.getAttribute("aria-pressed"))'),['false','true','false'])
  self.assertEqual(page.locator('[data-reaccion] svg').evaluate_all('ss=>ss.map(s=>[s.getAttribute("stroke-width"),getComputedStyle(s).width])'),[['1.6','18px']]*3)

 def test_metadata_validation(self):
  self.assertIsNone(document_dates(None))
  for bad in ('2026-02-30','22/10/2026','2026-10-1',{'updated':'2026-10-01'},{'published':'2026-10-22','updated':'2026-10-01'},{'published':'2026-10-01','extra':1},20261022):
   with self.subTest(date=bad),self.assertRaises(ValueError):document_dates(bad)
  for bad in ({'links':[{'label':'x','href':'javascript:alert(1)'}]},{'links':[{'label':'x','href':'http://plain.example'}]},{'links':[{'label':'x','href':'https://user:pw@host.example'}]},
              {'links':[{'label':'x','href':'https://a.example/"onmouseover="x'}]},{'links':[{'label':'x','href':'mailto:nadie'}]},{'author':'a\nb'},{'author':'x'*121},{'links':[{'label':'x','href':'https://a.example','icon':'y'}]},
              {'platform':'no'},{'author':None,'platform':False},{'unknown':1},{'links':[{'label':'x','href':'https://a.example'}]*9}):
   with self.subTest(footer=bad),self.assertRaises(ValueError):footer_options(bad)
  html=build('T',[{'id':'a','titulo':'T','html':'<p>x</p>'}],footer={'author':'<img src=x onerror=alert(1)>','platform':False})
  self.assertIn('&lt;img src=x onerror=alert(1)&gt;',html);self.assertNotIn('Hecho con Margen',html)
  with self.assertRaises(ValueError):build('T',[{'id':'a','titulo':'T','html':'<p>x</p>'}],reactions='yes')

 def test_generator_config_options(self):
  with tempfile.TemporaryDirectory() as tmp:
   folder=Path(tmp);(folder/'a.html').write_text('<section class="prosa" id="a"><h2>Uno</h2><p>Texto.</p></section>')
   def run(config,*extra):
    (folder/'c.json').write_text(json.dumps(config));return subprocess.run([sys.executable,str(ROOT/'scripts/create_artifact.py'),'--config',str(folder/'c.json'),'--no-project','--output',str(folder/'out.html'),*extra],capture_output=True,text=True)
   base={'title':'Nota','pages':[{'id':'uno','title':'Uno','content':'a.html','date':'2026-10-20'}]}
   result=run({**base,'date':'2026-10-01','footer':{'author':'Ana','platform':False},'reactions':True});self.assertEqual(result.returncode,0,result.stderr)
   out=(folder/'out.html').read_text()
   self.assertIn('<p class="cabecera-fecha"><time datetime="2026-10-20">20 oct 2026</time></p>',out)
   self.assertIn('<p class="pie-autor">Ana</p>',out);self.assertNotIn('Hecho con Margen',out);self.assertIn('data-reacciones',out)
   bad=run({**base,'footer':{'links':[{'label':'x','href':'javascript:alert(1)'}]}});self.assertEqual(bad.returncode,1);self.assertIn('footer.links[0].href',bad.stderr+bad.stdout)
   self.assertEqual(run(base,'--date','2026-02-30').returncode,1)

if __name__=='__main__':unittest.main()
