"""Guardar y «Me gusta» en Chromium real: ancla bajo «En esta página», teclado, guardados y frontera del iframe.

Sin red ni servidor: Playwright enruta https://portal.test al FastAPI real (TestClient) con el módulo montado.
La página anfitriona replica sólo el cableado que la raíz añade a app.js (op «reader-actions-anchor»).
"""
import sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from fastapi.testclient import TestClient
from portal.app import COOKIE
from portal.test_reader_actions import mounted,ORIGIN
from contract_artifact import build

PAGES=[{'id':'informe','titulo':'Informe','html':''.join(f'<section class="prosa" id="s{i}"><h2>Sección {i}</h2>'+'<p>Texto de lectura.</p>'*12+'</section>' for i in range(1,4))}]
DECK=[{'id':'uno','titulo':'Uno','html':'<p>Primera.</p>'},{'id':'dos','titulo':'Dos','html':'<p>Segunda.</p>'}]
HOST='''<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Lector</title>
<link rel="stylesheet" href="/static/reader-actions.css"><style>body{margin:0}#artifact-frame{display:block;width:100vw;height:100vh;border:0}.reader-dock{position:fixed;right:22px;bottom:22px;display:flex;gap:8px}</style></head>
<body><section id="reader"><div id="reader-dock" class="reader-dock"></div><iframe id="artifact-frame" sandbox="allow-scripts allow-downloads" title="Artefacto"></iframe></section>
<script src="/static/reader-actions.js"></script><script>
const aid=location.pathname.split('/').pop(),frame=document.getElementById('artifact-frame');
const actions=MargenReaderActions.create({frame:()=>frame,dock:()=>document.getElementById('reader-dock')});
addEventListener('message',e=>{if(e.source!==frame.contentWindow||e.origin!=='null'||e.data?.bottifact!==1)return;if(e.data.op==='reader-actions-anchor')actions.anchor(e.data.data);});
frame.src='/api/artifacts/'+aid+'/render';actions.load({id:aid,title:document.title=TITLE});
</script></body></html>'''
SAVED='''<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Guardados</title><link rel="stylesheet" href="/static/reader-actions.css"></head>
<body><main id="saved"></main><script src="/static/reader-actions.js"></script><script>MargenReaderActions.renderSaved(document.getElementById('saved')).then(()=>document.querySelector('.reader-saved-heading')?.focus());</script></body></html>'''


