# Gráficas del atlas: núcleo compartido, migración, treemap y recetas nuevas

22 de octubre de 2026 · run `run_d4fd3704f129` · task `task_b89d6825ae03` · rama `angelbotto/margen-atlas-graficas` (base `deb3f61`).

Escritor único de gráficas. No hice push, merge ni deploy, y no edité archivos reservados (`build.py`, `contract_artifact.py`, `library.py`, `validate.py`, `build_atlas.py`, CSS editorial, `reader.js`, `chapters.js`, `review.js`, portal). El wiring está en [`docs/charts-core-wiring.patch`](docs/charts-core-wiring.patch). Lo probé aplicado en una copia aparte del repositorio.

## Resumen

1. **Núcleo pequeño, sin dependencias.** `chart-core.js` ofrece escalas 1-2-5, formato por idioma y unidad, paleta de 8 slots con patrones, tip y teclado/táctil comunes, redibujo por ancho real, leyenda que aísla series, exportación CSV/SVG y *squarify*. La documentación está en [`docs/charts-core.md`](docs/charts-core.md).
2. **Las 22 gráficas migradas** (charts, analytics, reports, evidence, attention-map). No cambian los datos ni los cálculos. A 390 px solo se desplazan cohortes y Gantt, y lo hacen de forma declarada y etiquetada. El texto SVG pasa de 10,8–21,1 px a 12 px constantes (14 px en `.pieza`; el treemap usa 18 px serif y 11,5 px mono, como la referencia). Quedan 0 rótulos «X/Y» literales y 260 marcas navegables, frente a 0 antes.
3. **El treemap** reproduce la home de cmrg.me: celdas planas, nombre serif, duración mono abreviada según el área y filas en móvil. Conserva el foco por celda, el tip con el valor completo, los botones por categoría y la tabla. Las áreas son exactas. «Otros» solo agrupa la cola invisible y mantiene su suma exacta.
4. **Tres recetas nuevas** cubren huecos reales: columnas agrupadas o apiladas, antes y después (*dumbbell*) y avance frente a meta (*bullet*). Las tres usan tablas fuente reales y declaran sus límites.
5. **Pruebas**: 10/10 de unidad del núcleo; la suite de navegador `check_charts_atlas.py` sin fallos; las suites heredadas de componentes, analítica y evidencia en verde. Los fallos que quedan en `tests_second_batch` y `tests_polish` son los mismos que en la base.

## Archivos

| Archivo | Cambio |
| --- | --- |
| `packages/core/components/chart-core.js` | **Nuevo.** `window.MargenGraficas` (API en `docs/charts-core.md`). |
| `packages/core/styles/chart-core.css` | **Nuevo.** Paleta 5–8 derivada con `light-dark()` y OKLCH, tip, foco, leyenda, exportación, heatmap y treemap v2. |
| `packages/core/components/charts.js` | Reescrito sobre el núcleo: barras (rótulo encima por debajo de 480 px), líneas, temporal (ticks de calendario), dispersión, distribución, calor (matriz SVG con ejes; umbrales declarados, por cuantiles o divergentes) y los tipos nuevos `columnas`, `cambio` y `meta`. |
| `packages/core/components/analytics.js` | Calendario, torta (hasta 8 categorías), áreas, caja, velas y mapas (encuadre por la caja de Colombia, sin ocupar 720 px vacíos). Rótulos de ciudad sin solapes. |
| `packages/core/components/reports.js` | Cascada y múltiplos al ancho real, con exportación (los múltiplos en un solo SVG). Conciliación, escenario y recorrido no cambian. |
| `packages/core/components/evidence.js` | Sankey, cohortes, sensibilidad, Gantt, embudo, incertidumbre y relato: los datos se leen una vez y el dibujo es responsivo, con un listener delegado. `imagen` no cambia. |
| `packages/core/components/attention-map.js` | Treemap v2 (*squarify*). La partición binaria sigue disponible con `data-atencion-modo="particion"`. |
| `packages/core/recipes/{column,dumbbell,bullet}-chart/` | **Nuevas** recetas con ejemplo, README y `component.json`. |
| `packages/core/recipes/*/component.json` (27) | `chart-core.js` antes del runtime de datos. |
| READMEs de barras, attention-map, heatmap, torta, múltiplos y cascada | Límites actualizados: sin «mínimo de 800 px», sin partición binaria y con los formatos nuevos. |
| `packages/core/recipes/index.json`, `registry/component-aliases.json`, `VERSION.json`, `scripts/editorial_metadata.py` | Alta de las tres recetas (`columnas`, `cambio`, `meta`) con `new_component.py`. El número de componentes pasa de 90 a 93. |
| `scripts/test_chart_core.mjs` | **Nuevo.** Pruebas de unidad (`node --test`). |
| `scripts/check_charts_atlas.py`, `scripts/measure_charts.py` | **Nuevos.** Prueba y medición en navegador. |
| `packages/core/charts-responsive.test.tsx`, `scripts/tests_{components,analytics,evidence,second_batch}.js` | Ajustados al ancho real. Comprueban proporciones medidas sobre los ticks del propio eje, no píxeles fijos. |
| `docs/charts-core.md`, `docs/charts-core-wiring.patch`, este informe | Documentación y wiring. |

