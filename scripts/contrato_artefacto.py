"""Contrato reutilizable para crear y verificar artefactos Bottifact. Sin red."""
from pathlib import Path
from html.parser import HTMLParser
from html import escape
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
VERSION='4'
from temas import THEMES,FAMILIES,MODES,normalize
from marcas import BRANDS,identity,logo
STYLES=('editorial','sobrio','tecnico','libro','revista','bitacora')
NOSCRIPT='.nota-estandar > .pagina { display:grid!important; grid-template-columns:1fr min(var(--texto),calc(100% - 2 * var(--gutter))) 1fr; row-gap:28px; }.nota-estandar .indice,.nota-estandar ~ .regla,.navegacion-editorial,.nota-estandar .paginacion { display:none!important; }'
THREE='https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.1/three.min.js'
CORE=['audio.js','controles.js','piezas-editoriales.js','interacciones.js','codigo.js','revision.js']
ORDER=['audio.js','controles.js','piezas-editoriales.js','interacciones.js','multipagina.js','geografia.js','globo.js','flota.js','graficas.js','analitica.js','tablas.js','sonido.js','escritura.js','mano.js','atencion.js','escena.js','reportes.js','visor.js','pestanas.js','editorial.js','invitacion.js','codigo.js','explorador.js','jerarquia.js','evidencia.js','revision.js']
ATTRS={'data-evidencia':['evidencia.js'],'data-flota':['geografia.js','globo.js','flota.js'],'data-actividad':['piezas-editoriales.js'],'data-aviso-animado':['piezas-editoriales.js'],'data-galeria':['piezas-editoriales.js'],'data-grafica':['graficas.js'],'data-analitica':['geografia.js','analitica.js'],'data-tabla':['tablas.js'],'data-escena':['geografia.js','escena.js'],'data-reporte':['reportes.js'],'data-escritura':['sonido.js','escritura.js'],'data-mano':['mano.js'],'data-subrayar':['mano.js'],'data-atencion':['atencion.js'],'data-visor':['visor.js'],'data-pestanas':['pestanas.js'],'data-archivo':['editorial.js'],'data-config-editorial':['editorial.js'],'data-invitacion':['invitacion.js'],'data-explorador':['explorador.js'],'data-jerarquia':['jerarquia.js'],'data-canal-sonido':['sonido.js']}
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
 text=(ROOT/'componentes.md').read_text()
 return re.search(r'<!-- nota:ejemplo '+re.escape(key)+r' -->\s*```html\n(.*?)\n```',text,re.S).group(1)
def appearance():
 return re.search(r'<details class="apariencia-menu orbita"[\s\S]*?</details>',recipe('apariencia')).group().replace('apariencia-orbita','apariencia-principal')
def revision():
 s=recipe('revision').replace('<section class="pieza" id="revision-ejemplo" data-revision>','<div id="revision-base" data-revision hidden>')
 return s.removesuffix('</section>')+'</div>'
def modules_for(nodes,multipage=False):
 result=set(CORE)
 if multipage:result.add('multipagina.js')
 for n in nodes:
  for attr,modules in ATTRS.items():
   if attr in n.attrs:result.update(modules)
  if n.attrs.get('data-reporte')=='recorrido':result.add('globo.js')
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