class ReaderActionsRuntime(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from playwright.sync_api import sync_playwright
  cls.tmp=tempfile.TemporaryDirectory();cls.app=mounted(cls.tmp.name);store=cls.app.state.store
  def client(email):
   c=TestClient(cls.app,base_url=ORIGIN,headers={'Origin':ORIGIN});c.cookies.set(COOKIE,store.session(store.user(email,email.split('@')[0])['id']));return c
  cls.author=client('author@example.com');cls.reader=client('reader@example.com')
  def publish(title,html):
   aid=cls.author.post('/api/artifacts',json={'title':title,'html':html}).json()['id']
   cls.author.put('/api/artifacts/'+aid+'/access',json={'visibility':'invited','grants':[{'email':'reader@example.com','role':'viewer'}]})
   return aid
  cls.doc=publish('Informe trimestral',build('Informe trimestral',PAGES,reactions=True))
  cls.deck=publish('Presentación',build('Presentación',DECK,format='presentation'))
  cls.titles={cls.doc:'Informe trimestral',cls.deck:'Presentación'}
  shipped=(ROOT/'portal/static/editorial-pieces.js').read_text();source=(ROOT/'packages/core/components/editorial-pieces.js').read_text()
  cls.requests=[]
  def route(r):
   url=r.request.url;path=url[len(ORIGIN):]
   if path.startswith('/static/reader-actions.'):
    name=path.split('/')[-1];return r.fulfill(body=(ROOT/'portal/static'/name).read_text(),content_type='text/css' if name.endswith('.css') else 'text/javascript')
   if path.startswith('/a/'):return r.fulfill(body=HOST.replace('TITLE',repr(cls.titles.get(path[3:],''))),content_type='text/html')
   if path.startswith('/?view=saved'):return r.fulfill(body=SAVED,content_type='text/html')
   headers={k:v for k,v in r.request.all_headers().items() if k.lower() in ('cookie','origin','content-type','x-margen-reader-action')}
   cls.requests.append((r.request.method,path))
   bare=TestClient(cls.app,base_url=ORIGIN)
   res=bare.request(r.request.method,path,headers=headers,content=r.request.post_data_buffer)
   body=res.content
   # La raíz aún no reconstruye portal/static; el render usa la fuente nueva de editorial-pieces.
   if path.endswith('/render'):body=res.text.replace(shipped,source).encode()
   r.fulfill(status=res.status_code,body=body,headers={k:v for k,v in res.headers.items() if k.lower() in ('content-type','content-security-policy')})
  cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch()
  cls.context=cls.browser.new_context(viewport={'width':1280,'height':800})
  cls.context.add_cookies([{'name':COOKIE,'value':cls.reader.cookies.get(COOKIE),'url':ORIGIN,'secure':True,'httpOnly':True,'sameSite':'Lax'}])
  cls.context.route(ORIGIN+'/**',route)

 @classmethod
 def tearDownClass(cls):
  cls.browser.close();cls.pw.stop();cls.tmp.cleanup()

 def puts(self):return [p for m,p in self.requests if m=='PUT']

 def open(self,aid):
  page=self.context.new_page();page.goto(ORIGIN+'/a/'+aid);return page

 def state(self,aid):return self.reader.get('/api/artifacts/'+aid+'/reader-actions').json()

 def test_icon_actions_follow_all_index_links_and_keyboard_saves_to_a_useful_list(self):
  page=self.open(self.doc);overlay=page.locator('.reader-actions-anchor')
  overlay.wait_for(state='visible',timeout=5000)
  frame=page.frame_locator('#artifact-frame')
  links=frame.locator('.indice > ol').bounding_box();slot=frame.locator('.indice > [data-acciones-lector]').bounding_box();box=overlay.bounding_box()
  self.assertGreaterEqual(slot['y']-(links['y']+links['height']),15)
  self.assertEqual(overlay.locator('button svg').count(),2)
  self.assertEqual(overlay.locator('[data-action=liked] .reader-action-caption').text_content(),'0')
  self.assertEqual(overlay.locator('[data-action=saved]').evaluate('e=>getComputedStyle(e).borderTopWidth'),'0px')
  self.assertLessEqual(abs(box['y']-slot['y']),1);self.assertLessEqual(abs(box['x']-slot['x']),1)
  # Las reacciones locales del pie no se duplican con el «Me gusta» de la cuenta.
  self.assertTrue(frame.locator('[data-reacciones]').evaluate('n=>n.hidden'))
  for _ in range(8):
   page.keyboard.press('Tab')
   if page.evaluate('document.activeElement?.closest(".reader-actions-anchor")&&document.activeElement.dataset.action')=='saved':break
  else:self.fail('El ancla «Guardar» no se alcanza con Tab.')
  page.keyboard.press('Enter')
  dialog=page.locator('dialog.reader-actions-dialog[open]');dialog.wait_for()
  self.assertEqual(dialog.locator('.reader-actions-title').text_content(),'Informe trimestral')
  self.assertEqual(page.evaluate('document.activeElement.getAttribute("aria-label")'),'Cerrar')
  self.assertTrue(dialog.locator('[data-action=saved]').is_disabled())
  self.assertEqual(self.puts(),[])
  page.wait_for_timeout(700)
  page.keyboard.press('Tab');self.assertEqual(page.evaluate('document.activeElement.dataset.action'),'saved')
  page.keyboard.press('Enter')
  dialog.locator('.reader-actions-status',has_text='Guardado en tu lista.').wait_for()
  self.assertTrue(self.state(self.doc)['saved'])
  page.keyboard.press('Tab');page.keyboard.press('Tab')
  self.assertEqual(page.evaluate('document.activeElement.textContent'),'Ver mis guardados')
  page.keyboard.press('Enter');page.wait_for_url(ORIGIN+'/?view=saved')
  link=page.locator('.reader-saved-list a',has_text='Informe trimestral');link.wait_for()
  self.assertEqual(link.get_attribute('href'),'/a/'+self.doc)
  link.focus();page.keyboard.press('Enter');page.wait_for_url(ORIGIN+'/a/'+self.doc)
  page.locator('.reader-actions-anchor [data-action=saved]',has_text='Guardado').wait_for(state='visible')
  self.reader.put('/api/artifacts/'+self.doc+'/reader-actions',json={'saved':False},headers={'X-Margen-Reader-Action':'1'})
  page.close()

 def test_a_thin_figure_edge_never_overlays_the_icon_targets(self):
  page=self.open(self.doc);overlay=page.locator('.reader-actions-anchor');overlay.wait_for(state='visible')
  frame=page.frame_locator('#artifact-frame')
  for edge in ('top','bottom'):
   frame.locator('[data-acciones-lector]').evaluate('''(slot,edge)=>{const r=slot.getBoundingClientRect(),cover=document.createElement('div');cover.id='edge-cover';Object.assign(cover.style,{position:'fixed',left:r.left+'px',top:(edge==='top'?r.top:r.bottom-4)+'px',width:r.width+'px',height:'4px',background:'red',zIndex:'99999'});document.body.append(cover);dispatchEvent(new Event('scroll'));}''',edge)
   overlay.wait_for(state='hidden')
   frame.locator('#edge-cover').evaluate('e=>{e.remove();dispatchEvent(new Event("scroll"));}')
   overlay.wait_for(state='visible')
  page.close()

 def test_forged_messages_and_held_keys_never_mutate(self):
  page=self.open(self.doc);page.locator('.reader-actions-anchor').wait_for(state='visible',timeout=5000)
  before=len(self.puts())
  page.frame_locator('#artifact-frame').locator('body').evaluate('''()=>{for(const data of [{saved:true},{visible:true,x:0,y:0,width:900,height:44,vw:1280,vh:800,liked:true}])parent.postMessage({bottifact:1,id:'f',op:'reader-actions-anchor',data},'*');
   for(const op of ['reader-actions','save','like'])parent.postMessage({bottifact:1,id:'g',op,data:{saved:true,liked:true}},'*');}''')
  page.wait_for_timeout(300)
  self.assertEqual(len(self.puts()),before)
  page.locator('.reader-actions-anchor [data-action=liked]').focus()
  page.keyboard.down('Enter');page.keyboard.down('Enter');page.keyboard.down('Enter');page.keyboard.up('Enter')
  page.locator('dialog.reader-actions-dialog[open]').wait_for()
  page.wait_for_timeout(800);page.keyboard.press('Escape')
  self.assertEqual(len(self.puts()),before)
  self.assertFalse(self.state(self.doc)['liked'])
  page.close()

 def test_presentation_uses_the_host_dock_without_article_footer(self):
  page=self.open(self.deck);dock=page.locator('.reader-actions-dock');dock.wait_for(state='visible',timeout=5000)
  self.assertTrue(page.locator('.reader-actions-anchor').is_hidden())
  self.assertEqual(page.frame_locator('#artifact-frame').locator('main footer, [data-acciones-lector]').count(),0)
  like=dock.locator('[data-action=liked]');like.click()
  page.wait_for_function('document.querySelector(".reader-actions-dock [data-action=liked]").getAttribute("aria-pressed")==="true"')
  self.assertEqual(self.state(self.deck)['likes'],1)
  like.focus();page.keyboard.press('Enter')
  page.wait_for_function('document.querySelector(".reader-actions-dock [data-action=liked]").getAttribute("aria-pressed")==="false"')
  self.assertEqual(self.state(self.deck)['likes'],0)
  page.close()

 def test_standalone_file_has_no_slot_and_keeps_local_reactions(self):
  page=self.context.new_page();page.set_content(build('Informe trimestral',PAGES,reactions=True));page.wait_for_timeout(200)
  self.assertEqual(page.locator('[data-acciones-lector]').count(),0)
  self.assertTrue(page.locator('[data-reacciones]').is_visible())
  self.assertIn('No hay conteos compartidos',page.locator('[data-reacciones]').text_content())
  page.close()


if __name__=='__main__':unittest.main()
