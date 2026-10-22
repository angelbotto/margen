#!/usr/bin/env python3
"""Prepare a complete component atlas as sources for the canonical artifact CLI.

No publishing and no new rendering stack. The registry is the coverage authority;
the standard contract supplies navigation, comments and reader preferences.
"""
from __future__ import annotations

import argparse
import base64
from collections import OrderedDict
from html import escape
import json
import mimetypes
from pathlib import Path
import re

from contract_artifact import build

ROOT = Path(__file__).resolve().parents[1]
DOCUMENT_ID = "margen-atlas-componentes-20261022"
CHAPTERS = OrderedDict([
    ("publicaciones", ("Publicaciones", "La entrada, la firma y lo que sigue.")),
    ("lectura", ("Lectura", "Texto, contexto y anotaciones que acompañan.")),
    ("reportes", ("Decisiones", "Evidencia, incertidumbre y siguientes pasos.")),
    ("graficas", ("Gráficas", "Una forma distinta de interrogar cada dato.")),
    ("tablas", ("Tablas", "Encontrar un registro sin perder el conjunto.")),
    ("prototipos", ("Prototipos", "Recorrer una propuesta antes de construirla.")),
    ("expresion", ("Espacio y gesto", "Mapas, movimiento y sonido optativo.")),
    ("configuracion", ("Código y edición", "El documento también se puede inspeccionar.")),
])
TRIALS = {
    "galeria": "Desplaza las imágenes con el panel táctil o el teclado. Haz scroll hasta cruzar el índice: ni los enlaces ni sus textos deben quedar encima de las imágenes.",
    "atencion": "Compara las áreas y los valores. Cambia de tema y reduce el ancho: cada celda debe conservar su nombre o una forma accesible de consultarlo.",
    "gantt": "Recorre los hitos y contrasta sus fechas con las barras. En móvil, usa el desplazamiento del componente sin desplazar toda la página.",
    "codigo-lineas": "Copia el código y revisa los rangos destacados. Los números quedan fuera del texto copiado; cambiar el tema conserva la jerarquía de colores.",
    "codigo-poliglota": "Compara cómo se distinguen cadenas, comentarios, números y palabras clave en cada lenguaje. Prueba también el modo claro.",
    "archivo": "Busca una palabra, elige un tema y limpia los filtros. Comprueba el estado sin resultados.",
    "explorador": "Ordena, filtra y cambia de vista. Revisa un registro y vuelve al conjunto; el valor no debe desaparecer por el cambio de ancho.",
    "escenario": "Modifica los supuestos y comprueba qué resultados cambian. Las cifras son una simulación, no una previsión.",
    "pestanas": "Recorre las pestañas con las flechas del teclado. Solo el panel seleccionado debe quedar visible y accesible.",
    "metodologia": "Abre y cierra el detalle usando Enter. La explicación debe mantener su separación y legibilidad al pasar por el índice.",
    "pie-editorial": "Recorre los enlaces con Tab. La identidad y las redes pertenecen al autor de cada documento, mientras la atribución de Margen es independiente.",
    "encabezado-fecha": "La fecha viene de los metadatos del documento. Reduce el ancho: el día, el mes y el año deben mantenerse juntos.",
    "reacciones": "Selecciona una reacción y vuelve a pulsarla. El estado es local; la nota explica si se conserva en el navegador o solo mientras la página siga abierta.",
    "columnas": "Compara los grupos con la tabla, aísla una serie desde su leyenda y exporta los datos. Las alturas deben conservar la misma escala.",
    "cambio": "Compara el antes y el después. Recorre cada punto con el teclado para consultar el valor completo.",
    "meta": "Distingue el valor observado de la meta. Consulta los datos con el teclado y comprueba que la escala incluye el cero y los valores negativos.",
    "x-post": "La tarjeta conserva texto, autor, fecha y medios sin cargar scripts de X. Esta publicación es una demostración inventada y está identificada como tal.",
    "youtube": "Pulsa Cargar video para abrir el reproductor. Si el proveedor no permite reproducirlo aquí, usa el enlace al video original.",
    "instagram": "Carga la publicación de forma explícita. Instagram puede pedir acceso o limitar el contenido; el enlace original sigue disponible.",
    "sonido": "Activa el sonido solo si quieres probarlo y usa el control de volumen. El texto conserva toda la información con el sonido apagado.",
    "evidencia-ampliable": "Abre la evidencia, recórrela con teclado y ciérrala con Escape. El foco debe volver al control que la abrió.",
}


