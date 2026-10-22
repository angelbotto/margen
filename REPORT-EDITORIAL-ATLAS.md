# Informe: fidelidad editorial compartida para el atlas — 22 de octubre de 2026

Run `run_d4fd3704f129`, task `task_cfe19fb4cad5`, base `7d2135e`. Escritor único de la interfaz editorial en `margen-atlas-editorial`. No hice push, merge, despliegue ni cambios en producción. Tampoco abrí ni modifiqué la muestra publicada `2104ce89…`.

## Resultado

El índice fijo ya no se pinta encima de ninguna superficie ancha. El arreglo es del sistema compartido, no del atlas, y llega a los artefactos históricos por el refresco del portal (`refresh_editorial_reference`), porque solo cambia `editorial-reference.css` y `editorial-pieces.js`.

| Medición (atlas completo, 10 páginas, todos los `details` abiertos) | Antes (`7d2135e`) | Después |
| --- | --- | --- |
| 1440 oscuro: puntos de texto del índice dentro de superficies / con el índice encima | 931 / **737** | 933 / **0** |
| 1440 claro | 930 / 737 | 933 / 0 |
| 1280 oscuro | 1471 / **1002** | 1474 / **0** |
| 1280 claro | 1483 / 1011 | 1474 / 0 |
| Galería y `details` de 1000 líneas abierto con Enter, 1440/1280 × Editorial oscuro/claro, Catabum oscuro, Kaira claro (16 casos): puntos con el índice encima | 172 / 172 | 172 / **0** |
| Ídem, píxeles decodificados que cambian al ocultar el índice en la zona de solape | hasta 10,2 % | **0 %** en los 16 |
| Artefacto histórico (`atlas.html` de la base) pasado por `refresh_editorial_reference` | — | 0/18 galería, 0/3 `details`, 0 % píxeles |
| 390 / 320: ancho de scroll máximo en las 10 páginas | 390 / 320 | 390 / 320; índice estático |

Las 159 superficies anchas por anchura y modo se recorrieron una a una. El último residuo, 2 puntos a 1280, era un punto de muestreo exactamente en el borde inferior (`y = 545,0` sobre un `details` que termina en 545,0). El barrido final excluye el píxel de borde.

## Qué cambió

**Capas** (`packages/core/styles/editorial-reference.css`, fuera de `@scope`):
- A partir de 1280 px y solo en pantalla, cada `.ancho`, `.amplio`, `.marco-difuso` o `.marco-punteado` externo, más `.paginacion` y `.pie`, pasa a `position:relative; z-index:3` con fondo de papel opaco. El índice sigue en z 2.
- Un halo lateral de papel (sombra exterior solo a los lados) hace que el índice se desvanezca en el borde en vez de cortarse a mitad de palabra.
- El código sigue translúcido con `blur(12px)`. Ese blur se quita cuando el código está dentro de una superficie ya opaca: no cambia ningún píxel y, con los bordes de lectura, duplicaba el tiempo de frame.
- Las reglas usan `:where()` y quedan fuera del scope. Así alcanzan también composiciones `data-ritmo="propio"` y el explorador de datos, cuyo `data-presentation="auto"` de runtime coincidía con la frontera de diapositivas y lo dejaba fuera. El fondo y el posicionamiento propios de un componente siguen mandando.
- El índice enfocado sube a z 4 con papel; esa regla ya existía y la prueba se mantiene.
- Una superficie enfocada, o con `.control-menu[open]`, también sube a z 4, para que sus paneles no queden atrapados bajo la superficie siguiente. Solo un elemento tiene el foco a la vez, así que esto no compite con el índice.
- No hay `overflow:hidden` global y el índice no se oculta.

**Índice:**
- El tachado de secciones leídas funciona en capítulos (`.aqui-visto`). Un problema de especificidad lo anulaba (se ve en la captura de base de root). En documentos (`.visto`) ya funcionaba y ahora comparte el mismo estilo.
- Las entradas leídas y los números se muestran a media intensidad.
- Transición de 320 ms con `cubic-bezier(.645,.045,.355,1)`, desactivada con movimiento reducido.
- Activo y hover usan un tono intermedio. Los enlaces llevan la sombra medida y un foco con contorno discontinuo de 2 px.
- Todo es CSS, así que llega a los históricos. `chapters.js` y `reader.js` no se tocaron.

