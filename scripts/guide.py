"""Guía completa derivada del registro; conserva un único montaje de controles comunes."""
import re,json,html
from pathlib import Path
from contract_artifact import build,recipe,ROOT
from library import CHAPTERS
from themes import FAMILIES

def inline(text):
 text=html.escape(text)
 text=re.sub(r'`([^`]+)`',r'<code>\1</code>',text)
 text=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',text)
 return re.sub(r'\[([^]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',text)

def prose(text):
 """Markdown acotado de estas guías: párrafos, listas, tablas y código; sin paquetes externos."""
 result=[]
 for block in text.strip().split('\n\n'):
  lines=block.splitlines()
  if not lines:continue
  if lines[0].startswith('|'):
   rows=[[inline(c.strip()) for c in line.strip('|').split('|')] for line in lines if not re.match(r'^\|[\s:|-]+\|$',line)]
   result.append('<div class="tabla-caja" tabindex="0" role="region" aria-label="Criterios de composición, tabla desplazable"><table><caption>Comparar opciones</caption><thead><tr>'+''.join('<th scope="col">'+c+'</th>' for c in rows[0])+'</tr></thead><tbody>'+''.join('<tr>'+''.join(('<th scope="row">'+c+'</th>') if i==0 else '<td>'+c+'</td>' for i,c in enumerate(row))+'</tr>' for row in rows[1:])+'</tbody></table></div>')
  elif lines[0].startswith('```'):
   code='\n'.join(lines[1:-1]);result.append('<div class="codigo"><pre tabindex="0" aria-label="Comandos de ejemplo, desplazables"><code>'+html.escape(code)+'</code></pre></div>')
  elif re.match(r'^(?:- |\d+\. )',lines[0]):
   items=re.split(r'\n(?=- |\d+\. )',block);tag='ul' if lines[0].startswith('-') else 'ol'
   result.append('<'+tag+'>'+''.join('<li>'+inline(re.sub(r'^(?:- |\d+\. )','',item)).replace('\n',' ')+'</li>' for item in items)+'</'+tag+'>')
  else:result.append('<p>'+inline(block).replace('\n',' ')+'</p>')
 return ''.join(result)

def code_box(source,key,title):
 return f'<details class="receta-copia ancho"><summary>HTML completo · {html.escape(title)}</summary><div class="codigo codigo-editorial"><div class="cab"><span>{html.escape(title)}</span><button type="button" class="boton-icono-copia" data-copiar="guia-fuente-{key}" aria-label="Copiar HTML de {html.escape(title)}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M8 8h12v13H8zM16 8V3H4v13h4"/></svg></button><span class="copia-estado" role="status"></span></div><pre tabindex="0" aria-label="HTML de {html.escape(title)}, desplazable"><code id="guia-fuente-{key}" data-lenguaje="html">{html.escape(source)}</code></pre></div></details>'

