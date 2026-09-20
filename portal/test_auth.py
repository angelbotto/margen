import io
import json
import os
import tempfile
import time
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from urllib.parse import urlsplit, parse_qs
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from portal.app import create_app, COOKIE
from portal.auth import AUTH_COOKIE, target
from portal.test_app import HTML, ORIGIN


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.env=patch.dict(os.environ,{'BOTTIFACT_EMAIL_URL':'https://email.test','BOTTIFACT_EMAIL_KEY':'test','BOTTIFACT_EMAIL_FROM':'Margen <access@example.com>','BOTTIFACT_AUTH_SECRET':'test-secret','BOTTIFACT_GOOGLE_ID':'client','BOTTIFACT_GOOGLE_SECRET':'secret','BOTTIFACT_GOOGLE_ENABLED':'1','BOTTIFACT_ADMIN_EMAILS':'owner@example.com,alias@example.com,third@example.com','BOTTIFACT_OWNER_ALIASES':'owner@example.com,alias@example.com,third@example.com'})
        self.env.start();self.tmp=tempfile.TemporaryDirectory();self.app=create_app(self.tmp.name,origin=ORIGIN);self.store=self.app.state.store
        self.c=TestClient(self.app,base_url=ORIGIN,headers={'Origin':ORIGIN})

    def tearDown(self):self.tmp.cleanup();self.env.stop()

    def start(self,email='alias@example.com'):
        with patch('portal.auth.send_code',return_value={'id':'message-test'}) as send:
            response=self.c.post('/api/auth/email',json={'email':email,'next':'//evil.test'})
            self.assertEqual(response.status_code,200,response.text)
            return response.json()['challenge'],send.call_args.args[1]

    def test_return_context_and_untrusted_destinations(self):
        path = '/a/' + 'a' * 32
        self.assertEqual(target(path + '?thread=review-1&version=v_2&email=private@example.com'), path + '?thread=review-1&version=v_2')
        for view in ['brain', 'insights', 'work']:
            self.assertEqual(target('/?view=' + view), '/?view=' + view)
        for value in ['https://evil.test', '//evil.test', '/\\evil.test', '/%2f%2fevil.test', '/a/invalid', '/\n?view=brain', 'http://[', None]:
            self.assertEqual(target(value), '/')
        destination = path + '?thread=review-1&version=v_2'
        with patch('portal.auth.send_code', return_value={'id': 'message-test'}) as send:
            response = self.c.post('/api/auth/email', json={'email': 'reader@example.com', 'next': destination})
            code = send.call_args.args[1]
        verified = self.c.post('/api/auth/email/verify', json={'challenge': response.json()['challenge'], 'code': code})
        self.assertEqual(verified.json()['next'], destination)

    def test_cancelled_google_preserves_validated_return_context(self):
        destination = '/a/' + 'a' * 32 + '?thread=review-1'
        response = self.c.get('/auth/google', params={'next': destination}, follow_redirects=False)
        state = parse_qs(urlsplit(response.headers['location']).query)['state'][0]
        cancelled = self.c.get('/auth/google/callback', params={'state': state, 'error': 'access_denied'}, follow_redirects=False)
        params = parse_qs(urlsplit(cancelled.headers['location']).query)
        self.assertEqual(params['next'], [destination])
        self.assertEqual(params['error'], ['google_session'])

    def test_email_bound_single_use_and_admin_aliases(self):
        canonical=self.store.user('owner@example.com','Owner')
        cid,code=self.start()
        other=TestClient(self.app,base_url=ORIGIN,headers={'Origin':ORIGIN})
        body={'challenge':cid,'code':code}
        self.assertEqual(other.post('/api/auth/email/verify',json=body).status_code,401)
        response=self.c.post('/api/auth/email/verify',json=body)
        self.assertEqual(response.status_code,200);self.assertEqual(response.json()['next'],'/')
        user=self.c.get('/api/session').json()['user'];self.assertEqual(user['id'],canonical['id']);self.assertTrue(user['admin'])
        self.assertEqual(self.store.user('third@example.com','Third')['id'],canonical['id'])
        self.assertEqual(self.c.post('/api/auth/email/verify',json=body).status_code,401)
        self.assertIn('HttpOnly',response.headers['set-cookie'])
        self.assertNotIn(code,json.dumps(self.c.get('/api/session').json()))

    def test_email_attempt_limit_expiration_and_resend(self):
        cid,code=self.start('someone@example.com')
        wrong='000000' if code!='000000' else '111111'
        for _ in range(5):self.assertEqual(self.c.post('/api/auth/email/verify',json={'challenge':cid,'code':wrong}).status_code,401)
        self.assertEqual(self.c.post('/api/auth/email/verify',json={'challenge':cid,'code':code}).status_code,401)
        self.assertEqual(self.c.post('/api/auth/email',json={'email':'someone@example.com'}).status_code,429)
        cid,code=self.start('different@example.com')
        with self.store.db() as db:db.execute('UPDATE auth_challenges SET expires=0 WHERE id=?',(cid,))
        self.assertEqual(self.c.post('/api/auth/email/verify',json={'challenge':cid,'code':code}).status_code,401)
        self.assertEqual(self.c.post('/api/auth/email',headers={'Origin':'https://evil.test'},json={'email':'new@example.com'}).status_code,403)

    def test_login_wall_admin_catalog_and_public_links(self):
        self.assertEqual(self.c.get('/',follow_redirects=False).headers['location'],'/login')
        self.assertEqual(self.c.get('/api/artifacts?view=public').status_code,401)
        ordinary=self.store.user('ordinary@example.com','Ordinary');self.c.cookies.set(COOKIE,self.store.session(ordinary['id']))
        artifact=self.c.post('/api/artifacts',json={'html':HTML,'title':'Private'}).json()
        public=self.c.post('/api/artifacts',json={'html':HTML,'title':'Public','visibility':'public'}).json()
        browser=TestClient(self.app,base_url=ORIGIN)
        self.assertEqual(browser.get('/api/artifacts/'+public['id']).status_code,200)
        self.assertEqual(browser.get('/api/artifacts/'+artifact['id']).status_code,404)
        admin=self.store.user('alias@example.com','Owner');browser.cookies.set(COOKIE,self.store.session(admin['id']))
        self.assertEqual(len(browser.get('/api/artifacts?view=mine').json()['artifacts']),2)
        self.assertTrue(browser.get('/api/artifacts/'+artifact['id']).json()['permissions']['manage'])
        token=self.c.post('/api/tokens',json={}).json()['token']
        agent=TestClient(self.app,base_url=ORIGIN,headers={'Authorization':'Bearer '+token})
        self.assertEqual(agent.post('/api/artifacts',json={'html':HTML,'title':'Agent','visibility':'public'}).json()['visibility'],'public')
        self.assertEqual(agent.post('/api/artifacts/'+artifact['id']+'/versions',json={'html':HTML,'title':'Change','visibility':'public'}).status_code,422)
        self.assertEqual(agent.post('/api/tokens',json={}).status_code,403)

    def test_google_pkce_state_nonce_verified_email_and_replay(self):
        private=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        response=self.c.get('/auth/google?next=//evil.test',follow_redirects=False)
        params=parse_qs(urlsplit(response.headers['location']).query)
        self.assertEqual(params['code_challenge_method'],['S256'])
        state=params['state'][0];nonce=params['nonce'][0]
        claims={'iss':'https://accounts.google.com','aud':'client','sub':'123','email':'alias@example.com','email_verified':True,'iat':int(time.time()),'exp':int(time.time())+120,'nonce':nonce}
        callback='/auth/google/callback?state='+state+'&code=code'
        stranger=TestClient(self.app,base_url=ORIGIN)
        self.assertIn('error=',stranger.get(callback,follow_redirects=False).headers['location'])
        with patch('portal.auth.remote_json',return_value={'id_token':jwt.encode(claims,private,algorithm='RS256')}) as remote, patch('jwt.PyJWKClient.get_signing_key_from_jwt',return_value=SimpleNamespace(key=private.public_key())):
            good=self.c.get(callback,follow_redirects=False)
            self.assertEqual(good.headers['location'],'/')
            self.assertIn('code_verifier',remote.call_args.args[1])
            self.assertTrue(self.c.get('/api/session').json()['user']['admin'])
            self.assertIn('error=',self.c.get(callback,follow_redirects=False).headers['location'])
        for changes in [{'nonce':'wrong'},{'email_verified':False},{'aud':'wrong'},{'exp':1}]:
            response=self.c.get('/auth/google',follow_redirects=False);p=parse_qs(urlsplit(response.headers['location']).query)
            bad={**claims,'nonce':p['nonce'][0],**changes}
            with patch('portal.auth.remote_json',return_value={'id_token':jwt.encode(bad,private,algorithm='RS256')}),patch('jwt.PyJWKClient.get_signing_key_from_jwt',return_value=SimpleNamespace(key=private.public_key())):
                r=self.c.get('/auth/google/callback?state='+p['state'][0]+'&code=c',follow_redirects=False)
                self.assertIn('error=',r.headers['location'])

    def test_delivery_failure_is_visible_only_to_requesting_browser(self):
        cid,code=self.start('recipient@example.com')
        other=TestClient(self.app,base_url=ORIGIN)
        path='/api/auth/email/status?challenge='+cid
        self.assertEqual(other.get(path).status_code,404)
        with patch('portal.auth.delivery_status',return_value='failed') as check:
            response=self.c.get(path)
            self.assertEqual(response.json(),{'status':'failed'})
            self.assertNotIn('message-test',response.text)
            self.c.get(path);self.assertEqual(check.call_count,1)

    def test_resend_and_usesend_delivery_states(self):
        from portal.auth import delivery_status,send_code
        with patch.dict(os.environ,{'BOTTIFACT_EMAIL_PROVIDER':'resend','BOTTIFACT_EMAIL_URL':'https://api.resend.com'}),patch('portal.auth.remote_json',return_value={'id':'queued-id'}) as remote:
            send_code('reader@example.com','123456')
            self.assertEqual(remote.call_args.args[0],'https://api.resend.com/emails')
            self.assertEqual(remote.call_args.args[1]['to'],['reader@example.com'])
        for provider,data,expected in [('resend',{'last_event':'bounced'},'failed'),('resend',{'last_event':'delivered'},'delivered'),('resend',{'last_event':'sent'},'sent'),('usesend',{'emailEvents':[{'status':'SENT','createdAt':'1'},{'status':'FAILED','createdAt':'2'}]},'failed')]:
            with patch('portal.auth.remote_json',return_value=data):self.assertEqual(delivery_status(provider,'id'),expected)

    def test_mail_failure_does_not_create_session_or_valid_code(self):
        with patch('portal.auth.send_code',side_effect=OSError('Secret upstream message')):
            r=self.c.post('/api/auth/email',json={'email':'test@example.com'})
        self.assertEqual(r.status_code,503);self.assertNotIn('Secret',r.text)
        self.assertIsNone(self.c.get('/api/session').json()['user'])
        with self.store.db() as db:self.assertEqual(db.execute('SELECT count(*) FROM auth_challenges').fetchone()[0],0)


