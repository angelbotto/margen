"""Reconstruct supported static HTML/SVG; never round-trip raw parser text.

HTMLParser is not a browser sanitizer. A small positive tag/attribute grammar plus
escaped text prevents SVG/raw-text parsing differences from creating active DOM.
"""
import re
from html import escape
from html.parser import HTMLParser

TAGS = set('article section div main aside p h1 h2 h3 h4 h5 h6 figure figcaption blockquote ul ol li dl dt dd span strong em b i s mark small table thead tbody tfoot tr th td caption colgroup col pre code br hr a svg g path circle ellipse rect line polyline polygon text tspan title desc'.split())
NUMERIC = set('x y x1 y1 x2 y2 cx cy r rx ry width height dx dy stroke-width stroke-dashoffset opacity fill-opacity stroke-opacity font-size'.split())
TEXT = {'id', 'class', 'role', 'aria-label', 'aria-labelledby', 'aria-describedby'}
SVG_ATTRIBUTES = {'viewbox': 'viewBox', 'preserveaspectratio': 'preserveAspectRatio', 'text-anchor': 'text-anchor',
                  'stroke-linecap': 'stroke-linecap', 'stroke-linejoin': 'stroke-linejoin', 'fill-rule': 'fill-rule'}


class StaticComponent(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.blocked = None
        self.stack = []
        self.feed(source)
        self.close()
        self.parts.extend("</" + tag + ">" for tag in reversed(self.stack))

    def handle_starttag(self, tag, attrs):
        if self.blocked:
            return
        if tag in {'script', 'style', 'iframe', 'object', 'template', 'textarea', 'noscript', 'xmp', 'plaintext'}:
            self.blocked = tag
            return
        if tag not in TAGS:
            return
        safe = []
        for key, value in attrs:
            value = value or ''
            valid = False
            if key in TEXT:
                valid = len(value) <= 500
            elif key in NUMERIC or key in {'viewbox', 'points', 'stroke-dasharray'}:
                valid = bool(re.fullmatch(r'[0-9eE.,%+\-\s]+', value)) and len(value) < 10000
            elif key == 'd':
                valid = bool(re.fullmatch(r'[MmZzLlHhVvCcSsQqTtAa0-9eE.,+\-\s]+', value)) and len(value) < 50000
            elif key in {'fill', 'stroke', 'color'}:
                valid = bool(re.fullmatch(r'(?:none|currentColor|transparent|#[a-fA-F0-9]{3,8}|[a-zA-Z]{1,24}|var\(--[a-z0-9-]{1,60}\))', value))
            elif key in SVG_ATTRIBUTES:
                valid = bool(re.fullmatch(r'[a-zA-Z0-9\s-]{1,80}', value))
            elif key in {'colspan', 'rowspan', 'start'}:
                valid = value.isdigit() and len(value) <= 3
            elif key == 'scope':
                valid = value in {'row', 'col', 'rowgroup', 'colgroup'}
            if valid:
                safe.append(SVG_ATTRIBUTES.get(key, key) + '="' + escape(value, quote=True) + '"')
        self.parts.append('<' + tag + (' ' + ' '.join(safe) if safe else '') + '>')
        if tag not in {'br', 'hr', 'col'}:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if self.blocked:
            if tag == self.blocked:
                self.blocked = None
            return
        if tag in self.stack:
            index = len(self.stack) - 1 - self.stack[::-1].index(tag)
            self.parts.extend('</' + opened + '>' for opened in reversed(self.stack[index:]))
            del self.stack[index:]

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data):
        if not self.blocked:
            self.parts.append(escape(data))


def static_component(source):
    return ''.join(StaticComponent(source).parts)
