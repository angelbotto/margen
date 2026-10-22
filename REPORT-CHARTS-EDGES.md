# Gráficas: casos límite del atlas (D2, D3, D6)

22 de octubre de 2026 · task `task_d11669c262b3` · rama `angelbotto/margen-atlas-chart-edges` (base `8517f52`).

Solo toqué `charts.js`, `chart-core.js`, una prueba nueva y `docs/charts-core.md`. No edité capítulos, runtime de sintaxis, generadores, portal, CSS global ni `reports.js`, y no regeneré artefactos. No hice push, merge ni deploy.

## Qué cambió

| Defecto | Antes | Ahora |
| --- | --- | --- |
| **D2** calor constante o todo en cero | Todas las celdas en `--calor-4` y leyenda «0 a 1» / «5 a 6» | Un solo nivel neutro: `--calor-0` si todo vale 0, `--calor-2` en otro caso. La leyenda dice «Todas las celdas: 0 · sin variación» y el tip, «Sin variación». La tabla (`data-nivel`) usa el mismo índice que la figura. |
| D2 (relacionado) cuantiles con dos cortes (muchos ceros y un pico) | Ceros y pico salían los dos en `--calor-4` | El máximo forma su propio nivel. Los ceros quedan en `--calor-0` y la leyenda dice «0 a menos de 5» y «5». |
| **D3** meta con valor negativo | Dominio desde 0 y barra de 0,5 px | Dominio con signo (`min(0, …)`). La barra va del 0 al valor en su dirección: −12 frente a 30 mide exactamente 12/30. Los umbrales siguen siendo no negativos y crecientes. |
| **D6** líneas con todos los valores en 0 | Eje de −1 a 1 | Si el único valor es ≥ 0, el eje empieza en 0 (`[0, v || 1]`, sin relleno). |
| **D6** calor de 26 columnas a 320 px | 3 elementos fuera del SVG | Si la celda de 8 px no cabe, primero cede el rótulo de fila (mínimo 40 px, con «…»). 26 columnas caben sin desplazamiento. Si aun así no cabe (31 columnas con rótulo largo), el SVG conserva su ancho y `.grafica-caja` se desplaza con `role=region`, `tabindex=0` y «…, desplazable horizontalmente». Usa `.mg-desplazable`, que `chart-core.css` ya define. |
| **D6** SVG exportado | Sin leyenda ni nombres de serie; `aria-label` con «flechas para recorrer…» | `legendOf(figura)` lee la leyenda visible (series y niveles de calor) y `standaloneSvg` la dibuja bajo la gráfica, con colores resueltos, y la nombra en `<desc>`. La raíz lleva `role="img"` y `aria-label` = título. Las columnas apiladas de tres series ya se entienden fuera de la página. |

Conservé `oklch()` en los exportes: convertir colores ampliaba el alcance, y la revisión ya comprobó que se pintan en Chromium y WebKit.

## Pruebas

| Prueba | Resultado |
| --- | --- |
| `review/atlas-ui-runtime/test_defects.py`, las 3 de gráficas (`heatmap_all_zero…`, `heatmap_legend…`, `bullet_negative…`) | **Pasan** en Chromium y WebKit. Las otras 4 (D1, D4, D5) son de root y del worker de código, y siguen fallando como se esperaba. |
| `scripts/test_chart_edges.py` (**nueva**, Playwright, sin red) | **2/2**. Matriz: Chromium y WebKit × 320 y 1440 px × claro y oscuro (16 subcasos). Comprueba calor todo en 0, constante 5 y dos cortes; meta negativa (proporción y anclaje en el 0) y meta con valor y meta negativos; líneas en 0; calor de 26 y 31 columnas (nada fuera del SVG, región desplazable solo cuando hace falta); ningún desbordamiento de página ni `pageerror`; y una descarga real del SVG de columnas apiladas, que se abre sola en una página en blanco con 3 nombres de serie dentro del lienzo, 3 colores distintos, sin `var()`, sin URLs y sin instrucciones de teclado. |
| La misma prueba con `charts.js` y `chart-core.js` de `8517f52` | Falla 8/8 subcasos en Chromium, como debe. |
| `node --test scripts/test_chart_core.mjs` | 10/10 |
| `vitest run packages/core/charts-responsive.test.tsx` | 2/2 |

No corrí la matriz completa de 450 geometrías (`check_charts_atlas.py`). Según el brief, la corre root/CI tras integrar.

## Pendiente para root

- **Regenerar los artefactos.** `validate.py` falla ahora con «módulo desactualizado: chart-core.js» en `examples/generated/library.html`, porque los generados incrustan las fuentes. Se resuelve con `python3 scripts/build.py && npm run build`. Después, `check_charts_atlas.py` sobre el atlas renderizado.
- El README de la receta `bullet-chart` no menciona los negativos. No lo toqué para no desincronizar `docs/components.md`, que es un archivo generado. Frase sugerida: «Values and targets may be negative; the axis extends below zero. Thresholds stay non-negative.»
- Las leyendas de `analytics.js`, `evidence.js` y `reports.js` no usan `.mg-leyenda` ni `.calor-leyenda`, así que sus exportes siguen sin leyenda (`legendOf` devuelve `[]` y el archivo sale igual que antes, pero con `role=img` y sin instrucciones de teclado). No hacía falta tocar `analytics.js` para D2, D3 y D6.
