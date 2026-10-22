"""Regresiones de composición y omisiones reales; no instala dependencias."""
import json,unittest,re
from contract_artifact import build,validate,composition_warnings,Document,ROOT,recipe,THREE
class ContractTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.pages=[{'id':'inicio','titulo':'Inicio','html':'<section id="evidencia"><h2>Evidencia</h2><p>Una observación.</p></section>'}]
  cls.html=build('Informe',cls.pages)
 def test_single_and_multi(self):
  self.assertEqual(validate(self.html),[])
  multi=build('Informe',self.pages+[{'id':'detalle','titulo':'Detalle','html':recipe('barras')}])
  self.assertEqual(validate(multi),[]);self.assertIn('data-nota-sin-js',multi)
  self.assertIn('data-nota-modulo="packages/core/components/charts.js"',multi);self.assertIn('href="#evidencia"',multi)
 def test_missing_controls_fail(self):
  for attr in ['data-apariencia-menu','data-revision','data-audio-prueba','data-audio-volumen','data-buscar-tema','data-familia-tema','data-temas-resultados']:
   with self.subTest(attr=attr):self.assertTrue(validate(re.sub(' '+attr+r'(?=[\s>])', ' data-ausente',self.html,count=1)))
 def test_new_reading_styles_and_sound_default(self):
  for style in ['libro','revista','bitacora']:
   with self.subTest(style=style):self.assertEqual(validate(build('Lectura',self.pages,style=style)),[])
  self.assertTrue(validate(self.html.replace('data-audio-global aria-pressed="true"','data-audio-global aria-pressed="false"')))
  self.assertTrue(validate(self.html.replace('data-preferencia-tab="sonido"','data-preferencia-tab="otro"')))
 def test_stale_sources_and_missing_module(self):
  self.assertTrue(validate(self.html.replace('data-nota-modulo="packages/core/components/review.js"','data-no-modulo="packages/core/components/review.js"')))
  self.assertTrue(validate(self.html.replace('/* Sonido central:', '/* Versión anterior:')))
 def test_each_chapter_needs_its_index(self):
  multi=build('Informe',self.pages+[{'id':'detalle','titulo':'Detalle','html':'<section id="dato"><h2>El dato</h2></section>'}])
  broken=re.sub(r'(<article class="pagina"[^>]*>.*?)(<nav class="indice".*?</nav>)',r'\1',multi,count=1,flags=re.S)
  self.assertNotEqual(multi,broken);self.assertTrue(validate(broken))
 def test_refs_and_grid(self):
  for html in ['<section><h2>Sin ID</h2></section>','<section id="x"><h2>Figura</h2><figure class="ancho">Atrapada</figure></section>','<p id="x">Uno</p><p id="x">Dos</p>','<a href="#fantasma">Ir</a>','<section data-actividad data-actividad-tabla="ausente"></section>']:
   with self.subTest(html=html),self.assertRaises(ValueError):build('Mal',[{**self.pages[0],'html':html}])
 def test_family_and_mode(self):
  from themes import DATA,normalize
  for family in DATA['familias']:
   for mode in ['light','dark','system']:
    with self.subTest(family=family['id'],mode=mode):
     html=build('Tema',self.pages,theme=family['id'],mode=mode)
     self.assertEqual(validate(html),[])
     self.assertIn('name="nota-modo-inicial" content="'+mode+'"',html)
  self.assertEqual(normalize('linear-dark'),('linear','dark'))
  self.assertEqual(normalize('liftit','system'),('liftit','system'))
  with self.assertRaises(ValueError):build('Inválido',self.pages,mode='sepia')
  self.assertTrue(validate(self.html.replace('data-elegir-modo','data-modo-ausente')))
 def test_registry_can_be_composed(self):
  items=json.loads((ROOT/'packages/core/registry/registry.json').read_text())['componentes']
  for item in items:
   if item['id'] in {'apariencia','revision'}:continue # La base los incorpora una sola vez.
   html=item['html']+(recipe('archivo') if item['id']=='configuracion' else '')
   with self.subTest(recipe=item['id']):
    result=build(item['nombre'],[{**self.pages[0],'html':html}]);self.assertEqual(validate(result),[])
    # Three is requested by the 3D module when shown, never as a render-blocking tag.
    if THREE in item['dependencias']:self.assertEqual(result.count('<script src="'+THREE+'">'),0);self.assertIn("src='"+THREE+"'",result)
 def test_custom_prose_guidance_and_wide_article(self):
  source='<section class="business-summary" id="summary"><h2>Summary</h2><p>Evidence.</p></section>'
  render=lambda content:build('Report',[{'id':'start','titulo':'Start','html':content}])
  self.assertEqual(len(composition_warnings(render(source))),1)
  for content in [source.replace('business-summary','business-summary prosa'), source.replace('id="summary"','data-ritmo="propio" id="summary"'), source.replace('business-summary','seccion')]:
   self.assertEqual(composition_warnings(render(content)),[])
  self.assertEqual(composition_warnings(build('Deck',[{'id':'start','titulo':'Start','html':source}],format='presentation')),[])
  for attrs in ['data-ritmo="propio"','style="display:block"']:
   with self.assertRaises(ValueError):render('<article '+attrs+'><figure class="ancho"><p>Trapped.</p></figure></article>')
  self.assertEqual(validate(render('<article><section id="summary"><h2>Summary</h2><p>Evidence.</p></section><figure class="ancho"><p>Wide evidence.</p></figure></article>')),[])
 def test_brand_identity_is_independent_of_palette(self):
  from brands import BRANDS
  import base64,hashlib,xml.etree.ElementTree as ET
  for key,brand in BRANDS.items():
   with self.subTest(brand=key):
    source=(ROOT/brand['logo']).read_bytes()
    self.assertEqual(hashlib.sha256(source).hexdigest(),brand['sha256_logo'])
    ET.fromstring(source)
    for palette,override in [(key,None),('blueprint',key)]:
     html=build('Identidad',self.pages,theme=palette,marca=override)
     doc=Document(html)
     self.assertEqual(len([n for n in doc.live if n.attrs.get('data-marca')==key]),1)
     imgs=[n for n in doc.live if 'marca-logo' in n.classes]
     self.assertEqual(len(imgs),2)
     for img in imgs:
      prefix,data=img.attrs['src'].split(',',1)
      self.assertEqual(prefix,'data:image/svg+xml;base64')
      svg=ET.fromstring(base64.b64decode(data))
      self.assertTrue(svg.tag.endswith('svg'))
      for element in svg.iter():
       self.assertNotIn(element.tag.rsplit('}',1)[-1],['script','foreignObject'])
       self.assertFalse(any(k.lower().startswith('on') or k.rsplit('}',1)[-1]=='href' for k in element.attrib))
     self.assertEqual(validate(html),[])
    neutral=Document(build('Genérico',self.pages,theme=key,marca='bottifact'))
    self.assertFalse(any('data-marca' in n.attrs for n in neutral.live))
  with self.assertRaises(ValueError):build('Inválido',self.pages,marca='inventada')
if __name__=='__main__':unittest.main()
