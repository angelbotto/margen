#!/usr/bin/env python3
"""Genera fragmentos autocontenidos desde las fuentes del skill, sin red."""
from identity import mark as margen_mark, favicon as margen_favicon
from pathlib import Path
import json, base64, hashlib, re, html as html_escape
ROOT = Path(__file__).resolve().parents[1]
interface_path=ROOT/'packages/core/components/interface.js'
interface_source=interface_path.read_text()
identity_block='// IDENTITY START\n  const identityMarkup = '+json.dumps(margen_mark())+';\n  const faviconMarkup = '+json.dumps(margen_favicon())+';\n  // IDENTITY END'
interface_path.write_text(re.sub(r'// IDENTITY START.*?// IDENTITY END',lambda _:identity_block,interface_source,flags=re.S))
# Keep review styling identical in standalone and hosted documents.
review_css=(ROOT/'packages/core/styles/review-composer.css').read_text()
css_path=ROOT/'packages/core/styles/artifact.css'
css=css_path.read_text()
blocks = [
    ("SKETCH DIAGRAM", (ROOT/'packages/core/styles/sketch-diagram.css').read_text()),
    ("REVIEW COMPOSER", review_css),
    ("PRESENTATION", (ROOT/'packages/core/styles/presentation.css').read_text()),
    ("TABLE CONTENT", (ROOT/'packages/core/styles/table-content.css').read_text()),
]
for name, content in blocks:
    css = re.sub(r'\n*'+re.escape('/* '+name+' START */')+r'.*?'+re.escape('/* '+name+' END */')+r'\n*', '\n\n', css, flags=re.S)
prefix, marker, suffix = css.partition('/* GENERATED THEMES')
assert marker, 'Missing generated theme boundary'
css = prefix.rstrip() + '\n\n' + '\n\n'.join('/* '+name+' START */\n'+content.rstrip()+'\n/* '+name+' END */' for name, content in blocks) + '\n\n' + marker + suffix
css_path.write_text(css)
if (ROOT/'portal/static').is_dir():(ROOT/'portal/static/review-additions.css').write_text(review_css)
from recipes import assemble as assemble_recipes
assemble_recipes()
from themes import generate as generate_theme_registry
generate_theme_registry()
THREE = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.1/three.min.js'
DATA = {
 'points': [
  {'id':'BOG','label':'Bogotá','lat':4.711,'lon':-74.0721},
  {'id':'MAD','label':'Madrid','lat':40.4168,'lon':-3.7038},
  {'id':'JFK','label':'Nueva York','lat':40.6413,'lon':-73.7781},
  {'id':'HND','label':'Tokio','lat':35.5494,'lon':139.7798},
  {'id':'HKG','label':'Hong Kong','lat':22.308,'lon':113.9185},
  {'id':'SFO','label':'San Francisco','lat':37.6213,'lon':-122.379},
  {'id':'GRU','label':'São Paulo','lat':-23.4356,'lon':-46.4731},
  {'id':'FLN','label':'Florianópolis','lat':-27.672,'lon':-48.548},
 ],
 'arcs': [
  {'id':'bog-mad','from':'BOG','to':'MAD','label':'BOG → MAD','detail':'Bogotá · Madrid'},
  {'id':'mad-jfk','from':'MAD','to':'JFK','label':'MAD → JFK','detail':'Madrid · Nueva York'},
  {'id':'jfk-hnd','from':'JFK','to':'HND','label':'JFK → HND','detail':'Nueva York · Tokio'},
  {'id':'hnd-hkg','from':'HND','to':'HKG','label':'HND → HKG','detail':'Tokio · Hong Kong'},
  {'id':'hkg-sfo','from':'HKG','to':'SFO','label':'HKG → SFO','detail':'Hong Kong · San Francisco'},
  {'id':'sfo-bog','from':'SFO','to':'BOG','label':'SFO → BOG','detail':'San Francisco · Bogotá'},
  {'id':'bog-gru','from':'BOG','to':'GRU','label':'BOG → GRU','detail':'Bogotá · São Paulo'},
  {'id':'gru-fln','from':'GRU','to':'FLN','label':'GRU → FLN','detail':'São Paulo · Florianópolis'},
 ]
}