Commits: `ffa532f` (núcleo, charts, treemap), `bd3cb91` (analytics, reports, evidence), `7ad5977` (recetas, paleta, suite), `56f5fd1` (Otros, calor, suites heredadas) y el commit final de documentación. No hay archivos generados en la rama: `artifact.css`, `registry.json`, `docs/components.md`, `examples/generated/*` y los paquetes los regenera root tras el wiring.

## Mediciones antes y después

Chromium headless con Playwright, atlas de `build_atlas.py --render` sin red. «Antes» se construye desde `deb3f61` (`/tmp/atlas-charts-before`) y «después», desde esta rama con el wiring aplicado (`/tmp/atlas-charts`). Los datos están en `measure_charts.py`.

| A 390 px | Antes | Después |
| --- | --- | --- |
| Figuras con desplazamiento horizontal | 20 de 22 | 2 de 25 (cohortes y Gantt, declarados y etiquetados) |
| Tamaño del texto SVG | 10,8–14 px | 12–14 px (treemap: 11,5 mono / 18 serif) |
| Rótulos «X»/«Y» literales | 10 | 0 |
| Marcas navegables con teclado | 0 | 260 |
| Solapes de texto | 0 | 0 |

| A 1440 px | Antes | Después |
| --- | --- | --- |
| Tamaño del texto SVG | 12–21,1 px (cohortes 21,1; sankey 17,4; analítica 17,1) | 12 px (14 en `.pieza`) |
| Desplazamiento | 0 | 0 |

Por figura, en 390 → 1440: antes, barras era la única sin desplazamiento. Ahora ninguna figura escala el texto (`viewBox` = ancho; la suite lo verifica con tolerancia del 2 %).

**Peso** (gzip -9 concatenado de los runtimes de datos más `relationship-map.js`): de 28,3 KB (90,7 KB sin comprimir) a 47,0 KB (157 KB), más 3,0 KB de CSS. Por archivo: `chart-core.js` 11,7 KB (objetivo de 8 KB no alcanzado), `charts.js` de 6,7 a 10,0 KB (incluye tres tipos nuevos y el heatmap SVG), `analytics.js` de 6,1 a 8,1 KB, `evidence.js` de 8,2 a 9,5 KB, `reports.js` de 5,1 a 5,9 KB y `attention-map.js` de 3,2 a 3,7 KB. A modo de comparación, `fonts.css` pesa 538 KB.

**Ejecución** (390 px, CPU 6×, mediana de 3): el script de carga baja de 491 a 421 ms porque las figuras de páginas ocultas ya no se dibujan al cargar. En cambio, abrir la página «Gráficas» sube de 178 a 348 ms y la de «Decisiones», de 83 a 117 ms. Ahí se dibujan 23 figuras (3 más que antes) con sus marcas. Los nodos pasan de 89.035 a 90.806. La comparación no es exacta, porque el atlas nuevo tiene 93 componentes.

## Pruebas

