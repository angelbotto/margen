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


if __name__ == '__main__': unittest.main()
