#!/usr/bin/env python3
"""Contratos estáticos del skill y los fragmentos. Biblioteca estándar, sin red."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote
import re, subprocess, shutil, json

ROOT=Path(__file__).resolve().parents[1]
THREE='https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.1/three.min.js'
VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}

class Fragment(HTMLParser):
 def __init__(self):
  super().__init__();self.ids=set();self.refs=[];self.errors=[];self.scripts=[];self.stack=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs);classes=set(a.get('class','').split())
  if tag in ['html','head','body']:self.errors.append('Etiqueta envolvente: '+tag)
  if 'id' in a:
   if a['id'] in self.ids:self.errors.append('ID duplicado: '+a['id'])
   self.ids.add(a['id'])
  if a.get('href','').startswith('#'):self.refs.append(unquote(a['href'][1:]))
  if 'data-copiar' in a:self.refs.append(a['data-copiar'])
  if a.get('aria-labelledby'):self.refs.extend(a['aria-labelledby'].split())
  if a.get('aria-controls'):self.refs.extend(a['aria-controls'].split())
  if 'data-tema' in a and tag!='select':self.errors.append('data-tema está reservado al selector de apariencia')
  if tag=='img' and (not a.get('src','').startswith('data:') or 'alt' not in a):self.errors.append('Imagen sin incrustar o sin alt')
  if tag=='script' and a.get('src'):
   src=a['src'];u=urlparse(src);self.scripts.append(src)
   allowed=u.scheme=='https' and (u.hostname in ['cdnjs.cloudflare.com','cdn.tailwindcss.com','code.jquery.com'] or (u.hostname=='cdn.jsdelivr.net' and u.path.startswith('/npm/')))
   if not allowed:self.errors.append('Script fuera de CSP: '+src)
   if 'three' in src.lower() and src!=THREE:self.errors.append('Three sin versión fijada')
  if tag=='link' and a.get('rel')=='stylesheet' and not a.get('href','').startswith('https://fonts.googleapis.com/'):
   self.errors.append('Hoja externa fuera de CSP')
  if classes & {'tabla-caja','diagrama-caja','grafica-caja','escena-caja','escritura-caja','visor-caja','apariencia-panel','pestanas-caja','navegacion-scroll','galeria-pista'} or ('barra' in classes and 'navegacion-editorial' not in classes) or tag=='pre':
   if a.get('tabindex')!='0' or not (a.get('aria-label') or a.get('aria-labelledby')):self.errors.append('Desplazamiento sin foco/nombre: '+tag+' '+a.get('class',''))
  if classes & {'ancho','amplio'}:
   parent=self.stack[-1][1] if self.stack else set()
   section='seccion' in parent and any('por-seccion' in c for _,c in self.stack)
   page='pagina' in parent and any('multipagina' in c for _,c in self.stack)
   if not ('hoja' in parent or section or page):self.errors.append('Figura atrapada fuera de la rejilla: '+a.get('id',a.get('class','')))
  if tag not in VOID:self.stack.append((tag,classes))
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,-1,-1):
   if self.stack[i][0]==tag:del self.stack[i:];break
 def handle_startendtag(self,tag,attrs):
  self.handle_starttag(tag,attrs)
  if tag not in VOID:self.handle_endtag(tag)

MODULES={
 'examples/generated/library.html':['packages/core/components/chart-core.js','packages/core/components/embeds.js','packages/core/components/evidence.js','packages/core/components/fleet.js','packages/core/components/invitation.js','packages/core/components/handwriting.js','packages/core/components/attention-map.js','packages/core/components/geography.js','packages/core/components/analytics.js','packages/core/components/code.js','packages/core/components/table-model.js','packages/core/components/data-explorer.js','packages/core/components/review.js','packages/core/components/reader.js','packages/core/components/chapters.js','packages/core/components/globe.js','packages/core/components/charts.js','packages/core/components/tables.js','packages/core/components/sound.js','packages/core/components/writing.js','packages/core/components/scene.js','packages/core/components/reports.js','packages/core/components/prototype.js','packages/core/components/tabs.js','packages/core/components/catalog.js','packages/core/components/editorial.js'],
 'examples/generated/template.html':['packages/core/components/chart-core.js','packages/core/components/evidence.js','packages/core/components/fleet.js','packages/core/components/invitation.js','packages/core/components/handwriting.js','packages/core/components/attention-map.js','packages/core/components/geography.js','packages/core/components/analytics.js','packages/core/components/code.js','packages/core/components/table-model.js','packages/core/components/data-explorer.js','packages/core/components/review.js','packages/core/components/editorial.js','packages/core/components/reader.js','packages/core/components/globe.js','packages/core/components/charts.js','packages/core/components/tables.js','packages/core/components/sound.js','packages/core/components/writing.js','packages/core/components/scene.js','packages/core/components/reports.js','packages/core/components/prototype.js','packages/core/components/tabs.js','packages/core/components/catalog.js'],
 'examples/generated/report.html':['packages/core/components/reader.js','packages/core/components/chapters.js','packages/core/components/chart-core.js','packages/core/components/charts.js','packages/core/components/reports.js','packages/core/components/prototype.js','packages/core/components/tabs.js','packages/core/components/review.js'],
 'examples/generated/globe.html':['packages/core/components/reader.js','packages/core/components/globe.js'],
 'examples/generated/chapters.html':['packages/core/components/reader.js','packages/core/components/chapters.js'],
 'examples/generated/checks.html':['packages/core/components/reader.js','packages/core/components/chapters.js'],
}
for modules in MODULES.values():modules.extend(['packages/core/components/audio.js','packages/core/components/controls.js','packages/core/components/editorial-pieces.js'])
css=(ROOT/'packages/core/styles/artifact.css').read_text()
for name,modules in MODULES.items():
 content=(ROOT/name).read_text();f=Fragment();f.feed(content)
 assert content.startswith('<title>'),name+': falta título inicial'
 assert b'<meta charset="utf-8">' in content.encode()[:1024],name+': charset tardío'
 assert not f.errors,(name,f.errors)
 assert all(ref in f.ids for ref in f.refs),(name,'referencias inexistentes',set(f.refs)-f.ids)
 assert css in content,(name,'CSS generado desactualizado')
 assert (ROOT/'packages/core/styles/fonts.css').read_text() in content,(name,'fuentes sin incrustar o desactualizadas')
 for module in modules:assert (ROOT/module).read_text() in content,(name,'módulo desactualizado',module)
 for url in re.findall(r'url\([\'"]?([^\)\'\"]+)',content):
  assert url.startswith(('data:','#')),(name,'recurso CSS externo: '+url)
 assert f.scripts.count(THREE)==int('packages/core/components/globe.js' in modules or 'packages/core/components/scene.js' in modules),(name,'inclusión de Three duplicada o ausente')
 assert len(f.scripts)==len(set(f.scripts)),(name,'guiones externos duplicados')
 print(name+': fuentes sincronizadas, CSP, IDs, rejilla y regiones accesibles correctos')

legacy_css=css.split('/* 28 —')[0]
library=legacy_css.split('/* 12 — Librería de evidencia.')[1].split('/* 15 —')[0]
palettes=[set(re.findall(r'(--[\w-]+)\s*:',body)) for _,body in re.findall(r'(:root[^{}]*)\{([^{}]*)\}',library) if '--calor-0:' in body]
assert len(palettes)==4 and all(p==palettes[0] for p in palettes), 'Faltan tokens en un tema'
extras=legacy_css.split('/* 13 — Reportes, artículos y prototipos.')[1]
extra_palettes=[set(re.findall(r'(--[\w-]+)\s*:',body)) for _,body in re.findall(r'(:root[^{}]*)\{([^{}]*)\}',extras) if '--pieza-papel:' in body]
assert len(extra_palettes)==4 and all(p==extra_palettes[0] for p in extra_palettes), 'Faltan tokens de piezas en un tema'
menu_palettes=[set(re.findall(r'(--[\w-]+)\s*:',body)) for _,body in re.findall(r'(:root[^{}]*)\{([^{}]*)\}',legacy_css) if '--apariencia-papel:' in body]
assert len(menu_palettes)==4 and all(p==menu_palettes[0] for p in menu_palettes), 'Faltan tokens de apariencia en un tema'
new_palettes=[set(re.findall(r'(--[\w-]+)\s*:',body)) for _,body in re.findall(r'(:root[^{}]*)\{([^{}]*)\}',legacy_css.split('/* 15 —')[1]) if '--calor-0:' in body]
base_colors=set(re.findall(r'(--[\w-]+)\s*:',css.split('/* 01 —')[1].split('--texto:')[0]))
assert len(new_palettes)==3 and all(p==new_palettes[0] and p>=base_colors|palettes[0] for p in new_palettes), 'Paleta adicional incompleta'
new_themes=[set(re.findall(r'(--[\w-]+)\s*:',body)) for selector,body in re.findall(r'(:root[^{}]*)\{([^{}]*)\}',css.split('/* 28 —')[1].split('/* GENERATED THEMES')[0]) if '--calor-0:' in body]
assert len(new_themes)==5 and all(p==new_themes[0] and p>=new_palettes[0] for p in new_themes),'Tema nuevo incompleto'
for doc in ['SKILL.md','docs/components.md','docs/editorial-reference.md']:
 for ref in re.findall(r'\]\(([^)]+)\)',(ROOT/doc).read_text()):
  if ref.startswith(('https:','http:','#')):continue
  assert ((ROOT/doc).parent/ref.split('#')[0]).is_file(),(doc,ref)
for file in (ROOT/'packages/core/components').glob('*.js'):
 assert not re.search(r'\b(fetch|XMLHttpRequest)\s*\(',file.read_text()),(file.name,'red en tiempo de ejecución')
 if shutil.which('node'):subprocess.run(['node','--check',str(file)],check=True,capture_output=True)
print('Tokens de paletas heredadas y sintaxis completos; enlaces, ausencia de fetch y sintaxis JS correctos' if shutil.which('node') else 'Tokens, enlaces y ausencia de fetch correctos; Node no disponible: sintaxis JS no ejecutada')
registry=json.loads((ROOT/'packages/core/registry/registry.json').read_text())
recipes=dict(re.findall(r'<!-- nota:ejemplo ([\w-]+) -->\s*```html\n(.*?)\n```',(ROOT/'docs/components.md').read_text(),re.S))
expected=set(recipes)-{'informe','multipagina'}
assert {item['id'] for item in registry['componentes']}==expected, 'Registro incompleto'
assert len(registry['componentes'])==len(expected), 'Registro duplicado'
for item in registry['componentes']:
 assert item['html']==recipes[item['id']] and item['criterio_y_limites'], ('Fuente de registro distinta',item['id'])
 assert all(dep==THREE or (ROOT/dep).is_file() for dep in item['dependencias']), ('Dependencia inexistente',item['id'])
print('Registro local: '+str(len(expected))+' recetas con HTML original, documentación y dependencias existentes')
print('Esto NO comprueba píxeles, audio, WebGL, foco real ni comportamiento del navegador.')

from contract_artifact import validate
for name in ['examples/generated/workbench.html','examples/generated/standard.html','examples/generated/standard-chapters.html','examples/generated/priorities.html','examples/generated/guide.html','examples/generated/liftit.html','examples/generated/blueprint.html','examples/generated/hacker.html','examples/generated/evidence.html','examples/generated/collaborative.html','examples/generated/linear-light.html','examples/generated/linear-dark.html','examples/generated/themes.html','examples/generated/system.html','examples/generated/executive.html','examples/generated/brands.html','examples/generated/tikin.html','examples/generated/catabum.html']:
 errors=validate((ROOT/name).read_text());assert not errors,(name,errors)
 print(name+': contrato estándar de artefacto correcto')

from contract_artifact import Document,FAMILIES,MODES
guide=Document((ROOT/'examples/generated/guide.html').read_text())
represented=[n.attrs['data-guia-componente'] for n in guide.live if 'data-guia-componente' in n.attrs]
assert set(represented)==expected and len(represented)==len(expected),'Guía incompleta o duplicada'
for case in json.loads((ROOT/'packages/core/registry/use-cases.json').read_text())['casos']:
 assert set(case['componentes'])<=expected,('Caso con componente inexistente',case['id'])
assert set(json.loads((ROOT/'VERSION.json').read_text())['temas'])==set(FAMILIES)
print('Guía: inventario completo y casos de uso con destinos vigentes')

from themes import DATA,tokens
assert len(DATA["familias"])==len(set(FAMILIES))
assert json.loads((ROOT/"VERSION.json").read_text())["paletas"]==2*len(FAMILIES)
assert set(json.loads((ROOT/"VERSION.json").read_text())["modos"])==set(MODES)
for family in DATA["familias"]:
 for mode in ["light","dark"]:
  seed=family[mode]
  if isinstance(seed,dict):
   palette=tokens(seed,mode)
   assert set(palette)>=set(k[2:] for k in palettes[0]), (family["id"],mode,"Tokens incompletos")
   assert f':root[data-theme="{family["id"]}-{mode}"]' in css
print(f"{len(FAMILIES)} familias con claro/oscuro y selector Sistema verificadas")

compat=json.loads((ROOT/'packages/core/registry/compatibility.json').read_text())['documentos_publicados']
for filename,identity in compat.items():
 html=(ROOT/filename).read_text()
 if 'documento_id' in identity:
  assert 'name="nota-documento" content="'+identity['documento_id']+'"' in html,filename
 else:assert 'name="nota-titulo-anterior"' in html,filename
print('Identidades publicadas conservadas tras el cambio de marca')
