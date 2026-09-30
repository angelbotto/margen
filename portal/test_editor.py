import copy
import json
import unittest
from portal import test_app as fixtures
from portal.block_source import import_document, render_document, validate_document, changes

HTML='''<title>Report</title><meta name="nota-documento" content="editor-report"><meta name="margen-format" content="document"><style>body{color:red}</style><main class="nota-estandar"><header class="cabecera" id="start"><h1>Report</h1></header><section class="prosa" id="s1"><h2 id="heading">Section</h2><p id="paragraph">Hello <strong>world</strong> <a href="https://example.com">link</a></p><ul><li>First</li><li>Second</li></ul></section><figure class="pieza ancho tabla-editorial"><div class="tabla-caja"><table id="original-table"><thead><tr><th>Name</th><th>Value</th></tr></thead><tbody><tr><td>Alpha</td><td>10</td></tr></tbody></table></div></figure><figure id="map"><svg viewBox="0 0 10 10"><text>Keep diagram</text></svg></figure><footer class="pie">Footer</footer></main><script>const trustedRuntime = 1;</script>'''

class SourceTests(unittest.TestCase):
    def setUp(self):self.doc,self.template=import_document(HTML,'v1','Report')
    def test_semantic_import_preserves_markup_and_opaque(self):
        rendered=render_document(self.doc,self.template)
        self.assertIn('<strong>world</strong>',rendered)
        self.assertIn('<a href="https://example.com">link</a>',rendered)
        self.assertIn('<figure id="map"><svg',rendered)
        self.assertIn('<script>const trustedRuntime = 1;</script>',rendered)
        kinds=[b['type'] for r in self.doc['regions'] for b in r['blocks']]
        self.assertIn('table',kinds);self.assertIn('opaque',kinds)
    def test_escape_user_text_and_preserve_existing_anchors(self):
        b=self.doc['regions'][0]['blocks'][1]
        b['runs']=[{'text':'<img src=x onerror=alert(1)>','marks':['bold']}]
        doc=validate_document(self.doc,self.doc,self.template)
        html=render_document(doc,self.template)
        self.assertIn('&lt;img',html);self.assertIn('id="paragraph"',html);self.assertNotIn('<img',html)
    def test_reject_identity_tampering_and_opaque_edits(self):
        bad=copy.deepcopy(self.doc);bad['regions'][0]['blocks'].append(copy.deepcopy(bad['regions'][0]['blocks'][0]))
        with self.assertRaises(ValueError):validate_document(bad,self.doc,self.template)
        bad=copy.deepcopy(self.doc);bad['regions'][-1]['blocks'][0]['label']='Tampered'
        with self.assertRaises(ValueError):validate_document(bad,self.doc,self.template)
        bad=copy.deepcopy(self.doc);bad['regions'][0]['blocks'][1]['runs']=[{'text':'x','marks':[],'href':'javascript:alert(1)'}]
        with self.assertRaises(ValueError):validate_document(bad,self.doc,self.template)
    def test_title_move_delete_and_table_limits(self):
        after=copy.deepcopy(self.doc);after['title']='New title';after['regions'][0]['blocks'].reverse()
        kinds={c['kind'] for c in changes(self.doc,after)};self.assertIn('moved',kinds);self.assertIn('edited',kinds)
        html=render_document(after,self.template);self.assertIn('<h1>New title</h1>',html);self.assertIn('<title>New title</title>',html)
        table=next(b for r in after['regions'] for b in r['blocks'] if b['type']=='table');table['rows']=[['x'],['y','z']]
        with self.assertRaises(ValueError):validate_document(after,self.doc,self.template)
    def test_reject_presentation(self):
        with self.assertRaises(ValueError):import_document(HTML.replace('content="document"','content="presentation"'),'v','Title')
    def test_reimport_retains_table_identity_and_nested_anchors(self):
        rendered=render_document(self.doc,self.template)
        again,_=import_document(rendered,'v2','Report')
        before=next(b for r in self.doc['regions'] for b in r['blocks'] if b['type']=='table')
        after=next(b for r in again['regions'] for b in r['blocks'] if b['type']=='table')
        self.assertEqual(before['id'],after['id'])
        anchored=HTML.replace('<td>Alpha','<td id="anchored-cell">Alpha')
        doc,template=import_document(anchored,'v3','Report')
        self.assertIn('<td id="anchored-cell">Alpha',render_document(doc,template))
        self.assertTrue(any(b['type']=='opaque' and 'Alpha' in b['label'] for r in doc['regions'] for b in r['blocks']))
    def test_heading_edit_updates_navigation(self):
        html=HTML.replace('<section class="prosa"','<nav class="indice"><ol><li><a href="#heading">Section</a></li></ol></nav><section class="prosa"')
        doc,template=import_document(html,'v1','Report')
        doc['regions'][0]['blocks'][0]['runs']=[{'text':'New section','marks':[]}]
        result=render_document(doc,template)
        self.assertIn('<a href="#heading">New section</a>',result)
    def test_unwrapped_text_between_blocks_is_preserved(self):
        html=HTML.replace('</h2><p','</h2>Important unwrapped context<!-- retained marker --><p')
        doc,template=import_document(html,'v1','Report')
        doc['regions'][0]['blocks'][0]['runs']=[{'text':'Edited heading','marks':[]}]
        self.assertIn('Important unwrapped context<!-- retained marker -->',render_document(doc,template))

