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
        # Slightly imperfect closed paths; reproducible and no pseudo-random layout.
        path = ('M8 7 Q146 2 292 8 Q298 89 292 192 Q158 197 7 191 Q3 97 8 7Z'
                if index % 2 == 0 else 'M7 8 Q158 3 291 6 Q297 98 293 191 Q152 196 8 193 Q3 91 7 8Z')
        parts += [f'<li class="sketch-step" id="{identifier}-{node_id}"><div class="sketch-node">',
                  f'<svg class="sketch-outline" viewBox="0 0 300 200" preserveAspectRatio="none" aria-hidden="true" focusable="false"><path d="{path}"/><path class="sketch-echo" d="M10 10 Q164 6 290 10 L289 190 Q150 193 11 188 Q7 102 10 10Z"/></svg>',
                  f'<span class="sketch-number">0{index + 1}</span><strong class="sketch-title">{label}</strong><p class="sketch-body">{body}</p></div>']
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
