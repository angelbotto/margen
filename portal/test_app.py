import json
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from portal.app import create_app, COOKIE

HTML='<title>Informe</title><meta name="nota-documento" content="informe-prueba"><p id="dato">Cifra de ejemplo</p><script data-nota-modulo="packages/core/components/review.js"></script>'
ORIGIN='https://portal.test'


class PortalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.app=create_app(self.tmp.name,origin=ORIGIN,issuer='https://identity.test',audience='our-app')
        self.store=self.app.state.store
        self.owner=self.client('owner@example.com','Propietaria')
        self.other=self.client('other@example.com','Otra persona')
        self.guest=TestClient(self.app,base_url=ORIGIN,headers={'Origin':ORIGIN})
        self.a=self.owner.post('/api/artifacts',json={'title':'Informe privado','html':HTML}).json()
        self.path='/api/artifacts/'+self.a['id']

    def tearDown(self): self.tmp.cleanup()

    def client(self,email,name):
        c=TestClient(self.app,base_url=ORIGIN,headers={'Origin':ORIGIN})
        u=self.store.user(email,name);c.cookies.set(COOKIE,self.store.session(u['id']))
        return c

    def access(self,**kw):
        config={'visibility':'invited','grants':[{'email':'other@example.com','role':'commenter'}],'comments':'reviewers','guests':False,**kw}
        r=self.owner.put(self.path+'/access',json=config)
        self.assertEqual(r.status_code,200,r.text)

    def event(self,**kw):
        return {'id':'test-event-1','kind':'create','version':self.a['version'],'text':'Revisar la cifra','author':'Autor inventado',
                'anchor':{'reference':'dato','tag':'P','text':'Cifra de ejemplo','quote':'ejemplo','page':'Informe','x':.4,'y':.5},**kw}

    def test_speech_runtime_is_injected_once_without_relaxing_isolation(self):
        response=self.owner.get(self.path+'/render')
        self.assertEqual(response.status_code,200)
        self.assertIn('window.MargenSpeech =',response.text)
        self.assertIn('window.MargenSpeech?.mount(bar)',response.text)
        policy=response.headers['content-security-policy']
        self.assertIn('sandbox allow-scripts allow-downloads;',policy)
        self.assertIn("connect-src 'none'",policy)
        self.assertNotIn('allow-same-origin',policy)
        self.assertNotIn('speech-synthesis',policy)
        self.assertEqual(self.guest.get(self.path+'/render').status_code,404)

    def test_reader_updates_rhythm_without_rewriting_source(self):
        from portal.test_reader_style import OLD
        html=HTML+'<style>p{color:red}'+OLD+'</style>'
        artifact=self.owner.post('/api/artifacts',json={'title':'Legacy report','html':html}).json()
        path='/api/artifacts/'+artifact['id']
        before=self.owner.get(path).json()
        result=self.owner.get(path+'/render')
        self.assertEqual(result.status_code,200)
        self.assertNotIn('.legacy-flow',result.text)
        self.assertIn('Shared editorial rhythm',result.text)
        self.assertIn('p{color:red}',result.text)
        after=self.owner.get(path).json()
        self.assertEqual(before['current_version'],after['current_version'])
        self.assertEqual(before['visibility'],after['visibility'])
        with self.store.db() as db:
            row=db.execute('SELECT sha FROM versions WHERE id=?',(artifact['version'],)).fetchone()
        self.assertEqual((self.store.files/(row['sha']+'.html')).read_text(),html)

    def test_private_authorization_and_direct_render(self):
        self.assertEqual(self.owner.get(self.path).json()['visibility'],'private')
        for c in [self.other,self.guest]:
            for suffix in ['', '/render','/review']:
                self.assertEqual(c.get(self.path+suffix).status_code,404)
            self.assertEqual(c.get('/api/artifacts').status_code,401 if c is self.guest else 200)
        response=self.owner.get(self.path+'/render')
        self.assertIn('sandbox allow-scripts allow-downloads',response.headers['content-security-policy'])
        self.assertNotIn('allow-same-origin',response.headers['content-security-policy'])
        self.assertIn('BottifactReviewBridge',response.text)
        self.assertIn('no-store',response.headers['cache-control'])

    def test_verified_grant_viewer_commenter_editor(self):
        self.access(grants=[{'email':'other@example.com','role':'viewer'}])
        self.assertEqual(self.other.get(self.path).status_code,200)
        self.assertEqual(self.other.post(self.path+'/review',json=self.event()).status_code,404)
        self.access()
        response=self.other.post(self.path+'/review',json=self.event())
        self.assertEqual(response.status_code,200,response.text)
        event=response.json()['snapshot']['events'][0]
        self.assertEqual(event['author'],'Otra persona')
        self.assertTrue(event['verified'])
        self.assertEqual(self.other.put(self.path+'/access',json={'visibility':'public'}).status_code,404)
        self.access(grants=[{'email':'other@example.com','role':'editor'}])
        self.assertEqual(self.other.post(self.path+'/versions',json={'title':'Actualizado','html':HTML}).status_code,200)
        self.assertEqual(self.other.get(self.path).json()['permissions']['manage'],False)

    def test_guest_cannot_impersonate_and_internal_comments_stay_private(self):
        self.access(visibility='public',comments='readers',guests=True,grants=[])
        r=self.guest.post('/api/guest',json={'artifact':self.a['id'],'name':'Propietaria','email':'owner@example.com','verified':True})
        self.assertEqual(r.status_code,200)
        self.assertIn('HttpOnly',r.headers['set-cookie']);self.assertIn('Secure',r.headers['set-cookie'])
        self.assertFalse(self.guest.get('/api/session').json()['user']['verified'])
        self.assertEqual(self.guest.post(self.path+'/review',json=self.event()).status_code,200)
        self.assertFalse(self.owner.get(self.path+'/review').json()['snapshot']['events'][0]['verified'])
        self.access(visibility='public',comments='reviewers',guests=False,grants=[])
        self.assertEqual(self.guest.get(self.path+'/review').json()['snapshot']['events'],[])
        self.assertEqual(self.other.get(self.path+'/review').json()['snapshot']['events'],[])
        self.assertEqual(self.guest.get('/api/inbox').status_code,401)

    def test_idempotency_ownership_and_revocation(self):
        self.access();event=self.event()
        self.assertEqual(self.other.post(self.path+'/review',json=event).status_code,200)
        self.assertEqual(self.other.post(self.path+'/review',json=event).status_code,200)
        self.assertEqual(len(self.owner.get(self.path+'/review').json()['snapshot']['events']),1)
        self.assertEqual(self.other.post(self.path+'/review',json={**event,'text':'changed'}).status_code,409)
        self.assertEqual(self.other.post(self.path+'/review',json=self.event(id='resolve',kind='resolve',thread='test-event-1',resolved=True)).status_code,403)
        self.access(visibility='private')
        self.assertEqual(self.other.get(self.path).status_code,404)
        self.assertEqual(self.other.post(self.path+'/review',json=self.event(id='after-revoke')).status_code,404)

    def test_versions_export_restart_and_no_cross_document_thread(self):
        self.owner.post(self.path+'/review',json=self.event())
        old=self.a['version']
        revision=self.owner.post(self.path+'/versions',json={'title':'Nuevo título','html':HTML+'<p>Nuevo</p>'}).json()
        self.assertNotEqual(old,revision['version'])
        self.assertIn('Nuevo título',self.owner.get('/api/review/export').json()['text'])
        self.assertIn(old,self.owner.get('/api/review/export').json()['text'])
        self.assertNotIn('<p>Nuevo</p>',self.owner.get(self.path+'/render?version='+old).text)
        wrong=self.owner.post('/api/artifacts',json={'title':'Otro','html':HTML.replace('informe-prueba','otro-documento')}).json()
        self.assertEqual(self.owner.post('/api/artifacts/'+wrong['id']+'/review',json=self.event(id='wrong-thread',kind='reply',thread='test-event-1',version=wrong['version'])).status_code,404)
        rebuilt=create_app(self.tmp.name,origin=ORIGIN)
        c=TestClient(rebuilt,base_url=ORIGIN);c.cookies.update(self.owner.cookies)
        self.assertEqual(len(c.get(self.path+'/review').json()['snapshot']['events']),1)
        self.assertEqual(self.owner.post(self.path+'/versions',json={'title':'Cambio de ID','html':HTML.replace('informe-prueba','otro')}).status_code,409)

    def test_csrf_tokens_scope_and_bootstrap_once(self):
        self.assertEqual(self.owner.post('/api/tokens',headers={'Origin':'https://evil.test'},json={}).status_code,403)
        token=self.owner.post('/api/tokens',json={'label':'Hermes'}).json()['token']
        c=TestClient(self.app,base_url=ORIGIN,headers={'Authorization':'Bearer '+token})
        self.assertEqual(c.post('/api/artifacts',json={'title':'Desde agente','html':HTML}).status_code,200)
        self.assertEqual(c.put(self.path+'/access',json={'visibility':'public'}).status_code,403)
        hashes=self.owner.get('/api/tokens').json()['tokens'];self.owner.delete('/api/tokens/'+hashes[0]['hash'])
        self.assertEqual(c.get('/api/session').status_code,401)
        uid=self.owner.get('/api/session').json()['user']['id'];code=self.store.login_once(uid)
        self.assertEqual(self.guest.get('/auth/bootstrap?code='+code,follow_redirects=False).status_code,303)
        self.assertEqual(self.guest.get('/auth/bootstrap?code='+code,follow_redirects=False).status_code,401)

    def test_bad_payload_public_listing_and_foreign_edit(self):
        for value in [[], None, 'bad']:
            self.assertEqual(self.owner.post('/api/artifacts',json=value).status_code,422)
        self.assertEqual(self.owner.post('/api/artifacts',content='{',headers={'Content-Type':'application/json'}).status_code,422)
        self.assertEqual(self.owner.put(self.path+'/access',json={'visibility':'invited','grants':[None]}).status_code,422)
        self.access(visibility='unlisted',comments='readers',guests=False,grants=[])
        self.assertEqual(self.guest.get(self.path).status_code,200)
        self.assertEqual(self.guest.get('/api/artifacts?view=public').status_code,401)
        self.owner.post(self.path+'/review',json=self.event())
        self.assertEqual(self.other.post(self.path+'/review',json=self.event(id='foreign-edit',kind='edit',thread='test-event-1')).status_code,403)
        self.assertEqual(self.owner.post(self.path+'/review',json=self.event(id='bad-anchor',anchor=[])).status_code,422)
        self.access(visibility='public',comments='readers',guests=False,grants=[])
        self.assertEqual(len(self.other.get('/api/artifacts?view=public').json()['artifacts']),1)

    def test_library_separates_owned_shared_and_public(self):
        self.access()
        self.assertEqual(len(self.owner.get('/api/artifacts?view=mine').json()['artifacts']),1)
        self.assertEqual(self.owner.get('/api/artifacts?view=shared').json()['artifacts'],[])
        self.assertEqual(self.other.get('/api/artifacts?view=mine').json()['artifacts'],[])
        self.assertEqual(len(self.other.get('/api/artifacts?view=shared').json()['artifacts']),1)
        self.assertEqual(self.guest.get('/api/artifacts?view=mine').status_code,401)
        self.assertEqual(self.guest.get('/api/artifacts?view=shared').status_code,401)
        self.assertEqual(self.other.get('/api/artifacts?view=public').json()['artifacts'],[])
        self.assertEqual(len(self.other.get('/api/artifacts').json()['artifacts']),1)
        self.access(visibility='private')
        self.assertEqual(self.other.get('/api/artifacts?view=shared').json()['artifacts'],[])

    def test_external_catalog_is_personal_and_idempotent(self):
        body={'title':'Documento anterior','url':'https://pages.botto.is/informe/'}
        a=self.owner.post('/api/bookmarks',json=body)
        self.assertEqual(a.status_code,200)
        self.assertEqual(a.json(),self.owner.post('/api/bookmarks',json=body).json())
        self.assertEqual(len(self.owner.get('/api/artifacts?view=mine').json()['artifacts']),2)
        for client in [self.other]:
            self.assertEqual(client.get('/api/artifacts?view=mine').json()['artifacts'],[])
            self.assertEqual(client.get('/api/artifacts?view=public').json()['artifacts'],[])
        self.assertEqual(self.owner.post('/api/bookmarks',json={**body,'url':'javascript:alert(1)'}).status_code,422)
        self.assertEqual(self.owner.post('/api/bookmarks',json={**body,'url':'https://name:secret@example.com'}).status_code,422)

    def test_signed_login_rejects_wrong_audience_and_expired(self):
        private=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        claims={'iss':'https://identity.test','aud':['our-app'],'sub':'subject','email':'invited@example.com','iat':int(time.time()),'exp':int(time.time())+60,'type':'app'}
        with patch('jwt.PyJWKClient.get_signing_key_from_jwt',return_value=SimpleNamespace(key=private.public_key())):
            for bad in [{**claims,'aud':['other-app']},{**claims,'exp':int(time.time())-120}]:
                token=jwt.encode(bad,private,algorithm='RS256')
                self.assertEqual(self.guest.get('/auth/login',headers={'Cf-Access-Jwt-Assertion':token}).status_code,401)
            token=jwt.encode(claims,private,algorithm='RS256')
            response=self.guest.get('/auth/login?next=//evil.test',headers={'Cf-Access-Jwt-Assertion':token},follow_redirects=False)
            self.assertEqual(response.status_code,303);self.assertEqual(response.headers['location'],'/')
            self.assertEqual(self.guest.get('/api/session').json()['user']['email'],'invited@example.com')



