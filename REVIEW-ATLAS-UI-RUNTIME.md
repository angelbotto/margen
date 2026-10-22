# Revisión independiente: sistema editorial, gráficas y resaltado/runtime del atlas

Revisor independiente, 22 de octubre de 2026. Run `run_d4fd3704f129`, tarea `task_6f01971f0bb2`. Solo lectura del producto: no se modificó código, no hubo merge, push ni deploy. Pruebas y sondas en `review/atlas-ui-runtime/`; capturas, exportes y JSON completos en `~/.local/share/margen-review/atlas-ui-runtime-independent-20261022/` (privado).

## Bases exactas

| Estado | Commit | Cómo se obtuvo |
|---|---|---|
| Producción | `d61743a` | `git archive d61743a` |
| Rama revisada (checkpoint de resaltado integrado) | `b6bef04` (incluye `37a88b1`, `357b8bc`) | este worktree |
| Delta posterior del writer (Three diferido, wiring, refresco histórico) | `angelbotto/margen-atlas-main` @ `7c59dc6` (incluye `6103422`, `30f65aa`) | `git archive`, sin tocar este worktree |

Atlas renderizado en cada estado con `scripts/build_atlas.py --output-dir … --render` (98 componentes, 10 páginas). Navegadores: Chromium y WebKit de Playwright, sin red salvo indicación; Three se sirvió desde una copia local cuyo SHA‑512 coincide con el SRI fijado.

## Resultado

El delta `7c59dc6` corrige el único bloqueo encontrado en `b6bef04`. Quedan siete defectos reproducibles en ambos motores, ninguno bloqueante para el atlas tal como está, pero todos en código compartido que reciben los demás documentos. Los checkers existentes no los detectan. El más visible para un lector es el índice, que marca como actual la sección anterior a la que se acaba de abrir.

`review/atlas-ui-runtime/test_defects.py` codifica el comportamiento esperado. En `7c59dc6` falla 7/7 en Chromium y 7/7 en WebKit. Sirve como prueba de antes y después. No hay «después» porque no corregí nada.

## Hallazgos

### B1. En `b6bef04` no se dibuja ninguna gráfica del contrato (corregido en `7c59dc6`)

- **Reproducción:** `build_atlas.py --render` sobre `b6bef04` y después `probe_chart_errors.py atlas.html chromium`. Da `typeof MargenGraficas === 'undefined'`, 21 de 23 figuras con error en Gráficas y 3 más en Lectura y Decisiones. Cada una muestra «No se pudo dibujar: Incluye packages/core/components/chart-core.js…».
- **Causa:** `contract_artifact.py` (ORDER/ATTRS) y `artifact.css` (bloque CHART CORE) no incluían el núcleo. El cableado solo existía en `docs/charts-core-wiring.patch`.
- **Lo que preocupa más:** con las gráficas rotas siguen pasando `test_editorial_atlas`, `test_editorial_reference`, `test_code_syntax` (Chromium y WebKit), `test_prototype_resize` y `check_component_atlas.py --full` (406 comprobaciones, `passed: true`). Solo `check_charts_atlas.py` falla, y lo hace con una excepción, no con un diagnóstico. **Ninguna puerta del atlas comprueba que las figuras se hayan dibujado.** Recomiendo que `check_component_atlas` exija cero `.grafica-error/.evidencia-error` y al menos un `svg.mg-svg` por figura de datos.
- **En `7c59dc6`:** 30 figuras, 0 errores. Pasan `check_charts_atlas` (450 geometrías, 50 interacciones, 25 exportes, idempotencia de 377 listeners) y `check_component_atlas --full --browser webkit` (406).

### D1. El índice marca como actual la sección anterior tras un clic o un enlace profundo (media)