class EditorTests(unittest.TestCase):
    tearDown=fixtures.PortalTests.tearDown
    client=fixtures.PortalTests.client
    def setUp(self):
        fixtures.PortalTests.setUp(self)
        self.a=self.owner.post('/api/artifacts',json={'title':'Report','html':HTML}).json();self.path='/api/artifacts/'+self.a['id']
    def draft(self):
        r=self.owner.get(self.path+'/editor');self.assertEqual(r.status_code,200,r.text);return r.json()
    def save(self,d):
        r=self.owner.put(self.path+'/editor',json={k:d[k] for k in ('revision','base_version','document')});self.assertEqual(r.status_code,200,r.text);return r.json()
    def checkpoint(self,d,key='attempt-1'):
        r=self.owner.post(self.path+'/editor/checkpoint',json={'revision':d['revision'],'request_id':key});self.assertEqual(r.status_code,200,r.text);return r.json()
    def test_draft_checkpoint_release_and_identity(self):
        d=self.draft();d['document']['title']='Edited by owner';d=self.save(d)
        self.assertEqual(self.owner.get(self.path).json()['current_version'],self.a['version'])
        c=self.checkpoint(d);self.assertEqual(self.checkpoint(d)['version'],c['version'])
        r=self.owner.post(self.path+'/release',json={'version':c['version'],'expected_current':d['base_version']});self.assertEqual(r.status_code,200,r.text)
        html=self.owner.get(self.path+'/render').text;self.assertIn('<h1>Edited by owner</h1>',html)
        history=self.owner.get(self.path+'/history').json();self.assertEqual(history['versions'][0]['author'],'Propietaria')
        self.assertEqual(history['versions'][0]['changes'][0]['id'],'document-title')
        self.assertFalse(self.draft()['stale']);self.assertEqual(self.draft()['base_version'],c['version'])
        self.assertEqual(self.owner.get(self.path).json()['visibility'],'private')
        retry=self.owner.post(self.path+'/release',json={'version':c['version'],'expected_current':d['base_version']})
        self.assertEqual(retry.status_code,200,retry.text)
    def test_other_account_editor_role_and_csrf(self):
        for suffix in ['/editor','/source','/history']:
            self.assertEqual(self.other.get(self.path+suffix).status_code,404)
        self.owner.put(self.path+'/access',json={'visibility':'invited','comments':'reviewers','guests':False,'grants':[{'email':'other@example.com','role':'editor'}]})
        self.assertEqual(self.other.get(self.path+'/editor').status_code,403)
        self.assertEqual(self.other.get(self.path+'/source').status_code,200)
        d=self.draft();self.assertEqual(self.owner.put(self.path+'/editor',headers={'Origin':'https://evil.test'},json=d).status_code,403)
    def test_two_tabs_and_failed_retry_do_not_overwrite(self):
        d=self.draft();other=copy.deepcopy(d);d['document']['title']='Saved';saved=self.save(d)
        other['document']['title']='Stale';self.assertEqual(self.owner.put(self.path+'/editor',json=other).status_code,409)
        self.assertEqual(self.draft()['document']['title'],'Saved')
        self.assertEqual(self.save(saved)['revision'],saved['revision'])
        c=self.checkpoint(saved);self.assertEqual(self.owner.post(self.path+'/editor/checkpoint',json={'revision':0,'request_id':'attempt-1'}).status_code,409)
    def test_restore_preserves_old_versions_and_is_not_publication(self):
        d=self.draft();d['document']['title']='New';d=self.save(d);c=self.checkpoint(d)
        self.owner.post(self.path+'/release',json={'version':c['version'],'expected_current':d['base_version']})
        current=self.draft();r=self.owner.post(self.path+'/editor/restore',json={'version':self.a['version'],'expected_current':c['version'],'revision':current['revision']});self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(self.owner.get(self.path).json()['current_version'],c['version']);self.assertEqual(r.json()['document']['title'],'Report')
        restored=self.checkpoint(r.json(),'restore-checkpoint');self.assertNotEqual(restored['version'],self.a['version'])
        self.assertEqual(len(self.owner.get(self.path+'/history').json()['versions']),3)
    def test_agent_stale_upload_and_source(self):
        d=self.save(self.draft());self.checkpoint(d)
        self.assertEqual(self.owner.post(self.path+'/versions',json={'title':'Agent','html':HTML}).status_code,409)
        r=self.owner.post(self.path+'/versions',json={'title':'Agent','html':HTML,'mode':'draft','expected_current':self.a['version']});self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(self.owner.get(self.path+'/source').json()['document']['schema'],'margen-blocks/1')
    def test_preview_is_sandboxed_and_foreign_restore_rejected(self):
        d=self.save(self.draft());r=self.owner.get(self.path+'/editor/preview')
        self.assertIn('sandbox allow-scripts',r.headers['content-security-policy']);self.assertNotIn('allow-same-origin',r.headers['content-security-policy'])
        foreign=self.owner.post('/api/artifacts',json={'title':'Other','html':HTML.replace('editor-report','other-editor')}).json()
        r=self.owner.post(self.path+'/editor/restore',json={'version':foreign['version'],'expected_current':self.a['version'],'revision':d['revision']});self.assertEqual(r.status_code,404)
    def test_unsaved_draft_survives_new_head(self):
        d=self.save(self.draft());c=self.checkpoint(d);d['document']['title']='Later local work';d=self.save(d)
        self.owner.post(self.path+'/release',json={'version':c['version'],'expected_current':self.a['version']})
        latest=self.draft();self.assertTrue(latest['stale']);self.assertEqual(latest['document']['title'],'Later local work')
        self.assertEqual(self.owner.put(self.path+'/editor',json=latest).status_code,409)
    def test_stale_agent_proposal_cannot_publish_against_new_head(self):
        d=self.save(self.draft())
        proposal=self.owner.post(self.path+'/versions',json={'title':'Agent','html':HTML,'mode':'draft','expected_current':self.a['version']}).json()
        d['document']['title']='Human changes';d=self.save(d);checkpoint=self.checkpoint(d)
        self.owner.post(self.path+'/release',json={'version':checkpoint['version'],'expected_current':self.a['version']})
        response=self.owner.post(self.path+'/release',json={'version':proposal['version'],'expected_current':checkpoint['version']})
        self.assertEqual(response.status_code,409,response.text)
        self.assertEqual(self.owner.get(self.path).json()['title'],'Human changes')
    def test_malformed_restore_version_is_validation_error(self):
        response=self.owner.post(self.path+'/editor/restore',json={'version':[],'expected_current':self.a['version'],'revision':0})
        self.assertEqual(response.status_code,422,response.text)
    def test_assignment_contains_latest_human_source(self):
        d=self.draft();d['document']['title']='Human decision';d=self.save(d);c=self.checkpoint(d)
        self.owner.post(self.path+'/release',json={'version':c['version'],'expected_current':self.a['version']})
        event=fixtures.PortalTests.event(self)
        response=self.owner.post(self.path+'/review',json=event);self.assertEqual(response.status_code,200,response.text)
        response=self.owner.post('/api/creator/jobs',json={'artifact':self.a['id'],'threads':['test-event-1'],'target':{'agent':'Codex'}})
        self.assertEqual(response.status_code,200,response.text)
        packet=self.owner.get('/api/creator/jobs/'+response.json()['id']).json()['packet']
        self.assertEqual(packet['base_version'],c['version'])
        self.assertEqual(packet['editable_source']['document']['title'],'Human decision')
        self.assertEqual(packet['editable_source']['changes'][0]['after'],'Human decision')
        bundle=self.owner.post('/api/review/bundle',json={'artifact':self.a['id'],'threads':[]}).json()
        self.assertEqual(bundle['editable_source']['document']['title'],'Human decision')
        self.assertIn('Human decision',bundle['text'])
        self.owner.put(self.path+'/access',json={'visibility':'invited','comments':'reviewers','guests':False,'grants':[{'email':'other@example.com','role':'editor'}]})
        bundle=self.other.post('/api/review/bundle',json={'artifact':self.a['id'],'threads':[]}).json()
        self.assertIsNone(bundle['editable_source'])

