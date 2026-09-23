#!/usr/bin/env python3
"""Verifica los archivos enumerados por el manifiesto portable, sin red."""
import argparse,hashlib,json
from pathlib import Path,PurePosixPath

def verify(root):
 root=Path(root).resolve();manifest=json.loads((root/('manifest.json' if (root/'manifest.json').exists() else 'MANIFIESTO.json')).read_text())
 if manifest.get('formato') not in {'bottifact-portable','nota-tikin-portable'}:raise ValueError('Formato de paquete desconocido')
 files=manifest['archivos']
 if not isinstance(files,dict) or 'SKILL.md' not in files or 'packages/core/registry/registry.json' not in files:raise ValueError('Manifiesto incompleto')
 for name,digest in files.items():
  path=PurePosixPath(name)
  if path.is_absolute() or '..' in path.parts or '\\' in name or any(':' in p or p.endswith((' ','.')) or p.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]} for p in path.parts):raise ValueError('Ruta no portable: '+name)
  target=root.joinpath(*path.parts)
  if not target.is_file() or target.is_symlink() or not target.resolve().is_relative_to(root):raise ValueError('Archivo ausente o enlace: '+name)
  if hashlib.sha256(target.read_bytes()).hexdigest()!=digest:raise ValueError('SHA-256 distinto: '+name)
 return manifest
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('directorio',type=Path);args=p.parse_args()
 try:
  m=verify(args.directorio);print(str(len(m['archivos']))+' archivos íntegros. Versión '+m['version'])
 except (ValueError,KeyError,OSError) as e:p.exit(1,str(e)+'\n')