**Bordes de lectura** (`editorial-pieces.js` + CSS):
- Cuatro capas fijas por borde, con blur de 1/2/4/8 px, cada una enmascarada desde un cuarto posterior de `clamp(40px,10vh,160px)`.
- Quedan bajo la barra, la regla y el dock, sin eventos de puntero.
- Se eliminan con transparencia reducida, colores forzados e impresión. No aparecen en presentaciones.

**Galería:** el fade de borde se actualiza en el siguiente `requestAnimationFrame`; antes esperaba el debounce de 90 ms del estado. Revela papel, no el índice. Sombras y degradados medidos sin cambios.

**Callout esquina:** fondo radial con hueco de 16 px para el icono, barra de 3 px desde 15 px y título en peso 600 con el acento al 80 %. Sin fondo en impresión y con borde en colores forzados.

**Código, solo CSS de rango:** línea destacada con tinte del 6 %, regla de 1 px y número en acento; halo en `mark`; color de `::selection`. No toqué `code.js`.

**Generador** (`scripts/contract_artifact.py`, `scripts/create_artifact.py`):
- `date`: `AAAA-MM-DD` o `{"published","updated"}`, también por página, más `--date`. Se valida el calendario y el orden. Se muestra con `<time datetime>` bajo el h1. Nunca se infiere una fecha.
- `footer`: `author`, `note`, hasta 8 `links` con `label`/`href`/`detail` y `platform`. Solo acepta `https://` sin credenciales o `mailto:` con dirección. Todo el texto se escapa y los enlaces llevan `rel="noopener noreferrer"`. La línea «Hecho con Margen» es aparte y opcional. Sin `footer`, la salida anterior queda idéntica. En ningún artefacto aparecen las redes de Ángel ni las de nadie por defecto.
- `reactions`: tres botones con iconos de trazo 1,6 / 18 px, como el resto del lector. Se guardan solo en ese navegador, sin conteos, y el componente lo dice. No se imprimen.

**Documentación:** `docs/editorial-reference.md` (pase del 22 de octubre, diferencias deliberadas, tipografía) y `docs/document-formats.md` (opciones).

## Pruebas

| Comando (Python de Playwright de `margen-lector-voz/.venv`) | Resultado |
| --- | --- |
| `scripts/test_editorial_atlas.py` (nueva, 13 pruebas) | OK, estable en ejecuciones repetidas |
| `scripts/test_editorial_reference.py` | OK (12) |
| `scripts/test_editorial_flow.py` | OK (5) |
| `scripts/test_editorial_web.py` | OK (5) |
| `scripts/test_contract.py` | OK (10) |
| `python -m unittest portal.test_reader_style portal.test_app` | OK |
| `scripts/validate.py` | exit 0 |
| Mutación: la nueva prueba con la capa anulada por CSS | 41 fallos (detecta el defecto) |

Qué cubre `test_editorial_atlas.py`:
- Galería, `details` de 120 líneas abierto con Enter, tabla, bloque `data-ritmo="propio"` y vista con `data-presentation="auto"`.
- 1440 y 1280, en Editorial oscuro/claro, Catabum oscuro y Kaira claro.
- Hit testing y diff de píxeles decodificados (< 1 %).
- El fade de la galería revela papel en el mismo frame.
- Foco del índice: z 4, gana el hit test y conserva el orden de tabulación.
- Hover sobre la zona cubierta va a la superficie.
- Táctil a 390/320 (tap navega) y tap sobre la zona cubierta (no activa el índice).
- 1000 líneas: 22 px por línea, número sin salto y copia exacta.
- 120 líneas: copia exacta.
- Tachado en documento y capítulos; movimiento reducido.
- Bandas: 8 capas, sin puntero, texto debajo seleccionable; eliminadas con transparencia reducida y en impresión; ausentes en presentaciones.
- Fecha, pie (escape, enlaces y desenfoque que se quita al enfocar), reacciones locales (persisten al recargar, sin dígitos).
- Validación de fechas, URLs y textos, y CLI de punta a punta.

Ajuste de una prueba existente: en `test_code_blur_is_rendered_over_index`, la espera tras el scroll pasa de 80 a 400 ms y queda comentada. Con la transición de 320 ms del índice, la captura de 80 ms se tomaba a mitad de transición: 0,038–0,05 en vez de 0,108 en estado estable. El umbral (≥ 0,05) no cambió.