if __name__=='__main__':unittest.main()

class ComponentPreviewTests(unittest.TestCase):
    setUp=EditorTests.setUp
    tearDown=EditorTests.tearDown
    client=EditorTests.client
    draft=EditorTests.draft
    save=EditorTests.save
    checkpoint=EditorTests.checkpoint
    def test_visuals_before_autosave_are_isolated_and_owner_only(self):
        d=self.draft();block=next(b for r in d['document']['regions'] for b in r['blocks'] if b['type']=='opaque')
        route=self.path+'/editor/component/'+block['id']
        r=self.owner.get(route);self.assertEqual(r.status_code,200,r.text)
        self.assertIn('<svg',r.text);self.assertIn('Keep diagram',r.text)
        self.assertIn('body{color:red}',r.text)
        self.assertNotIn('Hello <strong>',r.text)
        self.assertNotIn('trustedRuntime',r.text)
        policy=r.headers['Content-Security-Policy']
        self.assertIn('sandbox allow-scripts;',policy);self.assertNotIn('allow-same-origin',policy)
        self.assertIn("script-src 'sha256-",policy);self.assertNotIn("script-src 'unsafe-inline'",policy)
        self.assertEqual(self.other.get(route).status_code,404)
        self.assertEqual(self.owner.get(self.path+'/editor/component/missing').status_code,404)
        normal=d['document']['regions'][0]['blocks'][0]['id']
        self.assertEqual(self.owner.get(self.path+'/editor/component/'+normal).status_code,404)
        self.owner.put(self.path+'/access',json={'visibility':'invited','comments':'reviewers','guests':False,'grants':[{'email':'other@example.com','role':'editor'}]})
        self.assertEqual(self.other.get(route).status_code,403)
    def test_visuals_survive_checkpoint_and_restore_without_source_changes(self):
        d=self.draft();block=next(b for r in d['document']['regions'] for b in r['blocks'] if b['type']=='opaque')
        route=self.path+'/editor/component/'+block['id'];before=self.owner.get(route).text
        d['document']['title']='Surrounding edit';d=self.save(d)
        self.assertEqual(self.owner.get(route).text,before)
        checkpoint=self.checkpoint(d)
        self.assertIn('<figure id="map"><svg',self.owner.get(self.path+'/render?version='+checkpoint['version']).text)
        self.assertEqual(self.owner.get(route).text,before)
    def test_large_image_fonts_and_hostile_markup(self):
        from portal.component_preview import render_component
        image='data:image/png;base64,'+'A'*150000
        html=HTML.replace('<svg viewBox="0 0 10 10"><text>Keep diagram</text></svg>', '<img alt="Evidence" src="'+image+'" onerror="alert(1)"><script>alert(2)</script><iframe src="https://example.com"></iframe>')
        html=html.replace('body{color:red}','@font-face{font-family:Sketch;src:url(data:font/woff2;base64,AAAA)}body{color:red}')
        doc,template=import_document(html,'v-large','Images')
        b=next(b for r in doc['regions'] for b in r['blocks'] if b['type']=='opaque')
        result=render_component(doc,template,b['id'])
        self.assertIn(image,result);self.assertIn('@font-face',result)
        self.assertNotIn('onerror',result);self.assertNotIn('alert(2)',result);self.assertNotIn('<iframe',result)