class PreviewAndAttachmentTests(unittest.TestCase):
    setUp=PortalTests.setUp
    tearDown=PortalTests.tearDown
    client=PortalTests.client
    access=PortalTests.access
    def test_private_preview_and_attachment_follow_document_permissions(self):
        from pathlib import Path
        root=self.store.files/'attachments'/self.a['version'];root.mkdir(parents=True)
        (root/'evidence.csv').write_text('id,total\n1,100')
        preview=self.path+'/preview';attachment=self.path+'/attachments/'+self.a['version']+'/evidence.csv'
        for c in [self.other,self.guest]:
            self.assertEqual(c.get(preview).status_code,404)
            self.assertEqual(c.get(attachment).status_code,404)
        r=self.owner.get(preview);self.assertEqual(r.status_code,200);self.assertIn("script-src 'none'",r.headers['content-security-policy']);self.assertNotIn('<script',r.text)
        r=self.owner.get(attachment);self.assertEqual(r.status_code,200);self.assertIn('attachment',r.headers['content-disposition'])
        self.assertEqual(self.owner.get(self.path+'/attachments/'+self.a['version']+'/%2e%2e/bottifact.sqlite3').status_code,404)
        self.access(visibility='public',comments='readers',guests=False,grants=[])
        self.assertEqual(self.guest.get(preview).status_code,200)
        self.assertEqual(self.guest.get(attachment).status_code,200)

if __name__=='__main__':unittest.main()
