"""Reader activity must preserve artifact, conversation and personal-note boundaries."""
from unittest.mock import patch
from portal.test_app import PortalTests, HTML


class ActivityTests(PortalTests):
    def share_activity(self):
        return self.owner.put(self.path + '/activity', json={'shared': True})

    def test_activity_hidden_until_creator_shares_and_requires_artifact_access(self):
        self.assertEqual(self.other.get(self.path + '/activity').status_code, 404)
        self.access(visibility='public', comments='readers', grants=[])
        self.assertEqual(self.guest.get(self.path + '/activity').json(), {'visible': False})
        self.assertEqual(self.other.put(self.path + '/activity', json={'shared': True}).status_code, 404)
        self.assertEqual(self.share_activity().status_code, 200)
        self.assertTrue(self.guest.get(self.path + '/activity').json()['visible'])
        self.owner.put(self.path + '/access', json={'visibility': 'private'})
        self.assertEqual(self.guest.get(self.path + '/activity').status_code, 404)

    def test_only_visible_comments_and_replies_count_not_notes_deleted_or_drafts(self):
        self.access(); self.share_activity()
        self.owner.post(self.path + '/review', json=self.event(id='comment'))
        self.other.post(self.path + '/review', json=self.event(id='reply', kind='reply', thread='comment'))
        self.other.post(self.path + '/review', json=self.event(id='private', entry_type='note'))
        self.owner.post(self.path + '/review', json=self.event(id='deleted'))
        self.owner.post(self.path + '/review', json=self.event(id='delete', kind='delete', thread='deleted'))
        draft = self.owner.post(self.path + '/versions', json={'title':'Draft','html':HTML+'<p>Draft</p>','mode':'draft'}).json()['version']
        self.owner.post(self.path + '/review', json=self.event(id='draft-comment', version=draft))
        data = self.owner.get(self.path + '/activity').json()
        self.assertEqual(data['comments'], 1); self.assertEqual(data['messages'], 2)
        self.assertEqual(data['participant_count'], 2)
        self.assertEqual(set(data['participants'][0]), {'name', 'verified'})
        self.assertNotIn('example.com', str(data))
        self.access(visibility='public', comments='reviewers', grants=[])
        data = self.guest.get(self.path + '/activity').json()
        self.assertEqual(data['comments'], 0); self.assertEqual(data['participants'], [])

    def test_owner_scoped_defaults_and_override(self):
        self.owner.put('/api/creator/analytics', json={'enabled': True, 'share_with_readers': True})
        self.access(visibility='public', comments='readers', grants=[])
        self.assertTrue(self.guest.get(self.path + '/activity').json()['visible'])
        self.owner.put(self.path + '/activity', json={'shared': False})
        self.assertEqual(self.guest.get(self.path + '/activity').json(), {'visible': False})
        self.assertEqual(self.owner.put('/api/creator/analytics', json={'enabled': True, 'share_with_readers': 'yes'}).status_code, 422)

    def test_umami_filtered_period_and_unavailable_not_zero_unique(self):
        self.owner.put('/api/creator/analytics', json={'enabled': True})
        self.access(visibility='public', comments='readers', grants=[]); self.share_activity()
        self.guest.post(self.path + '/visit', json={})
        with patch.object(self.app.state.umami_reports, 'stats', return_value={'views':5,'visitors':3}) as stats:
            data=self.guest.get(self.path+'/activity?days=7').json()
            self.assertEqual(data['views'],5); self.assertEqual(data['visitors'],3)
            self.assertEqual(stats.call_args.args[0],self.a['id'])
            self.assertEqual(data['days'],7)
        with patch.object(self.app.state.umami_reports, 'stats', return_value=None):
            data=self.guest.get(self.path+'/activity').json()
            self.assertEqual(data['views'],1); self.assertIsNone(data['visitors'])
        self.assertEqual(self.guest.get(self.path+'/activity?days=0').status_code,422)


import unittest
from urllib.parse import urlsplit, parse_qs
from portal.umami import UmamiReports

class UmamiTests(unittest.TestCase):
    @patch.dict('os.environ', {'MARGEN_UMAMI_TOKEN':'secret','MARGEN_UMAMI_API_VERSION':'3'})
    def test_v3_exact_path_and_cache(self):
        client=UmamiReports(lambda:{'origin':'https://umami.example','website':'site'})
        with patch.object(client,'request',return_value={'pageviews':12,'visitors':4}) as request:
            self.assertEqual(client.stats('artifact-one',1000,5000)['visitors'],4)
            query=parse_qs(urlsplit(request.call_args.args[0]).query)
            self.assertEqual(query['path'],['/a/artifact-one']); self.assertNotIn('url',query)
            client.stats('artifact-one',1000,6000); self.assertEqual(request.call_count,1)
            client.stats('artifact-two',1000,6000); self.assertEqual(request.call_count,2)

    @patch.dict('os.environ', {'MARGEN_UMAMI_TOKEN':'secret','MARGEN_UMAMI_API_VERSION':'2'})
    def test_v2_adapter_and_failure(self):
        client=UmamiReports(lambda:{'origin':'https://umami.example','website':'site'})
        with patch.object(client,'request',return_value={'pageviews':{'value':8},'visitors':{'value':2}}) as request:
            self.assertEqual(client.stats('a',1000,5000)['views'],8)
            self.assertIn('url=%2Fa%2Fa',request.call_args.args[0])
        with patch.object(client,'request',side_effect=ValueError('secret provider error')):
            self.assertIsNone(client.stats('b',1000,5000))

    @patch.dict('os.environ', {'MARGEN_UMAMI_SHARE_ID':'privatecapability123','MARGEN_UMAMI_TOKEN':''})
    def test_shared_reporting_is_website_scoped_and_not_sent_as_admin_auth(self):
        client=UmamiReports(lambda:{'origin':'https://umami.example','website':'site'})
        with patch.object(client,'request',side_effect=[{'websiteId':'site','token':'read-token'},{'pageviews':7,'visitors':2}]) as request:
            self.assertEqual(client.stats('a',1000,5000)['visitors'],2)
            self.assertEqual(request.call_args.kwargs['share_token'],'read-token')
            self.assertFalse(request.call_args.kwargs['token'])
        client=UmamiReports(lambda:{'origin':'https://umami.example','website':'site'})
        with patch.object(client,'request',return_value={'websiteId':'other','token':'wrong-site'}) as request:
            self.assertIsNone(client.stats('a',1000,5000)); self.assertEqual(request.call_count,1)
