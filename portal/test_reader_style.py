import unittest
from portal.reader_style import without_embedded_flow, with_initial_theme, initial_appearance, head_insertion_point

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

    def test_headless_documents_preserve_doctype_and_leading_comments(self):
        prefixes = ('<!doctype html>', '\n\t<!DOCTYPE html>', '<!-- editorial note -->\n<!DOCTYPE html>',
                    '<!-- <!doctype html> is only an example -->\n<!doctype html>')
        bodies = ('<main class="hoja"><h1>Evidence</h1></main>',
                  '<html><head><meta charset="utf-8"><body><main class="hoja">Evidence</main></body></html>')
        for prefix in prefixes:
            for body in bodies:
                with self.subTest(prefix=prefix, body=body):
                    source = prefix + body
                    result = self.refresh(source)
                    self.assertTrue(result.startswith(prefix+'<style data-margen-editorial-reference>'))
                    self.assertTrue(result.endswith(body))
                    self.assertEqual(self.refresh(result), result)

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

    def test_declared_light_or_dark_palette_paints_from_the_first_frame(self):
        registry = '<script>/* REGISTRO TEMAS */ const themeRegistry = {"familias":[{"id":"editorial","light":"light","dark":"dark"},{"id":"sea","light":{"papel":"#fff"},"dark":"sea"}]};</script>'
        meta = lambda family, mode: '<meta name="nota-tema-inicial" content="'+family+'"><meta name="nota-modo-inicial" content="'+mode+'">'
        dark = '<title>T</title>'+meta('editorial','dark')+'<p>x</p>'+registry
        self.assertEqual(with_initial_theme(dark), '<html data-theme="dark">'+dark)
        self.assertEqual(initial_appearance(dark), {'mode': 'dark'})
        typed = '<!doctype html>'+dark
        self.assertEqual(with_initial_theme(typed), '<!doctype html><html data-theme="dark">'+dark)
        tagged = '<!doctype html><html lang="es"><head>'+meta('editorial','light')+'</head><body>'+registry
        self.assertEqual(with_initial_theme(tagged), tagged.replace('<html lang', '<html data-theme="light" lang'))
        for unchanged in ('<html data-theme="hacker">'+meta('editorial','dark')+registry,  # author choice wins
                          meta('editorial','system')+registry,                           # follows the device
                          meta('sea','light')+registry,                                  # inline palette, left to reader.js
                          meta('editorial','dark'),                                      # no Margen reader registry
                          '<p>Documento ajeno</p>'):
            with self.subTest(html=unchanged[:60]):
                self.assertEqual(with_initial_theme(unchanged), unchanged)
        self.assertEqual(initial_appearance('<p>Documento ajeno</p>'), {'mode': None})

    def test_initial_theme_keeps_the_doctype_first_and_leaves_inert_markup_alone(self):
        registry = '<script>/* REGISTRO TEMAS */ const themeRegistry = {"familias":[{"id":"editorial","light":"light","dark":"dark"}]};</script>'
        meta = '<meta name="nota-tema-inicial" content="editorial"><meta name="nota-modo-inicial" content="dark">'
        body = '<title>T</title>' + meta + '<p>x</p>' + registry
        cases = {
            # A comment before the doctype: <html> must not land ahead of the doctype (quirks mode).
            '<!-- generado -->\n<!DOCTYPE html>' + body:
                '<!-- generado -->\n<!DOCTYPE html><html data-theme="dark">' + body,
            '\ufeff<!DOCTYPE html>' + body: '\ufeff<!DOCTYPE html><html data-theme="dark">' + body,
            # Tag-like text in comments, scripts and templates is not the root element.
            '<!DOCTYPE html><!-- <html data-x> <body> --><script>"<html>"</script>' + body:
                '<!DOCTYPE html><html data-theme="dark"><!-- <html data-x> <body> --><script>"<html>"</script>' + body,
            '<!DOCTYPE html><template><html lang="x"></template>' + body:
                '<!DOCTYPE html><html data-theme="dark"><template><html lang="x"></template>' + body,
            # A quoted ">" in an attribute does not cut the real tag short.
            '<!-- a --><!DOCTYPE html><html data-x="a>b" lang="es"><head>' + meta + '</head><body>' + registry:
                '<!-- a --><!DOCTYPE html><html data-theme="dark" data-x="a>b" lang="es"><head>' + meta + '</head><body>' + registry,
            # A real <html> after leading content still owns the root; its attributes merge onto it.
            '<!DOCTYPE html><!-- x --><HTML lang="es">' + body: '<!DOCTYPE html><!-- x --><HTML data-theme="dark" lang="es">' + body,
        }
        for source, expected in cases.items():
            with self.subTest(html=source[:50]):
                self.assertEqual(with_initial_theme(source), expected)
        # An author custom element named html-* is not the root element and keeps its markup.
        custom = '<!DOCTYPE html><html-include src="x"></html-include>' + body
        self.assertEqual(with_initial_theme(custom), '<!DOCTYPE html><html data-theme="dark"><html-include src="x"></html-include>' + body)
        self.assertEqual(head_insertion_point('<html-include src="x"></html-include><p>'), 0)
        for unchanged in ('<!-- <html> --><!DOCTYPE html><html DATA-THEME="hacker">' + body,
                          '<!DOCTYPE html><body><html data-theme="hacker">' + body):
            with self.subTest(html=unchanged[:50]):
                self.assertEqual(with_initial_theme(unchanged), unchanged)

    def test_host_scripts_go_after_the_real_head_or_doctype(self):
        for source, marker in (('<!-- c --><!DOCTYPE html><p>x', '<!DOCTYPE html>'),
                               ('<!DOCTYPE html><!-- <head> --><script>"<head>"</script><head lang="es"><title>', '<head lang="es">'),
                               ('<!DOCTYPE html><html data-x="a>b"><p>x', '<html data-x="a>b">'),
                               ('<!DOCTYPE html><p>x</p><html lang="es">', '<!DOCTYPE html>'),
                               ('\ufeff<p>x', '\ufeff'),
                               ('<p>x', '')):
            with self.subTest(html=source):
                self.assertEqual(head_insertion_point(source), source.index(marker) + len(marker))

if __name__ == '__main__': unittest.main()