def script(file): return (script('packages/core/components/interface.js')+script('packages/core/components/audio.js')+script('packages/core/components/controls.js')+script('packages/core/components/editorial-pieces.js') if file=='packages/core/components/reader.js' else '')+'<script>\n' + (ROOT / file).read_text() + '\n</script>\n'

def start(title):
 return '<title>' + title + '</title>\n<meta charset="utf-8">\n<style>\n' + (ROOT / 'packages/core/styles/fonts.css').read_text() + '\n' + (ROOT / 'packages/core/styles/artifact.css').read_text() + '\n</style>\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'

def tools():
 return '<div class="herramientas"><a href="#inicio" class="firma-editorial" aria-label="Inicio de la nota">'+margen_mark()+'</a>'+appearance()+'</div>'

def appearance():
 # Fuente única: copiar el control circular documentado, con IDs/nombres de cabecera.
 text=(ROOT/'docs/components.md').read_text()
 control=re.search(r'<details class="apariencia-menu orbita"[\s\S]*?</details>',text).group(0)
 return control.replace('apariencia-orbita','apariencia-principal')

def globe():
 return '<figure class="ancho"><div id="globo-rutas"></div><figcaption>Rutas ilustrativas para explorar el componente; no representan vuelos realizados. Máscara terrestre COBE · 15.000 muestras · arrastre, teclado y selección.</figcaption></figure>'

def globe_scripts():
 data = json.dumps(DATA, ensure_ascii=False, indent=2).replace('<', '\\u003c')
 return '<script src="' + THREE + '"></script>\n' + script('packages/core/components/globe.js') + '<script>\nwindow.globo = new NotaGlobo(document.getElementById("globo-rutas"), ' + data + ');\n</script>\n'

def cover(title,subtitle,color,n):
 svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="180" height="220" viewBox="0 0 180 220"><rect x="2" y="2" width="176" height="216" rx="2" fill="{color}"/><path d="M11 2v216" stroke="#fef8f2" opacity=".22"/><circle cx="90" cy="85" r="48" fill="none" stroke="#fef8f2" opacity=".45"/><path d="M42 85h96M90 37v96" stroke="#fef8f2" opacity=".4"/><text x="24" y="48" font-family="Georgia,serif" font-size="36" fill="#fef8f2">{n}</text><text x="24" y="162" font-family="Georgia,serif" font-size="24" fill="#fef8f2">{title}</text><text x="24" y="185" font-family="monospace" font-size="10" fill="#fef8f2">{subtitle}</text></svg>'''
 return 'data:image/svg+xml;base64,'+base64.b64encode(svg.encode()).decode()

body='''<a class="salto" href="#contenido">Saltar al contenido</a>
<main class="hoja" id="inicio" data-lectura lang="es">
TOOLS
<header class="cabecera" id="contenido" tabindex="-1">
  <p class="ceja">Cuaderno 01 / forma y evidencia / septiembre 2026</p>
  <h1>La forma también<br>explica.</h1>
  <p class="bajada">Una nota puede ser rigurosa y tener carácter. La lectura necesita una medida; la evidencia, espacio para respirar.</p>
  <p class="secundario mono">Referencia revisada: 16 rutas · 8 artículos</p>
</header>
<nav class="indice" aria-label="Índice del documento"><p class="ceja">En esta nota</p><ol>
  <li><a href="#criterio">Una idea a la vez</a></li><li><a href="#proporcion">El peso de cada cosa</a></li><li><a href="#evidencia">Dejar la evidencia</a></li><li><a href="#rutas">Los lugares se conectan</a></li><li><a href="#guardado">Lo que vale guardar</a></li>