def generate():
 registry=json.loads((ROOT/'packages/core/registry/registry.json').read_text())['componentes'];by_id={r['id']:r for r in registry}
 cases=json.loads((ROOT/'packages/core/registry/use-cases.json').read_text())['casos']
 sections={};parts=re.split(r'^## (.+)$',(ROOT/'docs/composition.md').read_text(),flags=re.M)
 for i in range(1,len(parts),2):sections[parts[i]]=parts[i+1]
 def section(title,id):return '<section class="seccion" id="'+id+'"><h2>'+title+'</h2></section>'+prose(sections[title]).replace('class="tabla-caja"','class="tabla-caja ancho"')
 links=''.join('<li data-category="'+r['capitulo']+'" data-intents="'+'|'.join(c['id'] for c in cases if r['id'] in c['componentes'])+'" data-claves="'+html.escape(r['criterio_y_limites']+' '+r['id'],quote=True)+'"><a href="#guia-'+r['id']+'"><strong>'+html.escape(r['nombre'])+'</strong><small>'+r['capitulo']+' · '+r['id']+'</small></a></li>' for r in registry)
 filters='<div class="relationship-tools"><label>Buscar componente o necesidad<input type="search" placeholder="evidencia, sesión, comparar, mapa…"></label><label>Familia<select data-catalog-category><option value="">Todas las familias</option>'+''.join('<option>'+html.escape(c)+'</option>' for c in sorted(set(r['capitulo'] for r in registry)))+'</select></label><label>Quiero…<select data-catalog-intent><option value="">Todos los recorridos</option>'+''.join('<option value="'+c['id']+'">'+html.escape(c['nombre'])+'</option>' for c in cases)+'</select></label></div><button type="button" data-catalog-reset>Limpiar búsqueda y filtros</button><p role="status"></p>'
 routes=''.join('<article class="card-editorial"><p class="ceja">'+c['id']+'</p><h3>'+c['nombre']+'</h3><p>'+c['pregunta']+'</p><p>'+', '.join('<a href="#guia-'+k+'">'+by_id[k]['nombre']+'</a>' for k in c['componentes'])+'</p></article>' for c in cases)
 intro='''<section class="seccion" id="guia-empezar"><p class="ceja">Manual de uso / edición 04</p><h2>Una biblioteca para pensar con ella.</h2><p>Elige una pregunta. Construye el argumento. Dale a cada pieza una tarea.</p><p>Esta guía reúne <strong>{component_count} componentes, {family_count} familias con claro y oscuro y {case_count} recorridos de composición</strong>. Cada receta se puede ver y copiar; la base siempre incluye apariencia, sonido optativo, comentarios y ayudas de lectura.</p><p>Los ejemplos son ilustrativos: ninguna cifra de las muestras describe resultados reales de Liftit o Tikin.</p></section><nav class="biblioteca-rutas ancho" aria-label="Entradas a la guía"><a href="#componer"><strong>01 / Encontrar la forma</strong><small>Del objetivo a la combinación de componentes.</small></a><a href="#voz"><strong>02 / Escribir entre líneas</strong><small>Notas izquierda y derecha, subrayado, audio y ayudas.</small></a><a href="#ambientes"><strong>03 / Probar los temas</strong><small>Familias, modo claro/oscuro/sistema y documentos completos.</small></a><a href="#entrega"><strong>04 / Llevarla a tu agente</strong><small>Generar, validar e instalar en Hermes, Claude o Codex.</small></a></nav>'''
 intro=intro.replace('{component_count}',str(len(registry))).replace('{case_count}',str(len(cases))).replace('{family_count}',str(len(FAMILIES)))
 intro+='<section class="ancho" id="guia-inventario" data-buscador-recetas><h2>Todas las piezas, a mano.</h2><p>Busca por necesidad, combina familia y recorrido, y abre la muestra real con sus límites y código copiable. Las recetas de sesión y relaciones son componentes locales, no integraciones nuevas del portal.</p>'+filters+'<nav aria-label="Todos los componentes"><ul class="catalogo-indice">'+links+'</ul></nav></section>'
 compose=section('Start with the reading task','guia-pregunta')+section('Useful compositions','guia-recorridos')+'<div class="cards-editoriales ancho">'+routes+'</div>'+section('Rhythm and hierarchy','guia-escala')+section('Data and interaction','guia-logistica')
 voice=section('Marginal voice','guia-voces')
 # IDs separados de la receta del catálogo: la muestra de composición es un documento distinto.
 sample=recipe('apuntes')
 for id in ['apuntes-ejemplo','apunte-izquierdo','apunte-derecho']:sample=sample.replace(id,'guia-demo-'+id)
 sample=sample.replace('Una decisión necesita contexto.','El denominador cambia la lectura.').replace('La evidencia sirve cuando nos ayuda a <span data-subrayar="referencia">decidir mejor</span>. Un reporte puede dejar una pregunta breve al margen sin interrumpir el argumento.','Antes de afirmar que el servicio mejoró, define si estás midiendo <span data-subrayar="referencia">entregas completadas</span> o todos los intentos. La cifra necesita ese contexto.').replace('menos ruido, más criterio.','¿incluye devoluciones?').replace('Explicar también es editar.','Una propuesta todavía es una pregunta.').replace('Antes de agregar otra gráfica, prueba a <span data-subrayar="referencia">quitar lo que sobra</span>. La anotación acompaña al párrafo; el subrayado se dibuja cuando aparece.','Un prototipo permite <span data-subrayar="referencia">observar una tarea</span>. Hasta hacer la prueba no sabemos si la interfaz ayuda a completarla.').replace('¿se entiende sin explicarlo?','primero, ver a alguien usarlo.')
 voice+=sample+code_box(sample,'composicion-notas','Composición de notas izquierda y derecha')+section('Reader controls','guia-ayudas')
 themes=section('Visual voice','guia-temas')+'<p><a href="examples/generated/brands.html">Liftit, Tikin y Catabum: logos, paletas y artefactos de ejemplo</a>.</p>'+ '<p><a href="examples/generated/themes.html">Explorar las {family_count} familias y los modos Claro, Oscuro y Sistema</a>.</p>'+'''<nav class="biblioteca-rutas ancho" aria-label="Ejemplos de temas"><a href="examples/generated/liftit.html"><span class="paleta-mini liftit" aria-hidden="true"><i></i><b></b></span><strong>Liftit / operación</strong><small>Rutas, datos y capacidad. Tokens del frontend LMS y logo del repositorio.</small></a><a href="examples/generated/blueprint.html"><span class="paleta-mini blueprint" aria-hidden="true"><i></i><b></b></span><strong>Blueprint / sistema</strong><small>Plano azul, cuadrícula blanca y explicación de una confirmación.</small></a><a href="examples/generated/hacker.html"><span class="paleta-mini hacker" aria-hidden="true"><i></i><b></b></span><strong>Hacker / runbook</strong><small>Contrato, código destacado, terminal y recuperación.</small></a></nav><aside class="aviso"><span class="num">i</span><div><p class="titulo">Prueba la guía entera en cada tema.</p><p>Abre la llave sol/luna de la cabecera. Las paletas se aplican también a tablas, gráficas, mapas, notas y comentarios. El sonido está habilitado y espera el primer clic real. Puedes apagarlo en la pestaña Sonido; esa elección se recuerda. En Letras prueba Libro, Revista y Bitácora.</p></div></aside>'''
 themes=themes.replace('{family_count}',str(len(FAMILIES)))
 pages=[{'id':id,'titulo':title,'html':body} for id,title,body in [('manual','Guía de la biblioteca',intro),('componer','Componer',compose),('voz','Voz y lectura',voice),('ambientes','Temas',themes)]]
 for chapter,label,_,desc,keys in CHAPTERS:
  body='<p class="bajada">'+desc+'</p>'
  for key in keys:
   r=by_id[key];body+='<section id="guia-'+key+'" data-guia-componente="'+key+'"><p class="ceja">'+chapter+' / '+key+'</p><h2>'+html.escape(r['nombre'])+'</h2></section>'
   if key in ['apariencia','revision']:body+='<p>Este componente ya está activo en la base: '+('abre la llave sol/luna de la cabecera.' if key=='apariencia' else 'usa la burbuja flotante para dejar y copiar un comentario.')+'</p>'
   else:body+=r['html']
   body+='<div class="receta-guia">'+prose(r['criterio_y_limites'])+'<p class="procedencia">Dependencias: '+html.escape(', '.join(r['dependencias']))+'</p></div>'+code_box(r['html'],key,r['nombre'])
  pages.append({'id':'piezas-'+chapter,'titulo':label,'html':body})
 install=(ROOT/'docs/installation.md').read_text();installparts=re.split(r'^## (.+)$',install,flags=re.M)
 delivery=section('Finish','guia-generar')+'<p><a href="examples/generated/system.html">Revisión del stack, el skill y la evolución de Margen</a>.</p>'
 for i in range(1,len(installparts),2):delivery+='<section id="guia-instalar-'+str(i)+'"><h2>'+html.escape(installparts[i])+'</h2>'+prose(installparts[i+1])+'</section>'
 pages.append({'id':'entrega','titulo':'Usar el skill','html':delivery})
 (ROOT/'examples/generated/guide.html').write_text(build('Margen · Guía de uso y componentes',pages,'Cómo construir documentos que se leen, se exploran y se revisan.'))
 (ROOT/'tests/evidence/guide-coverage.json').write_text(json.dumps({'paginas':[p['id'] for p in pages],'componentes':[r['id'] for r in registry],'casos':cases},ensure_ascii=False,indent=2)+'\n')
 print('Generada examples/generated/guide.html: '+str(len(pages))+' páginas y '+str(len(registry))+' recetas completas')

if __name__=='__main__':generate()
