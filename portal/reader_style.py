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


REFERENCE = re.compile(r'/\* EDITORIAL REFERENCE START \*/.*?/\* EDITORIAL REFERENCE END \*/', re.S)


def refresh_editorial_reference(content, css, code, pieces=None):
    """Refresh a rendered Margen copy; do not interpret arbitrary HTML as a theme.

    Only real style elements and the explicitly marked core code module change.
    Script strings, examples, custom modules and stored revisions remain verbatim.
    The late stylesheet upgrades old generated geometry without replacing themes.
    """
    runtimes = {'packages/core/components/code.js': code}
    if pieces is not None:
        runtimes['packages/core/components/editorial-pieces.js'] = pieces
    offsets = [0] + [match.end() for match in re.finditer('\n', content)]

    class Reference(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.literal = None
            self.block = None
            self.edits = []
            self.margen = False
            self.injected = False
            self.head_end = None
            self.last_style = None
            self.inert_depth = 0

        def pos(self):
            line, column = self.getpos()
            return offsets[line - 1] + column

        def handle_starttag(self, tag, attributes):
            if self.literal:
                return
            if tag in {'template', 'noscript'}:
                self.inert_depth += 1
                return
            if self.inert_depth:
                if tag in {'script','style','textarea','title','xmp','iframe','noembed','noframes','plaintext'}:
                    self.literal = tag
                return
            attrs = dict(attributes)
            if 'hoja' in (attrs.get('class') or '').split() and 'data-presentation' not in attrs and attrs.get('data-ritmo') != 'propio':
                self.margen = True
            if tag in {'script', 'style'}:
                self.literal = tag
                self.block = (self.pos() + len(self.get_starttag_text()), attrs)
            elif tag in {'textarea', 'title', 'xmp', 'iframe', 'noembed', 'noframes', 'plaintext'}:
                self.literal = tag

        def handle_endtag(self, tag):
            if self.literal:
                if tag != self.literal:
                    return
                if self.block:
                    start, attrs = self.block
                    end = self.pos()
                    old = content[start:end]
                    new = old
                    if tag == 'style':
                        self.last_style = content.find('>', end) + 1
                        if 'data-margen-editorial-reference' in attrs:
                            new = css
                            self.injected = True
                        else:
                            new = REFERENCE.sub('', old)
                    elif (attrs.get('data-nota-modulo') in runtimes
                          and not attrs.get('src') and attrs.get('type', '') in {'', 'text/javascript'}):
                        new = '\n' + runtimes[attrs['data-nota-modulo']] + '\n'
                    if new != old:
                        self.edits.append((start, end, new))
                self.literal = None
                self.block = None
                return
            if tag in {'template', 'noscript'} and self.inert_depth:
                self.inert_depth -= 1
                return
            if self.inert_depth:
                return
            if tag == 'head':
                self.head_end = self.pos()

    parser = Reference()
    parser.feed(content)
    parser.close()
    if not parser.margen:
        return content
    if not parser.injected:
        # Last stylesheet wins over the embedded library, including late body
        # styles. Inline component overrides and opt-out layouts remain intact.
        position = parser.last_style if parser.last_style is not None else (parser.head_end or 0)
        parser.edits.append((position, position, '<style data-margen-editorial-reference>' + css + '</style>'))
    for start, end, replacement in sorted(parser.edits, reverse=True):
        content = content[:start] + replacement + content[end:]
    return content
