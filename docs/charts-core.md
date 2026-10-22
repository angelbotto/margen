# Núcleo de gráficas (`chart-core.js`)

`packages/core/components/chart-core.js` expone `window.MargenGraficas`. Lo usan `charts.js`, `analytics.js`, `attention-map.js`, `reports.js` (cascada y múltiplos) y `evidence.js`, y debe cargarse antes que todos ellos. Sus estilos están en `packages/core/styles/chart-core.css`, que `build.py` compone en `artifact.css` como bloque `CHART CORE`. No tiene dependencias ni hace peticiones de red.

## Contrato que se conserva

- La tabla es la única fuente de cifras. Ninguna gráfica inventa, redondea ni suma valores que la tabla no permita sumar. Las cascadas y las áreas apiladas suman cantidades. Los porcentajes (cohortes, metas, conversiones) se calculan fila a fila y nunca se suman ni se promedian.
- «Sin dato» no equivale a 0. Cada tipo lo muestra de una forma propia: un trazo cortado, una cruz en el eje, un marcador discontinuo, una celda rayada o el texto «Sin dato».
- `init(raíz)`, `get(el)` y `destroy()` son idempotentes. `destroy()` deja la tabla tal como estaba, sin dejar ni siquiera un `class=""`.
- Funciona sin red. El tip respeta `prefers-reduced-motion`.

## Ancho real

`responsive(el, render)` mide la caja con `ResizeObserver`. Solo vuelve a llamar a `render(ancho)` cuando cambia el ancho entero o la tipografía (`nota:tema`, `document.fonts.ready`). Un ancho de 0 (página oculta o `details` cerrado) no dibuja: la figura se dibuja al hacerse visible. Un freno corta las oscilaciones de más de seis redibujos por segundo. Como el SVG mide lo mismo que su `viewBox`, el texto queda en 12 px (14 px en `.pieza`) a cualquier ancho.

Solo tres figuras pueden desplazarse, y únicamente cuando su mínimo legible no cabe: el calendario (celda de 12 px), las cohortes (celdas con «n / base») y el Gantt (320 px de línea de tiempo). En ese caso la caja se vuelve `role="region"` con `tabindex="0"` y una etiqueta, y aparece una nota visible.

## Escalas y formato

| Función | Qué hace |
| --- | --- |
| `nice(min, max, n)` | Dominio y ticks con pasos 1-2-5 que contienen los datos. Si `min === max`, amplía el dominio un 10 % (±1 cuando el valor es 0). Rechaza rangos no finitos. |
| `niceZero(valores)` | Igual que `nice`, pero incluye el 0. Para barras, columnas, áreas y cascadas. |
| `timeTicks(t0, t1, n)` | Ticks de calendario UTC (día, 2 días, semana, quincena, mes, trimestre, semestre, año) y su formato. |
| `format(v, spec, {lang, unit})` | Formato del idioma del documento (`lang`, o `data-locale`; `es` → `es-CO`). Un `null` produce «Sin dato» o «No data». |
| `tickFormat(ticks, spec)` | Saca los decimales del paso y usa notación compacta a partir de 10⁵. Añade cifras hasta que todos los rótulos sean distintos. |

Los formatos se nombran como en Evidence y se declaran con `data-formato` en la figura o en el `th` de la columna. La unidad se declara con `data-unidad`.

| Spec | Ejemplo `es-CO` |
| --- | --- |
| `auto` (por defecto) | `1.234,5` · `1.000.000.000.000` · `1,234E-5` |
| `num0`, `num1`, `num1k` | `1.235` · `1.234,5` · `1,2 K` |
| `pct0`, `pct1` (ratio) · `pts1` (el valor ya está en %) | `33,3%` |
| `cop0`, `usd2`, `cop1m` | `$ 1.500.000` · `US$ 1.234,50` · `$2,5 M` |
| `date`, `shortdate`, `month`, `year`, `iso` | `22/10/2026` · `22 de oct` · `oct de 2026` · `2026` · `2026-10-22` |
| `duration`, `duration_min`, `duration_h` (`:short`, `:min`) | `3 días, 10 horas, 16 minutos` → `3 días 10 h 16 min` → `3 días` |

## Paleta, trazos y patrones

- `color(i)` devuelve `var(--grafica-1…8)`. Los slots 1–4 son del tema. Los slots 5–8 se derivan de ellos en OKLCH con `light-dark()`, para que cada modo use su propia receta. Las rotaciones se eligieron midiendo los 32 temas: cada slot derivado queda a ΔE OK ≥ 0,08 de los demás, con contraste ≥ 3,15:1 sobre `--grafica-papel` (lo verifica `check_charts_atlas.py`).
- `dash(i)` y `shape(i, x, y, r)` dan ocho trazos y ocho marcadores distintos.
- `patterns(svg)` crea ocho texturas por figura (lisa, diagonales, puntos, horizontales, verticales, trama, diagonal inversa, rejilla) en `--grafica-papel` sobre el color. Las series se distinguen sin color en barras, columnas, torta y áreas. `data-patrones="no"` las desactiva.

## Interacción

