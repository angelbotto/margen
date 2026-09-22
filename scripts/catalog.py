#!/usr/bin/env python3
"""Find compact component summaries; load full recipes only by explicit ID."""
import argparse
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', value.casefold()) if not unicodedata.combining(c))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', action='append', help='Full recipe by canonical or compatibility ID; repeatable')
    parser.add_argument('--search', default='', help='Match all words in names, aliases, families or guidance')
    parser.add_argument('--family', default='', help='Filter by chapter/family text')
    parser.add_argument('--limit', type=int, help='Maximum index results; defaults to 12 for searches')
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error('--limit must be positive')
    items = json.loads((ROOT / 'packages/core/registry/registry.json').read_text())['componentes']
    aliases = json.loads((ROOT / 'packages/core/registry/component-aliases.json').read_text())
    if args.id:
        selected = []
        for identifier in args.id:
            found = next((r for r in items if r['id'] == identifier or aliases.get(r['id']) == identifier), None)
            if not found:
                parser.error('Unknown component: ' + identifier)
            if found not in selected:
                selected.append(found)
        print(json.dumps(selected[0] if len(selected) == 1 else selected, ensure_ascii=False, indent=2))
        return
    words = normalize(args.search).split()
    def score(recipe):
        primary = set(re.findall(r'\w+', normalize(' '.join([recipe['id'], aliases.get(recipe['id'], ''), recipe['nombre'], recipe['capitulo']]))))
        guidance = set(re.findall(r'\w+', normalize(recipe['criterio_y_limites'])))
        return sum(3 if word in primary else 1 for word in words) if all(word in primary or word in guidance for word in words) else -1
    results = [r for r in items if normalize(args.family) in normalize(r['capitulo']) and score(r) >= 0]
    if words:
        results.sort(key=score, reverse=True)
    limit = args.limit or (12 if args.search or args.family else len(results))
    for r in results[:limit]:
        print(' | '.join([aliases.get(r['id'], r['id']), r['capitulo'], r['nombre']]))
    print(f'{min(limit, len(results))} of {len(results)} matches. Use --id for HTML and guidance; refine --search or increase --limit.')


if __name__ == '__main__':
    main()
