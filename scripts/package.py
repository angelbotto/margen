#!/usr/bin/env python3
"""Build a reproducible, credential-free portable skill with explicit inputs."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = {'.md', '.css', '.js', '.cjs', '.json', '.html', '.py', '.sh', '.ps1', '.yaml', '.woff2', '.mp3', '.svg', '.txt'}
ROOT_FILES = ['SKILL.md', 'VERSION.json', 'README.md', 'README.es.md', 'LICENSE', 'NOTICE',
              'CONTRIBUTING.md', 'SECURITY.md', 'CODE_OF_CONDUCT.md', 'CHANGELOG.md', 'ROADMAP.md']
FOLDERS = ['compat', 'scripts', 'docs', 'examples/content', 'examples/generated', 'agents', 'licenses',
           'packages/core/components', 'packages/core/styles', 'packages/core/themes',
           'packages/core/brands', 'packages/core/registry', 'packages/core/recipes', 'packages/core/assets']
# Transitional entrypoints exist only in built ZIPs for older installed launchers.
LEGACY_COMMANDS = {'instalar.py': 'install.py', 'actualizar.py': 'update.py', 'publicar.py': 'publish.py',
                   'crear_artefacto.py': 'create_artifact.py', 'validar_artefacto.py': 'validate_artifact.py', 'catalogo.py': 'catalog.py'}


def package():
    files = [ROOT / name for name in ROOT_FILES]
    for folder in FOLDERS:
        files.extend(path for path in (ROOT / folder).rglob('*') if path.is_file() and not path.is_symlink()
                     and path.suffix in EXTENSIONS and '__pycache__' not in path.parts and 'node_modules' not in path.parts)
    files.append(ROOT/'tests/fixtures/agent-evaluation/cases.json')
    files.append(ROOT/'tests/fixtures/release-signature.json')
    for name in ['geography.json', 'sounds-cmrg.json', 'fonts.json', 'literata-fonts.json']:
        files.append(ROOT / 'tests/evidence' / name)
    blobs = {str(path.relative_to(ROOT)): path.read_bytes() for path in sorted(set(files))}
    # Only individually reviewed documentation captures may enter the skill ZIP.
    manifest = json.loads((ROOT / 'docs/assets/manifest.json').read_text())
    for item in manifest['images']:
        path = ROOT / item['file']
        if not item['synthetic'] or not item['reviewed'] or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('Unreviewed public image')
        blobs[item['file']] = path.read_bytes()
    for old, new in LEGACY_COMMANDS.items():
        blobs['scripts/' + old] = ("# Compatibility entrypoint for pre-0.2 installations.\nimport runpy\nfrom pathlib import Path\nrunpy.run_path(str(Path(__file__).with_name(" + repr(new) + ")), run_name='__main__')\n").encode()
    version = json.loads(blobs['VERSION.json'])['version']
    manifest = {'formato': 'bottifact-portable', 'version': version,
                'archivos': {name: hashlib.sha256(blob).hexdigest() for name, blob in blobs.items()}}
    encoded = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()
    blobs['manifest.json'] = encoded
    blobs['MANIFIESTO.json'] = encoded  # previous installers discover this name
    output = ROOT / 'dist'
    output.mkdir(exist_ok=True)
    target = output / 'bottifact-portable.zip'
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, blob in sorted(blobs.items()):
            info = zipfile.ZipInfo('bottifact/' + name, date_time=(2026, 9, 15, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, blob)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix('.sha256').write_text(digest + '  ' + target.name + '\n')
    print(f'{target}: {len(blobs)} files; SHA-256 {digest}')
    return target

if __name__ == '__main__':
    package()