**No ejecutadas o fallos ajenos:**
- `check_editorial.py` y `check_pieces_editorial.py` necesitan una pestaña del navegador de Orca (`browser_no_tab`).
- `check_chapters.py` necesita `pypdf`.
- Ejecuté `tests_pieces_editorial.js` con Playwright sobre `priorities.html`: 3/4 OK. El caso «marcos» espera `dotted` y falla igual en `HEAD`, porque el CSS de octubre usa `dashed`. Es preexistente y no lo cambié.
- No corrí `npm run check`; root ya verificó el build React/composer.

## Rendimiento

Script: `perf.py`, en Chromium headless con render por software. Mide 240 frames con `scrollBy(12)` por rAF, mediana de 3 ejecuciones, a 1440.

| Caso | Antes: mediana / p95 / máx (ms) | Después |
| --- | --- | --- |
| Galería | 16,7 / 16,8 / 16,8 | 16,7 / 16,8 / 33,3 |
| `details` con 1000 líneas abierto | 16,7 / 16,8 / 16,8 | 16,7 / 16,8 / 33,4 |

En ningún caso hubo tareas largas. La primera versión de las bandas, combinada con el blur del `pre` anidado, llevó el caso de 1000 líneas a 33 ms de mediana. Quitar ese blur redundante devolvió 16,7 ms. Queda un frame aislado de 33 ms por ejecución.

Por evento solo se hacen dos cosas: escribir dos propiedades por rAF en la galería mientras se desplaza y el cálculo existente del índice. Las bandas son CSS estático. Son mediciones de laboratorio en render por software, no de campo; en GPU real el coste del blur es distinto.

## Diferencias deliberadas y límites

- **Punto de corte 1328 y máscara superior anclada al artículo: no adoptados.** Con la máscara, el índice queda casi invisible al cargar y nunca llega a opacidad plena en páginas con menos de ~768 px de scroll, lo que esconde la navegación en capítulos cortos. La superposición se resuelve con capas, no ocultando. Las pruebas existentes fijan el índice visible a 1280 (328 px). Si root prefiere 1328, el cambio es de una regla, pero requiere actualizar esas pruebas.
- **Tachado:** es una línea tipográfica de 2 px, no el trazo a mano de rough-notation.
- **Tipografía:**
  - La serif original es Editorial New, comercial y no distribuida. Margen usa Instrument Serif (OFL), así que forma de glifos, anchos y cortes de línea de títulos difieren de forma medible. No se afirma igualdad del 100 %.
  - Geist y Geist Mono coinciden y van con OFL.
  - Departure Mono no se incluye: Margen no muestra conteos.
  - El tracking −0,025 em y el h2 móvil de 28,5/38 px se midieron con Editorial New y no los apliqué a Instrument Serif.
- **Cabecera:** Margen conserva la barra de capítulos visible; no la oculta al bajar como el header del sitio de referencia.
- **Código:** sin fade horizontal, porque una máscara en el scroller también desvanecería el blur. El resaltado sintáctico sigue siendo del siguiente escritor (`code.js`).
- **Superficies de texto:** el material es opaco, no translúcido con blur; la auditoría admite ambas opciones para `details`. Al cruzar, el índice queda tapado mientras la superficie pasa; vuelve a ser legible y operable al enfocarlo.
- **Trazos de marco:** las líneas que salen 64 px fuera de una superficie pertenecen a su capa y cruzan el índice, igual que en la referencia.

## Evidencia privada

`~/.local/share/margen-review/atlas-editorial-20261022/`. No subí capturas al repositorio.
- `before/` y `after/`: 16 casos con `results.json` y capturas.
- `sweep-before.txt` y `sweep-after.txt`.
- `perf.txt`.
- `visual-*`: fecha, callout y pie a 1440 en claro/oscuro y a 390.
- Scripts `atlas_check.py`, `sweep.py` y `perf.py`, que reciben la URL de un atlas renderizado con `scripts/build_atlas.py --render` y servido localmente.

## Para root

- Commits: fuentes, pruebas y documentación por un lado; generados por otro (`artifact.css`, `portal/static/*`, `portal/developers-*`, `examples/generated/*`). Root regenera al converger.
- `scripts/build_atlas.py` es de root. Para mostrar fecha y pie configurado en el atlas, pasa `date`, `footer` y, si se quiere, `reactions` a `build()`.
- La tarea de lazy init puede tocar `chapters.js`: esta entrega no lo modificó.