class AliasMigrationTests(unittest.TestCase):
    def test_existing_alias_sessions_tokens_documents_and_comments_move_together(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ,{'BOTTIFACT_ADMIN_EMAILS':'','BOTTIFACT_OWNER_ALIASES':''}):
            app=create_app(directory,origin=ORIGIN);store=app.state.store
            primary=store.user('owner@example.com','Owner');old=store.user('tikin@example.com','Owner Tikin')
            cookie=store.session(old['id']);token=store.token(old['id'])
            c=TestClient(app,base_url=ORIGIN,headers={'Origin':ORIGIN});c.cookies.set(COOKIE,cookie)
            a=c.post('/api/artifacts',json={'title':'Antes de unir','html':HTML}).json()
            event={'id':'alias-note','kind':'create','version':a['version'],'text':'Comentario conservado','anchor':{'reference':'dato','tag':'P','text':'dato','quote':'dato','page':'Informe','x':.5,'y':.5}}
            self.assertEqual(c.post('/api/artifacts/'+a['id']+'/review',json=event).status_code,200)
            with patch.dict(os.environ,{'BOTTIFACT_ADMIN_EMAILS':'owner@example.com,tikin@example.com,liftit@example.com','BOTTIFACT_OWNER_ALIASES':'owner@example.com,tikin@example.com,liftit@example.com'}):
                rebuilt=create_app(directory,origin=ORIGIN);client=TestClient(rebuilt,base_url=ORIGIN,headers={'Origin':ORIGIN});client.cookies.set(COOKIE,cookie)
                self.assertEqual(client.get('/api/session').json()['user']['id'],primary['id'])
                self.assertEqual(rebuilt.state.store.user('liftit@example.com','Owner')['id'],primary['id'])
                self.assertEqual(client.get('/api/artifacts').json()['artifacts'][0]['owner'],primary['id'])
                self.assertEqual(len(client.get('/api/inbox').json()['items']),1)
                self.assertIn('Comentario conservado',client.get('/api/review/export').json()['text'])
                agent=TestClient(rebuilt,base_url=ORIGIN,headers={'Authorization':'Bearer '+token})
                self.assertEqual(agent.get('/api/session').json()['user']['id'],primary['id'])
                rebuilt.state.store.merge_admin_aliases()
                with rebuilt.state.store.db() as db:self.assertEqual(db.execute("SELECT count(*) FROM audit WHERE action='merge-alias'").fetchone()[0],1)

class SeparateAdminsTests(unittest.TestCase):
    def test_admin_role_does_not_merge_independent_people(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ,{'BOTTIFACT_ADMIN_EMAILS':'one@example.com,two@example.com','BOTTIFACT_OWNER_ALIASES':''}):
            store=create_app(tmp,origin=ORIGIN).state.store
            one=store.user('one@example.com','One');two=store.user('two@example.com','Two')
            store.merge_admin_aliases()
            self.assertNotEqual(one['id'],two['id'])
            self.assertEqual(store.user('two@example.com','Two')['id'],two['id'])

if __name__=='__main__':unittest.main()
