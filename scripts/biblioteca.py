"""Edición organizada y registro local, construidos desde las recetas documentadas."""
import re,json,html
CHAPTERS=[
 ('publicaciones','Publicaciones','Un cuaderno que invita a volver.','Portada, archivo, autoría y siguientes lecturas.',['archivo','autor','relacionados','cards','cards-trazadas','estanteria','invitacion','pie-editorial','actividad-editorial','galeria']),
 ('lectura','Artículos','Leer con contexto.','Anotaciones, fuentes, definiciones y cambios editoriales.',['articulo','referencias','glosario','metodologia','revisiones','manuscrita','apuntes','lista-estados','lista-proyectos','conversacion','relato-visual','enlaces-icono','avisos-animados']),
 ('reportes','Reportes','De la evidencia a la decisión.','Afirmaciones, compensaciones, riesgos y escenarios explícitos.',['ficha-entrega','hallazgo','decision','cronologia','criterios','riesgos','escenario','conciliacion','trayectoria','gantt','sensibilidad']),
 ('graficas','Gráficas','La escala también es una afirmación.','Valores alcanzables, fuentes visibles y alternativas en tabla.',['barras','lineas','temporal','dispersion','distribucion','calor','cascada','multiples','calendario','torta','areas','caja','velas','mapa-rutas','mapa-burbujas','atencion','sankey','cohortes','embudo','incertidumbre']),
 ('tablas','Tablas','Cada dato conserva su lugar.','Comparación, totales, series y densidad sin cortar información.',['cola-novedades','tabla-densa','comparacion','totales','sparkline','explorador','tabla-jerarquica']),
 ('prototipos','Prototipos','La propuesta se puede recorrer.','Interfaz local, estados, vistas alternativas y explicaciones.',['visor','pestanas','antes-despues','anotaciones','evidencia-ampliable']),
 ('expresion','Espacio y gesto','Hay ideas que necesitan otra dimensión.','Geografía, composiciones con Three y sonido optativo.',['globo-flota','recorrido','xyz','etapas','columnas-mapa','arcos-mapa','almacen','sonido']),
 ('configuracion','Edición','Una voz, muchas maneras de editar.','Nueve papeles, escritura animada, sonido, código y comentarios.',['apariencia','escritura','configuracion','codigo-poliglota','terminal','revision','marco','navegacion','codigo-lineas'])]

