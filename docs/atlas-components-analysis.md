# Atlas de componentes: análisis de datos, gráficas y embeds

22 de octubre de 2026 · run `run_d4fd3704f129` · task `task_cd74624a920f` · base `d61743a`, atlas de root `4394481`.

Análisis de solo lectura. No cambia producto, build ni despliegue.

**Revisión del coordinador:** la comparación de attention map de la sección 3 describe la cuadrícula de actividad de `/now`, no el treemap de aplicaciones de la portada mostrado por Ángel. Esa comparación no es evidencia válida para diseñar el treemap: usar la auditoría de referencia de la portada. Las cifras de la simulación lazy permanecen provisionales hasta verificar que conserva completas las páginas con artículos anidados. El pedido del usuario ya autoriza implementar embeds; las propuestas de CSP necesitan revisión técnica y pruebas, no una nueva aprobación genérica inferida de este informe. La cobertura por ID está en [`atlas-components-coverage.json`](atlas-components-coverage.json). Las capturas y mediciones viven fuera del repositorio, en `~/.local/share/margen-review/atlas-datos-20261022/`.

## Resumen

1. **El registro está completo y el atlas puede cubrirlo.** Hay 90 IDs en `registry.json` y 92 manifests: los dos restantes son los layouts `report-layout` y `chapter-layout`. Las 22 gráficas se reparten en seis runtimes propios que, juntos, pesan **26 KB gzip**. No hace falta adoptar una librería de gráficas.
2. **El problema visible es de legibilidad, no de catálogo.** Los SVG usan un `viewBox` fijo de 720–960 px. A 390 px, **20 de las 21 figuras medidas** (todas menos barras) necesitan desplazamiento horizontal. En escritorio, el texto del SVG se escala de 12 a **15–21 px** según la gráfica: cada figura tiene un tamaño de letra distinto.
3. **Cada runtime resuelve lo común por su cuenta.** Hay cinco implementaciones de formato (`es-CO` fijo, con 4, 6 u 8 cifras significativas), dos de escala, tres de paleta (todas de 4 tonos) y tooltips solo con `<title>`, salvo en el attention map.
4. **El attention map existe** (`atencion`). Se diferencia de la referencia de cmrg.me en el algoritmo, el color y el ritmo, no en la ausencia de código. Ver [Attention map frente a la referencia](#attention-map-frente-a-la-referencia).
5. **El montaje diferido es la mejora de carga de mayor rendimiento.** En una simulación sobre el atlas de root, con las páginas ocultas convertidas en `<template>`, el script inicial pasa de **448 a 86 ms** con CPU 6x a 390 px. Los nodos bajan de 88.737 a 17.212.
6. **Los embeds no caben hoy en la CSP del lector alojado** (`default-src 'none'`, `img-src data: blob:`, sandbox sin `allow-popups`). Se pueden diseñar *click-to-load* sin abrir permisos en esta fase.

## 1. Inventario y cobertura

| Familia del registro | IDs | Runtimes adicionales a la base |
| --- | ---: | --- |
| publicaciones | 10 | `editorial.js`, `invitation.js` |
| lectura | 13 | `handwriting.js`, `evidence.js` |
| reportes | 15 | `reports.js`, `evidence.js`, `code.js` |
| graficas | 22 | `charts.js` (6), `analytics.js` (7), `reports.js` (2), `evidence.js` (4), `attention-map.js`, `relationship-map.js` |
| tablas | 7 | `tables.js`, `table-model.js`, `data-explorer.js` |
| prototipos | 5 | `prototype.js`, `tabs.js`, `evidence.js` |
| expresion | 8 | three.js 0.160.1 (CDN), `scene.js`, `globe.js`, `fleet.js`, `geography.js`, `sound.js` |
| configuracion | 10 | `review.js`, `code.js`, `writing.js`, `editorial.js` |

La base de **cada** receta incluye `fonts.css` (538 KB gzip), `artifact.css` (54 KB gzip) y `audio.js` (146 KB gzip, 20 muestras base64). Una tabla densa arrastra las mismas muestras de audio que un globo. En comparación, todos los runtimes de datos juntos pesan 26 KB gzip (83 KB sin comprimir).

Medición por receta en `library.html` (`recipe-audit.json`): ninguna de las 90 produjo errores de consola ni mensajes `.grafica-error` a 1280 o 390 px. Todas las gráficas SVG y 3D conservan una tabla fuente. Sin red, las siete piezas WebGL muestran su mensaje de respaldo y la tabla completa (`offline-expresion-xyz.png`).

### Qué es gráfica de verdad y qué es tabla con estilo

| Tipo | IDs |
| --- | --- |
| Gráfica SVG calculada desde la tabla | barras, lineas, temporal, dispersion, distribucion, cascada, multiples, calendario, torta, areas, caja, velas, mapa-rutas, mapa-burbujas, atencion, sankey, cohortes, embudo, incertidumbre, sensibilidad, gantt, relato-visual |
| Tabla con codificación visual | calor (celdas por nivel), sparkline, totales, comparacion |
| Escena WebGL con tabla de respaldo | xyz, etapas, columnas-mapa, arcos-mapa, almacen, globo-flota, recorrido |
| Grafo interactivo | relationship-map |
| Ilustración estática | sketch-diagram |

`calor` se llama "mapa de calor", pero es la tabla coloreada: no tiene ejes, orden ni escala continua. La decisión es buena para la accesibilidad, pero queda corta frente a un heatmap de Metabase, ECharts o Plot.

### Interacciones por runtime

| Runtime | Selección | Teclado | Tooltip | Redimensión | Movimiento |
| --- | --- | --- | --- | --- | --- |
| `charts.js` | ninguna | solo la región desplazable | `<title>` nativo | barras con `ResizeObserver`; resto `viewBox` 800 | sin animación |
| `analytics.js` | `<select>` + clic en marca | vía `<select>` | `<title>` nativo | `viewBox` 720 | sin animación |
| `evidence.js` | `<select>` + clic | vía `<select>` | `<title>` | ancho fijo por contenido | `IntersectionObserver` para relato |
| `reports.js` | escenario con inputs | controles nativos | `<title>` | `viewBox` fijo | — |
| `attention-map.js` | botones `aria-pressed` | botones + Escape | propio, en hover/foco/táctil, con recorte al viewport | etiquetas con `ResizeObserver`; mínimo 900 px | sin animación |
| `scene.js`/`globe.js`/`fleet.js` | lista/tabla | flechas | — | `ResizeObserver` | `prefers-reduced-motion`, pausa fuera de pantalla |

Lo bueno, que hay que conservar: tabla como única fuente de cifras, validación estricta (fechas ISO, sin solapes, límites de filas), "Sin dato ≠ 0", `init/get/destroy` idempotente y errores que dejan los datos visibles.

## 2. Defectos y límites confirmados

| ID | Hallazgo | Evidencia | Recetas |
| --- | --- | --- | --- |
| B1 | El SVG dibuja los rótulos literales "X" e "Y" encima y debajo del eje. Las unidades reales están en un `<p>` aparte. | `charts.js` `axes()`, `lines()`; `figs/desk-lineas-ejemplo.png` | barras, lineas, temporal, dispersion, distribucion |
| B2 | `color(i)` es `--grafica-(i%4+1)`, pero torta admite 6 categorías: la 5 y la 6 repiten los colores 1 y 2. evidence usa `ev-color-0..3`. | `analytics.js:59`, `read()` límite 6 | torta, areas, caja, sankey, embudo |
| B3 | `Intl.NumberFormat('es-CO')` está fijo en 8 runtimes, sin leer `lang` ni un `data-formato`. Las cifras significativas cambian de un runtime a otro (4, 6 u 8). No hay moneda, porcentaje, compactación (k/M) ni unidades de tiempo. | grep `es-CO` | todas las gráficas |
| B4 | Los ticks dividen el dominio en cuartos sin redondear (`min+(max-min)*i/4`) y producen valores como 13,5 u 8,5. El dominio no se ajusta a números redondos. | `charts.js` `axes()`; `analytics.js` `axis()` | líneas, temporal, dispersión, áreas, caja, velas |
| B5 | El `viewBox` fijo escala el texto con el contenedor. A 390 px, 20 de 21 figuras requieren scroll horizontal (solo barras se adapta). En escritorio el texto SVG mide 15,2–21,1 px (cohortes 21,1; calendario 17,1; sankey 17,4). | `recipe-audit.json`, `library-graficas-metrics.json` | las 21 figuras SVG medidas |
| B6 | Fuera del attention map, el detalle depende de `<title>`. Ese tooltip tiene retraso, no aparece con táctil ni con teclado y su estilo no sigue el tema. | código y prueba manual | 20 figuras |
| B7 | Las marcas no son enfocables. analytics/evidence ofrecen un `<select>` equivalente; charts.js no ofrece nada más allá de la tabla. | `recipe-audit.json` (`enfocables` 2–4) | charts.js |
| B8 | `three.min.js` se carga con `<script src>` síncrono desde cdnjs antes de los módulos. Con red lenta bloquea el parseo del resto: el DCL de `library.html` pasa de 170 ms (sin red) a 970 ms (con CDN). El respaldo sin red funciona. | `build.py`, `contract_artifact.py:118` | 7 escenas 3D, y todo el documento que las incluya |
| B9 | `audio.js` es dependencia base de las 90 recetas. | `registry.json` | todas |
| B10 | El attention map usa una partición binaria: la cola produce tiras de 3–4 % de ancho (`8. Otros`). En celdas pequeñas solo se ve un número. | `figs/desk-atencion-ejemplo.png` | atencion |
| B11 | `calor` exige seis umbrales manuales y 5 niveles fijos. No tiene escala divergente ni orden de filas o columnas. | `charts.js` `heatmap()` | calor |
| B12 | La leyenda de charts.js es una lista estática: no resalta series, no permite aislarlas y no se sincroniza con la tabla. | código | barras, lineas, temporal |
| B13 | El lector alojado sirve el documento con `sandbox allow-scripts allow-downloads; default-src 'none'; img-src data: blob:`. No hay `frame-src` (iframes bloqueados), `img-src` remoto ni `allow-popups` (los enlaces `target=_blank` no abren). | `portal/app.py:761` | embeds y enlaces salientes |

Ninguno de estos defectos rompe datos. Todos degradan lectura, consistencia o acceso.

## 3. Referentes: qué hacen bien y qué conviene tomar

Fuentes primarias consultadas: documentación oficial y repositorios de cada proyecto. Los tamaños se midieron descargando los bundles publicados en npm vía jsDelivr y comprimiéndolos con gzip -9.

| Plataforma | Qué resuelve que a Margen le falta | Coste | Encaje |
| --- | --- | --- | --- |
| **Observable Plot** 0.6.17 ([tip](https://github.com/observablehq/plot/blob/main/docs/marks/tip.md), [pointer](https://github.com/observablehq/plot/blob/main/docs/interactions/pointer.md), [accesibilidad](https://github.com/observablehq/plot/blob/main/docs/features/accessibility.md)) | El tip elige el ancla automáticamente (`preferredAnchor`) para no salirse del marco y admite un `format` por canal. El *pointer* fija el punto más cercano en 1D/2D con `maxRadius` y *click-to-stick*. `ariaLabel` por marca y `ariaHidden` para la decoración. `formatNumber(locale)`. | 69 KB gzip + d3 92 KB | Modelo de API a imitar: pointer + tip + `ariaLabel` por marca. No se incrusta. |
| **Apache ECharts** 5.6/6.0 ([aria](https://echarts.apache.org/handbook/en/best-practices/aria/), [canvas vs SVG](https://github.com/apache/echarts-handbook/blob/master/contents/en/best-practices/canvas-vs-svg.md), [import](https://github.com/apache/echarts-handbook/blob/master/contents/en/basics/import.md)) | Descripción ARIA generada desde título, series y datos. **Decal patterns** (`aria.decal.show`) para distinguir series sin color. Renderer SVG con menos memoria en móvil. Treemap con jerarquía, *drill-down* y migas. | 335–362 KB gzip completo; *tree-shaking* solo con bundler | Demasiado pesado para HTML portable. Tomar decals, descripción automática y la jerarquía del treemap. |
| **Vega-Lite + vega-embed** | Gramática declarativa y menú de exportación (SVG/PNG/fuente). | 276 KB gzip (vega+lite+embed) | Exportación como referencia de UX. |
| **Evidence** ([formato](https://docs.evidence.dev/core-concepts/formatting), [area chart](https://docs.evidence.dev/components/charts/area-chart)) | Formatos con nombre (`usd1m`, `pct1`, `num0k`, `shortdate`) aplicados por eje (`y_fmt`) o por serie (`fmt`). `reference_line`, `reference_area` y `reference_point` como hijos del gráfico. | usa ECharts | **Tomar los nombres de formato** y las referencias como marcas declarativas. |
| **Metabase** ([visualizaciones](https://www.metabase.com/docs/latest/questions/visualizations/visualizing-results), [trend](https://github.com/metabase/metabase/blob/master/docs/questions/visualizations/trend.md), [export](https://github.com/metabase/metabase/blob/master/docs/questions/exporting-results.md)) | *Trend* compara el último periodo con el anterior, con el valor previo o con una meta, hasta 3 comparaciones. Exporta CSV, XLSX, JSON y PNG. Treemap, sunburst, gauge, progress y combo. | servidor | La comparación de periodo y la exportación CSV/PNG son patrones de producto directos. |
| **Apache Superset** ([explorar datos](https://github.com/apache/superset/blob/master/docs/docs/using-superset/exploring-data.mdx)) | *Percent change* rebasa todas las series sobre una línea base arrastrable. *Rolling mean* con periodos mínimos. *Time comparison*. | servidor | La comparación rebasada es útil en `temporal`. |
| **Tremor** ([bar chart](https://www.tremor.so/docs/visualizations/bar-chart)), ahora parte de Vercel | `valueFormatter` único para ejes y tooltip. Leyenda que resalta una categoría (`onValueChange`). Componentes pequeños: Bar List, Category Bar, Tracker, Spark Chart, Progress. | React + Recharts | Formato único compartido; Category Bar y Tracker como recetas ligeras. |
| uPlot / Chart.js | Canvas rápido: 22 y 70 KB gzip. | — | Útiles solo para series muy largas; no recomendados aquí. |

Capturas: `external/echarts-treemap.png` (jerarquía con huecos de nivel y etiquetas), `external/tremor-barchart.png` (ticks compactos con moneda, rejilla sutil) y `external/cmrg-treemap-*.png`.

**Conclusión de stack:** el runtime de datos propio ocupa 26 KB y ya cumple el contrato tabla→SVG. La mayor librería razonable (Plot + d3) añadiría 161 KB, y ECharts entre 335 y 362 KB. Ninguna resuelve la portabilidad mejor que el código actual. Se recomienda un **núcleo común pequeño** que replique el método de estas librerías (escala, formato, tip y pointer, paleta y patrones), no una dependencia nueva.

## Attention map frente a la referencia

La pieza de cmrg.me (`/now`, "i've been up to a few things!") es un **mosaico sin huecos**. Cada día es un `<span role="img" aria-label="2 contributions on oct 1">`. La intensidad se codifica con opacidad (1 contribución = 60 %), el tono identifica el proyecto y una sombra cálida rodea el bloque. El día en curso cambia de tono. Las celdas no son enfocables (`tabindex=-1`) y no tienen texto ni tabla.

| Aspecto | cmrg.me | `atencion` actual | Propuesta |
| --- | --- | --- | --- |
| Algoritmo | rejilla de celdas por fecha | partición binaria por mitades de suma | **squarified** (Bruls et al.); la binaria se conserva como opción |
| Separación | sin huecos, sin bordes | bordes de 1 px en `--grafica-linea` | `gap:0` + 1 px de `--papel` como separador opcional |
| Color | tono por categoría + opacidad por intensidad | monocromo `atencion-area` | tono de la paleta temática por categoría y opacidad 0,55–1 por valor relativo |
| Texto | ninguno | nombre y valor en `foreignObject`; número en celdas pequeñas | igual, con umbral por lado mínimo (≥ 72×40 px nombre; ≥ 24 px número; resto sin texto) |
| Ritmo | aparición escalonada y sombra cálida | estático | reveal escalonado ≤ 400 ms, solo sin `prefers-reduced-motion`; sombra como token del tema |
| Acceso | `aria-label` por celda, sin teclado | botones, tooltip, status, tabla | **mantener lo actual**: es superior |
| Móvil | se encoge sin scroll | mínimo 900 px → scroll | layout a ancho real; en <480 px, 2 columnas o lista con barras |

Verificación propuesta: relación de aspecto media ≤ 3 con el ejemplo de 8 categorías (hoy, la cola binaria supera 6), 0 celdas con texto truncado y 390 px sin scroll horizontal.

## 4. Mejoras priorizadas

Orden recomendado. Cada una es reutilizable por varias recetas y no añade dependencias.

| # | Mejora | Recetas | Aceptación verificable |
| --- | --- | --- | --- |
| **P0-1** | **Núcleo `chart-core.js`** (≤ 8 KB gzip): `scale`/`nice` (ticks 1-2-5), `format(spec, lang)` con nombres tipo Evidence (`num0`, `num1k`, `pct1`, `cop0m`, `usd1k`, `shortdate`, `month`, `duration`), unidad por `data-formato`/`data-unidad`, paleta de 8 slots + patrones, `tip` y `pointer` compartidos. Los seis runtimes lo consumen. | 22 gráficas | un solo `Intl.NumberFormat` por `lang` del documento; ticks en múltiplos de 1, 2 o 5; prueba unitaria de `nice()` y `format()` con 0, negativos, 1e12 y `null` |
| **P0-2** | **Ancho real en lugar de `viewBox` fijo.** Render a ancho medido con `ResizeObserver` y fuente CSS constante (12–14 px). Por debajo de 480 px: leyenda debajo, menos ticks, etiquetas rotadas o abreviadas. Scroll solo en calendario, cohortes y gantt, con región etiquetada. | 21 figuras | a 390 px, 0 figuras con scroll salvo las 3 declaradas; texto SVG 11–14 px a 390 y 1440 px; repintado tras cambio de tema o fuente sin parpadeo |
| **P0-3** | **Tip + teclado unificados.** Extender el patrón de `attention-map.js`: *roving tabindex* sobre las marcas, flechas para recorrer, Enter para fijar, Escape para cerrar, `aria-describedby` hacia un `role=status`, tap para fijar en táctil y anclaje que no se salga del viewport (como `preferredAnchor` de Plot). | 21 figuras | se recorren todas las marcas con el teclado; táctil muestra el valor; el tip nunca queda fuera de `innerWidth`/`innerHeight`; se oculta con el cambio de página `nota:pagina` |
| **P0-4** | **Correcciones baratas:** quitar "X"/"Y" literales (B1); paleta de 8 + decal (B2); nombre de serie en tooltip y status; `aria-label` por marca. | charts, analytics, evidence | snapshot SVG sin `<text>X</text>`; torta de 6 categorías sin colores repetidos; contraste ≥ 3:1 de cada slot contra `--papel` en los 16 temas, claro y oscuro (validador en `scripts/themes.py`) |
| **P1-5** | **Attention map v2 "mosaico"** (sección anterior). Opción `data-atencion-modo="mosaico|particion"`. | atencion | ver la verificación de la sección anterior |
| **P1-6** | **Serie de comparación** (Metabase Trend, Superset percent change): periodo actual frente al anterior (línea punteada), meta (`reference_line`), banda (`reference_area`), anotación de punto y KPI de delta. Reutiliza `delta()` de charts.js. | temporal, lineas, areas, sparkline | delta con base 0 dice "no definido"; meta y banda aparecen en tabla y leyenda; pasa con datos faltantes |
| **P1-7** | **Heatmap SVG real** (matriz con ejes, escala secuencial o divergente, patrón para "sin dato", orden por fila o columna) sobre la misma tabla; la tabla coloreada queda como modo accesible. | calor, cohortes, calendario | umbrales opcionales (cuantiles por defecto); escala divergente con punto medio declarado; 31×31 a 390 px sin solapes de texto |
| **P1-8** | **Exportar y copiar datos:** "Descargar CSV" desde la tabla fuente, "Descargar SVG" y "Copiar datos". Funciona offline con `Blob`, y el sandbox alojado ya permite `allow-downloads`. | todas las gráficas y tablas | el CSV conserva los valores de `data-valor` (no el texto formateado) y la cabecera; el SVG exportado incluye `<title>`, fuente y unidad |
| **P2-9** | **Recetas nuevas solo donde hay hueco real:** columnas agrupadas o apiladas verticales (hoy solo hay barras horizontales); *dumbbell/slope* para antes-después cuantitativo; histograma desde valores crudos con bins automáticos y *strip/beeswarm*; *bullet/progress* (Tremor Category Bar). | huecos | cada una con tabla fuente, núcleo P0-1 y el mismo checklist de aceptación |
| **P2-10** | **Embed click-to-load** (sección 6). | nueva receta | ver sección 6 |

Fuera de alcance por ahora: canvas o WebGL para series de más de 500 puntos, *drill-down* jerárquico de treemap y *brush*/zoom temporal. Se pueden añadir después del núcleo si un caso real los pide.

## 5. Arquitectura de carga del atlas

### Medición

Entorno: Chromium headless (Playwright), MacBook m4, sin red externa. Fixture de root servido en `127.0.0.1:8896/atlas.html` (2,18 MB, 10 páginas). Datos completos en `atlas-lazy-simulation.json` y `perf-cpu6x.json`.

| Escenario | DCL | Script | Nodos | SVG | Tareas largas |
| --- | ---: | ---: | ---: | ---: | --- |
| Actual, 1440 px, CPU 1x | 204 ms | 74 ms | 88.530 | 208 | 0 |
| Actual, 390 px, CPU 6x | 1.009 ms | 448 ms | 88.737 | 208 | 70, 56, 173, 122 ms |
| Páginas ocultas en `<template>`, 390 px, CPU 6x | 658 ms | 86 ms | 17.212 | 37 | 56, 99 ms |
| `standard.html` (1 página), 390 px, CPU 6x | 403 ms | 52 ms | 1.078 | — | 116 ms |

La simulación da una cota y no sustituye a la implementación: convierte las páginas ocultas en plantillas inertes antes del parseo. El resto del coste, unos 650 ms, sale de parsear el CSS con fuentes base64 (`fonts.css`, 729 KB, 20 `@font-face` en el atlas) y de la página activa.

### Contrato de montaje diferido propuesto

Compatible con capítulos (`chapters.js`), deep links, `<details>`, temas y el contrato de módulos de `contract_artifact.py`.

1. **El generador Python** emite la página activa viva y cada página oculta como `<article data-pagina hidden><template data-diferida>…</template></article>`. El HTML sigue siendo un solo archivo, offline y sin `fetch`. El `<noscript>` existente se sustituye por una copia estática mínima de cada página, o por un enlace "versión sin JavaScript" generado aparte.
2. **`chapters.js`** expande el `<template>` en `nota:pagina` *antes* de despachar el evento. Lo mismo ocurre al resolver un hash `#receta-x` (busca el ID dentro de `template.content`) y con `?pagina=`. La búsqueda del índice usa un índice JSON generado en Python (id, nombre, página, palabras clave), no el DOM.
3. **Cada runtime** expone `init(root)`, `destroy(root)` e idempotencia; ya lo hacen todos los de datos. Se añade un despachador común: tras expandir, `window.Margen.mount(page)` llama a `init(page)` de cada módulo registrado. Al salir de una página se conserva el DOM (volver es instantáneo) y se llama a `pause()` en escenas WebGL y audio.
4. **Montaje por visibilidad dentro de la página:** las figuras pesadas (`data-escena`, `data-flota`, `relationship-map`) se montan con `IntersectionObserver` (`rootMargin: 200px`). Las gráficas SVG ligeras se montan al expandir.
5. **`<details>`:** las figuras dentro de un `details` cerrado se miden al abrir (`toggle`). charts.js ya cierra y abre `details` y no debe depender de medir con ancho 0.
6. **Tema:** las gráficas leen colores con `var(--grafica-n)`, así que el cambio de tema no requiere re-render. Solo P0-2 debe re-renderizar en `resize` y en cambios de tipografía (evento del control de apariencia).
7. **three.js:** no usar `<script src>` síncrono. Opciones: (a) incrustar `three.min.js` (167 KB gzip) solo en la página "Lugares y espacio", dentro de su `<template>`, para conservar el uso offline; (b) cargarlo con `defer`/dinámico desde la CDN permitida al montar la primera escena, con el respaldo de tabla actual. Para un HTML portable se recomienda (a).
8. **Base por receta:** separar `audio.js` en la base. Las muestras solo se incluyen si el documento usa `data-audio-*`, handwriting, escritura o sonido. `modules_for()` ya calcula módulos por atributos y puede hacerlo también para el audio.

Verificación: con CPU 6x a 390 px, script inicial ≤ 120 ms y nodos iniciales ≤ 20.000. Cada uno de los 90 deep links `#receta-<id>` abre su página y enfoca el título. Cambiar 10 veces de página no hace crecer los listeners (contar con `getEventListeners` en CDP). Con la red bloqueada, el atlas completo funciona salvo WebGL, que muestra su respaldo. `validate_artifact.py` sigue aceptando el manifiesto de módulos.

### Páginas propuestas del atlas

El registro conserva sus 8 familias. El atlas añade un campo de página propio para que ninguna página tenga más de unas 10 piezas pesadas:

| Página | IDs |
| --- | ---: |
| Publicar | 10 |
| Leer | 13 |
| Decidir | 15 |
| Datos · magnitud y parte del todo (barras, cascada, múltiplos, torta, atención, embudo, sankey) | 7 |
| Datos · tiempo (líneas, temporal, áreas, calendario, velas, cohortes) | 6 |
| Datos · distribución y relación (dispersión, distribución, caja, calor, incertidumbre, relationship-map, sketch-diagram) | 7 |
| Lugares y espacio (mapas 2D y las 7 escenas 3D) | 9 |
| Tablas | 7 |
| Prototipos (+ sonido) | 6 |
| Código y edición | 10 |

Las tres páginas de datos permiten mostrar en cada una la misma tabla de ejemplo en dos o tres formas, para enseñar cuándo usar cada gráfica. Todo lo de three.js queda aislado en una sola página. Los IDs por página están en `paginas_propuestas` del JSON.

## 6. Embeds de X, YouTube e Instagram

Investigación solamente. No se implementa nada ni se abren permisos.

| Proveedor | Mecanismo oficial | Qué carga | Privacidad | Comprobado hoy |
| --- | --- | --- | --- | --- |
| **YouTube** | `<iframe src="https://www.youtube-nocookie.com/embed/ID">`; IFrame API con `enablejsapi=1` y `origin` ([parámetros](https://developers.google.com/youtube/player_parameters)) | iframe del reproductor; viewport mínimo 200×200, recomendado ≥ 480×270 | El modo de privacidad mejorada evita que la vista personalice YouTube y la publicidad, pero la página oficial **no** dice que no use cookies. Requiere enviar `Referer` (error 153 sin él) ([soporte](https://support.google.com/youtube/answer/171780)) | `youtube.com/oembed` responde sin autenticación con título, autor y `thumbnail_url` (`i.ytimg.com`) |
| **X** | `blockquote.twitter-tweet` + `platform.twitter.com/widgets.js`; oEmbed `publish.twitter.com/oembed` con `omit_script=1` y `dnt=true` | script externo que sustituye el blockquote por un iframe | `data-dnt="true"`; sin el script queda el blockquote con texto, autor, fecha y enlace | oEmbed respondió (301 → 200) sin autenticación y devolvió un blockquote con `data-dnt="true"`. La documentación de developer.x.com respondió 402 a WebFetch |
| **Instagram** | `blockquote.instagram-media` + `embed.js`; `instgrm.Embeds.process()`; oEmbed `graph.facebook.com/<v>/instagram_oembed` con `omitscript=true` ([doc](https://developers.facebook.com/docs/instagram-platform/oembed)) | script e iframe | Uso de los metadatos restringido a mostrar el embed (prohibido usarlos para analítica). Sin cuentas privadas ni stories, y **sin Shadow DOM**. 1.000 solicitudes por hora | Hoy, una solicitud sin token devolvió el blockquote. La documentación no confirma si un token es obligatorio: no conviene depender de ello |

### Diseño recomendado: `embed` con carga explícita

- **El generador Python resuelve en tiempo de build**, nunca en el navegador del lector, los datos públicos: oEmbed (título, autor, fecha, texto del post) y la miniatura, **incrustada como `data:`**. Así el HTML funciona offline y cumple `img-src data:`.
- **Estado inicial:** una tarjeta con miniatura, título, autor, proveedor, fecha, un enlace "Abrir en YouTube/X/Instagram" y el botón "Cargar contenido de YouTube". El texto avisa de que, al cargar, el proveedor recibe la IP y puede usar cookies.
- **Al hacer clic:** YouTube crea un `<iframe src="youtube-nocookie…?autoplay=1" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" referrerpolicy="strict-origin-when-cross-origin" loading="lazy" title="…">`. X e Instagram requieren el script del proveedor. Para no inyectar scripts externos en el documento, se recomienda **solo el modo tarjeta y enlace** para X e Instagram, o un iframe al endpoint oficial de cada proveedor si existe y se aprueba.
- **Preferencia recordada** por proveedor ("cargar siempre YouTube en este navegador"), guardada en `localStorage` con try/catch y revocable.
- **Respaldo:** sin red, CSP que bloquee o proveedor caído, la tarjeta sigue mostrando el texto y el enlace. En impresión se imprime la tarjeta.
- **CSP del lector alojado:** requeriría añadir `frame-src https://www.youtube-nocookie.com` (y los dominios de X e Instagram si se aprueban) y `allow-popups allow-popups-to-escape-sandbox` para que funcionen los enlaces externos. Es decisión de Ángel y queda fuera de esta tarea.

Aceptación del embed: el HTML inicial no hace ninguna solicitud de red (lo comprueba Playwright con la ruta bloqueada) y el enlace y el texto están disponibles. Al hacer clic se carga exactamente un iframe del dominio declarado. Si la carga se bloquea, hay mensaje visible y el foco vuelve al botón. Con teclado, Enter y Space activan el botón.

## 7. Plan de implementación sugerido

1. **P0-1 a P0-4:** un escritor, con `chart-core.js` y la migración de charts.js y analytics.js. Prueba de referencia: `scripts/tests_components.js` y `scripts/tests_analytics.js`, más capturas a 390 y 1440 px en temas claro y oscuro.
2. **Montaje diferido:** otro escritor, propietario de `chapters.js`, `contract_artifact.py`, `library.py` y `build_atlas.py`. No toca runtimes de datos salvo el registro en `Margen.mount`.
3. **P1-5 a P1-8:** después de integrar el núcleo.
4. **Embeds:** primero el diseño de la tarjeta offline; la CSP la decide Ángel.

## Evidencia

En `~/.local/share/margen-review/atlas-datos-20261022/`, fuera del repositorio:

- `recipe-audit.json`: medición de las 90 recetas a 1280 y 390 px
- `library-graficas-metrics.json`: escala y overflow de cada figura
- `figs/{desk,mob}-*.png`: 38 capturas por figura
- `perf-baseline.json`, `perf-cpu6x.json`, `atlas-lazy-simulation.json`: mediciones de carga
- `offline-expresion-xyz.png`: respaldo WebGL sin red
- `external/`: cmrg.me (`/now` treemap, `/am` globo), ECharts treemap, Tremor y Plot
