"""Refresh only the marked shared reading rules in a rendered copy of old HTML."""
from html.parser import HTMLParser
import json
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
            self.doctype_end = None
            self.last_style = None
            self.inert_depth = 0

        def pos(self):
            line, column = self.getpos()
            return offsets[line - 1] + column

        def handle_decl(self, declaration):
            # A declaration callback identifies real markup, not a doctype-like
            # string in a comment, script, template or literal example.
            if not self.literal and not self.inert_depth and self.doctype_end is None and re.match(r'doctype(?:\s|$)', declaration, re.I):
                self.doctype_end = self.pos() + len(declaration) + 3

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
        # When head tags are omitted, inserting before a valid doctype would
        # switch the rendered document from standards mode to quirks mode.
        position = next((offset for offset in (parser.last_style, parser.head_end, parser.doctype_end) if offset is not None), 0)
        parser.edits.append((position, position, '<style data-margen-editorial-reference>' + css + '</style>'))
    for start, end, replacement in sorted(parser.edits, reverse=True):
        content = content[:start] + replacement + content[end:]
    return content



def _initial_metas(content):
    class Metas(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.values = {}

        def handle_starttag(self, tag, attrs):
            if tag == 'meta':
                a = dict(attrs)
                if a.get('name') in ('nota-modo-inicial', 'nota-tema-inicial'):
                    self.values.setdefault(a['name'], a.get('content') or '')

    parser = Metas()
    parser.feed(content[:65536])
    return parser.values


def initial_appearance(content):
    """Declared first-paint mode, so the host can back the frame before the document paints."""
    mode = _initial_metas(content).get('nota-modo-inicial')
    return {'mode': mode if mode in ('light', 'dark', 'system') else None}


REGISTRY = '/* REGISTRO TEMAS */ const themeRegistry = '


def with_initial_theme(content):
    """Paint a declared light or dark palette from the first frame.

    The value comes from the document's own embedded theme registry, the same one reader.js
    applies at the end of the body; system mode, unknown families and existing data-theme stay as they are.
    """
    metas = _initial_metas(content)
    mode, family = metas.get('nota-modo-inicial'), metas.get('nota-tema-inicial')
    at = content.find(REGISTRY)
    if mode not in ('light', 'dark') or not family or at < 0:
        return content
    try:
        registry = json.JSONDecoder().raw_decode(content, at + len(REGISTRY))[0]
        palette = next(f for f in registry['familias'] if f.get('id') == family)[mode]
    except (ValueError, KeyError, TypeError, StopIteration):
        return content
    if not isinstance(palette, str) or not re.fullmatch(r'[a-z0-9-]{1,40}', palette):
        return content
    tag = re.search(r'<html\b[^>]*>', content, re.I)
    first = re.search(r'<(?:script|style|body)\b', content, re.I)
    if tag and (not first or tag.start() < first.start()):
        if re.search(r'\sdata-theme\s*=', tag[0], re.I):
            return content
        return content[:tag.start() + 5] + ' data-theme="' + palette + '"' + content[tag.start() + 5:]
    if tag:
        return content
    doctype = re.match(r'\s*<!doctype[^>]*>', content, re.I)
    position = doctype.end() if doctype else 0
    return content[:position] + '<html data-theme="' + palette + '">' + content[position:]
