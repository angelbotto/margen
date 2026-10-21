import unittest
from portal.reader_style import without_embedded_flow

OLD = '/* EDITORIAL FLOW START */.legacy-flow { margin:0 }/* EDITORIAL FLOW END */'


class ReaderStylesTest(unittest.TestCase):
    def test_only_marked_rules_change(self):
        html = '<head>\n<style data-nota-fuente="packages/core/styles/artifact.css">p{color:red}\n'+OLD+'\nh2{color:blue}</style></head><p>Evidence</p>'
        self.assertEqual(without_embedded_flow(html), html.replace(OLD, ''))

    def test_script_and_escaped_examples_remain_verbatim(self):
        html = '<script>const example = "<style>'+OLD+'</style>";</script><pre>&lt;style&gt;'+OLD+'&lt;/style&gt;</pre>'
        self.assertEqual(without_embedded_flow(html), html)

    def test_literal_text_containers_across_python_versions(self):
        for tag in ('textarea','title','xmp','iframe','noembed','noframes','plaintext'):
            html='<'+tag+'><style>'+OLD+'</style></'+tag+'>'
            with self.subTest(tag=tag):
                self.assertEqual(without_embedded_flow(html),html)

    def test_offsets_follow_parser_line_numbers(self):
        for separator in ('\u2028', '\v', '\r', '\r\n', '\n'):
            html='<p>A'+separator+'B</p>\n<style>'+OLD+'</style>'
            with self.subTest(separator=repr(separator)):
                self.assertEqual(without_embedded_flow(html),html.replace(OLD,''))

    def test_multiple_styles_and_idempotence(self):
        html = '<STYLE>\n'+OLD+'\n</STYLE><style>p{margin:0}</style><style>'+OLD+'</style>'
        result = without_embedded_flow(html)
        self.assertEqual(result, html.replace(OLD, ''))
        self.assertEqual(without_embedded_flow(result), result)
        self.assertEqual(without_embedded_flow('<style>'+OLD), '<style>'+OLD)




class EditorialReferenceRefreshTest(unittest.TestCase):
    def refresh(self, html):
        from portal.reader_style import refresh_editorial_reference
        return refresh_editorial_reference(html, '.hoja{color:blue}', 'window.currentCode = true;')

    def test_refreshes_only_marked_styles_and_module(self):
        old = '/* EDITORIAL REFERENCE START */.old{}/* EDITORIAL REFERENCE END */'
        source = ('<html><head><style>p{color:red}'+old+'</style></head><body><main class="hoja"></main>'
                  '<script data-nota-modulo="packages/core/components/code.js">old();</script>'
                  '<script>const example="<style>'+old+'</style>";</script><style>.custom{color:red}</style></body></html>')
        result = self.refresh(source)
        self.assertIn('p{color:red}', result)
        self.assertIn('<script>const example="<style>'+old+'</style>";</script>', result)
        self.assertIn('<script data-nota-modulo="packages/core/components/code.js">\nwindow.currentCode = true;\n</script>', result)
        self.assertIn('<style>.custom{color:red}</style><style data-margen-editorial-reference>', result)
        self.assertEqual(self.refresh(result), result)
        self.assertIn('old();', source)

    def test_preserves_non_margen_presentations_and_literal_html(self):
        for content in ('<main>Custom app</main>', '<main class="hoja" data-presentation></main>',
                        '<main class="hoja" data-ritmo="propio"></main>',
                        '<textarea><main class="hoja"></main></textarea>',
                        '<script>const fake=`<main class="hoja"></main>`</script>'):
            with self.subTest(content=content):
                self.assertEqual(self.refresh(content), content)

    def test_custom_scripts_and_incomplete_blocks_are_not_rewritten(self):
        for script in ('<script data-nota-modulo="mine/code.js">custom();</script>',
                       '<script data-nota-modulo="packages/core/components/code.js" type="application/json">{"own":1}</script>',
                       '<script data-nota-modulo="packages/core/components/code.js" src="own.js"></script>',
                       '<script data-nota-modulo="packages/core/components/code.js">unfinished();'):
            result = self.refresh('<main class="hoja"></main>' + script)
            self.assertIn(script, result)

    def test_real_elements_only_across_line_separators(self):
        for separator in ('\u2028', '\v', '\r', '\r\n', '\n'):
            source = '<p>A'+separator+'B</p><main class="hoja"></main><style>.own{}</style>'
            self.assertTrue(self.refresh(source).startswith(source))


class EditorialReferenceInertTemplateTest(unittest.TestCase):
    def test_templates_do_not_capture_styles_or_document_detection(self):
        from portal.reader_style import refresh_editorial_reference
        source = '<style>h1{font-size:10px}</style><main class="hoja"><h1>Visible</h1></main><template><style>.card{color:red}</style><script data-nota-modulo="packages/core/components/code.js">inert();</script></template>'
        result = refresh_editorial_reference(source, 'h1{font-size:50px}', 'current();')
        self.assertIn('</style><style data-margen-editorial-reference>h1{font-size:50px}</style><main', result)
        self.assertIn('<template><style>.card{color:red}</style><script data-nota-modulo="packages/core/components/code.js">inert();</script></template>', result)
        inert = '<template><main class="hoja"></main><style data-margen-editorial-reference>inert{}</style></template>'
        self.assertEqual(refresh_editorial_reference(inert, 'current{}', 'current();'), inert)

    def test_noscript_fallback_is_not_an_insertion_target(self):
        from portal.reader_style import refresh_editorial_reference
        source='<main class="hoja"></main><noscript><style>p{color:red}</style></noscript>'
        result=refresh_editorial_reference(source,'.hoja{color:blue}','current();')
        self.assertTrue(result.startswith('<style data-margen-editorial-reference>'))
        self.assertTrue(result.endswith(source))

if __name__ == '__main__': unittest.main()
