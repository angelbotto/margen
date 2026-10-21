"""Contrato reutilizable para crear y verificar artefactos Margen. Sin red."""
from pathlib import Path
from html.parser import HTMLParser
from html import escape
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
VERSION='4'
from themes import THEMES,FAMILIES,MODES,normalize
from brands import BRANDS,identity,logo
from identity import mark as margen_mark, favicon as margen_favicon
from project_profile import FORMATS, company_logo
STYLES=('editorial','sobrio','tecnico','libro','revista','bitacora')
NOSCRIPT='.nota-estandar > .pagina { display:grid!important; grid-template-columns:1fr min(var(--texto),calc(100% - 2 * var(--gutter))) 1fr; row-gap:28px; }.nota-estandar .indice,.nota-estandar ~ .regla,.navegacion-editorial,.nota-estandar .paginacion { display:none!important; }'
THREE='https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.1/three.min.js'
CORE=['packages/core/components/interface.js','packages/core/components/reader-controls.js','packages/core/components/audio.js','packages/core/components/controls.js','packages/core/components/editorial-pieces.js','packages/core/components/reader.js','packages/core/components/code.js','packages/core/components/review.js']
ORDER=['packages/core/components/interface.js','packages/core/components/reader-controls.js','packages/core/components/relationship-map.js','packages/core/components/catalog.js','packages/core/components/audio.js','packages/core/components/controls.js','packages/core/components/editorial-pieces.js','packages/core/components/reader.js','packages/core/components/chapters.js','packages/core/components/presentation.js','packages/core/components/geography.js','packages/core/components/globe.js','packages/core/components/fleet.js','packages/core/components/charts.js','packages/core/components/analytics.js','packages/core/components/tables.js','packages/core/components/sound.js','packages/core/components/writing.js','packages/core/components/handwriting.js','packages/core/components/attention-map.js','packages/core/components/scene.js','packages/core/components/reports.js','packages/core/components/prototype.js','packages/core/components/tabs.js','packages/core/components/editorial.js','packages/core/components/invitation.js','packages/core/components/code.js','packages/core/components/table-model.js','packages/core/components/data-explorer.js','packages/core/components/evidence.js','packages/core/components/review.js']
ATTRS={'data-presentation':['packages/core/components/presentation.js'],'data-relationship-map':['packages/core/components/relationship-map.js'],'data-buscador-recetas':['packages/core/components/catalog.js'],'data-evidencia':['packages/core/components/evidence.js'],'data-flota':['packages/core/components/geography.js','packages/core/components/globe.js','packages/core/components/fleet.js'],'data-actividad':['packages/core/components/editorial-pieces.js'],'data-aviso-animado':['packages/core/components/editorial-pieces.js'],'data-galeria':['packages/core/components/editorial-pieces.js'],'data-grafica':['packages/core/components/charts.js'],'data-analitica':['packages/core/components/geography.js','packages/core/components/analytics.js'],'data-tabla':['packages/core/components/tables.js'],'data-escena':['packages/core/components/geography.js','packages/core/components/scene.js'],'data-reporte':['packages/core/components/reports.js'],'data-escritura':['packages/core/components/sound.js','packages/core/components/writing.js'],'data-mano':['packages/core/components/handwriting.js'],'data-subrayar':['packages/core/components/handwriting.js'],'data-atencion':['packages/core/components/attention-map.js'],'data-visor':['packages/core/components/prototype.js'],'data-pestanas':['packages/core/components/tabs.js'],'data-archivo':['packages/core/components/editorial.js'],'data-config-editorial':['packages/core/components/editorial.js'],'data-invitacion':['packages/core/components/invitation.js'],'data-explorador':['packages/core/components/table-model.js','packages/core/components/data-explorer.js'],'data-canal-sonido':['packages/core/components/sound.js']}
VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
class Node:
 def __init__(self,tag='',attrs=(),parent=None):self.tag=tag;self.attrs=dict(attrs);self.parent=parent;self.children=[];self.parts=[]
 @property
 def classes(self):return set((self.attrs.get('class') or '').split())
 def has_ancestor(self,tag):return bool(self.parent and (self.parent.tag==tag or self.parent.has_ancestor(tag)))
 def text(self):return ''.join(p.text() if isinstance(p,Node) else p for p in self.parts)
 def descendants(self):return [c for child in self.children for c in [child,*child.descendants()]]
