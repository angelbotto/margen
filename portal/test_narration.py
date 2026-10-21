"""No network: candidate transport is replaced by a deterministic byte stream."""
import io
import json
import os
import tempfile
import unittest
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPResponse
from unittest.mock import patch
from fastapi.testclient import TestClient
from portal.app import create_app, COOKIE
from portal.narration_providers import Configuration, request_data
from portal.narration_text import manifest, select_blocks

HTML='<html lang="es"><head><meta name="nota-documento" content="synthetic-narration"><title>No leer</title></head><body><main><h1 id="title">Informe de prueba</h1><p id="first">Cifra &amp; contexto. <span lang="en-US">Next steps.</span></p><p hidden>Oculto</p><nav>Control</nav><pre id="code">a &lt; b</pre></main></body></html>'
ORIGIN='https://portal.test'

class FakeProvider:
    def __init__(self):self.calls=[];self.handles=[]
    def open(self,*args):
        self.calls.append(args);handle=io.BytesIO(b'fake-mp3');self.handles.append(handle);return handle

class NarrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.app=create_app(self.tmp.name,origin=ORIGIN)
        self.store=self.app.state.store;self.service=self.app.state.narration
        self.owner=self.client('owner@example.com');self.other=self.client('other@example.com')
        self.guest=TestClient(self.app,base_url=ORIGIN,headers={'Origin':ORIGIN})
        self.a=self.owner.post('/api/artifacts',json={'title':'Synthetic','html':HTML}).json()
        self.path='/api/artifacts/'+self.a['id']+'/narration'
        self.config=Configuration(enabled=True,provider='elevenlabs',model='eleven_multilingual_v2',key='fake-test-key',voices=[{'id':'test','label':'Synthetic voice','voice':'stock-test'}],daily_chars=100000,user_chars=10000,daily_micro_usd=1000000,price_per_million='30')
        self.service.config=self.config;self.fake=FakeProvider();self.service.provider=self.fake
    def tearDown(self):
        for s in list(self.service.sessions.values()):self.service.stop(s)
        self.tmp.cleanup()
    def client(self,email):
        c=TestClient(self.app,base_url=ORIGIN,headers={'Origin':ORIGIN});u=self.store.user(email,email);c.cookies.set(COOKIE,self.store.session(u['id']));return c
    def body(self):
        m=self.owner.get(self.path+'/manifest',params={'version':self.a['version']}).json()
        return {'version':m['version'],'sha':m['sha'],'voice':'test','profile':'report','confirmed':True,'blocks':[{'id':m['blocks'][1]['id'],'start':0,'end':len(m['blocks'][1]['text'])}]}
    def session(self):
        r=self.owner.post(self.path+'/sessions',json=self.body());self.assertEqual(r.status_code,200,r.text);return self.path+'/sessions/'+r.json()['id']
    def clip(self,s):
        r=self.owner.post(s+'/blocks/0',json={});self.assertEqual(r.status_code,200,r.text);return r.json()['url']
    def test_disabled_does_not_discover_credentials_or_fallback(self):
        self.service.config=Configuration()
        with patch.dict(os.environ,{'OPENAI_API_KEY':'do-not-use'},clear=True):self.assertFalse(Configuration.environment().enabled)
        response=self.owner.get(self.path,params={'version':self.a['version']})
        self.assertFalse(response.json()['enabled']);self.assertEqual(self.fake.calls,[])
        self.assertEqual(self.owner.get(self.path+'/manifest',params={'version':self.a['version']}).status_code,503)
    def test_manifest_exact_text_language_and_safe_adapters(self):
        blocks=manifest(HTML);self.assertEqual([x['text'] for x in blocks],['Informe de prueba','Cifra & contexto. Next steps.','a < b'])
        b=select_blocks(HTML,[{'id':blocks[1]['id'],'start':0,'end':len(blocks[1]['text'])}])[0]
        self.assertEqual(b['runs'][-1],{'text':'Next steps.','lang':'en-US'})
        url,body,headers=request_data(self.config,b,self.config.voices[0],'report')
        self.assertEqual(json.loads(body)['text'],b['text']);self.assertNotIn('instructions',json.loads(body))
        azure=Configuration(provider='azure',region='eastus',key='fake')
        _,body,_=request_data(azure,b,{'voice':'en-US-AvaMultilingualNeural'},'report')
        self.assertIn(b'Cifra &amp; contexto.',body);self.assertIn(b'<lang xml:lang="en-US">Next steps.</lang>',body)
        self.assertNotIn('fake-test-key',json.dumps(self.config.public()))
    def test_confirmation_version_hash_refs_and_identity_required(self):
        body=self.body()
        for change in [{'confirmed':False},{'sha':'wrong'},{'voice':'other'},{'blocks':[{'id':'wrong','start':0,'end':1}]},{'blocks':[{'id':body['blocks'][0]['id'],'start':False,'end':1}]}]:
            r=self.owner.post(self.path+'/sessions',json={**body,**change});self.assertIn(r.status_code,(409,422),r.text)
        for client in (self.guest,self.other):self.assertIn(client.post(self.path+'/sessions',json=body).status_code,(401,403,404))
        self.assertFalse(self.fake.calls)
    def test_post_claims_once_get_head_range_do_not_generate_and_cache_reuses(self):
        s=self.session();self.assertEqual(self.owner.get(s+'/audio/0').status_code,409)
        url=self.clip(s);self.assertEqual(len(self.fake.calls),1)
        self.assertEqual(self.owner.head(url).status_code,405)
        self.assertEqual(self.owner.get(url,headers={'Range':'bytes=3-'}).status_code,416)
        self.assertEqual(self.owner.post(s+'/blocks/0',json={}).status_code,409)
        self.assertEqual(self.owner.get(url).content,b'fake-mp3')
        self.assertEqual(self.owner.get(s+'/status/0').json()['state'],'complete')
        self.assertEqual(self.owner.get(url).content,b'fake-mp3');self.assertEqual(len(self.fake.calls),1)
        self.owner.delete(s);s2=self.session();self.assertEqual(self.owner.get(self.clip(s2)).content,b'fake-mp3');self.assertEqual(len(self.fake.calls),1)
    def test_cancellation_closes_provider_no_audio_or_regeneration(self):
        s=self.session();url=self.clip(s);self.assertFalse(self.fake.handles[0].closed)
        self.assertEqual(self.owner.delete(s).status_code,200);self.assertTrue(self.fake.handles[0].closed)
        self.assertEqual(self.owner.get(url).status_code,404);self.assertEqual(self.owner.post(s+'/blocks/0',json={}).status_code,404)
    def test_hard_character_and_cost_caps_reserve_before_provider_and_survive_restart(self):
        self.config.daily_chars=1;s=self.session();self.assertEqual(self.owner.post(s+'/blocks/0',json={}).status_code,429);self.assertFalse(self.fake.calls)
        self.owner.delete(s);self.config.daily_chars=100000;self.config.daily_micro_usd=1;s=self.session();self.assertEqual(self.owner.post(s+'/blocks/0',json={}).status_code,429);self.assertFalse(self.fake.calls)
        self.owner.delete(s);self.config.daily_micro_usd=1000000;s=self.session();self.clip(s)
        with self.store.db() as db:
            row=db.execute('SELECT * FROM narration_usage').fetchone();self.assertGreater(row['chars'],0);self.assertGreater(row['micro_usd'],0)
        self.owner.delete(s)
        with self.store.db() as db:self.assertEqual(db.execute('SELECT chars FROM narration_usage').fetchone()['chars'],row['chars'])
    def test_access_revoked_blocks_cached_delivery_and_other_user_session(self):
        s=self.session();url=self.clip(s);self.owner.get(url)
        self.assertEqual(self.other.get(url).status_code,404)
        with patch('portal.narration.cited_version_readable',return_value=False):self.assertEqual(self.owner.get(url).status_code,404)
    def test_expired_audio_is_not_served_by_an_existing_session(self):
        s=self.session();url=self.clip(s);self.owner.get(url)
        with self.store.db() as db:db.execute('UPDATE narration_cache SET created=0')
        self.assertEqual(self.owner.get(url).status_code,410);self.assertEqual(len(self.fake.calls),1)
    def test_owner_purge_cancels_and_deletes_cache(self):
        s=self.session();url=self.clip(s);self.owner.get(url)
        self.assertEqual(self.other.delete(self.path+'/cache').status_code,404)
        self.assertEqual(self.owner.delete(self.path+'/cache').status_code,200);self.assertEqual(self.owner.get(url).status_code,404)
        with self.store.db() as db:self.assertEqual(db.execute('SELECT count(*) FROM narration_cache').fetchone()[0],0)
    def test_failed_stream_not_complete_or_cached(self):
        class Broken(io.BytesIO):
            def read1(self,n):
                if self.tell():raise OSError('synthetic failure')
                return self.read(n)
        self.fake.open=lambda *args:Broken(b'partial')
        s=self.session();self.owner.get(self.clip(s));self.assertEqual(self.owner.get(s+'/status/0').json()['state'],'failed')
        with self.store.db() as db:self.assertEqual(db.execute('SELECT count(*) FROM narration_cache').fetchone()[0],0)
    def test_optimized_python_cannot_bypass_billing_approval(self):
        env={**os.environ,'MARGEN_NARRATION_ENABLED':'1','MARGEN_NARRATION_PROVIDER':'elevenlabs','MARGEN_NARRATION_KEY':'fake','MARGEN_NARRATION_MODEL':'eleven_multilingual_v2','MARGEN_NARRATION_VOICES':json.dumps(self.config.voices),'MARGEN_NARRATION_DAILY_CHARS':'1000','MARGEN_NARRATION_USER_CHARS':'1000','MARGEN_NARRATION_DAILY_MICRO_USD':'100000','MARGEN_NARRATION_USD_PER_MILLION_CHARS':'30'}
        env.pop('MARGEN_NARRATION_BILLING_APPROVED',None)
        result=subprocess.run([sys.executable,'-O','-c','from portal.narration_providers import Configuration; print(Configuration.environment().enabled)'],env=env,capture_output=True,text=True,check=True)
        self.assertEqual(result.stdout.strip(),'False')
    def test_http_content_length_truncation_never_completes_or_caches(self):
        class Socket:
            def makefile(self,*args):return io.BytesIO(b'HTTP/1.1 200 OK\r\nContent-Length: 100\r\nContent-Type: audio/mpeg\r\n\r\npartial')
        response=HTTPResponse(Socket());response.begin();self.fake.open=lambda *args:response
        s=self.session();self.owner.get(self.clip(s));self.assertEqual(self.owner.get(s+'/status/0').json()['state'],'failed')
        with self.store.db() as db:self.assertEqual(db.execute('SELECT count(*) FROM narration_cache').fetchone()[0],0)
    def test_concurrent_reservations_cannot_exceed_global_limit(self):
        one=self.session();two=self.session();chars=self.body()['blocks'][0]['end'];self.config.daily_chars=chars
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda path:self.owner.post(path+'/blocks/0',json={}).status_code,[one,two]))
        self.assertEqual(sorted(results),[200,429]);self.assertEqual(len(self.fake.calls),1)
    def test_cancel_while_provider_is_opening_closes_late_handle(self):
        entered=threading.Event();release=threading.Event();handle=io.BytesIO(b'audio')
        def opening(*args):entered.set();release.wait(5);return handle
        self.fake.open=opening;s=self.session()
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending=pool.submit(self.owner.post,s+'/blocks/0',json={});self.assertTrue(entered.wait(5));self.owner.delete(s);release.set();self.assertEqual(pending.result().status_code,404)
        self.assertTrue(handle.closed)
    def test_purge_during_stream_prevents_cache_reinsertion(self):
        entered=threading.Event();release=threading.Event()
        class Waiting(io.BytesIO):
            def read1(self,n):entered.set();release.wait(5);return b'partial'
        self.fake.open=lambda *args:Waiting(b'audio');s=self.session();url=self.clip(s)
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending=pool.submit(self.owner.get,url);self.assertTrue(entered.wait(5));self.owner.delete(self.path+'/cache');release.set();pending.result()
        with self.store.db() as db:self.assertEqual(db.execute('SELECT count(*) FROM narration_cache').fetchone()[0],0)
    def test_text_limits_and_escaping_instead_of_ssml_injection(self):
        source='<main><p>&lt;/voice&gt; &lt;audio src="evil"/&gt;</p></main>';b=manifest(source)[0]
        block=select_blocks(source,[{'id':b['id'],'start':0,'end':len(b['text'])}])[0]
        _,body,_=request_data(Configuration(provider='azure',region='eastus'),block,{'voice':'test'},'neutral')
        self.assertIn(b'&lt;/voice&gt;',body);self.assertNotIn(b'<audio',body)
        with self.assertRaises(ValueError):select_blocks(source,[{'id':b['id'],'start':0,'end':999999}])

if __name__=='__main__':unittest.main()
