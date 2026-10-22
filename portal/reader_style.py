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
    root = _root_markup(content)
    if root['themed']:
        return content
    if root['html'] is not None:
        position = root['html'] + 5
        return content[:position] + ' data-theme="' + palette + '"' + content[position:]
    position = root['doctype'] if root['doctype'] is not None else root['bom']
    return content[:position] + '<html data-theme="' + palette + '">' + content[position:]


LITERAL = {'script', 'style', 'textarea', 'title', 'xmp', 'iframe', 'noembed', 'noframes', 'plaintext'}


def _root_markup(content):
    """Offsets of the real doctype, <html> and <head> tags.

    Comments, scripts, templates and other literal text are not markup, so a tag-like
    string inside them never moves an insertion; whatever precedes a real doctype stays before it.
    """
    offsets = [0] + [match.end() for match in re.finditer('\n', content)]
    bom = len(content) - len(content.lstrip('\ufeff'))

    class Root(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.found = {'doctype': None, 'html': None, 'html_end': None, 'head': None, 'themed': False, 'bom': bom}
            self.literal = None
            self.inert = 0
            self.started = False

        def pos(self):
            line, column = self.getpos()
            return offsets[line - 1] + column

        def handle_decl(self, declaration):
            if (not self.started and not self.literal and not self.inert and self.found['doctype'] is None
                    and re.match(r'doctype(?:\s|$)', declaration, re.I)):
                self.found['doctype'] = self.pos() + len(declaration) + 3

        def handle_startendtag(self, tag, attrs):
            self.handle_starttag(tag, attrs)

        def handle_starttag(self, tag, attrs):
            if self.literal:
                return
            leading, self.started = not self.started, True
            if tag == 'template':
                self.inert += 1
            elif tag in LITERAL:
                self.literal = tag
            elif self.inert:
                return
            elif tag == 'html':
                self.found['themed'] = self.found['themed'] or any(name == 'data-theme' for name, _ in attrs)
                if self.found['html'] is None:
                    self.found['html'] = self.pos()
                    if leading:
                        self.found['html_end'] = self.pos() + len(self.get_starttag_text())
            elif tag == 'head' and self.found['head'] is None:
                self.found['head'] = self.pos() + len(self.get_starttag_text())

        def handle_endtag(self, tag):
            if self.literal:
                if tag == self.literal:
                    self.literal = None
            elif tag == 'template' and self.inert:
                self.inert -= 1

    parser = Root()
    parser.feed(content)
    parser.close()
    return parser.found


def head_insertion_point(content):
    """Where host scripts go: after the real <head> or <html>, else after the real doctype, never before it."""
    root = _root_markup(content)
    return next(offset for offset in (root['head'], root['html_end'], root['doctype'], root['bom']) if offset is not None)