- **Reproducción:** a 1440 px, en Lectura, hago clic físico en «Glosario editorial» (`#receta-glosario`). El destino queda a `top = 124 px`, pero `aria-current` queda en «Referencias con regreso». Pasa lo mismo al cargar `…#receta-glosario` y en ambos motores. Sigue igual en `7c59dc6`.
- **Causa:** `chapters.js` usa `getBoundingClientRect().top <= 120`. El desplazamiento real es `scroll-padding-top: 32px` (html) más `scroll-margin-top: max(85px, var(--lectura-cabecera)) = 92px`, es decir, 124 px. El umbral debería derivarse del mismo offset. No verifiqué si el defecto ya existía en `d61743a`.
- **Prueba:** `test_index_marks_clicked_section_current`.

### D2. Un mapa de calor constante o todo en cero se pinta con la intensidad máxima e inventa un rango (media)

- **Reproducción:** `data-grafica="calor"` con todas las celdas en 0. Todas las celdas salen `var(--calor-4)` y la leyenda dice «0 a 1». Con todas en 5 dice «5 a 6».
- **Causa:** `charts.js heatScale` toma cuantiles únicos, que dan un solo límite. Entonces fuerza `[v, v + 1]` y `fill()` con `levels === 1` devuelve `--calor-4`. Un período sin actividad parece el de máxima actividad.
- **Pruebas:** `test_heatmap_all_zero_is_not_maximum_intensity` y `test_heatmap_legend_does_not_invent_range`.

### D3. En la gráfica de meta, un valor negativo se acepta pero se dibuja como 0 (media‑baja)

- **Reproducción:** `data-grafica="meta"` con NPS −12 y meta 40. El dominio empieza en 0 y la barra mide 0,5 px. El tip dice «−12 puntos · −30 % de la meta», pero la figura muestra cero.
- **Causa:** `read()` valida umbrales no negativos, pero no valor ni meta. `bullet()` usa `Math.max(.5, x(value) - x(0))`. Hay que rechazar el negativo con un mensaje o extender el dominio por debajo de 0.
- **Prueba:** `test_bullet_negative_value_is_drawn_or_rejected`.

### D4. El resaltado de código pierde el envoltorio interior cuando el autor anida dos (media‑baja)

- **Reproducción:** `<mark>// ver <a href="#s1">enlace</a></mark>` pierde el enlace (desaparecen `<a>` y `href`). `<a href><mark>…</mark></a>` pierde el `mark`. Ocurre en ambos motores y en `b6bef04` y `7c59dc6`.
- **Causa:** `syntax/runtime.js overlays()` conserva solo el ancestro OVERLAY más externo y `build()` lo clona con `cloneNode(false)`. El texto copiado sigue siendo exacto, pero se pierde una función: un enlace del autor.
- **Pruebas:** `test_code_link_inside_mark_survives` y `test_code_mark_inside_link_survives`.

### D5. Un salto de línea final crea una línea numerada vacía (baja)

- `const a = 1;\nconst b = 2;\n` con `data-lineas` produce 3 líneas y la tercera está vacía. Es habitual en código pegado o convertido desde Markdown. Ninguna receta del registro termina en `\n`.
- **Prueba:** `test_code_trailing_newline_is_not_a_numbered_line`.

### D6. Escalas y densidad en casos límite (baja)

- **Líneas con todos los valores en 0:** el eje va de −1 a 1 (`nice()` rellena de forma simétrica). Para conteos debería empezar en 0.
- **Calor con 26 columnas a 320 px:** 3 elementos quedan fuera del SVG. La celda mínima de 8 px no cabe en 272 px con el rótulo de fila.
- **Exporte SVG:**
  - los colores salen en `oklch()`. Se abren y pintan sin estilos en Chromium y WebKit (comprobado: `painted > 0`, ninguna `url()` sin resolver, ninguna URL http), pero los editores no web pueden no soportarlo;
  - el archivo no incluye leyenda ni nombres de serie, así que unas columnas apiladas de tres series quedan ambiguas fuera de la página;
  - el `aria-label` arrastra instrucciones de teclado («flechas para recorrer…»).

### D7. Ancho de código fuera de prosa (baja, visual)

