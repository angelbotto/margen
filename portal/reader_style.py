"""Refresh only the marked shared reading rules in a rendered copy of old HTML."""
from html.parser import HTMLParser
import re

FLOW = re.compile(r'/\* EDITORIAL FLOW START \*/.*?/\* EDITORIAL FLOW END \*/', re.S)


def without_embedded_flow(content):
    # Track literal-text elements across supported Python versions. A CSS-looking
    # string inside script, textarea or an escaped example is not a stylesheet.
    if '/* EDITORIAL FLOW START */' not in content:
        return content
    # HTMLParser line numbers count LF only, not Unicode or standalone CR separators.
    offsets = [0] + [match.end() for match in re.finditer('\n', content)]

    class Styles(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.start = None
            self.literal = None
            self.edits = []

        def source_offset(self):
            line, column = self.getpos()
            return offsets[line - 1] + column

        def handle_starttag(self, tag, attrs):
            if self.literal:
                return
            if tag in {'script','textarea','title','xmp','iframe','noembed','noframes','plaintext'}:
                self.literal = tag
                return
            if tag == 'style':
                self.start = self.source_offset() + len(self.get_starttag_text())

        def handle_endtag(self, tag):
            if self.literal:
                if tag == self.literal:
                    self.literal = None
                return
            if tag == 'style' and self.start is not None:
                end = self.source_offset()
                old = content[self.start:end]
                new = FLOW.sub('', old)
                if new != old:
                    self.edits.append((self.start, end, new))
                self.start = None

    parser = Styles()
    parser.feed(content)
    parser.close()
    for start, end, replacement in reversed(parser.edits):
        content = content[:start] + replacement + content[end:]
    return content