| Prueba | Resultado |
| --- | --- |
| `node --test scripts/test_chart_core.mjs` | 10/10: `nice` con 0, negativos, 1e12, `min=max` y no finitos; formato de 0, negativos, 1e12, `null`/sin dato, porcentajes, monedas, fechas y duraciones por idioma; ticks únicos y compactos; `squarify` exacto y sin solapes con 26 categorías y ceros; 8 colores, formas y trazos distintos; `fit`/`wrap` sin desbordar. |
| `npx vitest run packages/core/charts-responsive.test.tsx` | 2/2 |
| `check_charts_atlas.py` (Playwright) | **0 fallos.** 450 mediciones geométricas (320/390/1440 × Editorial, Catabum y Kaira en claro y oscuro × 25 figuras), 50 recorridos de teclado y tip (1440 y 390 táctil), 25 exportes, 26 tablas restauradas tras `destroy`, 9 treemaps y el heatmap 31 × 31 a 3 anchos. |
| Suites heredadas en la copia con wiring | `tests_components` 15/15, `tests_analytics` 13/13, `tests_evidence` 88/88. `tests_second_batch` 19/21 y `tests_polish` 3/8: los fallos son los mismos que en `deb3f61` (índice de búsqueda, radios de apariencia, visor) y ajenos a las gráficas. |
| `validate.py` en la copia con wiring | Pasa, con la regla de `url(#id)` del parche. |

Qué comprueba `check_charts_atlas.py`, sin usar capturas como prueba:

- No hay desbordamiento de página, y cualquier desplazamiento de figura es de calendario, cohortes o Gantt y tiene `role=region`.
- El texto mide entre 11 y 18,5 px reales, sin solapes y sin salirse del SVG. Cada rótulo del treemap queda dentro de su celda.
- Paleta: contraste ≥ 3:1 de los 8 slots sobre el papel y distancia mínima de los slots derivados. Medido en los 33 temas: contraste mínimo de 3,15:1.
- Teclado: el foco avanza con las flechas, Fin llega a la última marca, Enter escribe el estado y Escape oculta el tip. El tip queda dentro de `innerWidth` e `innerHeight` y la marca enfocada tiene `aria-describedby`.
- Táctil: un toque sobre la geometría real fija el tip dentro del viewport.
- `nota:pagina` oculta el tip.
- Un cambio de tema sin cambio de fuente no redibuja (el SVG es el mismo nodo).
- Cuatro resizes y cinco ciclos de página no añaden listeners (364 → 364 tras el calentamiento), no duplican SVG ni botones, y el SVG mide lo mismo que su caja.
- `destroy()` deja cada tabla idéntica al HTML original.
- El CSV coincide con los `data-valor` y la cabecera, y neutraliza fórmulas. El SVG es XML válido con `<title>` y `<desc>`, sin `var()`, `currentColor` ni URLs externas. Además se hace una descarga real de cada botón.
- Treemap a 320, 390 y 1440 px con 26 categorías, una distribución extrema con ceros y una uniforme: el error de área es menor de 1 px², cada área es proporcional (error < 10⁻⁶), el total pintado coincide con el de la tabla, los ceros no se pintan, ninguna categoría con un 1 % o más queda en «Otros», el lado mínimo es ≥ 10 px y hay 26 botones.
- Heatmap 31 × 31 con huecos y escala por cuantiles: 961 celdas navegables en 2D, sin desplazamiento ni solapes a 320, 390 y 1440 px.

Cómo reproducirlo tras el wiring:

```sh
python3 scripts/build_atlas.py --output-dir /tmp/atlas-charts --render
PY=/Users/angelbotto/orca/workspaces/margen/margen-lector-voz/.venv/bin/python
$PY scripts/check_charts_atlas.py /tmp/atlas-charts/atlas.html /tmp/atlas-charts/charts-check.json
$PY scripts/measure_charts.py /tmp/atlas-charts/atlas.html /tmp/atlas-charts/charts-measure.json
node --test scripts/test_chart_core.mjs && npx vitest run
```

## Treemap frente a la referencia

| Aspecto | cmrg.me (home) | Margen |
| --- | --- | --- |
| Marco | 1024 px máx., *padding* 8, trazos discontinuos con desvanecimiento | Igual (`.atencion-marco`, 64 rem, máscara lateral) |
| SVG | 1008 × 380; 320 de alto en móvil | Igual; filas por debajo de 640 px |
| Celdas | #2e2821 con trazo de 1 px #3b3229 | `--panel-2` / `--grafica-linea` (los mismos valores en Editorial oscuro; tokens del tema en los demás) |
| Texto | serif 18 y mono 11,5; «3 days, 10 hours…» → «3d…» → «Spo…» | Igual con `duration*` (`3 días, 10 horas, 36 minutos` → `3 días 10 h 36 min` → `3 días`); nombre abreviado con «…» |
| Acceso | ninguno | foco por celda, tip con el valor completo y su porcentaje, botones, estado, tabla, CSV y SVG |
| Algoritmo | rejilla de celdas | *squarify* exacto; «Otros» solo para la cola invisible |