La regla de 48rem solo cubre `.codigo-editorial` como hijo directo de `.pagina`, `.seccion` o `.prosa`. El código dentro de componentes (`#configuracion-ejemplo`) mide 528 px y el de los `.ancho`, 952–1024 px. La referencia usa 768 px. No bloquea.

## Lo que comprobé y está bien

- **Capas del índice a 1328 y 1440, en Chromium y WebKit, con `details` cerrados y abiertos, sobre `b6bef04` y sobre `b6bef04` con el wiring aplicado:** hice hit‑test en todas las páginas, con scroll de 450 px, de todo elemento interactivo visible que solapa el carril. Solo apareció `a.web-salto`. Es un enlace de salto desplazado fuera de vista; al darle foco con el teclado queda en pantalla y gana el hit‑test (`self`). Es un falso positivo. Ningún rótulo del índice pinta sobre contenido.
- **Medidas** (320/390/1280/1328/1440, ambos motores), iguales a la referencia:
  - prosa: 528 px, 15,5/24,025;
  - h1: 44,5/49,44 en escritorio y 36,4/43,68 en móvil;
  - h2: 36,4/43,68 en escritorio y 28,5/38 en móvil;
  - tracking −0,025em;
  - código: 13,7/22, con `blur(12px)` fuera de superficies anchas;
  - fecha en una sola línea (`22 oct 2026`, `datetime=2026-10-22`);
  - sin desbordamiento horizontal.
- **Índice:** el tachado se dibuja con un `path` por línea dentro del enlace, con `dashoffset` 0 en lo leído y sin transición con movimiento reducido. La máscara sigue el origen del artículo (`--indice-fade-y` igual a la diferencia medida en cada scroll) y desaparece con foco de teclado. A 1327 px el índice no es fijo y no hay tachado ni máscara.
- **Pie del documento:** con Tab real (Alt+Tab en WebKit), el detalle de cada enlace pierde el blur, el contorno es punteado de 2 px y el enlace queda en vista.
- **Reacciones:** un clic físico activa la reacción y sobrevive a la recarga. La clave de `localStorage` es por documento y no hay conteos compartidos.
- **Impresión:** se muestran las 10 páginas, se ocultan reacciones y bordes de lectura, y el blur del detalle es `none`.
- **Sin JavaScript:** a 390 px se ven las 10 páginas y las 9 tablas de las gráficas.
- **Código:**
  - 1000 líneas abiertas con un clic físico sobre `summary`: numeración hasta 1000, `--codigo-cifras: 4`, el número cabe en su canal (32,9 px necesarios frente a 32,9 disponibles en Chromium; 31,2 frente a 31,2 en WebKit), los rangos destacados 2–5 y 998–1000 son correctos y la copia con clic físico es exacta. En Chromium lo comprobé con el portapapeles real; en WebKit, con la escritura que pide la aplicación;
  - tabs, emoji, combinantes y CJK se conservan y la selección completa coincide con `textContent`;
  - el cambio de tema no provoca ninguna mutación DOM, así que no hay retokenizado;
  - el código en páginas ocultas y en `details` cerrados se colorea al mostrarse;
  - varios `init()` no duplican cabeceras ni botones;
  - no hay peticiones de red;
  - el contraste mínimo de tokens frente al fondo efectivo es ≥ 5,1:1 en los 6 temas.
- **Gráficas con wiring:** ceros, faltantes («Sin dato» y marcador discontinuo, nunca una barra 0), negativos en barras y columnas agrupadas, y 26 categorías en barras y columnas, a 320 y 1440 px, sin SVG escalado. Hice CSV y SVG con clic físico en todas las figuras: 46/46 descargas en WebKit. En Chromium también pasan todas si entre clics hay un ritmo humano (300 ms). Con 0 ms fallaron siempre las mismas 4, que es un artefacto del ritmo de la automatización, no del producto.
- **Three diferido (`7c59dc6`, ambos motores):**
  - ninguna petición mientras la página está oculta;
  - una sola petición en línea, con SRI verificado contra los bytes de cdnjs;
  - sin red, respaldo legible en `flota` y `escena` («La vista 3D no está disponible. La tabla conserva todos los datos.»);
  - con 3 s de latencia, hacer clic en controles durante la carga no produce `pageerror`.
  - Detalle menor: sin red se reintenta una vez por figura (7 peticiones).
