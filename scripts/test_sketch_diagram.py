#!/usr/bin/env python3
"""Source safety and semantics, independent of the hand-drawn coordinates."""
import copy
import json
from pathlib import Path
import unittest
from html.parser import HTMLParser
from sketch_diagram import render, ICONS

ROOT = Path(__file__).resolve().parents[1]
SOURCE = json.loads((ROOT/'packages/core/recipes/sketch-diagram/source.json').read_text())


class Nodes(HTMLParser):
    def __init__(self, markup):
        super().__init__(); self.tags = []; self.ids = []; self.feed(markup)
    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        attrs = dict(attrs)
        if 'id' in attrs: self.ids.append(attrs['id'])


class SketchTests(unittest.TestCase):
    def test_stable_identity_and_semantic_source(self):
        markup = render(SOURCE)
        parsed = Nodes(markup)
        self.assertEqual(parsed.tags.count('li'), len(SOURCE['nodes']))
        self.assertEqual(len(parsed.ids), len(set(parsed.ids)))
        for node in SOURCE['nodes']:
            self.assertIn(SOURCE['id']+'-'+node['id'], parsed.ids)
            self.assertIn(node['body'], markup)
        edited = copy.deepcopy(SOURCE); edited['nodes'][1]['body'] = 'New evidence'
        self.assertEqual(parsed.ids, Nodes(render(edited)).ids)
        self.assertNotIn('script', parsed.tags)
        self.assertEqual(render(SOURCE), markup)

    def test_untrusted_labels_are_text(self):
        source = copy.deepcopy(SOURCE)
        source['nodes'][0]['title'] = '<script>alert(1)</script>'
        source['transitions'][0] = '<img src=x onerror=alert(1)>'
        markup = render(source)
        self.assertNotIn('script', Nodes(markup).tags)
        self.assertNotIn('img', Nodes(markup).tags)
        self.assertIn('&lt;script&gt;', markup)

    def test_invalid_sources_fail_before_output(self):
        variants = [None, {}, {**SOURCE, 'schema':'other'}, {**SOURCE, 'id':'" onload="x'},
                    {**SOURCE, 'nodes':[]}, {**SOURCE, 'transitions':[]},
                    {**SOURCE, 'nodes':[SOURCE['nodes'][0]]*3},
                    {**SOURCE, 'nodes':[None]*3}, {**SOURCE, 'title':'x'*181}]
        for source in variants:
            with self.subTest(source=source), self.assertRaises(ValueError): render(source)

    def test_generated_specimen_is_current(self):
        self.assertEqual(render(SOURCE), (ROOT/'packages/core/recipes/sketch-diagram/example.html').read_text())

    def test_symbols_preserve_labels_and_reject_arbitrary_markup(self):
        for icon in ICONS:
            source = copy.deepcopy(SOURCE)
            source['nodes'][0]['icon'] = icon
            markup = render(source)
            self.assertIn('class="sketch-symbol"', markup)
            self.assertIn(source['nodes'][0]['title'], markup)
            self.assertIn('aria-hidden="true"', markup)
        for icon in ('<svg onload="alert(1)">', 'unknown', {}, ['person']):
            source = copy.deepcopy(SOURCE); source['nodes'][0]['icon'] = icon
            with self.assertRaises(ValueError): render(source)


if __name__ == '__main__': unittest.main()