La comparación visual con 26 aplicaciones en Editorial oscuro a 1440 y 390 px da la misma composición que la captura de referencia: Arc y ChatGPT en dos grandes bloques, Slack y Tuple a la derecha y la cola en mosaico.

## Límites y pendientes

- **El wiring sigue pendiente de root.** Sin él, `chart-core.js` y `chart-core.css` no entran en los artefactos. Los runtimes muestran entonces el error «Incluye chart-core.js…» y dejan la tabla visible. Los valores de `reports.js` y `evidence.js` vuelven a `Intl` `es-CO` sin el núcleo.
- **Generados.** Tras el wiring, root debe ejecutar `python3 scripts/build.py` y `npm run build`. `packages/react/src/components.test.tsx` espera `version.componentes` = 93, y solo pasa cuando se regeneran los paquetes.
- **El peso de `chart-core.js` (11,7 KB gzip) supera el objetivo de 8 KB.** No recorté accesibilidad ni exportación para cumplirlo.
- **Coste al abrir la página «Gráficas»** (+170 ms a CPU 6×). El dibujo diferido evita el coste en la carga, pero dibuja todas las figuras de la página al abrirla. Una mejora posible: montar por visibilidad con `IntersectionObserver` dentro de `responsive()`. Implica que `get(el).chart` no exista hasta hacer scroll, y por eso no la hice sin acordarla.
- **Colores base del tema.** En algunos temas, los slots 1–4 (generados por `themes.py` a partir de naranja, verde, rojo y azul) están cerca entre sí: en Catabum oscuro la distancia RGB es de 26,9. Los slots 5–8 no empeoran esa cercanía, y los patrones, trazos y formas distinguen las series sin color. Corregirlo es una decisión de temas, fuera de mi propiedad.
- **Capas (otro writer).** En el atlas a 1440 px, el índice «En esta página» y la cabecera interceptan clics sobre los botones de exportación de algunas figuras. La suite lo esquiva con `click()` programático. Hay que comprobarlo cuando se integre el contrato de capas.
- **Calendario, cohortes y Gantt** se desplazan cuando su mínimo legible no cabe. Los demás no lo necesitan a 320 px.
- **No implementado de las propuestas P1/P2:** serie de comparación y meta en temporal (P1-6), histograma desde valores crudos y *beeswarm*, *drill-down* jerárquico del treemap y migración de las tablas con codificación visual (`sparkline`, `totales`, `comparacion`, de `tables.js`, que no son de mi propiedad). `relationship-map.js` no tenía un defecto compartido que justificara cambiarlo.
- La validación de la torta admite ahora de 1 a 8 categorías (antes, 6), porque la paleta tiene 8 slots distintos.

## Wiring exacto que debe aplicar root

`git apply docs/charts-core-wiring.patch` (verificado con `git apply --check` sobre `deb3f61`). Contiene:

1. `scripts/contract_artifact.py`: añade `packages/core/components/chart-core.js` en `ORDER` justo antes de `charts.js`, y al principio de `ATTRS` para `data-evidencia`, `data-grafica`, `data-analitica`, `data-reporte` y `data-atencion`.
2. `scripts/build.py`: añade el bloque `("CHART CORE", chart-core.css)` a `blocks`, tras `TABLE CONTENT`. Inserta `script('…/chart-core.js')` en `template.html`, antes de `attention-map.js`, y en `report.html`, antes de `charts.js`.
3. `scripts/library.py`: añade `chart-core.js` al principio de `modules`.
4. `scripts/validate.py`: incluye `chart-core.js` en los módulos esperados de `library.html`, `template.html` y `report.html`, y acepta `url(#id)` (referencias dentro del documento a los patrones SVG) además de `data:`.
5. `scripts/test_developers_runtime_browser.py`: añade `'chart-core.js': 'MargenGraficas'`.

Después: `python3 scripts/build.py && npm run build && python3 scripts/validate.py && python3 scripts/build_atlas.py --output-dir /tmp/atlas-charts --render` y las pruebas de la sección anterior.
