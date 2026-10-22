"""Pie del autor opcional, crédito de plataforma opt-in y presentaciones sin pie de artículo. Sin navegador."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from contract_artifact import build,footer_options

PAGE=[{'id':'a','titulo':'A','html':'<section class="prosa" id="uno"><h2>Uno</h2><p>x</p></section><section class="prosa" id="dos"><h2>Dos</h2><p>y</p></section>'}]
DECK=PAGE+[{'id':'b','titulo':'B','html':'<p>z</p>'}]
main=lambda html:html.split('<main',1)[1].split('</main>',1)[0]

class FooterContract(unittest.TestCase):
 def test_absent_footer_renders_nothing(self):
  body=main(build('Doc',PAGE))
  self.assertNotIn('<footer',body);self.assertNotIn('Hecho con Margen',body);self.assertIn('class="indice"',body)

 def test_platform_credit_is_opt_in(self):
  self.assertFalse(footer_options({'author':'Ana'})['platform'])
  self.assertNotIn('Hecho con Margen',build('Doc',PAGE,footer={'author':'Ana'}))
  self.assertIn('<p class="pie-plataforma">Hecho con Margen</p>',build('Doc',PAGE,footer={'author':'Ana','platform':True}))
  only=main(build('Doc',PAGE,footer={'platform':True}))
  self.assertIn('<footer class="pie pie-documento"><p class="pie-plataforma">Hecho con Margen</p></footer>',only)
  for bad in ({},{'platform':False},{'author':''}):
   with self.subTest(footer=bad),self.assertRaises(ValueError):footer_options(bad)

 def test_local_reactions_without_footer_do_not_invent_one(self):
  body=main(build('Doc',PAGE,reactions=True))
  self.assertIn('data-reacciones',body);self.assertIn('solo en este navegador',body);self.assertNotIn('<footer',body)
  self.assertNotRegex(body.split('data-reacciones',1)[1],r'sincroniza|cuenta|servidor')

 def test_presentations_get_no_article_footer(self):
  self.assertNotIn('<footer',main(build('Deck',DECK,format='presentation')))
  for extra in ({'footer':{'author':'Ana'}},{'reactions':True}):
   with self.subTest(**extra),self.assertRaises(ValueError):build('Deck',DECK,format='presentation',**extra)

 def test_chapters_keep_author_footer_once(self):
  html=main(build('Libro',DECK,format='chapters',footer={'author':'Ana','note':'Notas.'}))
  self.assertEqual(html.count('<footer class="pie pie-documento">'),1);self.assertNotIn('Hecho con Margen',html)

if __name__=='__main__':unittest.main()
