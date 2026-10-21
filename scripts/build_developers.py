"""Bundle the real library catalog for the independently deployed portal."""
import json
import re
import colorsys
from pathlib import Path
from themes import DATA, original

ROOT = Path(__file__).resolve().parents[1]
REPO = 'https://github.com/angelbotto/margen'
# Reviewed local enhancement modules; never populated from submitted packages.
PREVIEW_RUNTIME = ('charts.js', 'geography.js', 'analytics.js', 'relationship-map.js')


def hex_color(value):
    match = re.fullmatch(r'hsl\((\d+) (\d+)% (\d+)%\)', value)
    if match:
        h, saturation, lightness = map(int, match.groups())
        rgb = colorsys.hls_to_rgb(h / 360, lightness / 100, saturation / 100)
        return '#' + ''.join(f'{round(channel * 255):02x}' for channel in rgb)
    if not re.fullmatch(r'#[a-fA-F0-9]{6}', value):
        raise ValueError('Unsupported palette value: ' + value)
    return value


def generate():
    css = (ROOT / 'packages/core/styles/artifact.css').read_text()
    items = []
    for family in DATA['familias']:
        palettes = {}
        for mode in ('light', 'dark'):
            palette = family[mode]
            if isinstance(palette, str):
                palette = original(css, palette)
            palettes[mode] = {key: hex_color(palette[key]) for key in (
                'papel', 'panel', 'panel-2', 'tinta', 'tinta-2', 'tinta-3',
                'naranja', 'verde', 'rojo', 'azul')}
        items.append(dict(id='theme-' + family['id'], slug=family['id'], kind='theme',
                          title=family['nombre'], description=family['descripcion'],
                          category=family['grupo'], content=palettes,
                          source_url=REPO + '/tree/main/packages/core/themes/families/' + family['id'] + '.json'))
    manifests = {}
    for path in sorted((ROOT / 'packages/core/recipes').glob('*/component.json')):
        manifest = json.loads(path.read_text())
        manifests[manifest.get('legacyId', manifest['id'])] = (path, manifest)
    registry = json.loads((ROOT / 'packages/core/registry/registry.json').read_text())
    for recipe in registry['componentes']:
        found = manifests.get(recipe['id'])
        slug = found[1]['id'] if found else recipe['id']
        source = ('/tree/main/packages/core/recipes/' + found[0].parent.name
                  if found else '/blob/main/docs/components.md')
        items.append(dict(id='component-' + slug, slug=slug, kind='component',
                          title=recipe['nombre'], description=recipe.get('criterio_y_limites', ''),
                          category=recipe['capitulo'], content=recipe['html'],
                          dependencies=recipe.get('dependencias', []), source_url=REPO + source))
    runtime = {name: (ROOT / 'packages/core/components' / name).read_text() for name in PREVIEW_RUNTIME}
    for item in items:
        if item['kind'] == 'component':
            dependencies = item.get('dependencies', [])
            item['preview_runtime'] = [name for name in PREVIEW_RUNTIME
                                       if 'packages/core/components/' + name in dependencies
                                       # Geography supports analytics; it cannot render a standalone 3D recipe.
                                       and (name != 'geography.js' or 'packages/core/components/analytics.js' in dependencies)]
    (ROOT / 'portal/developers-runtime.json').write_text(json.dumps(runtime, ensure_ascii=False, indent=2) + '\n')
    version = json.loads((ROOT / 'VERSION.json').read_text())
    for item in items:
        item.update(origin='bundled', author='Contribuidores de Margen', license='MIT',
                    version=str(version.get('version', version.get('release', 'bundled'))),
                    status='bundled')
    target = ROOT / 'portal/developers-catalog.json'
    target.write_text(json.dumps({'schema': 1, 'items': items}, ensure_ascii=False, indent=2) + '\n')
    (ROOT / 'portal/developers-preview.css').write_text(css)
    extra = ROOT / 'packages/core/styles/community-fonts.css'
    extra_css = extra.read_text() if extra.is_file() else ''
    (ROOT / 'portal/developers-community-fonts.css').write_text(extra_css)
    (ROOT / 'portal/developers-fonts.css').write_text((ROOT / 'packages/core/styles/fonts.css').read_text() + extra_css)
    from contract_artifact import build
    shell = build('Nuevo documento', [{'id': 'contenido', 'titulo': 'Empieza aquí', 'html': '<p id="community-slot">Contenido inicial.</p>'}], document_id='margen-community-starter')
    (ROOT / 'portal/developers-shell.html').write_text(shell)
    return len(items)


if __name__ == '__main__':
    print('Developer catalog:', generate(), 'entries')