- `marks(host, svg, {items, describe, onSelect, status, columns})` crea un *roving tabindex*: la figura ocupa un solo tabulador. Las flechas recorren las marcas (en 2D para el mapa de calor), Inicio y Fin saltan a los extremos, Enter o Espacio fijan la marca y Escape cierra. Cada marca lleva `role="img"` y un `aria-label`. Los listeners se delegan en el SVG, nunca en cada marca.
- El tip es una sola capa por documento, `position: fixed`, ligada con `aria-describedby`. Aparece con el puntero, con el foco o con un toque, que lo deja fijado. Cambia de ancla para no salir nunca del viewport, y se oculta con `nota:pagina`, Escape, un clic fuera o un resize. Con scroll se reposiciona si la marca tiene el foco y, si no, se oculta.
- `legend(nombres, {targets})` crea botones con `aria-pressed`. Un clic o Enter aísla la serie y otro las muestra todas. Pasar el puntero o el foco la resalta. Una línea de ayuda explica el uso y un `role=status` anuncia el estado.

## Exportación

`exporter(figura, {table, getSvg, title})` añade dos botones.

- **Descargar CSV** usa la cabecera de la tabla y los `data-valor` crudos (o `time[datetime]`). Una celda vacía se exporta vacía. Los textos que empiezan como fórmula (`= + - @`) llevan `'` delante. Los números fuente no cambian. El archivo va en UTF-8 con BOM.
- **Descargar SVG** genera un SVG autónomo. Los estilos computados quedan en línea, sin `var()`, `currentColor` ni clases, y sin referencias externas. Incluye `<title>` y un `<desc>` con la unidad y la fuente (`figcaption`) y un fondo `--grafica-papel` resuelto. Los múltiplos exportan sus paneles en un solo SVG.
- El SVG exportado se entiende solo: `legendOf(figura)` lee la leyenda visible (series de `.mg-leyenda` y niveles de `.calor-leyenda`) y `standaloneSvg` la dibuja bajo la gráfica, con sus colores resueltos, y la nombra en el `<desc>` («Leyenda: Norte, Centro, Sur»). La raíz lleva `role="img"` y `aria-label` igual al título: el archivo no es interactivo, así que no promete flechas ni Enter. Los colores salen tal como los computa el navegador (puede ser `oklch()`).

## Casos límite

- **Calor constante o todo en cero:** un solo nivel neutro (`--calor-0` si todo vale 0; `--calor-2` en otro caso), nunca el máximo. La leyenda dice «Todas las celdas: 0 · sin variación», sin inventar un rango. Si los cuantiles solo dan dos cortes (muchos ceros y un pico), el máximo forma su propio nivel y el resto queda en el mínimo.
- **Meta con negativos:** valor y meta pueden ser negativos. El eje se extiende por debajo de 0 y la barra va del 0 al valor en su dirección. Los umbrales siguen siendo no negativos y crecientes.
- **Líneas con un único valor no negativo** (p. ej. conteos todos en 0): el eje empieza en 0.
- **Calor denso:** si la celda mínima de 8 px no cabe, primero cede el rótulo de fila (mínimo 40 px, truncado con «…»). Si aun así no cabe, el SVG conserva su ancho y la caja se desplaza en horizontal con `role="region"`, `tabindex="0"` y `aria-label` «…, desplazable horizontalmente». 26 columnas caben a 320 px; 31 columnas con rótulo largo se desplazan.

## Treemap (`attention-map.js`)

Es un treemap *squarified* (Bruls et al.) a ancho real, como máximo 1008 × 380 (marco de 64 rem con 8 px de *padding*), y 320 px de alto por debajo de 640 px, dispuesto en filas. Las celdas usan `--panel-2` con un trazo de 1 px `--grafica-linea` (en Editorial oscuro, #2e2821 y #3b3229). El nombre va en serif de 18 px y la duración en mono de 11,5 px, con niveles completo, corto, mínimo o ninguno según el área. Las áreas son exactas.

Cuando la cola es demasiado pequeña para verse o enfocarse (lado < 10 px o área < 196 px²), se agrupa en «Otros (n)». La celda conserva la suma exacta, no recibe un área mínima inventada y su tip lista a cada miembro. Una categoría visible nunca entra en «Otros». Los botones por categoría, el estado y la tabla siguen dando acceso a cada una. Las categorías en 0 no tienen área. La partición binaria anterior sigue disponible con `data-atencion-modo="particion"`.

## Pruebas

- `node --test scripts/test_chart_core.mjs` prueba `nice`, el formato (0, negativos, 1e12, `null`, porcentajes, monedas, fechas y duraciones), los ticks, `squarify` (áreas exactas, sin solapes, 26 categorías, ceros), la paleta y `fit`/`wrap`.
- `npx vitest run packages/core/charts-responsive.test.tsx`
- `scripts/check_charts_atlas.py <atlas.html> <salida.json>` usa Playwright. Recorre 320, 390 y 1440 px con Editorial, Catabum y Kaira en claro y oscuro, y comprueba teclado, táctil, tip, resize, tema, páginas, listeners, tablas tras `destroy`, exportes, treemaps extremos y el mapa de calor de 31 × 31.
- `scripts/test_chart_edges.py` (Playwright, sin red) cubre los casos límite y el SVG exportado en Chromium y WebKit, a 320 y 1440 px, en claro y oscuro. `MARGEN_BROWSER=webkit` limita el motor.
- `scripts/measure_charts.py <atlas.html> <salida.json>` mide el desbordamiento, el tamaño del texto, los solapes y el número de marcas de cada figura.