def build(title,pages,description='',brand='Bottifact',theme=None,style=None,document_id=None,mode=None,marca=None):
 if document_id is not None and (not isinstance(document_id,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,120}',document_id)):raise ValueError('documento_id: 1–120 letras, números, guiones o subrayados.')
 if theme is not None or mode is not None:theme,mode=normalize(theme,mode)
 brand_id=identity(marca,theme)
 if brand_id:brand=BRANDS[brand_id]['nombre']
 if style is not None and style not in STYLES:raise ValueError('Estilo desconocido: '+str(style))
 if not isinstance(title,str) or not title.strip() or not isinstance(pages,list) or not pages:raise ValueError('Faltan título o páginas.')
 if not isinstance(description,str) or any(not isinstance(p,dict) or any(not isinstance(p.get(k),str) for k in ['id','titulo','html']) for p in pages):raise ValueError('Cada página requiere id, titulo y html de texto.')
 ids=[p['id'] for p in pages]
 if len(ids)!=len(set(ids)) or any(not re.fullmatch(r'[a-z][a-z0-9-]*',i) for i in ids):raise ValueError('IDs de página únicos: minúsculas, números y guiones.')
 for p in pages:
  for n in Document(p['html']).live:
   if n.tag in {'html','head','body','main','script','style','link','iframe'}:raise ValueError('El contenido sólo lleva bloques de la hoja; no '+n.tag+'.')
   if 'data-apariencia-menu' in n.attrs or 'data-revision' in n.attrs:raise ValueError('Apariencia y comentarios ya pertenecen a la base; no los dupliques.')
 multi=len(pages)>1;nodes=[n for p in pages for n in Document(p['html']).live];modules=modules_for(nodes,multi)
 nav=''
 if multi:
  nav='<div class="navegacion-scroll" data-capitulos-scroll tabindex="0" role="region" aria-label="Capítulos, desplazables"><nav aria-label="Capítulos">'+('<span class="nav-separador" aria-hidden="true">/</span>'.join('<button type="button" data-ir="'+p['id']+'">'+escape(p['titulo'])+'</button>' for p in pages))+'</nav></div>'
 else:nav='<span class="procedencia">Documento para revisión</span>'
 header='<a class="salto" href="#'+ids[0]+'">Saltar al contenido</a><header class="barra capitulos navegacion-editorial" id="nota-inicio"><a class="firma-editorial" aria-label="'+escape(brand,quote=True)+' · Inicio" href="#'+ids[0]+'">'+(logo(brand_id) if brand_id else '<span>'+escape(brand)+'</span>')+'</a>'+nav+appearance()+'</header>'
 pieces=[]
 for i,p in enumerate(pages):
  heading='<header class="cabecera"'+('' if multi else ' id="'+p['id']+'"')+'><h1>'+escape(p['titulo'] if multi else title)+'</h1>'+('<p class="bajada">'+escape(description)+'</p>' if i==0 and description else '')+'</header>'
  items=toc(p['html'])
  index='<nav class="indice" tabindex="0" aria-label="En esta página"><p class="ceja">En esta página</p><ol>'+''.join('<li><a href="#'+escape(id,quote=True)+'">'+escape(label)+'</a></li>' for id,label in items)+'</ol></nav>' if items else ''
  block=heading+index+p['html']
  if multi:block='<article class="pagina'+(' viva' if i==0 else '')+'" id="'+p['id']+'" data-pagina'+('' if i==0 else ' hidden')+'>'+block+'</article>'
  pieces.append(block)
 pag='<div class="paginacion" data-paginacion><button type="button" data-nav="prev"><span class="et">Anterior</span><span class="tit"></span></button><button type="button" data-nav="next"><span class="et">Siguiente</span><span class="tit"></span></button></div>' if multi else ''
 main='<main class="hoja lectura-guiada nota-estandar marcos-editoriales'+(' multipagina edicion' if multi else '')+'" data-lectura'+(' data-progreso-pagina data-historial data-enlaces-internos' if multi else '')+' lang="es">'+''.join(pieces)+pag+'<footer class="pie"><p>'+escape(brand)+' · '+escape(title)+'</p></footer></main>'
 ruler='<div class="regla regla-guiada" role="slider" tabindex="0" aria-orientation="horizontal" aria-label="Progreso de lectura" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><div class="ticks"></div><div class="cursor"></div><span class="val">0%</span></div>'
 files=['fuentes.css','estilo.css',*modules]
 manifest={'version':VERSION,'paginas':ids,'modulos':modules,'fuentes':{f:hashlib.sha256((ROOT/f).read_text().encode('utf-8')).hexdigest() for f in files}}
 result='<title>'+escape(title)+'</title>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n<meta name="nota-tikin-version" content="'+VERSION+'">\n'
 result+='<meta name="nota-documento" content="'+(document_id or 'nota-'+hashlib.sha256(title.encode()).hexdigest()[:24])+'">\n'
 for name,value in [('nota-tema-inicial',theme),('nota-modo-inicial',mode),('nota-estilo-inicial',style)]:
  if value is not None:result+='<meta name="'+name+'" content="'+value+'">\n'
 for file in files[:2]:result+='<style data-nota-fuente="'+file+'">\n'+(ROOT/file).read_text()+'\n</style>\n'
 result+=header+main+ruler+revision()
 if multi:result+='<noscript><style data-nota-sin-js>'+NOSCRIPT+'</style><p>JavaScript está desactivado: se muestran todos los capítulos para lectura.</p></noscript>'
 if any(m in modules for m in ['globo.js','escena.js']):result+='<script src="'+THREE+'"></script>'
 for module in modules:result+='<script data-nota-modulo="'+module+'">\n'+(ROOT/module).read_text()+'\n</script>\n'
 result+='<script type="application/json" data-nota-manifiesto>'+json.dumps(manifest,ensure_ascii=False).replace('<','\\u003c')+'</script>'
 errors=validate(result)
 if errors:raise ValueError('\n'.join(errors))
 return result

def validate(html):
 doc=Document(html);nodes=doc.live;errors=[]
 def require(condition,message):
  if not condition:errors.append(message)
 def has(attr):return [n for n in nodes if attr in n.attrs]
 def classes(cls):return [n for n in nodes if cls in n.classes]
 require(html.startswith('<title>') and '<meta charset="utf-8">' in html[:1024],'Faltan título o charset temprano.')
 require(not any(n.tag in {'html','head','body','iframe'} for n in nodes),'El artefacto debe ser un fragmento sin iframe.')
 for name,allowed in [('nota-tema-inicial',FAMILIES),('nota-modo-inicial',MODES),('nota-estilo-inicial',STYLES)]:
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
  if n.classes & {'ancho','amplio'}:require(bool(n.parent and ('hoja' in n.parent.classes or 'pagina' in n.parent.classes)),'Figura ancha fuera de la rejilla: '+n.attrs.get('id',n.tag))
  if n.classes & {'tabla-caja','grafica-caja','diagrama-caja','escena-caja','escritura-caja','visor-caja','apariencia-panel','navegacion-scroll','galeria-pista'} or n.tag=='pre':require(n.attrs.get('tabindex')=='0' and bool(n.attrs.get('aria-label') or n.attrs.get('aria-labelledby')),'Desplazamiento sin foco o nombre: '+n.tag)
  require(not any(a.lower().startswith('on') for a in n.attrs),'Manejador inline fuera de los módulos: '+n.tag)
  if n.tag=='img':require(n.attrs.get('src','').startswith('data:') and 'alt' in n.attrs,'Imagen externa o sin alternativa.')
  for attr in ['href','src','style']:
   value=n.attrs.get(attr) or '';require(not re.search(r'javascript:|@import|url\(\s*[\'"]?https?:',value,re.I),'Recurso o código fuera del contrato: '+attr)
  if n.tag=='link':require(False,'El estilo y las fuentes deben estar incrustados.')
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
 external=[n.attrs['src'] for n in scripts if n.attrs.get('src')];require(external==([THREE] if any(m in names for m in ['globo.js','escena.js']) else []),'Three debe estar fijado e incluido una sola vez si hace falta.')
 fallbacks=[n for n in nodes if 'data-nota-sin-js' in n.attrs]
 require(len(fallbacks)==int(multi) and all(n.has_ancestor('noscript') and n.text()==NOSCRIPT for n in fallbacks),'Falta la lectura multipágina sin JavaScript.')
 styles=[n for n in nodes if n.tag=='style' and 'data-nota-sin-js' not in n.attrs];require(len(styles)==2,'Debe haber dos fuentes CSS canónicas: fuentes.css y estilo.css.')
 for name in ['fuentes.css','estilo.css']:
  found=[n for n in styles if n.attrs.get('data-nota-fuente')==name];require(len(found)==1 and found[0].text().strip()==(ROOT/name).read_text().strip(),'CSS ausente, modificado o desactualizado: '+name)
 manifests=has('data-nota-manifiesto');require(len(manifests)==1,'Falta manifiesto de versión y fuentes.')
 if len(manifests)==1:
  try:
   m=json.loads(manifests[0].text());require(m.get('version')==VERSION and m.get('modulos')==names,'Manifiesto incompatible con los módulos.')
   for name in ['fuentes.css','estilo.css',*names]:
    if name in ['fuentes.css','estilo.css',*ORDER]:require(m.get('fuentes',{}).get(name)==hashlib.sha256((ROOT/name).read_text().encode('utf-8')).hexdigest(),'Hash desactualizado: '+name)
  except (ValueError,TypeError,AttributeError):errors.append('Manifiesto inválido.')
 return list(dict.fromkeys(errors))
