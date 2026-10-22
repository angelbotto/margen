import re
import tempfile
import unittest

from fastapi.testclient import TestClient
from portal.app import create_app, COOKIE, MEDIA_FRAMES

HTML='<title>Video</title><meta name="nota-documento" content="video-prueba"><figure data-embed="youtube" data-embed-id="M7lc1UVf-VE"></figure>'
ORIGIN='https://portal.test'


def directives(policy):
    return {part.split()[0]:part.split()[1:] for part in (p.strip() for p in policy.split(';')) if part}


class MediaEmbedPolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.app=create_app(self.tmp.name,origin=ORIGIN,issuer='https://identity.test',audience='our-app')
        store=self.app.state.store
        self.owner=TestClient(self.app,base_url=ORIGIN,headers={'Origin':ORIGIN})
        self.owner.cookies.set(COOKIE,store.session(store.user('owner@example.com','Propietaria')['id']))
        self.a=self.owner.post('/api/artifacts',json={'title':'Video','html':HTML}).json()

    def tearDown(self): self.tmp.cleanup()

    def test_reader_allows_only_exact_provider_frames(self):
        policy=directives(self.owner.get('/a/'+self.a['id']).headers['Content-Security-Policy'])
        self.assertEqual(policy['frame-src'],["'self'",'https://www.youtube-nocookie.com/embed/','https://www.instagram.com/p/','https://www.instagram.com/reel/'])
        self.assertEqual(tuple(policy['frame-src'][1:]),MEDIA_FRAMES)
        # Ni scripts ni conexiones del proveedor en el portal.
        self.assertEqual(policy['script-src'],["'self'"])
        self.assertEqual(policy['connect-src'],["'self'"])
        self.assertEqual(policy['frame-ancestors'],["'none'"])

    def test_library_and_other_pages_keep_the_closed_policy(self):
        for path in ('/','/login','/static/app.js'):
            policy=self.owner.get(path).headers['Content-Security-Policy']
            self.assertEqual(directives(policy)['frame-src'],["'self'"],path)

    def test_render_stays_opaque_and_without_provider_frames(self):
        response=self.owner.get('/api/artifacts/'+self.a['id']+'/render')
        policy=response.headers['Content-Security-Policy']
        self.assertTrue(policy.startswith('sandbox allow-scripts allow-downloads;'))
        self.assertNotIn('allow-same-origin',policy)
        self.assertNotIn('allow-popups',policy)
        self.assertNotIn('frame-src',policy)
        self.assertEqual(directives(policy)['connect-src'],["'none'"])
        self.assertNotIn('youtube',policy+response.headers.get('Referrer-Policy',''))
        self.assertEqual(response.headers['Referrer-Policy'],'no-referrer')

    def test_reader_iframe_sandbox_is_unchanged(self):
        page=self.owner.get('/a/'+self.a['id']).text
        frame=re.search(r'<iframe id="artifact-frame"[^>]*>',page)[0]
        self.assertIn('sandbox="allow-scripts allow-downloads"',frame)
        self.assertIn('/static/media-embeds.js',page)


if __name__=='__main__':
    unittest.main()