- **Refresco histórico (`7c59dc6`):** generé 58 recetas de gráficas, decisiones, expresión y lectura con el contrato de `d61743a` y apliqué `refresh_editorial_reference` con `runtime-refresh.json`. Se inserta un único `chart-core`. Antes y después: 0 errores y 0 `pageerror`, sin SVG escalado a 320/390/1440 px en ambos motores.
- **Suites del root:**
  - `b6bef04`: `node --test test_chart_core.mjs`, `test_code_syntax` (Chromium/WebKit), `test_editorial_atlas`, `test_editorial_reference` y `test_prototype_resize` pasan.
  - `7c59dc6`: pasan `test_deferred_runtime` y `portal.test_reader_style` (16).
- **Rendimiento:** wheel scroll físico de 24 000 px en Gráficas, Configuración y Pruebas, con y sin movimiento reducido. 0 long tasks y ningún hueco de rAF > 50 ms en Chromium headless. Con movimiento reducido no hay animaciones activas; sin él solo quedan las transiciones del índice.

## Suficiencia de las pruebas existentes

Los conteos no sostienen las conclusiones. `check_component_atlas --full` reporta 406 comprobaciones pasadas con 24 figuras rotas. `check_charts_atlas` no cubre:

- el calor constante o en cero;
- la meta negativa;
- las líneas en cero;
- el exporte en WebKit;
- el contenido semántico del SVG exportado.

`test_code_syntax` no cubre envoltorios anidados ni el salto final. Ninguna prueba compara `aria-current` con el destino de un clic o de un hash.

## Límites reales

- **Entorno:** navegadores headless de Playwright, no Safari ni Chrome de escritorio, sin GPU real ni dispositivo táctil. El tacto lo cubre el checker del root (tap a 390 px); yo no lo repetí.
- **Teclado en WebKit:** Tab no enfoca enlaces por defecto, así que usé Alt+Tab. El portapapeles real solo lo verifiqué en Chromium.
- **«Scroll blanco»:** no lo reproduje y no se lo atribuyo a nada. Las capas `.lectura-bordes` (8 `backdrop-filter`) son la candidata obvia en GPU reales, pero sin reproducción es una hipótesis, no un hallazgo.
- **cmrg.me:** no lo volví a medir en vivo. Usé `docs/atlas-reference-audit.md`.
- **Alcance:** no revisé la rama `main` posterior a `7c59dc6` ni el contenido de medios externos (X, YouTube, Instagram), que corresponde a otra revisión.

## Cómo reproducir

```sh
PY=/Users/angelbotto/orca/workspaces/margen/margen-lector-voz/.venv/bin/python
python3 scripts/build_atlas.py --output-dir /tmp/a --render
cd review/atlas-ui-runtime
$PY probe_chart_errors.py /tmp/a/atlas.html chromium        # B1 en b6bef04
$PY probe_layering.py /tmp/a/atlas.html webkit out.json     # capas índice/superficies
$PY probe_toc.py /tmp/a/atlas.html chromium shots           # D1
$PY probe_charts.py /tmp/a/atlas.html webkit outdir         # exportes y casos límite (requiere wiring)
$PY probe_three.py /tmp/a/atlas.html webkit three.min.js    # Three diferido (7c59dc6)
python3 make_historical.py <arbol d61743a> <arbol 7c59dc6> outdir && $PY probe_chart_errors.py outdir/historical-refreshed.html webkit
MARGEN_ROOT=<arbol 7c59dc6> MARGEN_BROWSER=webkit $PY test_defects.py   # D1–D5: 7 fallos esperados hasta corregir
```
