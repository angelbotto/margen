"""Data-only themes. User input never supplies CSS selectors, URLs or JavaScript."""
import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent
FONTS = {
    'geist': ('Geist', 'sans-serif'), 'instrument': ('Instrument Serif', 'serif'),
    'literata': ('Literata', 'serif'), 'mono': ('Geist Mono', 'monospace'),
    'manrope': ('Manrope', 'sans-serif'), 'source-serif': ('Source Serif 4', 'serif'),
}


def font(value):
    name, fallback = FONTS[value]
    return '"' + name + '",' + fallback


def palette_css(palette):
    values = dict(palette)
    values.update({'linea': 'color-mix(in srgb,var(--panel),var(--tinta) 17%)',
                   'linea-fuerte': 'color-mix(in srgb,var(--panel),var(--tinta) 48%)',
                   'naranja-suave': 'color-mix(in srgb,var(--papel),var(--naranja) 10%)',
                   'marcador': 'var(--naranja)', 'foco': 'var(--naranja)'})
    for key, source in {
        'grafica-1': 'naranja', 'grafica-2': 'verde', 'grafica-3': 'rojo', 'grafica-4': 'azul',
        'grafica-papel': 'papel', 'grafica-tinta': 'tinta-2', 'grafica-linea': 'linea',
        'tabla-elegida': 'naranja-suave', 'tabla-total': 'panel', 'calor-tinta': 'tinta',
        'calor-ausente': 'panel-2', 'pieza-papel': 'panel', 'pieza-tinta': 'tinta',
        'pieza-secundaria': 'tinta-2', 'pieza-linea': 'linea-fuerte', 'pieza-acento': 'naranja',
        'pieza-suave': 'panel', 'pieza-sube': 'verde', 'pieza-baja': 'azul',
        'apariencia-papel': 'papel', 'apariencia-tinta': 'tinta', 'apariencia-secundaria': 'tinta-2',
        'apariencia-linea': 'linea-fuerte', 'apariencia-suave': 'panel',
        'verde-suave': 'panel', 'rojo-suave': 'panel', 'azul-suave': 'panel',
        'escena-1': 'naranja', 'escena-2': 'verde', 'escena-3': 'rojo', 'escena-tinta': 'tinta-2',
        'escena-linea': 'linea-fuerte', 'escritura-trazo': 'naranja', 'escritura-papel': 'panel',
        'sonido-papel': 'papel', 'sonido-activo': 'verde', 'sonido-tinta': 'tinta',
    }.items():
        values[key] = 'var(--' + source + ')'
    for i, amount in enumerate((2, 9, 17, 25, 33)):
        values['calor-' + str(i)] = f'color-mix(in srgb,var(--papel),var(--naranja) {amount}%)'
    return ''.join('--' + key + ':' + value + ';' for key, value in values.items())


def theme_css(package, selector=':root[data-margen-community-theme]'):
    palettes = package['content']
    css = selector + '{' + palette_css(palettes['light']) + 'color-scheme:light;}'
    css += selector + '[data-color-mode="dark"]{' + palette_css(palettes['dark']) + 'color-scheme:dark;}'
    typography = package.get('typography', {'heading': 'instrument', 'body': 'geist'})
    css += selector + ':not([data-community-typography-override]) :is(main,.hoja,.prosa){font-family:' + font(typography['body']) + ';}'
    css += selector + ':not([data-community-typography-override]) :is(h1,h2,h3,h4){font-family:' + font(typography['heading']) + ';}'
    return css


def apply_theme(content, item):
    # Replace only the marked attachment of a previously applied community theme.
    # Its payload is generated here and never contains user CSS/JS.
    from portal.block_source import Tree
    tree = Tree(content)
    edits = [(node.start, node.end) for node in tree.nodes
             if node.tag in {'style', 'script'} and 'data-margen-community-attachment' in node.attrs]
    for start, end in sorted(edits, reverse=True):
        content = content[:start] + content[end:]
    title = json.dumps(item['title'], ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    css = (ROOT / 'developers-community-fonts.css').read_text() + theme_css(item)
    js = (ROOT / 'static/community-theme-reader.js').read_text().replace('/* THEME TITLE */ "Tema compartido"', title)
    attachment = '<style data-margen-community-attachment>' + css + '</style><script data-margen-community-attachment>' + js + '</script>'
    end = re.search(r'</body\s*>', content, re.I)
    return content[:end.start()] + attachment + content[end.start():] if end else content + attachment


def visual_component(kind, title, body):
    """Small recipes edited through fields, not through code."""
    heading = escape(title)
    raw_lines = [line.strip() for line in body.splitlines() if line.strip()][:12]
    lines = [escape(line) for line in raw_lines]
    key = __import__('uuid').uuid4().hex[:12]
    if kind == 'steps':
        return '<section class="prosa" id="piece-' + key + '"><h2>' + heading + '</h2><ol>' + ''.join('<li>' + line + '</li>' for line in lines) + '</ol></section>'
    if kind == 'diagram':
        height = max(100, len(lines) * 84)
        out = ['<figure class="pieza" id="piece-' + key + '"><figcaption>' + heading + '</figcaption><svg role="img" aria-label="' + heading + '" viewBox="0 0 500 ' + str(height) + '">']
        for index, line in enumerate(lines):
            y = index * 84 + 10
            label = escape(raw_lines[index][:43] + '…' if len(raw_lines[index]) > 44 else raw_lines[index])
            if index:
                out.append(f'<path d="M250 {y-28}v24m-5-6 5 6 5-6" fill="none" stroke="currentColor"/>')
            out.append(f'<rect x="20" y="{y}" width="460" height="56" rx="8" fill="var(--panel)" stroke="currentColor"/><text x="250" y="{y+33}" text-anchor="middle" fill="currentColor" font-size="15">{label}</text>')
        out.append('</svg><ol>' + ''.join('<li>' + line + '</li>' for line in lines) + '</ol></figure>')
        return ''.join(out)
    return '<section class="pieza prosa" id="piece-' + key + '"><h2>' + heading + '</h2>' + ''.join('<p>' + line + '</p>' for line in lines) + '</section>'
