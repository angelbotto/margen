import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from portal.app import create_app, COOKIE, permissions
from portal.backup import backup, restore, verify
from portal.worker import digests
from portal.auth import target

ORIGIN='https://portal.test'
def html(text):return '<meta name="nota-documento" content="roadmap"><section id="resumen"><h2>Prioridades</h2><p>'+text+'</p></section>'

class WorkspaceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.app=create_app(self.root/'data',origin=ORIGIN);self.store=self.app.state.store
  self.owner=self.client('owner@example.com');self.reviewer=self.client('reviewer@example.com');self.stranger=self.client('stranger@example.com')
  self.a=self.owner.post('/api/artifacts',json={'title':'Roadmap','html':html('Fase uno'),'source':{'agent':'Codex','session':'sesion-original'}}).json();self.path='/api/artifacts/'+self.a['id']
  self.owner.put(self.path+'/access',json={'visibility':'invited','grants':[{'email':'reviewer@example.com','role':'commenter'}]})
 def tearDown(self):self.tmp.cleanup()
 def client(self,email):
  c=TestClient(self.app,base_url=ORIGIN,headers={'Origin':ORIGIN});u=self.store.user(email,email);c.cookies.set(COOKIE,self.store.session(u['id']));return c
 def event(self,id='comment',**kw):return {'id':id,'kind':'create','version':self.a['version'],'text':'Aclarar el criterio','session':'reunion-semana-3','anchor':{'reference':'resumen','section':'Prioridades','tag':'P','text':'Fase uno','quote':'uno','page':'Roadmap','x':.5,'y':.5},**kw}
 def test_admin_counts_distinguish_verified_guests_visibility_and_utc_window(self):
  import time
  with self.store.db() as db:db.execute("INSERT INTO users VALUES('guest-test',NULL,'Invitado',0)")
  now=int(time.time())
  today=time.strftime('%Y-%m-%d',time.gmtime(now))
  start=time.strftime('%Y-%m-%d',time.gmtime(now-29*86400))
  before=time.strftime('%Y-%m-%d',time.gmtime(now-30*86400))
  future=time.strftime('%Y-%m-%d',time.gmtime(now+86400))
  with self.store.db() as db:
   db.executemany('INSERT INTO artifact_visits VALUES(?,?,?)',[(self.a['id'],day,views) for day,views in [(today,7),(start,3),(before,100),(future,100)]])
  self.assertEqual(self.owner.get('/api/admin').status_code,403)
  with patch.dict('os.environ',{'BOTTIFACT_ADMIN_EMAILS':'owner@example.com'}):
   response=self.owner.get('/api/admin').json()
  self.assertEqual(response['counts']['verified_users'],3)
  self.assertEqual(response['counts']['guest_users'],1)
  self.assertEqual(response['counts']['users'],4)
  self.assertEqual(response['visibility'],{'private':0,'invited':1,'unlisted':0,'public':0})
  self.assertEqual(response['traffic'],{'views':10,'since':start,'until':today,'days':30})
  self.assertNotIn('email',str(response))

 def test_private_notes_stay_private_in_review_inbox_export_and_notifications(self):
  response=self.owner.post(self.path+'/review',json=self.event('personal',entry_type='note'));self.assertEqual(response.status_code,200,response.text)
  self.assertEqual(self.reviewer.get(self.path+'/review').json()['snapshot']['events'],[])
  self.assertEqual(self.reviewer.get('/api/review/export?artifact='+self.a['id']).json()['count'],0)
  self.assertEqual(self.reviewer.get('/api/inbox').json()['items'],[])
  self.assertEqual(self.reviewer.get('/api/notifications').json()['items'],[])
  attack=self.event('reply',kind='reply',thread='personal',text='No puedo leerla')
  self.assertEqual(self.reviewer.post(self.path+'/review',json=attack).status_code,404)
  self.assertEqual(self.owner.get('/api/review/export').json()['count'],1)
 def test_viewer_can_keep_own_notes_but_cannot_comment_or_read_others_notes(self):
  self.owner.put(self.path+'/access',json={'visibility':'invited','grants':[{'email':'reviewer@example.com','role':'viewer'}]})
  self.assertEqual(self.reviewer.post(self.path+'/review',json=self.event()).status_code,404)
  self.assertEqual(self.reviewer.post(self.path+'/review',json=self.event(entry_type='note')).status_code,200)
  self.assertEqual(self.owner.get(self.path+'/review').json()['snapshot']['events'],[])
  self.assertEqual(self.reviewer.post(self.path+'/review',json=self.event('resolve',kind='resolve',thread='comment',resolved=True)).status_code,200)
 def test_prompt_has_original_version_section_session_full_quote_and_replies(self):
  self.reviewer.post(self.path+'/review',json=self.event())
  self.owner.post(self.path+'/review',json=self.event('reply',kind='reply',thread='comment',text='Recibido'))
  data=self.owner.get('/api/review/export').json();text=data['text']
  for value in ['Roadmap','roadmap',self.a['version'],'Prioridades','Fase uno','uno','reunion-semana-3','sesion-original','Codex','Recibido','?thread=comment','SHA-256']:
   self.assertIn(value,text)
  self.assertEqual(data['items'][0]['context']['anchor_status'],'exact')
  self.assertEqual(self.stranger.get('/api/review/export').json()['count'],0)
 def test_draft_does_not_change_public_html_search_or_comments_until_release(self):
  self.owner.post(self.path+'/review',json=self.event())
  draft=self.owner.post(self.path+'/versions',json={'title':'Roadmap nuevo','html':html('Fase dos confidencial'),'mode':'draft'}).json()
  self.assertEqual(self.owner.get(self.path).json()['current_version'],self.a['version'])
  self.assertNotIn('confidencial',self.reviewer.get(self.path+'/render').text)
  self.assertEqual(self.reviewer.get(self.path+'/render?version='+draft['version']).status_code,404)
  self.assertEqual(self.reviewer.get('/api/artifacts?q=confidencial').json()['total'],0)
  self.owner.post(self.path+'/review',json=self.event('draft-note',version=draft['version'],text='Secreto'))
  self.assertEqual(len(self.reviewer.get(self.path+'/review').json()['snapshot']['events']),1)
  self.assertNotIn('Secreto',self.reviewer.get('/api/review/export?artifact='+self.a['id']).json()['text'])
  diff=self.owner.get(self.path+'/compare',params={'from':self.a['version'],'to':draft['version']}).json()
  self.assertTrue(diff['text_changed']);self.assertEqual(diff['anchors'][0]['status'],'changed')
  self.assertEqual(self.reviewer.get(self.path+'/compare',params={'to':draft['version']}).status_code,404)
  self.assertEqual(self.owner.post(self.path+'/release',json={'version':draft['version'],'expected_current':'stale'}).status_code,409)
  self.assertEqual(self.owner.post(self.path+'/release',json={'version':draft['version'],'expected_current':self.a['version']}).status_code,200)
  self.assertIn('confidencial',self.reviewer.get(self.path+'/render').text)
  self.assertEqual(self.reviewer.get('/api/artifacts?q=confidencial').json()['total'],1)
 def test_notifications_mentions_unread_revocation_and_opt_in_digest(self):
  self.reviewer.post(self.path+'/review',json=self.event(text='@owner@example.com revisar'))
  items=self.owner.get('/api/notifications').json()['items'];self.assertEqual(len(items),1);self.assertEqual(items[0]['kind'],'mention')
  self.reviewer.post(self.path+'/review',json=self.event(text='@owner@example.com revisar'))
  self.assertEqual(len(self.owner.get('/api/notifications').json()['items']),1)
  sent=[];send=lambda *args:sent.append(args)
  digests(self.store,ORIGIN,permissions,send);self.assertEqual(sent,[])
  self.owner.put('/api/notifications/settings',json={'frequency':'daily'})
  digests(self.store,ORIGIN,permissions,send);digests(self.store,ORIGIN,permissions,send);self.assertEqual(len(sent),1);self.assertIn('?thread=comment',sent[0][1])
  self.owner.post(self.path+'/seen',json={});self.assertFalse(self.owner.get('/api/inbox').json()['items'][0]['unread'])
  self.owner.post(self.path+'/review',json=self.event('response',kind='reply',thread='comment',text='Listo'))
  self.assertTrue(self.reviewer.get('/api/notifications').json()['items'])
  self.owner.put(self.path+'/access',json={'visibility':'private'})
  self.assertEqual(self.reviewer.get('/api/notifications').json()['items'],[])
 def test_organization_archive_is_reversible_and_does_not_break_links(self):
  payload={'tags':['qa','operaciones'],'collections':['Dirección'],'archived':False}
  self.assertEqual(self.reviewer.patch(self.path+'/organization',json=payload).status_code,404)
  self.assertEqual(self.owner.patch(self.path+'/organization',json=payload).status_code,200)
  self.assertEqual(self.owner.get('/api/artifacts?collection=Direcci%C3%B3n&tag=qa').json()['total'],1)
  self.owner.patch(self.path+'/organization',json={'archived':True})
  self.assertEqual(self.owner.get('/api/artifacts?view=mine').json()['total'],0)
  self.assertEqual(self.owner.get('/api/artifacts?view=archived').json()['total'],1)
  self.assertEqual(self.owner.get('/api/artifacts?document_id=roadmap').json()['total'],1)
  self.assertEqual(self.reviewer.get(self.path+'/render').status_code,200)
  self.owner.patch(self.path+'/organization',json={'archived':False});self.assertEqual(self.owner.get('/api/artifacts?view=mine').json()['total'],1)
 def test_backup_restore_preserves_files_events_grants_and_rejects_tampering(self):
  self.owner.post(self.path+'/review',json=self.event(entry_type='note'))
  source=backup(self.store.root,self.root/'backups');target=self.root/'restored';proof=restore(source,target)
  self.assertEqual(proof['counts']['events'],1);self.assertEqual(proof['counts']['grants'],1)
  restored=create_app(target,origin=ORIGIN);client=TestClient(restored,base_url=ORIGIN);client.cookies.update(self.owner.cookies)
  self.assertEqual(client.get(self.path+'/render').status_code,200);self.assertEqual(client.get('/api/review/export').json()['count'],1)
  with self.assertRaises(ValueError):restore(source,target)
  f=next((source/'files').glob('*.html'));f.write_text('tampered')
  with self.assertRaises(ValueError):verify(source)
 def test_reading_one_thread_keeps_other_threads_unread(self):
  self.reviewer.post(self.path+'/review',json=self.event('first'))
  self.reviewer.post(self.path+'/review',json=self.event('second'))
  self.owner.post(self.path+'/seen',json={'thread':'first'})
  items=self.owner.get('/api/inbox').json()['items'];state={i['thread']['thread']:i['unread'] for i in items}
  self.assertEqual(state,{'first':False,'second':True})
 def test_admin_and_login_deep_link(self):
  self.assertEqual(self.reviewer.get('/api/admin').status_code,403)
  with patch.dict('os.environ',{'BOTTIFACT_ADMIN_EMAILS':'owner@example.com'}):self.assertEqual(self.owner.get('/api/admin').json()['counts']['artifacts'],1)
  self.assertEqual(target('/a/'+self.a['id']+'?thread=comment'),'/a/'+self.a['id']+'?thread=comment')
  self.assertEqual(target('//evil.test/a'),'/')

if __name__=='__main__':unittest.main()
