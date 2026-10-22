#!/usr/bin/env python3
"""Live Chromium checks of measured editorial geometry and interactions; offline."""
import base64,json,sys,unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from contract_artifact import build
SOURCE='#include <iostream>\n\nint main() {\n    std::cout << "Hello Margen";\n    return 0;\n}'
CONTENT='''<section class="prosa" id="first"><h2>Leer con atención</h2><p>Una columna de lectura conserva una medida estable. El código tiene más espacio para mostrar cada línea.</p></section>
<figure class="codigo ancho" id="snippet"><div class="cab"><span>C++</span><button type="button" data-copiar="source">Copiar código</button><span class="copia-estado" role="status"></span></div><pre tabindex="0" aria-label="Código de ejemplo"><code id="source" data-lenguaje="cpp">#include &lt;iostream&gt;\n\nint main() {\n    std::cout &lt;&lt; "<mark>Hello Margen</mark>";\n    return 0;\n}</code></pre></figure>
<section class="prosa" id="second"><h2>Conservar el contexto</h2><p>El índice permite volver a una sección sin perder el hilo.</p><div class="codigo" id="plain"><pre tabindex="0" aria-label="Código de ejemplo"><code data-lenguaje="javascript">const text = "&lt;script&gt;alert(1)&lt;/script&gt;";</code></pre></div></section>
<section class="ancho" id="cards"><div class="cards-trazadas">'''+''.join('<a href="#first"><h4>Una lectura de ejemplo</h4><p>Información de la publicación.</p><span class="procedencia">ENSAYO · 4 min</span></a>' for _ in range(3))+'''</div></section>
<section id="last"><h2>Final de la lectura</h2>'''+('<p>Un párrafo suficiente para comprobar el desplazamiento y el índice marginal.</p>'*30)+'</section>'
class EditorialReference(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch()
  cls.html=build('La forma de leer',[{'id':'content','titulo':'La forma de leer','html':CONTENT}],theme='editorial',mode='dark')
 @classmethod
 def tearDownClass(cls):cls.browser.close();cls.pw.stop()
 def page(self,width=1440,motion='no-preference',js=True,html=None,scheme='light'):
  context=self.browser.new_context(viewport={'width':width,'height':1000},reduced_motion=motion,color_scheme=scheme,java_script_enabled=js,permissions=['clipboard-read','clipboard-write'])
  self.addCleanup(context.close);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  context.route('https://margen.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=html or self.html))
  page.goto('https://margen.test/reference');page.evaluate('document.fonts.ready') if js else None
  return page,errors
 def test_measures_and_copy(self):
  page,errors=self.page();code=page.locator('#source');self.assertEqual(code.text_content(),SOURCE)
  self.assertEqual(code.locator('mark').text_content(),'Hello Margen')
  self.assertEqual(code.locator('.codigo-linea').count(),6)
  self.assertTrue(page.locator('#snippet .cab > span').first.is_visible())
  self.assertEqual(page.locator('#plain .codigo-lenguaje').text_content(),'JavaScript')
  self.assertEqual(page.locator('#plain script').count(),0)
  self.assertEqual(page.locator('#snippet').bounding_box()['width'],768)
  self.assertEqual(page.locator('#first').bounding_box()['width'],528)
  self.assertEqual(page.locator('#first').bounding_box()['x'],456)
  self.assertEqual(page.locator('#snippet pre').evaluate('e=>getComputedStyle(e).backdropFilter'),'blur(12px)')
  lines=code.locator('.codigo-linea').evaluate_all('es=>es.map(e=>e.getBoundingClientRect().y)')
  self.assertTrue(all(abs(b-a-22)<.1 for a,b in zip(lines,lines[1:])),lines)
  page.locator('[data-copiar=source]').click();self.assertEqual(page.evaluate('navigator.clipboard.readText()'),SOURCE)
  self.assertIn('copiado',page.locator('#snippet [role=status]').text_content().lower())
  page.locator('.indice a').first.focus();self.assertEqual(page.locator('.indice').evaluate('e=>getComputedStyle(e).zIndex'),'4')
  self.assertEqual(errors,[])
  page.locator('.indice a').first.blur();page.mouse.move(1200,600);page.screenshot(path='/tmp/margen-reference-desktop.png')
 def test_responsive_print_and_reduced_motion(self):
  for width in (300,320,390,640,768,1024,1279,1280,1440):
   with self.subTest(width=width):
    page,errors=self.page(width,motion='reduce')
    self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
    for selector in ('#snippet','#first','#cards'):
     box=page.locator(selector).bounding_box();self.assertGreaterEqual(box['x'],0);self.assertLessEqual(box['x']+box['width'],width+.5)
    self.assertEqual(page.locator('#snippet button').evaluate('e=>getComputedStyle(e).transitionDuration'),'0s')
    columns=page.locator('.cards-trazadas').evaluate('e=>getComputedStyle(e).gridTemplateColumns.split(" ").length')
    self.assertEqual(columns,3 if width>=1024 else 2 if width>=640 else 1)
    self.assertEqual(errors,[])
    if width==390:self.assertEqual(page.locator('#first').bounding_box()['width'],342);page.screenshot(path='/tmp/margen-reference-mobile.png')
    page.close()
  page,_=self.page();page.emulate_media(media='print');self.assertEqual(page.locator('#snippet pre').evaluate('e=>getComputedStyle(e).backdropFilter'),'none');self.assertFalse(page.locator('#snippet button').is_visible())
 def test_components_and_reader_preferences(self):
  recipes=('archive','timeline','animated-callouts','bookshelf','gallery')
  html=build('Patrones editoriales',[{'id':'patterns','titulo':'Patrones editoriales','html':''.join((ROOT/'packages/core/recipes'/name/'example.html').read_text() for name in recipes)}],theme='editorial',mode='dark')
  for width in (300,390,768,1440):
   with self.subTest(width=width):
    page,errors=self.page(width,html=html)
    self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
    styles=page.locator('.publicaciones h4').first.evaluate('e=>[getComputedStyle(e).fontSize,getComputedStyle(e).lineHeight]')
    self.assertEqual(styles,['22.4px','31.36px'])
    self.assertEqual(page.locator('.publicaciones').evaluate('e=>getComputedStyle(e).gridTemplateColumns.split(" ").length'),1)
    self.assertEqual(page.locator('.aviso-esquina > div').first.evaluate('e=>getComputedStyle(e).padding'),'16px')
    track=page.locator('[data-galeria-pista]');self.assertEqual(track.evaluate('e=>getComputedStyle(e).padding'),'12px 0px')
    self.assertEqual(track.evaluate('e=>e.style.getPropertyValue("--galeria-fade-inicio")'),'0px')
    track.evaluate('e=>e.scrollLeft=e.scrollWidth');page.wait_for_timeout(150)
    self.assertEqual(track.evaluate('e=>e.style.getPropertyValue("--galeria-fade-fin")'),'0px')
    track.focus();self.assertEqual(track.evaluate('e=>getComputedStyle(e).maskImage'),'none')
    page.evaluate('document.documentElement.setAttribute("data-lectura-comoda","")')
    self.assertEqual(page.locator('body').evaluate('e=>getComputedStyle(e).fontSize'),'18px')
    self.assertEqual(errors,[]);page.close()
 def test_code_exact_text_and_clipboard_fallback(self):
  import html as html_lib
  sources=['\n\n','x\n','\nconst value = "<script>unsafe()</script>";\n','/* first\nsecond */\nlet n = 2;','a < b && b > c']
  samples=''.join('<figure class="codigo"><pre tabindex="0" aria-label="Código"><code data-lenguaje="javascript">'+html_lib.escape(source)+'</code></pre></figure>' for source in sources)
  samples+='<figure class="codigo"><pre tabindex="0" aria-label="Código"><code data-lenguaje="javascript">const <mark>a = "a\nb"</mark>;<mark>\n</mark>return a;</code></pre></figure>'
  html=build('Texto literal',[{'id':'codes','titulo':'Texto literal','html':samples}])
  page,errors=self.page(html=html)
  for index,source in enumerate(sources):self.assertEqual(page.locator('.hoja .codigo code').nth(index).text_content(),source)
  marked=page.locator('.hoja .codigo code').last
  self.assertEqual(marked.text_content(),'const a = "a\nb";\nreturn a;')
  self.assertEqual(''.join(marked.locator('mark').all_text_contents()),'a = "a\nb"'.replace('\n',''))
  before=page.locator('.hoja .codigo').all_text_contents();page.evaluate('NotaCodigo.init()');self.assertEqual(page.locator('.hoja .codigo').all_text_contents(),before)
  page.evaluate('() => { navigator.clipboard.writeText=()=>Promise.reject(new Error("denied")); }')
  sample=page.locator('.hoja .codigo').nth(2);sample.locator('button').click()
  self.assertEqual(page.evaluate('getSelection().toString()'),sources[2])
  self.assertIn('seleccionado',sample.locator('[role=status]').text_content())
  self.assertEqual(page.locator('.codigo script').count(),0);self.assertEqual(errors,[])
 def test_hosted_reference_upgrade(self):
  sys.path.insert(0,str(ROOT))
  from portal.reader_style import refresh_editorial_reference
  import re
  css=(ROOT/'packages/core/styles/editorial-reference.css').read_text();code=(ROOT/'packages/core/components/code.js').read_text()
  old=re.sub(r'/\* EDITORIAL REFERENCE START \*/.*?/\* EDITORIAL REFERENCE END \*/','',self.html,flags=re.S)
  old=old.replace('--texto: 33rem','--texto: 35rem').replace('--gutter:24px','--gutter:18px')
  old=re.sub(r'(<script data-nota-modulo="packages/core/components/code.js">).*?</script>',r'\1/* stale code runtime */</script>',old,flags=re.S)
  result=refresh_editorial_reference(old,css,code)
  page,errors=self.page(390,html=result);self.assertEqual(page.locator('#first').bounding_box()['width'],342);self.assertEqual(page.locator('#source').text_content(),SOURCE);self.assertEqual(errors,[])
  self.assertIn('stale code runtime',old);self.assertNotIn('stale code runtime',result)
 def test_hosted_upgrade_preserves_browser_document_mode(self):
  sys.path.insert(0,str(ROOT))
  from portal.reader_style import refresh_editorial_reference
  sources=[prefix+body for prefix in ('<!doctype html>','\n<!DOCTYPE html>','<!-- note -->\n<!doctype html>','<!-- <!doctype html> example -->\n<!DOCTYPE html>')
           for body in ('<main class="hoja"><h1>Evidence</h1></main>','<html><head><meta charset="utf-8"><body><main class="hoja"><h1>Evidence</h1></main></body></html>')]
  sources.append('<main class="hoja"><h1>Intentional fragment</h1></main>')
  for source in sources:
   with self.subTest(source=source):
    modes=[]
    updated=refresh_editorial_reference(source,'h1{font-size:50px}','')
    for html in (source,updated):
     page,errors=self.page(html=html);modes.append(page.evaluate('document.compatMode'))
     if html==updated:self.assertEqual(page.locator('h1').evaluate('e=>getComputedStyle(e).fontSize'),'50px')
     self.assertEqual(errors,[]);page.close()
    self.assertEqual(modes[0],modes[1])
    self.assertEqual(modes[1],'BackCompat' if source==sources[-1] else 'CSS1Compat')
 def test_author_owned_and_presentation_boundaries(self):
  import re
  css=(ROOT/'packages/core/styles/artifact.css').read_text()
  old=re.sub(r'/\* EDITORIAL REFERENCE START \*/.*?/\* EDITORIAL REFERENCE END \*/','',css,flags=re.S)
  code=(ROOT/'packages/core/components/code.js').read_text()
  for boundary in ('data-ritmo="propio"','data-presentation'):
   with self.subTest(boundary=boundary):
    content='<main class="hoja" '+boundary+'><h1 '+boundary+'>Own layout</h1><figure class="codigo"><pre style="font:13px/25px monospace;padding:20px"><code data-lenguaje="javascript">const own = 1;</code></pre></figure><div class="cards-trazadas"><a href="#own"><h4>Own card</h4><p>Own text</p></a></div></main>'
    snapshots=[]
    for styles,runtime in ((old,''),(css,code)):
     page,errors=self.page(html='<style>'+styles+'</style>'+content+'<script>'+runtime+'</script>')
     snapshots.append(page.locator('h1,pre,.cards-trazadas>a').evaluate_all('es=>es.map(e=>{const s=getComputedStyle(e);return [s.fontSize,s.lineHeight,s.padding,s.margin,s.backdropFilter,s.width]})'))
     self.assertEqual(page.locator('.codigo-editorial,.codigo-linea').count(),0)
     self.assertEqual(errors,[]);page.close()
    self.assertEqual(snapshots[0],snapshots[1])
  # A heading may opt out on the node itself, not just on an ancestor.
  for styles in (old,css):
   page,_=self.page(html='<style>'+styles+'</style><main class="hoja"><h1 data-ritmo="propio" style="font-size:19px">Owned</h1></main>')
   self.assertEqual(page.locator('h1').evaluate('e=>getComputedStyle(e).fontSize'),'19px');page.close()
 def test_code_blurs_index_at_real_overlap(self):
  html=self.html.replace('Leer con atención','Leer con atención: ejemplos y decisiones con suficiente contexto')
  page,errors=self.page(html=html);offset=page.locator('#snippet pre').bounding_box()['y']-150
  page.evaluate('top=>scrollTo({top,behavior:"instant"})',offset);page.wait_for_timeout(80)
  index=page.locator('.indice').bounding_box();code=page.locator('#snippet pre').bounding_box()
  self.assertGreater(index['x']+index['width'],code['x'])
  self.assertLess(max(index['y'],code['y']),min(index['y']+index['height'],code['y']+code['height']))
  point=[(max(index['x'],code['x'])+min(index['x']+index['width'],code['x']+code['width']))/2,(max(index['y'],code['y'])+min(index['y']+index['height'],code['y']+code['height']))/2]
  self.assertTrue(page.evaluate('([x,y])=>!!document.elementFromPoint(x,y)?.closest("#snippet")',point))
  self.assertTrue(page.locator('.indice a').first.evaluate('(e,box)=>{const range=document.createRange();range.selectNodeContents(e);return [...range.getClientRects()].some(r=>r.right>box.x&&r.bottom>box.y&&r.top<box.y+box.height)}',code))
  page.screenshot(path='/tmp/margen-reference-overlap.png')
  page.locator('.indice a').first.focus()
  self.assertTrue(page.evaluate('([x,y])=>!!document.elementFromPoint(x,y)?.closest(".indice")',point))
  self.assertEqual(errors,[])
 def test_reading_type_frame_air_and_index_width(self):
  # Regressions seen on 2026-10-21: body type stayed 16px/1.65 because a scoped
  # :root selector never matched, and text in open frames touched the strokes.
  frame='<section class="ancho" id="marco-texto"><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,240px),1fr));gap:24px">'+'<div><p class="ceja">Comparación</p><h3>Una idea necesita espacio.</h3><p>El título y el párrafo compiten cuando no hay separación entre bloques de texto.</p></div>'*2+'</div></section>'
  text_gap='''e=>{const l=e.querySelector(':scope > .marco-lineas'),r=l.getBoundingClientRect(),b=getComputedStyle(l,'::before'),a=getComputedStyle(l,'::after');
   const top=r.top+parseFloat(b.top),bottom=r.bottom-parseFloat(b.bottom),left=r.left+parseFloat(a.left),right=r.right-parseFloat(a.right);
   const walk=document.createTreeWalker(e,NodeFilter.SHOW_TEXT),rects=[];for(let n;n=walk.nextNode();){if(!n.data.trim())continue;const range=document.createRange();range.selectNodeContents(n);rects.push(...[...range.getClientRects()].filter(q=>q.width&&q.height));}
   return Math.min(...rects.map(q=>Math.min(q.top-top,bottom-q.bottom,q.left-left,right-q.right)))}'''
  for mode,scheme in (('dark','dark'),('light','light'),('light','dark')):
   html=build('La forma de leer',[{'id':'content','titulo':'La forma de leer','html':CONTENT.replace('<section class="ancho" id="cards">',frame+'<section class="ancho" id="cards">')}],theme='editorial',mode=mode)
   for width in (320,390,1280,1440):
    with self.subTest(mode=mode,scheme=scheme,width=width):
     page,errors=self.page(width,html=html,scheme=scheme)
     self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
     self.assertEqual(page.locator('#first p').evaluate('e=>[getComputedStyle(e).fontSize,getComputedStyle(e).lineHeight]'),['15.5px','24.025px'])
     self.assertGreaterEqual(page.locator('#marco-texto').evaluate(text_gap),15.5)
     self.assertEqual(page.locator('#marco-texto').bounding_box()['width'],min(1024,width-48))
     if width>=1280:
      index=page.locator('.indice').bounding_box();self.assertEqual(index['width'],360 if width==1440 else 328)
      self.assertLessEqual(index['x']+index['width'],page.locator('#first').bounding_box()['x']-24)
     self.assertEqual(errors,[]);page.close()
  page,_=self.page(html=html);page.evaluate('document.documentElement.setAttribute("data-lectura-comoda","")')
  self.assertEqual(page.locator('#first p').evaluate('e=>getComputedStyle(e).fontSize'),'18px')
  # Reader-selected styles stay independent of the measured body type.
  body='e=>[getComputedStyle(e).fontSize,getComputedStyle(e).lineHeight]'
  for comfortable in (False,True):
   for style,expected in (('editorial',['15.5px','24.025px']),('sobrio',['15.5px','24.025px']),('tecnico',['15.5px','24.025px']),('libro',['16px','28.8px']),('revista',['16px','28.8px']),('bitacora',['16px','28.8px'])):
    with self.subTest(style=style,comfortable=comfortable):
     page.evaluate('([s,c])=>{const r=document.documentElement;r.dataset.estilo=s;r.toggleAttribute("data-lectura-comoda",c)}',[style,comfortable])
     want=(['18px','32.4px'] if style in ('libro','revista','bitacora') else ['18px','30.6px']) if comfortable else expected
     self.assertEqual(page.locator('#first p').evaluate(body),want)
 def test_code_blur_is_rendered_over_index(self):
  # Computed blur is not enough: the index must contribute blurred pixels behind code.
  html=self.html.replace('Leer con atención','Leer con atención: ejemplos y decisiones con suficiente contexto')
  page,errors=self.page(html=html);offset=page.locator('#snippet pre').bounding_box()['y']-150
  # Read/active index items change colour over 320 ms (measured reference easing);
  # compare the settled frame, not one captured mid-transition.
  page.evaluate('top=>scrollTo({top,behavior:"instant"})',offset);page.wait_for_timeout(400);page.mouse.move(1300,980)
  index=page.locator('.indice').bounding_box();code=page.locator('#snippet pre').bounding_box()
  clip={'x':code['x']+1,'y':code['y']+1,'width':index['x']+index['width']-code['x']-2,'height':code['height']-2}
  self.assertGreater(clip['width'],40)
  blurred=page.screenshot(clip=clip)
  page.locator('#snippet pre').evaluate('e=>e.style.backdropFilter="none"');sharp=page.screenshot(clip=clip)
  page.locator('#snippet pre').evaluate('e=>e.style.backdropFilter=""');page.locator('.indice').evaluate('e=>e.style.visibility="hidden"')
  hidden=page.screenshot(clip=clip)
  # PNG bytes differ from capture noise alone; decode and require real pixel change.
  changed='''async([a,b])=>{const px=async s=>{const i=await createImageBitmap(await (await fetch('data:image/png;base64,'+s)).blob()),c=new OffscreenCanvas(i.width,i.height),x=c.getContext('2d');x.drawImage(i,0,0);return x.getImageData(0,0,i.width,i.height).data};
   const [p,q]=await Promise.all([px(a),px(b)]);let n=0;for(let i=0;i<p.length;i+=4)if(Math.max(Math.abs(p[i]-q[i]),Math.abs(p[i+1]-q[i+1]),Math.abs(p[i+2]-q[i+2]))>8)n++;return n/(p.length/4)}'''
  encode=lambda png:base64.b64encode(png).decode()
  self.assertGreaterEqual(page.evaluate(changed,[encode(blurred),encode(sharp)]),.05)
  self.assertGreaterEqual(page.evaluate(changed,[encode(blurred),encode(hidden)]),.05)
  page.locator('.indice').evaluate('e=>e.style.visibility=""');self.assertLess(page.evaluate(changed,[encode(blurred),encode(page.screenshot(clip=clip))]),.01)
  self.assertEqual(errors,[])
 def test_line_numbers_stay_one_per_line(self):
  # Regression seen on 2026-10-21: inside a reading section (overflow-wrap:anywhere)
  # an author pre with inline white-space:pre-wrap let the 16px number gutter wrap,
  # so 10+ broke into stacked, overlapping digits. One readable number per line.
  import html as html_lib
  long_line='const resumen = "'+'palabra '*40+'";'
  big='\n'.join('' if n%7==0 else long_line if n in (50,999) else f'let fila{n} = {n};' for n in range(1,1001))
  mid='\n'.join(f'• regla {n}' for n in range(1,121))
  short='a = 1\n\nb = 2'
  def block(id,source,pre='',code=''):return f'<figure class="codigo" id="{id}"><pre tabindex="0" aria-label="Código"{pre}><code data-lenguaje="javascript"{code}>{html_lib.escape(source)}</code></pre></figure>'
  content=(block('mil',big)+'<section>'+block('envuelto',mid,pre=' style="white-space:pre-wrap;max-height:34rem;overflow:auto"')+'</section>'+block('corto',short,code=' data-destacar="1"')
   +block('sin',short,code=' data-sin-lineas')+'<figure class="codigo" id="marcas"><pre tabindex="0" aria-label="Código"><code data-lenguaje="javascript">let <mark>a</mark> = 1;</code></pre></figure>')
  check='''e=>{const ls=[...e.querySelectorAll('.codigo-linea')],out=[];for(const n of [1,2,9,10,99,100,120,999,1000]){const l=ls[n-1];if(!l)continue;
    const b=getComputedStyle(l,'::before'),s=getComputedStyle(l),probe=document.createElement('span');probe.style.cssText='position:absolute;visibility:hidden;white-space:pre';probe.textContent=l.dataset.numero;l.append(probe);
    out.push({n,number:l.dataset.numero,height:parseFloat(b.height),row:parseFloat(s.lineHeight),text:probe.getBoundingClientRect().width,width:parseFloat(b.width),end:parseFloat(b.left)+parseFloat(b.width),start:parseFloat(s.paddingLeft),color:b.color});probe.remove();}
   return out}'''
  def luminance(color):
   r,g,b=[int(v)/255 for v in color[color.index('(')+1:color.index(')')].split(',')[:3]]
   return sum(k*(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4) for k,c in zip((.2126,.7152,.0722),(r,g,b)))
  for theme,mode in (('editorial','light'),('editorial','dark'),('catabum','light'),('catabum','dark')):
   html=build('Numeración',[{'id':'lineas','titulo':'Numeración','html':content}],theme=theme,mode=mode)
   for width in (320,390,1440):
    for media in ('screen','print'):
     with self.subTest(theme=theme,mode=mode,width=width,media=media):
      page,errors=self.page(width,html=html,scheme=mode);page.emulate_media(media=media)
      self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
      for id,source,total in (('mil',big,1000),('envuelto',mid,120),('corto',short,3)):
       code=page.locator(f'#{id} code');self.assertEqual(code.text_content(),source)
       self.assertEqual(code.locator('.codigo-linea').count(),total)
       for line in code.evaluate(check):
        self.assertEqual(line['number'],str(line['n']))
        self.assertAlmostEqual(line['height'],line['row'],delta=.5,msg=line)
        self.assertLessEqual(line['text'],line['width']+.5,line)
        self.assertLessEqual(line['end']+8,line['start'],line)
       if media=='screen':
        paper=page.evaluate('getComputedStyle(document.body).backgroundColor');ink=code.evaluate(check)[0]['color']
        light,dark=sorted((luminance(paper),luminance(ink)),reverse=True);self.assertGreaterEqual((light+.05)/(dark+.05),4.5,(paper,ink))
      if media=='screen':
       pre=page.locator('#mil pre');self.assertGreater(pre.evaluate('e=>e.scrollWidth-e.clientWidth'),0)
       self.assertEqual(page.locator('#sin .codigo-linea').count(),0);self.assertEqual(page.locator('#sin code').text_content(),short)
       self.assertEqual(page.locator('#marcas mark').text_content(),'a')
       self.assertEqual(page.locator('#corto .codigo-linea.destacada').count(),1)
       if width==390 and theme=='catabum':page.locator('#envuelto pre').evaluate('e=>e.scrollTop=e.scrollHeight');page.screenshot(path=f'/tmp/margen-line-numbers-{mode}.png',full_page=False)
      self.assertEqual(errors,[]);page.close()
  page,_=self.page(html=html);page.locator('#envuelto button').click();self.assertEqual(page.evaluate('navigator.clipboard.readText()'),mid)
  page.locator('#envuelto code').evaluate('e=>{const r=document.createRange();r.selectNodeContents(e);getSelection().removeAllRanges();getSelection().addRange(r)}')
  self.assertEqual(page.evaluate('getSelection().toString()'),mid)
  # Hosted upgrade replaces only the reference layer and code runtime; an old
  # embedded base gutter must not bring the wrapping back.
  import re
  sys.path.insert(0,str(ROOT))
  from portal.reader_style import refresh_editorial_reference
  old=re.sub(r'/\* EDITORIAL REFERENCE START \*/.*?/\* EDITORIAL REFERENCE END \*/','',html,flags=re.S)
  old=re.sub(r'\.codigo-linea::before \{[^}]*\}','.codigo-linea::before { content:attr(data-numero); position:absolute; left:12px; width:24px; text-align:right; color:var(--tinta-2); font:inherit; }',old,count=1)
  old=re.sub(r'(<script data-nota-modulo="packages/core/components/code.js">).*?</script>',r'\1/* stale code runtime */</script>',old,flags=re.S)
  css=(ROOT/'packages/core/styles/editorial-reference.css').read_text();runtime=(ROOT/'packages/core/components/code.js').read_text()
  page,errors=self.page(390,html=refresh_editorial_reference(old,css,runtime))
  for line in page.locator('#envuelto code').evaluate(check):
   self.assertAlmostEqual(line['height'],line['row'],delta=.5,msg=line);self.assertLessEqual(line['text'],line['width']+.5,line)
  self.assertEqual(errors,[])
 def test_no_script(self):
  page,_=self.page(js=False);self.assertEqual(page.locator('#source').text_content(),SOURCE);self.assertTrue(page.locator('#snippet .cab > span').first.is_visible())
if __name__=='__main__':unittest.main()