def build(root,start,script,appearance,recipes,labels,three):
 docs=(root/'componentes.md').read_text();all_recipes=dict(recipes());metadata=[]
 def rich(text):
  text=html.escape(text.strip());text=re.sub(r'\*\*(.*?)\*\*',r'<strong>\1</strong>',text,flags=re.S);text=re.sub(r'`([^`]+)`',r'<code>\1</code>',text)
  text=re.sub(r'\[([^]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',text)
  return ''.join('<p>'+p.replace('\n',' ')+'</p>' for p in text.split('\n\n') if p.strip())
 def deps(key):
  if key in ['relato-visual','sankey','cohortes','sensibilidad','gantt','embudo','incertidumbre','evidencia-ampliable']:return ['evidencia.js']
  if key=='globo-flota':return [three,'geografia.js','globo.js','flota.js']
  if key=='cola-novedades':return ['controles.js','explorador.js']
  if key in ['actividad-editorial','avisos-animados','galeria']:return ['piezas-editoriales.js']
  if key=='codigo-lineas':return ['codigo.js']
  if key in ['manuscrita','apuntes']:return ['mano.js']
  if key=='invitacion':return ['invitacion.js']
  if key=='atencion':return ['atencion.js']
  if key in ['calendario','torta','areas','caja','velas']:return ['analitica.js']
  if key in ['mapa-rutas','mapa-burbujas']:return ['geografia.js','analitica.js']
  if key in ['columnas-mapa','arcos-mapa']:return [three,'geografia.js','escena.js']
  if key=='almacen':return [three,'escena.js']
  if key in ['barras','lineas','temporal','dispersion','distribucion','calor']:return ['graficas.js']
  if key in ['comparacion','totales','sparkline']:return ['tablas.js']
  if key in ['cascada','multiples','conciliacion','escenario']:return ['reportes.js']
  if key=='recorrido':return [three,'globo.js','reportes.js']
  if key in ['xyz','etapas']:return [three,'escena.js']
  return {'visor':['visor.js'],'pestanas':['pestanas.js'],'sonido':['sonido.js'],'escritura':['sonido.js','escritura.js'],'explorador':['explorador.js'],'tabla-jerarquica':['jerarquia.js'],'codigo-poliglota':['codigo.js','pestanas.js'],'revision':['revision.js'],'archivo':['editorial.js'],'configuracion':['editorial.js']}.get(key,[])
 def recipe(key,page):
  source=all_recipes[key];anchor='receta-'+key
  # Una envoltura sólo para el título; el componente ancho sigue siendo hijo directo de .pagina.
  heading=f'<section class="seccion" id="{anchor}" tabindex="-1"><p class="ceja">Componente / {labels[key]}</p><h2>{labels[key]}</h2></section>'
  after=docs.split('<!-- nota:ejemplo '+key+' -->',1)[1].split('```',2)[2].split('\n## ',1)[0].strip()
  modules=list(dict.fromkeys(['fuentes.css','estilo.css','audio.js','controles.js','piezas-editoriales.js','interacciones.js']+deps(key)))
  metadata.append({'id':key,'nombre':labels[key],'capitulo':page,'href':'biblioteca.html#'+anchor,'dependencias':modules,'html':source,'criterio_y_limites':after})
  codeid='biblioteca-codigo-'+key
  return heading+source+f'<div class="receta-guia">{rich(after)}</div><details class="receta-copia ancho"><summary>Copiar HTML · {labels[key]}</summary><p class="procedencia">Dependencias: {html.escape(", ".join(modules))}</p><div class="codigo"><div class="cab"><span>{labels[key]}</span><button type="button" data-copiar="{codeid}" aria-label="Copiar HTML de {labels[key]}">Copiar HTML</button><span role="status" class="copia-estado"></span></div><pre tabindex="0" aria-label="HTML de {labels[key]}, desplazable"><code id="{codeid}">{html.escape(source)}</code></pre></div></details>'
 def index(items,label):
  return '<nav class="indice" tabindex="0" aria-label="'+html.escape(label)+'"><p class="ceja">En esta página</p><ol>'+''.join('<li><a href="#'+id+'">'+html.escape(title)+'</a></li>' for id,title in items)+'</ol></nav>'
 pages=''
 for n,(id,label,title,desc,keys) in enumerate(CHAPTERS,2):
  pages+=f'<article class="pagina" id="{id}" data-pagina hidden><header class="cabecera"><p class="ceja">Capítulo {n:02d} / 09</p><h1>{title}</h1><p class="bajada">{desc}</p></header>'+index([('receta-'+key,labels[key]) for key in keys],'Índice de '+label)+''.join(recipe(key,id) for key in keys)+'</article>'
 assert len(metadata)==len(set(m['id'] for m in metadata))==len(all_recipes)-2
 cards=''.join(f'<a href="#{id}"><span class="ceja">{n:02d} / {len(keys)} piezas</span><strong>{label}</strong><small>{desc}</small></a>' for n,(id,label,title,desc,keys) in enumerate(CHAPTERS,2))
 links=''.join(f'<li data-claves="{m["capitulo"]}"><a href="#{m["href"].split("#")[1]}">{m["nombre"]}</a></li>' for m in metadata)
 intro=f'''<article class="pagina viva" id="portada" data-pagina><header class="cabecera"><p class="ceja">Edición 03 / Biblioteca editorial</p><h1>Todo lo que una buena idea puede llegar a ser.</h1><p class="bajada">Un artículo que se lee con calma. Un informe que se puede comprobar. Un prototipo que invita a probar.</p><p class="secundario">{len(metadata)} recetas · 9 capítulos · 11 papeles</p></header>{index([("rutas-biblioteca","Explorar capítulos"),("buscar-biblioteca","Buscar componentes"),("componer-biblioteca","Componer una historia")],"Índice de inicio")}<nav class="biblioteca-rutas ancho" id="rutas-biblioteca" aria-label="Explorar la biblioteca">{cards}</nav><section class="seccion" id="buscar-biblioteca"><h2>Encuentra la pieza que necesitas.</h2><p>Cada ejemplo incluye HTML completo, dependencias, criterio de uso y límites. Las cifras y publicaciones de demostración están identificadas como ejemplos.</p><div data-buscador-recetas><div class="buscador-recetas"><label for="biblioteca-buscar">Buscar componentes</label><input id="biblioteca-buscar" type="search" placeholder="Globo, tabla, autor, escenario…" aria-describedby="biblioteca-resultados"><p id="biblioteca-resultados" role="status"></p></div><nav aria-label="Recetas de la biblioteca"><ul class="catalogo-indice">{links}</ul></nav></div></section><aside class="aviso bien" id="componer-biblioteca"><span class="num">↳</span><div><p class="titulo">Ver las piezas en una historia completa</p><p><a href="informe.html">Recorrer el informe de cuatro capítulos →</a></p><p><a href="plantilla.html">Abrir el cuaderno de una sola página →</a></p></div></aside></article>'''
 nav='<button type="button" data-ir="portada" aria-current="page">Inicio</button>'+''.join(f'<span class="nav-separador" aria-hidden="true">/</span><button type="button" data-ir="{id}">{label}</button>' for id,label,*_ in CHAPTERS)
 body=f'''<a class="salto" href="#portada">Saltar al contenido</a><header class="barra capitulos navegacion-editorial" id="inicio"><a class="firma-editorial" href="#portada" aria-label="Inicio de la biblioteca"><span>Bottifact</span></a><div class="navegacion-scroll" data-capitulos-scroll tabindex="0" role="region" aria-label="Nueve capítulos, desplazables"><nav aria-label="Capítulos">{nav}</nav></div>{appearance()}</header><main class="hoja multipagina edicion biblioteca lectura-guiada marcos-editoriales" data-progreso-pagina data-historial data-enlaces-internos data-lectura lang="es">{intro}{pages}<div class="paginacion" data-paginacion><button type="button" data-nav="prev"><span class="et">Anterior</span><span class="tit"></span></button><button type="button" data-nav="next"><span class="et">Siguiente</span><span class="tit"></span></button></div><footer class="pie pie-editorial"><div><h3>Bottifact</h3><nav aria-label="Enlaces de cierre"><a href="#portada">Volver al inicio</a><a href="informe.html">Leer el informe</a><a href="plantilla.html">El cuaderno completo</a></nav></div><div class="pie-carta"><h3>Para quien sigue el hilo.</h3><p>Una biblioteca para explicar mejor. Dejamos el criterio, el HTML y los límites de cada pieza a la vista.</p><p><em>La siguiente versión comienza con una buena pregunta.</em></p></div><div class="pie-colofon"><span>{len(metadata)} componentes · 15 familias con claro y oscuro</span><span>Artículos / reportes / prototipos</span></div></footer></main><div class="regla regla-guiada" role="slider" tabindex="0" aria-orientation="horizontal" aria-label="Progreso de lectura de esta página" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><div class="ticks"></div><div class="cursor"></div><span class="val">0%</span></div>'''
 modules=['evidencia.js','invitacion.js','mano.js','atencion.js','geografia.js','analitica.js','interacciones.js','multipagina.js','globo.js','flota.js','graficas.js','tablas.js','sonido.js','escritura.js','escena.js','reportes.js','visor.js','pestanas.js','editorial.js','catalogo.js','codigo.js','explorador.js','revision.js']
 (root/'biblioteca.html').write_text(start('Bottifact · Biblioteca editorial')+'<noscript><style>.hoja.biblioteca > .pagina { display:grid !important; grid-template-columns:minmax(var(--gutter),1fr) minmax(0,var(--texto)) minmax(var(--gutter),1fr); margin-bottom:48px; }.barra.capitulos,.biblioteca .paginacion { display:none; }.hoja.lectura-guiada { margin-inline:0; }.hoja.lectura-guiada .indice { position:static; width:auto; max-height:none; overflow:visible; }.regla-guiada { display:none; }</style></noscript>'+body+'<script src="'+three+'"></script>'+''.join(script(m) for m in modules))
 (root/'registro.json').write_text(json.dumps({'version':1,'formato':'bottifact-local','componentes':metadata},ensure_ascii=False,indent=2)+'\n')