def portable(source: str) -> str:
    """Embed repository images and route example links inside this atlas."""
    def asset(match):
        value = match.group(2)
        if value.startswith("data:"):
            return match.group(0)
        path = (ROOT / value.removeprefix("./")).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise ValueError("Missing local atlas asset: " + value)
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return 'src="data:' + mime + ';base64,' + base64.b64encode(path.read_bytes()).decode() + '"'
    source = re.sub(r'\bsrc=([\"\'])(.*?)\1', asset, source)
    # Recipes point to bundled example files; hosted artifacts have no directory
    # of sibling examples. Route those demonstration links to their atlas peers.
    destinations = {
        "resumen": "receta-decision", "evidencia": "receta-hallazgo",
        "prototipo": "receta-visor", "siguientes": "receta-ficha-entrega",
        "inicio": "atlas-inicio", "portada": "atlas-inicio",
    }
    def example_link(match):
        fragment = match.group(2).partition("#")[2]
        return 'href="#' + destinations.get(fragment, "atlas-inicio") + '"'
    return re.sub(r'\bhref=([\"\'])((?:\./)?examples/generated/[^\"\']+)\1', example_link, source)


def code_box(key: str, source: str) -> str:
    return (f'<details class="receta-copia ancho" id="fuente-{key}">'
            '<summary>Ver y copiar el HTML</summary>'
            '<div class="codigo"><div class="cab"><span>HTML</span>'
            f'<button type="button" data-copiar="atlas-codigo-{key}" aria-label="Copiar HTML">Copiar</button>'
            '<span class="copia-estado" role="status"></span></div>'
            '<pre tabindex="0" aria-label="HTML del componente, desplazable">'
            f'<code id="atlas-codigo-{key}" data-lenguaje="html" data-sin-lineas>{escape(source)}</code></pre></div></details>')


def shared_demo(key: str) -> str:
    if key == "apariencia":
        return ('<section class="pieza" id="atlas-apariencia"><h3>Este atlas es la muestra.</h3>'
                '<p>Abre Preferencias en la barra flotante. Cambia la familia, el modo claro u oscuro y la tipografía. '
                'Todos los componentes de estas páginas reciben la misma elección.</p>'
                '<p>Prueba Editorial, Catabum y Kaira. Después activa Lectura cómoda y comprueba que los títulos, '
                'el texto y los números conservan espacio suficiente.</p></section>')
    return ('<section class="pieza" id="atlas-comentarios"><h3>Comenta una parte de la muestra.</h3>'
            '<p>Selecciona esta frase o activa Comentar en la barra flotante. Escribe una observación, '
            'guárdala y vuelve a abrir el hilo para revisar la autoría y el fragmento al que se refiere.</p>'
            '<p>En el portal, los comentarios siguen los permisos del documento. En una copia local, '
            'la identidad es declarada y los comentarios permanecen en ese navegador hasta que los exportas.</p></section>')