class Document(HTMLParser):
 def __init__(self,html):
  super().__init__(convert_charrefs=True);self.root=Node();self.stack=[self.root];self.nodes=[];self.feed(html)
 def handle_starttag(self,tag,attrs):
  n=Node(tag,attrs,self.stack[-1]);n.parent.children.append(n);n.parent.parts.append(n);self.nodes.append(n)
  if tag not in VOID:self.stack.append(n)
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i].tag==tag:del self.stack[i:];break
 def handle_data(self,data):self.stack[-1].parts.append(data)
 def handle_startendtag(self,tag,attrs):self.handle_starttag(tag,attrs);self.handle_endtag(tag)
 @property
 def live(self):return [n for n in self.nodes if not n.has_ancestor('template')]

def recipe(key):
 text=(ROOT/'docs/components.md').read_text()
 return re.search(r'<!-- nota:ejemplo '+re.escape(key)+r' -->\s*```html\n(.*?)\n```',text,re.S).group(1)
def appearance():
 return re.search(r'<details class="apariencia-menu orbita"[\s\S]*?</details>',recipe('apariencia')).group().replace('apariencia-orbita','apariencia-principal')
def revision():
 s=recipe('revision').replace('<section class="pieza" id="revision-ejemplo" data-revision>','<div id="revision-base" data-revision hidden>')
 return s.removesuffix('</section>')+'</div>'
def modules_for(nodes,multipage=False):
 result=set(CORE)
 if multipage:result.add('packages/core/components/chapters.js')
 for n in nodes:
  for attr,modules in ATTRS.items():
   if attr in n.attrs:result.update(modules)
  if n.attrs.get('data-reporte')=='recorrido':result.add('packages/core/components/globe.js')
 return [m for m in ORDER if m in result]
def toc(content):
 items=[]
 for n in Document(content).live:
  if n.tag!='h2':continue
  anchor=n
  while anchor and not anchor.attrs.get('id'):anchor=anchor.parent
  if not anchor:raise ValueError('Cada h2 necesita un id propio o en su sección.')
  items.append((anchor.attrs['id'],n.text().strip()))
 return items

