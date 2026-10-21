#!/usr/bin/env python3
"""Synthetic browser checks. Requires Playwright 1.58 + Chromium; no account/data.
SPEECH_HEADED=1 uses a visible browser. SPEECH_REAL=1 adds an actual device-voice
smoke test (audible); it skips explicitly if the device has no voices.
"""
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
import sys
import threading
import time
import tempfile
import unittest
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from contract_artifact import build
CONTENT=(ROOT/'examples/content/reader-speech.html').read_text()
STUB='''window.spoken=[];const engine=new EventTarget();Object.assign(engine,{getVoices:()=>[{name:'Voz de prueba',lang:'es',voiceURI:'test',localService:true}],speak(u){spoken.push(u);u.onstart?.();},cancel(){window.cancelled=(window.cancelled||0)+1},pause(){window.paused=true},resume(){window.paused=false}});Object.defineProperty(window,'speechSynthesis',{value:engine});window.SpeechSynthesisUtterance=class {constructor(text){this.text=text}};'''
CSP="sandbox allow-scripts allow-downloads; default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; media-src data:; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'"

def fixture(legacy=False,hosted=False,real=False,chapters=False):
    if legacy:
        html='<!doctype html><html lang="es"><head><title>Documento sintético antiguo</title></head><body><main>'+CONTENT+'</main></body></html>'
    else:
        pages=[{'id':'documento','titulo':'Documento','html':CONTENT}]
        if chapters:pages.append({'id':'chapter-two','titulo':'Segundo capítulo','html':'<section id=chapter-final><h2>Capítulo final</h2><p>Texto del segundo capítulo.</p></section>'})
        html=build('Lector de voz · Ejemplo sintético',pages,document_id='speech-synthetic',theme='kaira',mode='light')
    scripts=''
    if not real:scripts+='<script>'+STUB+'</script>'
    if hosted:
        scripts+='<script>'+''.join((ROOT/'portal/static'/name).read_text()+'\n' for name in ['bridge.js','reader-speech.js','reader-controls.js'])+'</script>'
    return html.replace('<head>','<head>'+scripts,1) if '<head>' in html else '<!doctype html><html lang="es"><head>'+scripts+'</head><body>'+html+'</body></html>'

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        frame=self.path.startswith('/frame')
        if self.path.startswith('/host'):
            mode='legacy' if 'legacy' in self.path else 'modern'
            real='&real' if 'real' in self.path else ''
            html='''<!doctype html><style>body{margin:0}iframe{display:block;border:0;width:100%;height:100vh}</style><iframe sandbox="allow-scripts allow-downloads" src="/frame?'''+mode+real+'''"></iframe><script>
            window.addEventListener('message',e=>{if(e.source!==document.querySelector('iframe').contentWindow||e.origin!=='null'||e.data?.bottifact!==1)return;const {id,op}=e.data;window.operations=(window.operations||[]).concat(op);const snapshot={author:'Persona de ejemplo',verified:true,permissions:{comment:true,review:true},events:[],reader:{preferences:{},manage:false}};e.source.postMessage({bottifact:1,id,data:op==='ready'?snapshot:{ok:true}},'*');});</script>'''
        else:html=fixture(legacy='legacy' in self.path,hosted=frame,real='real' in self.path,chapters='chapters' in self.path)
        self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8')
        if frame:self.send_header('Content-Security-Policy',CSP)
        self.end_headers();self.wfile.write(html.encode())