def prepare(output: Path, render: bool = False) -> dict:
    recipes = json.loads((ROOT / "packages/core/registry/registry.json").read_text())["componentes"]
    ids = [r["id"] for r in recipes]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate registry IDs")
    output.mkdir(parents=True, exist_ok=True)
    groups = OrderedDict((key, []) for key in CHAPTERS)
    for recipe in recipes:
        groups.setdefault(recipe["capitulo"], []).append(recipe)
    pages, coverage = [], []
    cards = ''.join(f'<a href="#atlas-{key}"><span class="ceja">{len(items)} componentes</span>'
                    f'<strong>{escape(CHAPTERS.get(key, (key, key))[0])}</strong>'
                    f'<small>{escape(CHAPTERS.get(key, (key, key))[1])}</small></a>'
                    for key, items in groups.items())
    links = ''.join(f'<li data-claves="{escape(r["capitulo"])}"><a href="#receta-{r["id"]}">'
                    f'{escape(r["nombre"])}</a></li>' for r in recipes)
    intro = ('<section class="seccion" id="atlas-recorrido"><p class="ceja">Atlas de componentes · 22 de octubre de 2026</p>'
             '<h2>Ábrelo, muévelo, cámbiale el tema.</h2>'
             f'<p>Esta muestra reúne los {len(recipes)} componentes del registro de Margen. '
             'Cada página permite probar una familia y consultar el HTML que la produce.</p>'
             '<p>Las cifras, personas, empresas y eventos de las demostraciones son ejemplos. '
             'No representan métricas de usuarios ni resultados de producción.</p>'
             '<p>Empieza por <a href="#receta-galeria">la galería</a>, '
             '<a href="#receta-atencion">el mapa de atención</a> o '
             '<a href="#atlas-pruebas">las pruebas de lectura</a>.</p></section>'
             '<section class="seccion" id="atlas-novedades"><h2>Qué cambió en la lectura.</h2>'
             '<p>El índice acompaña el recorrido con un trazo sobre las secciones leídas. Las figuras anchas lo cubren; '
             'el fondo de los bloques de código lo difumina. Los títulos, las fechas y el pie comparten un ritmo de lectura.</p>'
             '<p>Prueba los <a href="#receta-codigo-poliglota">lenguajes de código</a>, '
             '<a href="#receta-columnas">las gráficas nuevas</a>, <a href="#receta-youtube">los medios</a> y '
             '<a href="#receta-pie-editorial">el pie del autor</a>. El HTML de cada muestra se puede copiar.</p>'
             '<p class="secundario">La referencia visual es <a href="https://www.cmrg.me">cmrg.me</a>. '
             'Esta adaptación usa Instrument Serif, una fuente abierta distinta de la original. '
             'Los colores y los ajustes de lectura siguen el tema que elijas.</p></section>'
             f'<nav class="biblioteca-rutas ancho" aria-label="Explorar familias">{cards}</nav>'
             '<section class="seccion" id="atlas-busqueda"><h2>Encuentra un componente.</h2>'
             '<div data-buscador-recetas><div class="buscador-recetas"><label for="atlas-buscar">Buscar por nombre</label>'
             '<input type="search" id="atlas-buscar" placeholder="Código, mapa, tabla…" aria-describedby="atlas-resultados">'
             '<p id="atlas-resultados" role="status"></p></div>'
             f'<nav aria-label="Todos los componentes"><ul class="catalogo-indice">{links}</ul></nav></div></section>')
    pages.append({"id": "atlas-inicio", "title": "Atlas", "content": "inicio.html"})
    (output / "inicio.html").write_text(intro)
    for category, items in groups.items():
        blocks = [f'<p class="bajada">{escape(CHAPTERS.get(category, (category, category))[1])}</p>']
        for recipe in items:
            key, name = recipe["id"], recipe["nombre"]
            source = portable(recipe["html"])
            demo = shared_demo(key) if key in ("apariencia", "revision") else source
            blocks.append(f'<section class="seccion" id="receta-{key}" data-atlas-componente="{key}">'
                          f'<p class="ceja">{escape(category)} · {escape(key)}</p><h2>{escape(name)}</h2>'
                          f'<p>{TRIALS.get(key, "Explora la muestra y cambia el tema. Comprueba la lectura en una ventana estrecha y recorre sus controles con el teclado.")}</p></section>')
            blocks += [demo, code_box(key, source)]
            coverage.append({"id": key, "page": "atlas-" + category, "anchor": "receta-" + key,
                             "mode": "shared-control" if key in ("apariencia", "revision") else "live-recipe",
                             "dependencies": recipe["dependencias"]})
        filename = category + ".html"
        (output / filename).write_text('\n'.join(blocks))
        pages.append({"id": "atlas-" + category, "title": CHAPTERS.get(category, (category, category))[0], "content": filename})
    long_code = '\n'.join(f'const registro{n:04d} = {{ numero: {n}, estado: "ejemplo" }};' for n in range(1, 1001))
    stress = ('<section class="seccion" id="prueba-espaciado"><h2>Un título necesita espacio.</h2>'
              '<p>Este párrafo empieza después del título. La separación debe mantenerse al cambiar de tema, '
              'tipografía, tamaño de ventana y modo de lectura.</p><h3>La siguiente idea.</h3>'
              '<p>Un subtítulo tampoco debe quedar pegado al bloque que lo precede o al texto que explica.</p></section>'
              '<section class="seccion" id="prueba-desplegable"><h2>El índice se cruza con un desplegable.</h2>'
              '<p>Abre el detalle y desplaza lentamente la página. Su encabezado, explicación y código deben '
              'seguir legibles en el área donde coincide el índice.</p></section>'
              '<details class="ancho" id="prueba-mil-lineas"><summary>Mil líneas: de 1 a 1000</summary>'
              '<p>Datos sintéticos para probar el espacio de la numeración. Desplaza el bloque hasta el final '
              'y copia su contenido: los números del margen no forman parte del código.</p>'
              '<div class="codigo"><div class="cab"><span>registros.js · JavaScript</span></div>'
              '<pre tabindex="0" aria-label="Mil líneas de código, desplazable">'
              f'<code data-lenguaje="javascript" data-lineas data-destacar="2-5,998-1000">{escape(long_code)}</code>'
              '</pre></div></details>'
              '<section class="seccion" id="prueba-formatos"><h2>Capítulos y documento completo.</h2>'
              '<p>El atlas demuestra el formato de capítulos con enlaces internos, historial y navegación Anterior/Siguiente. '
              'Las páginas Decisiones y Lectura muestran las piezas con las que se compone un informe o artículo de una sola página.</p>'
              '<p>Desactiva JavaScript para comprobar que el contenido sigue disponible para lectura. '
              'Los efectos e interacciones avanzadas necesitan JavaScript.</p></section>')
    (output / "pruebas.html").write_text(stress)
    pages.append({"id": "atlas-pruebas", "title": "Pruebas de lectura", "content": "pruebas.html"})
    config = {"title": "Margen · Atlas de componentes", "description": "Una biblioteca que puedes recorrer, probar y comentar.",
              "document_id": DOCUMENT_ID, "format": "chapters", "theme": "editorial", "mode": "dark", "pages": pages,
              "date": "2026-10-22", "reactions": True,
              "footer": {"author": "Una biblioteca compartida", "note": "Las mejores piezas empiezan con una observación. Prueba, comenta y comparte lo que debería cambiar.",
                         "links": [{"label": "Proyecto", "href": "https://github.com/angelbotto/margen", "detail": "Código abierto y contribuciones"},
                                   {"label": "Plataforma", "href": "https://artifacts.botto.is", "detail": "Leer, publicar y conversar"}], "platform": True}}
    (output / "atlas.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')
    (output / "coverage.json").write_text(json.dumps({"registry_count": len(ids), "components": coverage,
            "layouts": [{"id": "chapter-layout", "mode": "atlas-shell"}, {"id": "report-layout", "page": "atlas-reportes"}]}, ensure_ascii=False, indent=2) + '\n')
    if render:
        html = build(config["title"], [{"id": p["id"], "titulo": p["title"], "html": (output / p["content"]).read_text()} for p in pages],
                     description=config["description"], document_id=DOCUMENT_ID, format="chapters", theme="editorial", mode="dark",
                     date=config["date"], footer=config["footer"], reactions=config["reactions"])
        (output / "atlas.html").write_text(html)
    return {"directory": str(output), "pages": len(pages), "components": len(coverage), "rendered": render}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--render", action="store_true", help="Render locally for development. Final publication uses the installed canonical release.")
    args = parser.parse_args()
    print(json.dumps(prepare(args.output_dir, args.render), ensure_ascii=False))