def build(title,pages,description='',brand='Margen',theme=None,style=None,document_id=None,mode=None,marca=None,project=None,format=None,theme_policy=None):
 if document_id is not None and (not isinstance(document_id,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,120}',document_id)):raise ValueError('documento_id: 1–120 letras, números, guiones o subrayados.')
 if theme is not None or mode is not None:theme,mode=normalize(theme,mode)
 project=project or {};company=project.get('company',{});project_info=project.get('project',{})
 if marca is not None:company={'brand':marca} if marca not in ('bottifact','margen') else {}
 elif company:marca=company.get('brand','margen')
 brand_id=identity(marca,theme)
 if brand_id:brand=BRANDS[brand_id]['nombre']
 elif company.get('name'):brand=company['name']
 brand_markup=logo(brand_id) if brand_id else company_logo(company,project['_root']) if company.get('logo') else margen_mark() if brand=='Margen' else '<span>'+escape(brand)+'</span>'
 format=format or ('chapters' if len(pages)>1 else 'document')
 if format not in FORMATS or format=='document' and len(pages)>1:raise ValueError('Use chapters or presentation for multiple pages.')
 theme_policy=theme_policy or ('project' if project.get('company') else 'reader')
 if theme_policy not in ('project','reader'):raise ValueError('Unknown theme policy.')
 if style is not None and style not in STYLES:raise ValueError('Estilo desconocido: '+str(style))
 if not isinstance(title,str) or not title.strip() or not isinstance(pages,list) or not pages:raise ValueError('Faltan título o páginas.')
 if not isinstance(description,str) or any(not isinstance(p,dict) or any(not isinstance(p.get(k),str) for k in ['id','titulo','html']) for p in pages):raise ValueError('Cada página requiere id, titulo y html de texto.')
 ids=[p['id'] for p in pages]
 if len(ids)!=len(set(ids)) or any(not re.fullmatch(r'[a-z][a-z0-9-]*',i) for i in ids):raise ValueError('IDs de página únicos: minúsculas, números y guiones.')
 for p in pages:
  for n in Document(p['html']).live:
   if n.tag in {'html','head','body','main','script','style','link','iframe'}:raise ValueError('El contenido sólo lleva bloques de la hoja; no '+n.tag+'.')
   if 'data-apariencia-menu' in n.attrs or 'data-revision' in n.attrs:raise ValueError('Apariencia y comentarios ya pertenecen a la base; no los dupliques.')
 multi=format in ('chapters','presentation');nodes=[n for p in pages for n in Document(p['html']).live];modules=modules_for(nodes,multi)
 if format=='presentation':modules=[m for m in ORDER if m in modules or m=='packages/core/components/presentation.js']
 nav=''
 if multi:
  nav='<div class="navegacion-scroll" data-capitulos-scroll tabindex="0" role="region" aria-label="Capítulos, desplazables"><nav aria-label="Capítulos">'+('<span class="nav-separador" aria-hidden="true">/</span>'.join('<button type="button" data-ir="'+p['id']+'">'+escape(p['titulo'])+'</button>' for p in pages))+'</nav></div>'
 else:nav='<span class="procedencia">'+escape(project_info.get('name') or 'Documento para revisión')+'</span>'
 header='<a class="salto" href="#'+ids[0]+'">Saltar al contenido</a><header class="barra capitulos navegacion-editorial" id="nota-inicio"><a class="firma-editorial" aria-label="'+escape(brand,quote=True)+' · Inicio" title="'+escape(brand,quote=True)+'" href="#'+ids[0]+'">'+brand_markup+'</a>'+nav+appearance()+'</header>'
 pieces=[]
 for i,p in enumerate(pages):
  heading='<header class="cabecera"'+('' if multi else ' id="'+p['id']+'"')+'><h1>'+escape(p['titulo'] if multi else title)+'</h1>'+('<p class="bajada">'+escape(description)+'</p>' if i==0 and description else '')+'</header>'
  items=toc(p['html'])
  index='<nav class="indice" tabindex="0" aria-label="En esta página"><p class="ceja">En esta página</p><ol>'+''.join('<li><a href="#'+escape(id,quote=True)+'">'+escape(label)+'</a></li>' for id,label in items)+'</ol></nav>' if items else ''
  print_brand='<div class="presentation-print-brand" aria-hidden="true">'+brand_markup+'</div>' if format=='presentation' else ''
  block=print_brand+heading+index+p['html']
  if multi:block='<article class="pagina'+(' viva' if i==0 else '')+'" id="'+p['id']+'" data-pagina'+('' if i==0 else ' hidden')+'>'+block+'</article>'
  pieces.append(block)
 pag='<div class="paginacion" data-paginacion><button type="button" data-nav="prev"><span class="et">Anterior</span><span class="tit"></span></button><button type="button" data-nav="next"><span class="et">Siguiente</span><span class="tit"></span></button></div>' if multi else ''
 main='<main class="hoja lectura-guiada nota-estandar marcos-editoriales'+(' multipagina edicion' if multi else '')+'" data-lectura'+(' data-presentation' if format=='presentation' else '')+(' data-progreso-pagina data-historial data-enlaces-internos' if multi else '')+' lang="es">'+''.join(pieces)+pag+'<footer class="pie"><p>'+escape(brand)+' · '+escape(title)+'</p></footer></main>'
 ruler='<div class="regla regla-guiada" role="slider" tabindex="0" aria-orientation="horizontal" aria-label="Progreso de lectura" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><div class="ticks"></div><div class="cursor"></div><span class="val">0%</span></div>'
 files=['packages/core/styles/fonts.css','packages/core/styles/artifact.css',*modules]
 manifest={'version':VERSION,'paginas':ids,'modulos':modules,'fuentes':{f:hashlib.sha256((ROOT/f).read_text().encode('utf-8')).hexdigest() for f in files}}
 result='<title>'+escape(title)+'</title>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n<meta name="nota-tikin-version" content="'+VERSION+'">\n'
 result+=margen_favicon()+'\n'
 result+='<meta name="nota-documento" content="'+(document_id or 'nota-'+hashlib.sha256(title.encode()).hexdigest()[:24])+'">\n'
 for name,value in [('nota-tema-inicial',theme),('nota-modo-inicial',mode),('nota-estilo-inicial',style),('margen-format',format),('margen-project-id',project_info.get('id')),('margen-project-name',project_info.get('name')),('margen-company',brand if brand!='Margen' else None),('margen-brand',brand_id),('margen-theme-policy',theme_policy)]:
  if value is not None:result+='<meta name="'+name+'" content="'+escape(str(value),quote=True)+'">\n'
 for file in files[:2]:result+='<style data-nota-fuente="'+file+'">\n'+(ROOT/file).read_text()+'\n</style>\n'
 result+=header+main+ruler+revision()
 if multi:result+='<noscript><style data-nota-sin-js>'+NOSCRIPT+'</style><p>JavaScript está desactivado: se muestran todos los capítulos para lectura.</p></noscript>'
 if any(m in modules for m in ['packages/core/components/globe.js','packages/core/components/scene.js']):result+='<script src="'+THREE+'"></script>'
 for module in modules:result+='<script data-nota-modulo="'+module+'">\n'+(ROOT/module).read_text()+'\n</script>\n'
 result+='<script type="application/json" data-nota-manifiesto>'+json.dumps(manifest,ensure_ascii=False).replace('<','\\u003c')+'</script>'
 errors=validate(result)
 if errors:raise ValueError('\n'.join(errors))
 return result

def composition_warnings(html):
 """Flag custom prose wrappers whose rhythm cannot be inferred from canonical CSS."""
 doc=Document(html);warnings=[]
 css=(ROOT/'packages/core/styles/artifact.css').read_text()
 known=set(re.findall(r'\.([A-Za-z_][A-Za-z0-9_-]*)',css))
 for node in doc.live:
  if node.tag not in {'section','article','div'} or not node.classes:continue
  ancestors=[];parent=node
  while parent:ancestors.append(parent);parent=parent.parent
  if not any('hoja' in n.classes for n in ancestors):continue
  if any('data-presentation' in n.attrs or 'data-visor' in n.attrs or 'data-explorador' in n.attrs or n.attrs.get('data-ritmo')=='propio' or n.tag in {'nav','form','dialog','table','pre'} for n in ancestors):continue
  if 'prosa' in node.classes or node.classes & (known-{'ancho','amplio'}):continue
  if node.classes <= {'ancho','amplio'}:continue
  if any(a.tag in {'h1','h2','h3','h4','h5','h6'} and b.tag in {'p','ul','ol','dl','blockquote'} for a,b in zip(node.children,node.children[1:])):
   warnings.append((node.attrs.get('id') or node.tag+'.'+'.'.join(sorted(node.classes)))+': custom prose wrapper has no canonical rhythm; add class="prosa" or data-ritmo="propio" for an intentionally custom layout. Check heading spacing in a browser.')
 return warnings

def layout_boundary(node):
 if node is None:return False
 if node.classes & {'hoja','pagina'}:return True
 if node.tag!='article' or 'class' in node.attrs or 'style' in node.attrs or not node.parent or not node.parent.classes & {'hoja','pagina'}:return False
 parent=node
 while parent:
  if 'data-presentation' in parent.attrs or parent.attrs.get('data-ritmo')=='propio':return False
  parent=parent.parent
 return True

def validate(html):
 doc=Document(html);nodes=doc.live;errors=[]
 def require(condition,message):
  if not condition:errors.append(message)
 def has(attr):return [n for n in nodes if attr in n.attrs]
 def classes(cls):return [n for n in nodes if cls in n.classes]
 require(html.startswith('<title>') and '<meta charset="utf-8">' in html[:1024],'Faltan título o charset temprano.')
 require(not any(n.tag in {'html','head','body','iframe'} for n in nodes),'El artefacto debe ser un fragmento sin iframe.')
 for name,allowed in [('margen-format',FORMATS),('margen-theme-policy',('project','reader')),('nota-tema-inicial',FAMILIES),('nota-modo-inicial',MODES),('nota-estilo-inicial',STYLES)]:
  settings=[n for n in nodes if n.tag=='meta' and n.attrs.get('name')==name]
  require(len(settings)<=1 and all(n.attrs.get('content') in allowed for n in settings),'Preferencia inicial inválida: '+name)
 ids=[n.attrs['id'] for n in nodes if n.attrs.get('id')];require(len(ids)==len(set(ids)),'Hay IDs duplicados.')
 menus=has('data-apariencia-menu');require(len(menus)==1 and 'orbita' in menus[0].classes,'Debe existir una sola llave circular sol/luna de Apariencia.')
 if menus:
  children=menus[0].descendants()
  require(set(FAMILIES)=={n.attrs.get('value') for n in children if 'data-elegir-tema' in n.attrs},'Apariencia debe ofrecer todas las familias.')
  require(set(MODES)=={n.attrs.get('value') for n in children if 'data-elegir-modo' in n.attrs},'Apariencia debe ofrecer Claro, Oscuro y Sistema por separado.')
  require(all(any(c in n.classes for n in children) for c in ['icono-sol','icono-luna','paleta-mini']),'Faltan iconos sol/luna o muestras de color.')
 require(set(STYLES)<={n.attrs.get('value') for n in has('data-elegir-estilo')},'Apariencia debe ofrecer las seis combinaciones tipográficas.')
 require({n.attrs.get('data-preferencia-tab') for n in has('data-preferencia-tab')}=={'temas','letras','sonido'},'Apariencia necesita pestañas Temas, Letras y Sonido.')
 for attr in ['data-buscar-tema','data-familia-tema','data-temas-resultados']:
  require(bool(has(attr)),'Falta exploración de temas: '+attr)
 for attr in ['data-audio-global','data-audio-prueba','data-audio-volumen','data-audio-estado','data-comodidad','data-papel-tramado']:
  require(bool(has(attr)),'Falta el control estándar '+attr+'.')
 require(all(n.attrs.get('aria-pressed')=='true' for n in has('data-audio-global')),'La preferencia inicial de sonido debe estar habilitada; el contexto espera el primer clic.')
 require(len(has('data-revision'))==1,'Falta el montaje único de comentarios flotantes.')
 for attr in ['data-revision-editor','data-revision-panel','data-revision-texto','data-revision-contexto','data-revision-notas','data-revision-prompt','data-revision-estado','data-revision-modo','data-revision-lista','data-revision-guardar','data-revision-cancelar','data-revision-cerrar']:
  require(len(has(attr))==1,'Falta o se duplica '+attr+'.')
 mains=[n for n in nodes if n.tag=='main'];require(len(mains)==1 and {'hoja','lectura-guiada','nota-estandar','marcos-editoriales'}<=mains[0].classes,'Falta la hoja estándar con lectura guiada.')
 multi=bool(mains and 'multipagina' in mains[0].classes)
 formats=[n.attrs.get('content') for n in nodes if n.tag=='meta' and n.attrs.get('name')=='margen-format']
 if formats:require(bool(has('data-presentation'))==(formats[0]=='presentation'),'Presentation format and runtime marker must agree.')
 require(len(classes('regla-guiada'))==1,'Falta la regla de lectura.')
 for page in (classes('pagina') if multi else mains):
  headings=[n for n in page.descendants() if n.tag=='h2' and not n.has_ancestor('template')]
  indices=[n for n in page.children if 'indice' in n.classes]
  require(len(indices)==int(bool(headings)),'Índice ausente o duplicado en '+page.attrs.get('id','hoja')+'.')
  if headings and indices:
   anchors=[]
   for heading in headings:
    node=heading
    while node and not node.attrs.get('id'):node=node.parent
    if node:anchors.append('#'+node.attrs['id'])
   require([n.attrs.get('href') for n in indices[0].descendants() if n.tag=='a']==anchors,'El índice no corresponde a los h2 de '+page.attrs.get('id','hoja')+'.')
 for n in nodes:
  if n.attrs.get('href','').startswith('#'):require(n.attrs['href'][1:] in ids,'Enlace sin destino: '+n.attrs['href'])
  for attr in ['aria-controls','aria-labelledby','aria-describedby','data-copiar','data-ir','data-actividad-tabla']:
   if n.attrs.get(attr):require(all(x in ids for x in n.attrs[attr].split()),'Referencia sin destino: '+n.attrs[attr])
  if n.classes & {'ancho','amplio'}:require(layout_boundary(n.parent),'Figura ancha fuera de la rejilla: '+n.attrs.get('id',n.tag))
  if n.classes & {'tabla-caja','grafica-caja','diagrama-caja','escena-caja','escritura-caja','visor-caja','apariencia-panel','navegacion-scroll','galeria-pista'} or n.tag=='pre':require(n.attrs.get('tabindex')=='0' and bool(n.attrs.get('aria-label') or n.attrs.get('aria-labelledby')),'Desplazamiento sin foco o nombre: '+n.tag)
  require(not any(a.lower().startswith('on') for a in n.attrs),'Manejador inline fuera de los módulos: '+n.tag)
  if n.tag=='img':require(n.attrs.get('src','').startswith('data:') and 'alt' in n.attrs,'Imagen externa o sin alternativa.')
  for attr in ['href','src','style']:
   value=n.attrs.get(attr) or '';require(not re.search(r'javascript:|@import|url\(\s*[\'"]?https?:',value,re.I),'Recurso o código fuera del contrato: '+attr)
  if n.tag=='link':require(n.attrs.get('rel')=='icon' and n.attrs.get('type')=='image/svg+xml' and n.attrs.get('href','').startswith('data:image/svg+xml;base64,'),'El estilo y las fuentes deben estar incrustados; el favicon debe ser un SVG incrustado.')
 scripts=[n for n in nodes if n.tag=='script' and n.attrs.get('type')!='application/json'];module_nodes=[n for n in scripts if 'data-nota-modulo' in n.attrs]
 names=[n.attrs['data-nota-modulo'] for n in module_nodes];required=modules_for(nodes,multi)
 require(len(names)==len(set(names)),'Hay módulos duplicados.')
 require(set(required)<=set(names),'Faltan módulos: '+', '.join(sorted(set(required)-set(names))))
 require(names==[m for m in ORDER if m in names],'Orden de módulos incorrecto.')
 for n in module_nodes:
  name=n.attrs['data-nota-modulo'];require(name in ORDER,'Módulo desconocido: '+name)
  if name in ORDER:require(n.text().strip()==(ROOT/name).read_text().strip(),'Módulo modificado o desactualizado: '+name)
 for n in scripts:
  require('data-nota-modulo' in n.attrs or n.attrs.get('src')==THREE,'Script sin módulo estándar.')
 external=[n.attrs['src'] for n in scripts if n.attrs.get('src')];require(external==([THREE] if any(m in names for m in ['packages/core/components/globe.js','packages/core/components/scene.js']) else []),'Three debe estar fijado e incluido una sola vez si hace falta.')
 fallbacks=[n for n in nodes if 'data-nota-sin-js' in n.attrs]
 require(len(fallbacks)==int(multi) and all(n.has_ancestor('noscript') and n.text()==NOSCRIPT for n in fallbacks),'Falta la lectura multipágina sin JavaScript.')
 styles=[n for n in nodes if n.tag=='style' and 'data-nota-sin-js' not in n.attrs];require(len(styles)==2,'Debe haber dos fuentes CSS canónicas: packages/core/styles/fonts.css y packages/core/styles/artifact.css.')
 for name in ['packages/core/styles/fonts.css','packages/core/styles/artifact.css']:
  found=[n for n in styles if n.attrs.get('data-nota-fuente')==name];require(len(found)==1 and found[0].text().strip()==(ROOT/name).read_text().strip(),'CSS ausente, modificado o desactualizado: '+name)
 manifests=has('data-nota-manifiesto');require(len(manifests)==1,'Falta manifiesto de versión y fuentes.')
 if len(manifests)==1:
  try:
   m=json.loads(manifests[0].text());require(m.get('version')==VERSION and m.get('modulos')==names,'Manifiesto incompatible con los módulos.')
   for name in ['packages/core/styles/fonts.css','packages/core/styles/artifact.css',*names]:
    if name in ['packages/core/styles/fonts.css','packages/core/styles/artifact.css',*ORDER]:require(m.get('fuentes',{}).get(name)==hashlib.sha256((ROOT/name).read_text().encode('utf-8')).hexdigest(),'Hash desactualizado: '+name)
  except (ValueError,TypeError,AttributeError):errors.append('Manifiesto inválido.')
 return list(dict.fromkeys(errors))