class ReaderSpeech(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        threading.Thread(target=cls.server.serve_forever,daemon=True).start()
        cls.url=f'http://127.0.0.1:{cls.server.server_port}'
        cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch(headless=not os.getenv('SPEECH_HEADED'))
    @classmethod
    def tearDownClass(cls):cls.browser.close();cls.pw.stop();cls.server.shutdown();cls.server.server_close()
    def open(self,path='/',width=1280):
        page=self.browser.new_page(viewport={'width':width,'height':900},reduced_motion='reduce')
        page.goto(self.url+path)
        frame=page.frames[1] if path.startswith('/host') else page
        frame.locator('[data-speech-tool]').wait_for()
        self.addCleanup(page.close)
        return page,frame
    def wait_expr(self,f,expression,timeout=15):
        # Playwright wait_for_function uses eval, intentionally disallowed by hosted CSP.
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            if f.evaluate(expression):return
            time.sleep(.1)
        self.fail('Browser condition timed out: '+expression)
    def listen(self,f):
        f.locator('[data-speech-tool] summary').click();f.get_by_role('button',name='Escuchar documento completo',exact=True).click()
    def test_geometry_themes_mobile_and_keyboard(self):
        for width in (320,390,1280):
            for dark in (False,True):
                with self.subTest(width=width,dark=dark):
                    p,f=self.open(width=width)
                    if dark:f.evaluate("document.documentElement.dataset.theme='kaira-dark';document.documentElement.style.colorScheme='dark'")
                    before=f.locator('#first').bounding_box();self.listen(f)
                    self.assertEqual(f.locator('#first').bounding_box(),before)
                    self.assertEqual(f.locator('[data-speech-current]').count(),1)
                    self.assertFalse(f.evaluate('document.documentElement.scrollWidth>innerWidth'))
                    box=f.locator('.bottifact-toolbar').bounding_box();self.assertGreaterEqual(box['x'],0);self.assertLessEqual(box['x']+box['width'],width)
                    player=f.locator('.bf-speech-player').bounding_box();self.assertGreaterEqual(player['x'],0);self.assertLessEqual(player['x']+player['width'],width)
                    f.get_by_role('button',name='Pausar',exact=True).focus();p.keyboard.press('Enter');self.assertTrue(f.evaluate('paused'))
                    f.get_by_role('button',name='Reanudar',exact=True).click();self.assertFalse(f.evaluate('paused'))
                    f.get_by_role('button',name='Detener',exact=True).click();self.assertEqual(f.locator('[data-speech-current]').count(),0)
                    if dark:f.get_by_text('Velocidad y voz',exact=True).click()
                    target=ROOT/'tests/screenshots'/f'speech-{width}-{"dark" if dark else "light"}.png';target.parent.mkdir(exist_ok=True)
                    p.screenshot(path=str(target))
    def test_standalone_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'reader.html';path.write_text(fixture())
            p=self.browser.new_page();self.addCleanup(p.close);p.goto(path.as_uri())
            self.listen(p);self.assertEqual(p.evaluate('spoken.length'),1)
            self.assertTrue(p.evaluate('!window.BottifactReviewBridge'))
            p.get_by_role('button',name='Detener',exact=True).click();self.assertEqual(p.evaluate('cancelled'),1)
    def test_complete_reading_advances_chapters_and_manual_navigation_stops(self):
        p,f=self.open('/chapters');self.listen(f)
        f.evaluate("for(let i=0;i<80 && !spoken.at(-1).text.includes('Texto del segundo capítulo');i++)spoken.at(-1).onend()")
        self.assertIn('Texto del segundo capítulo',f.evaluate('spoken.at(-1).text'))
        self.assertFalse(f.locator('#chapter-two').evaluate('el=>el.hidden'))
        self.assertEqual(f.locator('[data-speech-current]').count(),1)
        f.locator('[data-ir=documento]').first.click()
        self.assertEqual(f.locator('[data-speech-current]').count(),0)
        self.assertTrue(f.get_by_role('button',name='Pausar',exact=True).is_disabled())
    def test_selection_native_menu_and_point_picker(self):
        p,f=self.open(width=390)
        f.evaluate("const r=document.createRange();r.setStart(document.querySelector('#first').firstChild,5);r.setEnd(document.querySelector('#second').firstChild,10);getSelection().addRange(r)")
        f.wait_for_function("!document.querySelector('[data-speech-tool] button:nth-child(2)').disabled")
        selected_text=f.evaluate('getSelection().toString()')
        native=f.evaluate("const e=new MouseEvent('contextmenu',{bubbles:true,cancelable:true});document.querySelector('#first').dispatchEvent(e);!e.defaultPrevented")
        self.assertTrue(native)
        f.locator('[data-speech-tool] summary').click();f.get_by_role('button',name='Leer selección',exact=True).click()
        self.assertTrue(f.evaluate("spoken[0].text.startsWith('documento sintético')"))
        self.assertEqual(f.evaluate('getSelection().toString()'),selected_text)
        f.evaluate('getSelection().removeAllRanges()');f.get_by_role('button',name='Detener',exact=True).click()
        f.locator('[data-speech-tool] summary').click();f.get_by_role('button',name='Elegir desde dónde leer',exact=True).click()
        f.locator('#second').focus();p.keyboard.press('Enter');f.get_by_role('menuitem',name='Leer desde aquí',exact=True).click()
        self.assertTrue(f.evaluate("spoken.at(-1).text.startsWith('Cada bloque')"))
        self.assertFalse(f.locator('#second').evaluate("el=>el.hasAttribute('tabindex')"))
    def test_existing_review_copy_preferences_and_context(self):
        p,f=self.open()
        f.locator('#first').click(button='right');self.assertEqual(f.get_by_role('menuitem').count(),3)
        f.get_by_role('menuitem',name='Comentar aquí',exact=True).click()
        self.assertTrue(f.locator('[data-revision-editor]').is_visible());p.keyboard.press('Escape')
        self.assertTrue(f.evaluate("const e=new MouseEvent('contextmenu',{bubbles:true,cancelable:true,shiftKey:true});document.querySelector('#first').dispatchEvent(e);!e.defaultPrevented"))
        f.get_by_label('Preferencias',exact=True).click();self.assertTrue(f.locator('[data-apariencia-menu]').evaluate('el=>el.open'))
        f.get_by_label('Compartir',exact=True).click();self.assertTrue(f.get_by_role('button',name='Enlace y acceso',exact=True).is_visible())
    def test_switching_point_pickers_restores_keyboard_targets(self):
        p,f=self.open()
        f.locator('[data-speech-tool] summary').click();f.get_by_role('button',name='Elegir desde dónde leer',exact=True).click()
        f.locator('[data-review-tool] summary').click();f.get_by_role('button',name='Añadir comentario',exact=True).click()
        self.assertEqual(f.locator('#first').get_attribute('tabindex'),'0')
        p.keyboard.press('Escape');self.assertIsNone(f.locator('#first').get_attribute('tabindex'))
        f.locator('[data-review-tool] summary').click();f.get_by_role('button',name='Añadir comentario',exact=True).click()
        f.locator('[data-speech-tool] summary').click();f.get_by_role('button',name='Elegir desde dónde leer',exact=True).click()
        self.assertEqual(f.locator('#first').get_attribute('tabindex'),'0')
        self.assertFalse(f.evaluate("document.documentElement.hasAttribute('data-revisando')"))
        p.keyboard.press('Escape');self.assertIsNone(f.locator('#first').get_attribute('tabindex'))
    def test_hosted_and_legacy_bridge(self):
        for path in ('/host','/host?legacy'):
            with self.subTest(path=path):
                p,f=self.open(path)
                self.assertEqual(f.evaluate('spoken.length'),0);self.listen(f)
                self.assertEqual(f.evaluate('spoken.length'),1)
                p.evaluate("document.querySelector('iframe').contentWindow.postMessage({bottifact:1,op:'stop-speech'},'*')")
                self.wait_expr(f,'window.cancelled===1');self.assertEqual(f.locator('[data-speech-current]').count(),0)
                f.locator('[data-speech-tool] summary').click();f.get_by_role('button',name='Elegir desde dónde leer',exact=True).click();p.keyboard.press('Escape')
                f.locator('[data-review-tool] summary').click();f.get_by_role('button',name='Añadir comentario',exact=True).click()
                if 'legacy' in path:
                    p.wait_for_function("operations.includes('action')")
                else:self.assertTrue(f.locator('.bf-controls-status').count()>0)
    @unittest.skipUnless(os.getenv('SPEECH_REAL'),'Set SPEECH_REAL=1 for audible device speech')
    def test_real_device_voice_in_sandbox(self):
        p,f=self.open('/host?real')
        try:self.wait_expr(f,'speechSynthesis.getVoices().length>0')
        except Exception:self.skipTest('No device voices available in this browser')
        f.evaluate("window.nativeEvents=[];const original=speechSynthesis.speak.bind(speechSynthesis);speechSynthesis.speak=u=>{for(const e of ['start','end','pause','resume','error'])u.addEventListener(e,x=>nativeEvents.push({event:e,error:x.error}));original(u)};void 0")
        self.listen(f);self.wait_expr(f,"nativeEvents.some(x=>x.event==='start')")
        f.get_by_role('button',name='Pausar',exact=True).click();self.wait_expr(f,'speechSynthesis.paused')
        f.get_by_role('button',name='Reanudar',exact=True).click();self.wait_expr(f,'!speechSynthesis.paused')
        self.wait_expr(f,"nativeEvents.some(x=>x.event==='end')",timeout=20)
        f.get_by_role('button',name='Detener',exact=True).click()
        self.wait_expr(f,'!speechSynthesis.speaking')
        print('REAL SPEECH:',self.browser.version,f.evaluate('nativeEvents'))

if __name__=='__main__':unittest.main()