</ol></nav>
<section class="seccion" id="criterio"><p class="ceja">01 / criterio</p><h2>Una idea a la vez.</h2>
<p>Lo primero que debe verse es <span class="marca">la decisión que importa</span>. Los detalles llegan después, con una jerarquía que permite leer sin perder el hilo.</p>
<p>Este sistema conserva la voz editorial de cmrg.me: títulos con serif, texto sereno, datos en mono y una anotación humana cuando aporta otra perspectiva.</p></section>
<div class="con-margen"><p>Un número necesita una fuente y una explicación. Si todavía no se midió, se dice: <span class="dato">pendiente de medir</span>. La precisión también consiste en mostrar los límites.</p><aside class="margen" aria-label="Nota al margen">¿se entiende sin estar en la reunión?</aside></div>
<aside class="aviso ojo" aria-label="Aviso 1: criterio"><span class="num">1</span><div><p class="titulo">El estilo no sustituye la evidencia.</p><p>Las proporciones del siguiente mapa son ilustrativas. Las medidas del análisis se citan con su página y su CSS.</p></div></aside>
<section class="seccion" id="proporcion"><p class="ceja">02 / proporción</p><h2>El peso de cada cosa.</h2><p>El área comunica participación. El valor escrito permite verificarla. Tres grupos bastan para mostrar la relación sin convertir la lectura en una búsqueda.</p></section>
<figure class="ancho"><div class="mapa" role="group" aria-label="Reparto ilustrativo de 100 horas"><div class="bloque destaca"><span class="n">Investigar</span><span class="d">60 h · 60 %</span></div><div class="bloque"><span class="n">Construir</span><span class="d">25 h · 25 %</span></div><div class="bloque"><span class="n">Revisar</span><span class="d">15 h · 15 %</span></div></div><figcaption>01 — Ejemplo de 100 horas. Rejilla 3:2 y 5:3; las áreas incluyen el borde interior de cada celda.</figcaption></figure>
<dl class="datos"><div><dt>Cobertura del análisis</dt><dd>8 páginas + 8 artículos</dd></div><div><dt>Texto original</dt><dd>15,5 px / 1,55</dd></div><div><dt>Medida de lectura aquí</dt><dd>máximo 35 rem</dd></div><div><dt>Figuras y tablas</dt><dd>hasta 62 / 76 rem</dd></div></dl>
<div class="medida"><label for="cobertura">Rutas del sitemap revisadas</label><span class="pct">100 %</span><meter id="cobertura" min="0" max="16" value="16">16 de 16 rutas</meter></div>
<section class="seccion" id="evidencia"><p class="ceja">03 / evidencia</p><h2>Lo importante puede ocupar más.</h2><p>El código, las tablas y los diagramas comparten la rejilla del documento. Una figura puede ser más ancha que el texto y seguir perteneciendo a la misma historia.</p></section>
<figure class="ancho"><div class="codigo"><div class="cab"><span>reporte.js · JavaScript</span><button type="button" data-copiar="codigo-ejemplo" aria-label="Copiar código de reporte.js">Copiar</button><span class="copia-estado" role="status" aria-live="polite"></span></div><pre tabindex="0" aria-label="Código de ejemplo"><code id="codigo-ejemplo"><span class="com">// Un dato sin fuente aún no es evidencia.</span>
<span class="kw">const</span> lectura = {
  fuente: <span class="str">"CSS publicado de cmrg.me"</span>,
  paginas: 16,
  cuerpo: <span class="str">"15.5px / 1.55"</span>,
  observacion: <span class="str">"El tema claro es una adaptación documentada."</span>
};</code></pre></div><figcaption>02 — Encabezado y copia explícita. El contenido se puede seleccionar también si el portapapeles está bloqueado.</figcaption></figure>
<figure class="amplio"><div class="tabla-caja" tabindex="0" role="region" aria-label="Comparación de componentes, desplazable horizontalmente"><table><caption>Decisiones de la adaptación</caption><thead><tr><th scope="col">Componente</th><th scope="col">Referencia observada</th><th scope="col">Decisión para las notas</th><th scope="col">Estado</th></tr></thead><tbody>
<tr><th scope="row">Cuerpo</th><td>15,5 px · interlineado 1,55</td><td>16 px · interlineado 1,65 para informes</td><td><span class="pildora p-si">✓ Aplicado</span></td></tr>
<tr><th scope="row">Tipografía</th><td>Editorial New 400</td><td>Instrument Serif 400, con comparación visual</td><td><span class="pildora p-medio">≈ Adaptado</span></td></tr>
<tr><th scope="row">Desvanecido</th><td>Máscaras y blur de lectura</td><td>Solo extracto decorativo, texto íntegro desplegable</td><td><span class="pildora p-si">✓ Accesible</span></td></tr>
<tr><th scope="row">Imágenes externas</th><td>Recursos de distintos orígenes</td><td>Incrustar como data: URI</td><td><span class="pildora p-no">× No permitido</span></td></tr>
</tbody></table></div><figcaption>03 — En pantallas pequeñas la tabla conserva todos sus datos y ofrece desplazamiento dentro de su región.</figcaption></figure>
<figure class="ancho"><div class="diagrama-caja" tabindex="0" role="region" aria-label="Diagrama de observación, explicación y verificación, desplazable"><svg class="diagrama" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 180" role="img" aria-labelledby="flujo-titulo flujo-desc"><title id="flujo-titulo">De observación a informe</title><desc id="flujo-desc">Observar el dato, explicar la decisión y verificar el resultado, en ese orden.</desc><g fill="none" stroke="currentColor"><rect x="15" y="42" width="200" height="94" rx="4"/><rect x="260" y="42" width="200" height="94" rx="4"/><rect x="505" y="42" width="200" height="94" rx="4"/><path d="M215 89h40m-9-7 9 7-9 7M460 89h40m-9-7 9 7-9 7"/></g><g font-size="17" text-anchor="middle"><text x="115" y="83">01 / observar</text><text x="360" y="83">02 / explicar</text><text x="605" y="83">03 / verificar</text><text x="115" y="109" font-size="12">dato + fuente</text><text x="360" y="109" font-size="12">criterio + límite</text><text x="605" y="109" font-size="12">resultado visible</text></g></svg></div><figcaption>04 — Observar el dato y su fuente → explicar el criterio y su límite → verificar el resultado. El gráfico se puede desplazar en pantallas pequeñas.</figcaption></figure>
<aside class="aviso bien" aria-label="Aviso 2: accesibilidad"><span class="num">2</span><div><p class="titulo">La jerarquía no depende solo del color.</p><p>Los estados tienen palabra y símbolo. El foco es visible, y el texto secundario conserva contraste suficiente.</p></div></aside>
<aside class="aviso mal" aria-label="Aviso 3: límite"><span class="num">3</span><div><p class="titulo">Lo que falta debe poder verse.</p><p>Un error de carga del globo muestra un mensaje y conserva la lista de rutas. Ningún dato vive solamente en el canvas.</p></div></aside>
<section class="seccion" id="rutas"><p class="ceja">04 / lugares</p><h2>Los lugares se conectan.</h2><p>La Tierra es una superficie de puntos, con rutas que se elevan sobre ella. La lista permite elegir cada conexión y entenderla sin depender del movimiento.</p></section>
GLOBE
<p class="nota">el mapa ayuda a orientarse; la lista cuenta qué hay</p>
<section class="seccion" id="guardado"><p class="ceja">05 / guardado</p><h2>Lo que vale guardar.</h2><p>Un objeto, una nota breve y una razón para volver. Las tarjetas funcionan cuando cada una guarda algo distinto.</p></section>
<div class="kept ancho">
<article><img class="portada" src="COVER1" alt="" width="180" height="220"><h3>La decisión</h3><p>Qué se eligió y por qué. Un registro que permita volver a pensar, con el contexto a mano.</p><p class="meta">NOTA / 01 · ejemplo editorial</p></article>
<article><img class="portada" src="COVER2" alt="" width="180" height="220"><h3>La evidencia</h3><p>Medidas, fuentes y límites. Lo suficiente para distinguir lo observado de lo supuesto.</p><p class="meta">REGISTRO / 02 · ejemplo editorial</p></article>
<article><img class="portada" src="COVER3" alt="" width="180" height="220"><h3>La siguiente pregunta</h3><p>Lo que todavía necesita respuesta. Una invitación concreta a seguir, sin fabricar certeza.</p><p class="meta">PENDIENTE / 03 · ejemplo editorial</p></article>
</div>
<div class="extracto"><p class="desvanece" aria-hidden="true">Una nota se termina cuando alguien puede tomar una decisión con ella. La forma prepara el terreno; la evidencia sostiene lo que decimos.</p><details><summary>Leer la nota completa</summary><p>Una nota se termina cuando alguien puede tomar una decisión con ella. La forma prepara el terreno; la evidencia sostiene lo que decimos. Si la pieza necesita una segunda lectura para entender qué propone, todavía queda trabajo editorial.</p></details></div>
<aside class="aviso cita"><span class="num" aria-hidden="true">↳</span><div><blockquote>Dejar una buena nota es dejarle contexto a quien llega después.</blockquote><p class="secundario">Principio de esta plantilla</p></div></aside>
<footer class="pie"><p>Margen · Muestra de todos los componentes. Inspirada en <a href="https://www.cmrg.me">cmrg.me</a>; el tema claro, los ajustes de acceso y Dark Sea están documentados en el informe.</p><button type="button" data-sonido aria-pressed="false">Sonido apagado</button></footer>
</main>
<div class="regla" role="slider" tabindex="0" aria-orientation="vertical" aria-label="Progreso de lectura" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><div class="ticks"></div><div class="cursor"></div><span class="val">0%</span></div>
'''
body=body.replace('TOOLS',tools()).replace('GLOBE',globe())
for i,(title,subtitle,color) in enumerate([('La decisión','CUADERNO DE CRITERIO','#755a42'),('La evidencia','REGISTRO DE MEDIDAS','#516344'),('Lo que sigue','PREGUNTAS ABIERTAS','#56627f')],1):
 body=body.replace('COVER'+str(i),cover(title,subtitle,color,str(i).zfill(2)))
def recipes():
 text=(ROOT/'docs/components.md').read_text()
 return re.findall(r'<!-- nota:ejemplo ([\w-]+) -->\s*```html\n(.*?)\n```',text,re.S)

catalog='''<section class="seccion" id="libreria"><p class="ceja">06 / componentes para copiar</p>
<h2>La evidencia tiene muchas formas.</h2><p>Gráficas, tablas y experiencias opcionales. Cada ejemplo conserva sus datos, su criterio y su límite en docs/components.md.</p>NAV_COMPONENTES</section>'''
labels={'globo-flota':'Globo operativo de Colombia','ficha-entrega':'Ficha de entrega e hitos','cola-novedades':'Cola de despacho y novedades','tabla-densa':'Tabla densa','terminal':'Terminal','manuscrita':'Nota manuscrita','barras':'Barras','lineas':'Líneas','temporal':'Serie temporal','dispersion':'Dispersión','distribucion':'Distribución','calor':'Mapa de calor','comparacion':'Comparación','totales':'Totales y ordenación','sparkline':'Tabla con serie','sonido':'Sonido optativo','escritura':'Escritura por trazos','xyz':'Three.js · XYZ','etapas':'Three.js · etapas'}
labels.update({'apariencia':'Apariencia y lectura cómoda','decision':'Ficha de decisión','cronologia':'Cronología anotada','articulo':'Ficha de artículo','referencias':'Referencias con regreso','glosario':'Glosario editorial','metodologia':'Metodología desplegable','antes-despues':'Antes y después','cascada':'Cascada de cantidades','multiples':'Pequeños múltiples','conciliacion':'Conciliación de registros','escenario':'Calculadora de escenarios','recorrido':'Globo narrado','visor':'Visor de prototipos'})
labels.update({'pestanas':'Pestañas de una pieza','hallazgo':'Ficha de hallazgo'})
from editorial_metadata import ETIQUETAS
labels.update(ETIQUETAS)
new_keys={'apariencia','decision','cronologia','articulo','referencias','glosario','metodologia','antes-despues','cascada','multiples','conciliacion','escenario','recorrido','visor'}
labels.update({'relato-visual': 'Relato visual por pasos', 'sankey': 'Flujos Sankey', 'cohortes': 'Cohortes de recurrencia', 'sensibilidad': 'Sensibilidad de escenarios', 'gantt': 'Gantt editorial', 'embudo': 'Embudo explicado', 'incertidumbre': 'Rangos de incertidumbre', 'evidencia-ampliable': 'Evidencia ampliable'})
keywords={'apariencia':'tema lectura','decision':'reporte informe','cronologia':'historia fechas','articulo':'blog autor fecha','referencias':'blog fuentes citas','glosario':'blog definiciones','metodologia':'blog informe supuestos','antes-despues':'blog cambios','cascada':'reporte balance','multiples':'graficas reporte sedes','conciliacion':'tabla reporte diferencias','escenario':'calculadora reporte supuestos','recorrido':'globo three geografia historia','visor':'prototipo estados responsive'}
from recipes import metadata as recipe_metadata
labels.update({item['legacyId']: item['title'] for item in recipe_metadata()})
links=[]
for key,html in recipes():
 if key in {'multipagina','informe'}:continue
 first=re.match(r'<[\w-]+\b[^>]*>',html)
 existing=re.search(r'\bid="([^"]+)"',first.group(0))
 anchor=existing.group(1) if existing else 'pieza-'+key
 if not existing:html=html[:first.end()-1]+' id="'+anchor+'"'+html[first.end()-1:]
 links.append('<li data-claves="'+keywords.get(key,'')+'"><a href="#'+anchor+'">'+labels[key]+'</a></li>')
 if key=='apariencia':catalog += '<section class="seccion" id="segunda-tanda"><h2>Historias que se pueden explorar.</h2><p>Más piezas para reportes, artículos y prototipos. Empieza por la apariencia o prueba un escenario y el visor.</p></section>'
 catalog += '\n' + html + '\n'
 # El código escapado conserva exactamente la receta; los IDs aquí son texto, no elementos.
 code_id='receta-fuente-'+key
 catalog += '<details class="receta-copia ancho"><summary>HTML y dependencias · '+labels[key]+'</summary><p class="procedencia">Requiere packages/core/styles/fonts.css, packages/core/styles/artifact.css e packages/core/components/reader.js. '+('Añade packages/core/components/reports.js; para el recorrido también packages/core/components/globe.js y Three 0.160.1.' if key in {'cascada','multiples','conciliacion','escenario','recorrido'} else 'Añade packages/core/components/prototype.js.' if key=='visor' else 'Consulta los módulos y límites de esta receta en docs/components.md.')+'</p><div class="codigo"><div class="cab"><span>'+labels[key]+'</span><button type="button" data-copiar="'+code_id+'" aria-label="Copiar HTML de '+labels[key]+'">Copiar HTML</button><span role="status" class="copia-estado"></span></div><pre tabindex="0" aria-label="HTML de '+labels[key]+', desplazable"><code id="'+code_id+'">'+html_escape.escape(html)+'</code></pre></div></details>'
catalog=catalog.replace('NAV_COMPONENTES','<div data-buscador-recetas><div class="buscador-recetas"><label for="buscar-receta">Encuentra una pieza</label><input id="buscar-receta" type="search" placeholder="Tabla, globo, artículo, prototipo…" aria-describedby="buscar-estado"><p id="buscar-estado" role="status"></p></div><nav aria-label="Ejemplos de componentes"><ul class="catalogo-indice">'+''.join(links)+'</ul></nav></div>')
body=body.replace('<footer class="pie">',catalog+'<footer class="pie">')
body=body.replace('<li><a href="#guardado">Lo que vale guardar</a></li>','<li><a href="#guardado">Lo que vale guardar</a></li><li><a href="#libreria">Librería de evidencia</a></li><li><a href="#segunda-tanda">Artículos y prototipos</a></li>')
body=re.sub(r'(<p class="bajada">.*?</p>)',r'\1<p class="enlace-edicion"><a href="examples/generated/report.html">Explorar el informe con capítulos →</a> · <a href="examples/generated/library.html">Abrir la biblioteca completa →</a></p>',body,count=1)
(ROOT/'examples/generated/template.html').write_text(start('Margen — la forma también explica')+body+script('packages/core/components/reader.js')+globe_scripts()+script('packages/core/components/invitation.js')+script('packages/core/components/handwriting.js')+script('packages/core/components/attention-map.js')+script('packages/core/components/geography.js')+script('packages/core/components/fleet.js')+script('packages/core/components/analytics.js')+script('packages/core/components/charts.js')+script('packages/core/components/tables.js')+script('packages/core/components/sound.js')+script('packages/core/components/writing.js')+script('packages/core/components/scene.js')+script('packages/core/components/reports.js')+script('packages/core/components/prototype.js')+script('packages/core/components/tabs.js')+script('packages/core/components/catalog.js')+script('packages/core/components/editorial.js')+script('packages/core/components/code.js')+script('packages/core/components/table-model.js')+script('packages/core/components/data-explorer.js')+script('packages/core/components/evidence.js')+script('packages/core/components/review.js'))
globe_body='<main class="hoja" id="inicio" lang="es">'+tools()+'''<header class="cabecera"><p class="ceja">Nota / geografía</p><h1>Planes, puntos<br>y lugares.</h1><p class="bajada">Un globo de puntos para explorar conexiones. Elige una ruta, gira la Tierra o pausa la vista.</p></header>'''+globe()+'''<footer class="pie">Ejemplo reutilizable · Three.js desde cdnjs · máscara geográfica incrustada · ambos temas y movimiento reducido.</footer></main>'''
(ROOT/'examples/generated/globe.html').write_text(start('Margen — globo de rutas')+globe_body+script('packages/core/components/reader.js')+globe_scripts())
(ROOT/'examples/generated/chapters.html').write_text(start('Margen — capítulos')+dict(recipes())['multipagina']+script('packages/core/components/reader.js')+script('packages/core/components/chapters.js'))
informe=dict(recipes())['informe'].replace('<div class="edicion-acciones"><span>Edición 02</span></div>','<div class="edicion-acciones"><span>Edición 02</span>'+appearance()+'</div>')
informe=re.sub(r'<figure class="pieza amplio" id="visor-ejemplo"[\s\S]*?</figure>',lambda _:dict(recipes())['visor'],informe,count=1)
from contract_artifact import revision, build as build_estandar
(ROOT/'examples/generated/report.html').write_text(start('Margen · Una revisión antes de confirmar')+informe+revision()+''.join(script(file) for file in ['packages/core/components/reader.js','packages/core/components/chapters.js','packages/core/components/charts.js','packages/core/components/reports.js','packages/core/components/prototype.js','packages/core/components/tabs.js','packages/core/components/review.js']))
from library import build as build_biblioteca
build_biblioteca(ROOT,start,script,appearance,recipes,labels,THREE)
from fixture_regression import build
build(start,script)
print('Generados examples/generated/library.html, packages/core/registry/registry.json, examples/generated/template.html, examples/generated/globe.html, examples/generated/chapters.html, examples/generated/report.html y examples/generated/checks.html')

config=json.loads((ROOT/'examples/content/standard-chapters.json').read_text())
pages=[{**p,'html':(ROOT/'examples/content'/p['contenido']).read_text()} for p in config['paginas']]
(ROOT/'examples/generated/standard.html').write_text(build_estandar(config['titulo'],[pages[0]],config['descripcion']))
(ROOT/'examples/generated/standard-chapters.html').write_text(build_estandar(config['titulo'],pages,config['descripcion']))
print('Generados examples/generated/standard.html y examples/generated/standard-chapters.html con contrato verificable')
piece_ids=['actividad-editorial','codigo-lineas','enlaces-icono','avisos-animados','trayectoria','galeria']
(ROOT/'examples/content/priorities-pieces.html').write_text(''.join('<section id="ver-'+key+'"><h2>'+labels[key]+'</h2></section>\n'+dict(recipes())[key]+'\n' for key in piece_ids))
config=json.loads((ROOT/'examples/content/priorities.json').read_text())
pages=[{**p,'html':(ROOT/'examples/content'/p['contenido']).read_text()} for p in config['paginas']]
(ROOT/'examples/generated/priorities.html').write_text(build_estandar(config['titulo'],pages,config['descripcion']))
print('Generado examples/generated/priorities.html: propuesta y nuevas piezas editoriales')
from examples_themes import generate as build_temas
build_temas()
from guide import generate as build_guia
build_guia()

# La muestra nueva se regenera desde las mismas recetas del registro.
from guide import prose,code_box
new_ids=['relato-visual','sankey','cohortes','sensibilidad','gantt','embudo','incertidumbre','evidencia-ampliable']
new_registry={r['id']:r for r in json.loads((ROOT/'packages/core/registry/registry.json').read_text())['componentes']}
new_body='<section id="ocho-piezas"><p class="ceja">Ocho componentes · datos ilustrativos</p><h2>Una pregunta, una forma de verla.</h2><p>Relatos, escenarios y evidencia que se pueden recorrer. Cada vista conserva sus datos y explica su alcance.</p></section>'
for key in new_ids:
 r=new_registry[key]
 new_body+='<section id="ver-'+key+'"><h2>'+r['nombre']+'</h2></section>'+r['html']+'<div class="receta-guia">'+prose(r['criterio_y_limites'])+'</div>'+code_box(r['html'],'nuevo-'+key,r['nombre'])
(ROOT/'examples/content/evidence-content.html').write_text(new_body)
(ROOT/'examples/generated/evidence.html').write_text(build_estandar('Margen · Ocho formas de explicar',[{'id':'evidencia','titulo':'Ocho formas de explicar','html':(ROOT/'examples/content/evidence-content.html').read_text()}],'Lectura guiada, escenarios y revisión visual. Datos ilustrativos.',theme='dark'))
print('Generado examples/generated/evidence.html: ocho piezas nuevas')
from example_collaborative import generate as build_colaborativo
build_colaborativo()
print('Generados examples/generated/collaborative.html y temas Linear Light / Dark')

from example_appearance import generate as build_apariencia
build_apariencia()
print("Generado examples/generated/themes.html: 15 familias y 30 versiones")

from example_executive import generate as build_ejecutivo
build_ejecutivo()
from example_brands import generate as build_marcas
build_marcas()
from example_system import generate as build_sistema
build_sistema()
print("Generado examples/generated/system.html: stack y skill de Margen")

from example_workbench import generate as build_workbench
build_workbench()

# Congela la identidad de demos ya publicados, aunque cambie su marca visible.
for filename,identity in json.loads((ROOT/'packages/core/registry/compatibility.json').read_text())['documentos_publicados'].items():
 path=ROOT/filename
 if not path.is_file():continue
 content=path.read_text()
 if 'documento_id' in identity:
  content=re.sub(r'(<meta name="nota-documento" content=")[^"]+',lambda m:m[1]+identity['documento_id'],content,count=1)
 else:
  marker='<meta name="nota-titulo-anterior" content="'+html_escape.escape(identity['titulo'],quote=True)+'">'
  content=content.replace('</title>','</title>\n'+marker,1)
 path.write_text(content)

# Recursos compartidos del portal; no se incluyen credenciales ni datos de instancia.
if (ROOT/"portal/static").is_dir():
 for source,target in [("packages/core/components/interface.js","interface.js"),("packages/core/components/review.js","review.js"),("packages/core/components/reader-controls.js","reader-controls.js"),("packages/core/styles/fonts.css","fonts.css")]:
  (ROOT/"portal/static"/target).write_bytes((ROOT/source).read_bytes())

 # External copy keeps the account UI compatible with its strict style-src policy.
 interface = (ROOT/'packages/core/components/interface.js').read_text()
 interface_css = re.search(r'style\.textContent\s*=\s*`(.*?)`', interface, re.S).group(1)
 (ROOT/'portal/static/interface.css').write_text('/* Generated from core/components/interface.js. */\n'+interface_css+'\n')

if (ROOT/'portal/static').is_dir():
 for asset in (ROOT/'packages/core/assets/identity').glob('*.svg'):
  (ROOT/'portal/static'/asset.name).write_bytes(asset.read_bytes())

# Resolve navigation from the generated examples directory without touching runtime code.
for page in (ROOT / 'examples/generated').glob('*.html'):
 content=page.read_text()
 if 'rel="icon"' not in content:page.write_text(content.replace('</title>','</title>'+margen_favicon(),1))
 text = page.read_text()
 text = re.sub(r'(href=")examples/generated/', r'\1', text)
 text = re.sub(r'(href=")docs/', r'\1../../docs/', text)
 page.write_text(text)

from example_formats import generate as generate_project_formats
generate_project_formats()
