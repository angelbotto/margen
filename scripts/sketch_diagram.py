#!/usr/bin/env python3
"""Render an accessible, hand-drawn directed flow from margen-sketch/1 JSON.

No remote assets or JavaScript. The same ordered HTML is reflowed on phones.
This is a Margen recipe, not an Excalidraw canvas or file-format converter.
"""
import argparse
from html import escape
import json
from pathlib import Path
import re

# Original, intentionally simple strokes. Never accept SVG markup from a source.
ICONS = {
    'person': 'M24 18 C23 5 43 5 42 18 C43 31 23 31 24 18 M14 55 C13 31 51 31 51 55 M23 47 L22 56 M42 46 L43 56',
    'team': 'M24 19 C23 6 41 6 40 19 C40 31 24 31 24 19 M17 56 C15 33 49 33 47 56 M10 18 C3 17 3 31 11 31 M5 52 C1 36 13 33 18 38 M53 18 C61 18 61 31 53 31 M47 38 C56 32 64 39 59 52',
    'server': 'M9 9 Q31 6 55 9 L54 29 L9 30 Z M10 36 L54 35 L55 55 Q34 57 9 55 Z M17 19 L19 19 M26 19 L28 19 M37 19 L47 19 M17 46 L19 46 M26 46 L28 46 M37 46 L47 46',
    'database': 'M11 15 C11 3 53 3 53 15 C53 28 11 28 11 15 M11 15 L12 49 C12 62 53 62 53 49 L53 15 M12 32 C14 43 51 43 53 32',
    'cloud': 'M17 48 C1 49 1 29 15 26 C14 5 44 2 48 24 C63 23 67 48 49 48 Z',
    'document': 'M15 6 Q31 5 39 7 L51 20 L50 57 Q33 58 14 56 Z M39 7 L39 21 L51 20 M23 31 L42 30 M23 40 L42 40 M23 49 L36 48',
    'payment': 'M7 14 Q31 11 57 14 L56 51 Q32 53 7 50 Z M8 25 L56 25 M17 40 L29 40 M40 40 L47 40',
    'store': 'M10 27 L11 57 L53 56 L53 27 M7 27 L13 9 L51 10 L58 27 M7 27 Q15 37 24 27 Q32 37 41 27 Q51 38 58 27 M24 55 L24 39 L40 39 L40 56',
    'approval': 'M18 8 L46 8 L57 24 L52 47 L32 59 L11 46 L7 25 Z M19 32 L29 42 L46 23',
    'agent': 'M13 20 Q31 17 52 20 L53 51 Q30 54 12 51 Z M32 8 L32 18 M27 7 L37 7 M5 29 L12 29 M53 30 L60 30 M23 31 L24 35 M41 31 L40 35 M23 44 Q32 48 42 44',
}


def _text(value, label, limit):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f'{label}: expected 1–{limit} characters.')
    return escape(value.strip())


def render(source):
    if not isinstance(source, dict) or source.get('schema') != 'margen-sketch/1':
        raise ValueError('Expected schema margen-sketch/1.')
    identifier = source.get('id', '')
    if not isinstance(identifier, str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,79}', identifier):
        raise ValueError('Use a unique English kebab-case diagram id.')
    title = _text(source.get('title'), 'title', 180)
    nodes = source.get('nodes')
    transitions = source.get('transitions')
    if not isinstance(nodes, list) or not 2 <= len(nodes) <= 3:
        raise ValueError('Use 2–3 nodes; split a longer process into named diagrams.')
    if not isinstance(transitions, list) or len(transitions) != len(nodes) - 1:
        raise ValueError('Provide exactly one directed transition between adjacent nodes.')
    parts = [f'<figure class="pieza amplio sketch-diagram" id="{identifier}" data-sketch-diagram="1" aria-labelledby="{identifier}-caption">',
             f'<figcaption id="{identifier}-caption">{title}</figcaption>', '<ol class="sketch-flow">']
    seen = set()
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise ValueError('Each node must be an object.')
        node_id = node.get('id', '')
        if not isinstance(node_id, str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,59}', node_id) or node_id in seen:
            raise ValueError('Node ids must be unique English kebab-case values.')
        seen.add(node_id)
        label = _text(node.get('title'), 'node title', 70)
        body = _text(node.get('body'), 'node body', 240)
        icon = node.get('icon')
        if icon is not None and (not isinstance(icon, str) or icon not in ICONS):
            raise ValueError('Unknown icon; choose a named sketch symbol or omit icon.')
        symbol = (f'<svg class="sketch-symbol" viewBox="0 0 64 64" aria-hidden="true" focusable="false"><path d="{ICONS[icon]}"/></svg>' if icon else '')
        # Slightly imperfect closed paths; reproducible and no pseudo-random layout.
        path = ('M8 7 Q146 2 292 8 Q298 89 292 192 Q158 197 7 191 Q3 97 8 7Z'
                if index % 2 == 0 else 'M7 8 Q158 3 291 6 Q297 98 293 191 Q152 196 8 193 Q3 91 7 8Z')
        parts += [f'<li class="sketch-step" id="{identifier}-{node_id}"><div class="sketch-node">',
                  f'<svg class="sketch-outline" viewBox="0 0 300 200" preserveAspectRatio="none" aria-hidden="true" focusable="false"><path d="{path}"/><path class="sketch-echo" d="M10 10 Q164 6 290 10 L289 190 Q150 193 11 188 Q7 102 10 10Z"/></svg>',
                  f'<div class="sketch-meta"><span class="sketch-number">0{index + 1}</span>{symbol}</div><strong class="sketch-title">{label}</strong><p class="sketch-body">{body}</p></div>']
        if index < len(transitions):
            transition = _text(transitions[index], 'transition', 65)
            target = _text(nodes[index + 1].get('title') if isinstance(nodes[index + 1], dict) else None, 'target', 70)
            parts += [f'<div class="sketch-connection"><svg class="sketch-arrow" viewBox="0 0 64 40" aria-hidden="true" focusable="false"><path d="M4 22 Q27 12 58 19 M46 8 L59 19 L47 30"/></svg><span>{transition}<span class="sr-only"> → {target}</span></span></div>']
        parts.append('</li>')
    parts.append('</ol>')
    if source.get('note') is not None:
        parts.append('<p class="sketch-note">' + _text(source['note'], 'note', 200) + '</p>')
    parts.append('</figure>')
    return '\n'.join(parts) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.source.resolve() == args.output.resolve():
            raise ValueError('Output must not overwrite the editable JSON source.')
        result = render(json.loads(args.source.read_text()))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result)
    except (ValueError, TypeError, OSError) as error:
        parser.exit(1, str(error) + '\n')
    print(args.output)


if __name__ == '__main__':
    main()
