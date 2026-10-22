"""Regression probes for reviewed upload expansion and metadata denial of service."""
import os
import time
import unittest
from unittest.mock import patch
from fastapi import HTTPException
from portal.uploads import Site, title_of, with_document_id, warnings_for, UPLOAD_SLOTS
from portal import test_app as app_tests


class ExpansionTests(unittest.TestCase):
    def test_repeated_asset_rejected_before_building_huge_output(self):
        site = Site({'index.html': b'<img src="a.png">' * 1600, 'a.png': os.urandom(65536)}, 'index.html')
        start = time.monotonic()
        with self.assertRaises(HTTPException) as caught:
            site.render()
        self.assertEqual(caught.exception.status_code, 422)
        self.assertEqual(len(site.encoded), 1)
        self.assertLess(time.monotonic() - start, 3)

    def test_css_fanout_is_bounded_even_with_tiny_files(self):
        site = Site({'index.html': b'<link rel="stylesheet" href="a.css">',
                     'a.css': b'@import "b.css";' * 60, 'b.css': b'@import "c.css";' * 60,
                     'c.css': b'@import "d.css";' * 60, 'd.css': b'body{color:red}'}, 'index.html')
        with self.assertRaises(HTTPException): site.render()
        self.assertLessEqual(site.css_imports, 129)

    def test_unclosed_metadata_does_not_scan_quadratically(self):
        start = time.monotonic()
        self.assertEqual(title_of('<title>' * 200000, 'Fallback'), 'Fallback')
        self.assertIn('nota-documento', with_document_id('<head ' * 200000, 'stable'))
        warnings_for('<meta ' * 200000)
        self.assertLess(time.monotonic() - start, 3)

    def test_many_elements_have_a_bound(self):
        site = Site({'index.html': b'<i>' * 30001}, 'index.html')
        with self.assertRaises(HTTPException): site.render()


class UploadConcurrencyTests(unittest.TestCase):
    setUp = app_tests.PortalTests.setUp
    tearDown = app_tests.PortalTests.tearDown
    client = app_tests.PortalTests.client
    def test_busy_import_does_not_read_or_process_another_file(self):
        self.assertTrue(UPLOAD_SLOTS.acquire(False)); self.assertTrue(UPLOAD_SLOTS.acquire(False))
        try:
            self.assertEqual(self.owner.post('/api/uploads/inspect',json={}).status_code, 503)
            self.assertEqual(self.owner.post('/api/uploads',json={}).status_code, 503)
        finally:
            UPLOAD_SLOTS.release(); UPLOAD_SLOTS.release()

    def test_revision_requires_current_version_even_for_plain_html(self):
        import base64
        r=self.owner.post('/api/uploads',json={'name':'plain.html','data':base64.b64encode(b'<h1>Revision</h1>').decode(),'artifact':self.a['id']})
        self.assertEqual(r.status_code,409)
