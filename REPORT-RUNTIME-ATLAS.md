# Runtime del atlas — resaltado por lenguaje y trabajo por página

Task `task_96bc99afa2c8`, dispatch `ctx_9abbeba78a6a`, run `run_d4fd3704f129`. Rama `angelbotto/margen-atlas-runtime`.
Sin push ni despliegue. Mediciones de laboratorio en una sola máquina; no son datos de campo ni FPS.

## Commits

| Fuente | Generado | Contenido |
| --- | --- | --- |
| `d0e4d19` | `db912b8` | Gramáticas Prism, runtime de código, `syntax.css`, montaje diferido, `NotaPaginas` |
| `a383463` | `0d6dca1` | Three al primer uso, wiring chart-core + embeds, refresco histórico de módulos |
| `d0f7d95` | `469da30` | Envoltorios anidados (`mark`⊃`a`, `a`⊃`mark`) y salto final |
| `e47df5d` | `69df656` | `pendientes()` (en curso) separado de `esperando()` (ocultos) |

## 1. Resaltado por lenguaje

**Decisión: Prism 1.30.0 incrustado, no Shiki.** `packages/core/components/code.js` pasa a ser generado por
`scripts/build_syntax.py` (Python, sin Node ni red) a partir de:

- `packages/core/syntax/runtime.js` — runtime propio (fuente).
- `packages/core/styles/syntax.css` — colores por categoría (fuente); code.js lo inserta una vez como `style[data-margen-codigo]`.
- `packages/core/syntax/vendor/prismjs-1.30.0/` — núcleo + 19 gramáticas `.min.js` sin modificar del tarball oficial
  (`npm pack --ignore-scripts`; sha512 del registro verificado). `lock.json` fija SHA-256 por archivo y del aviso
  `licenses/prismjs-MIT.txt`; el generador se niega a construir si algo cambia. `NOTICE` y `PROVENANCE.md` actualizados.

Lenguajes: markup (HTML/XML/SVG, con `<style>`/`<script>` embebidos), css, clike, javascript, typescript, jsx, tsx,
json, python, bash, sql, c, cpp, markdown, yaml, diff, rust, go, perl, más `salida` (estados y cifras de terminal).
Cubre todos los de la referencia (`ts,tsx,json,css,sh,py,cpp,perl,text`). Desconocido → texto plano con su nombre original.

Cómo funciona: Prism corre en su propio ámbito (sin `window`, `document`, `module` ni `global`; `manual`), solo
tokeniza (`before/after-tokenize` incluidos, necesarios para JSX). El DOM se construye con nodos de texto y
`createElement`, nunca con HTML del tokenizador. El texto del bloque (`textContent`) es la fuente: si la suma de
tokens no coincide, se muestra sin color. Envoltorios del autor (`mark`, `.subra`, `.tenue`, `a`, `strong`, `em`…)
se conservan como cadena completa sobre los tokens, partidos por línea. Escapes (`\n`, `\x41`, `\u{…}`) dentro de
cadenas se marcan aparte (no en SQL/HTML/YAML ni en raw strings de Python).

Clases: se mantienen las antiguas (`kw`, `str`, `com`, `codigo-numero`, `codigo-funcion`, `codigo-atributo`,
`codigo-alerta`) para temas y copias históricas, y se añaden `codigo-etiqueta`, `codigo-puntuacion`,
`codigo-escape`, `codigo-regex`, `codigo-variable`, `codigo-insertado`, `codigo-eliminado`. Cada categoría es una
variable `--codigo-*` resuelta por bloque contra la paleta (`--naranja`, `--verde`, `--azul`, `--rojo`, `--tinta-*`,
`--sintaxis-numero`): cambiar tema o modo no vuelve a tokenizar (el nodo sigue conectado en la prueba).
Contraste medido en las **32 paletas** (16 familias × claro/oscuro) contra el fondo real del `pre`: mínimo **5,14:1**.

Conservado: `mark`/`.subra`, `data-destacar` (tinte + borde), etiqueta de lenguaje o `data-nombre-archivo`, figcaption,
copia exacta (botón y selección), tabs, CR sueltos, unicode astral, números 1–1000 con gutter `--codigo-cifras` fuera
del texto copiado, `NotaCodigo.init(root)` idempotente. Nuevo: `data-atenuar` (opcional, explícito) quita color a las
líneas no destacadas usando el color de comentario, sin bajar de 4,5:1; fade lateral según el desplazamiento real
(`data-desborde="inicio|fin"`, un oyente de scroll en captura para todo el documento), sin máscara con foco de teclado,
colores forzados ni impresión. Un salto final ya no abre una línea **numerada**; queda una fila final sin número
porque Chromium omite el salto al copiar una selección si no hay una caja después (medido en ambos motores).

### Diferencias reales con Shiki (la referencia)

- Shiki usa gramáticas TextMate con scopes finos (`variable.parameter`, `entity.name.function`, `support.type`…);
  Prism usa expresiones regulares más gruesas: muchos identificadores quedan como texto (`total`, `n`), heurísticas
  como `P` en TS se ven como constante y no hay distinción de parámetros fuera de algunas gramáticas.
- Shiki tokeniza en el build (cero coste en el lector); aquí se tokeniza en el navegador. Coste medido abajo.
- Shiki pinta temas concretos (`github-light-high-contrast`/`quietude`) con `--shiki-*` por token; Margen deriva los
  colores de la paleta elegida (32 combinaciones) con 13 categorías. No es igual pixel a pixel, a propósito.
- Bloques de código dentro de Markdown no se colorean por su lenguaje (eso usa el hook `wrap` de Prism, que aquí no se usa).
- Escapes: Shiki los reconoce por gramática; aquí es un post-proceso sobre tokens de cadena (aproximación documentada).
- Tamaño: un bundle Shiki con motor Oniguruma/WASM y estas gramáticas cuesta cientos de KB; Prism núcleo + 19
  gramáticas son 52 KB min. code.js total: **73,9 KB → 74,5 KB / 26,9 KB gzip** (antes 8,7 KB / 3,7 KB). Va en todos
  los documentos (CORE): +66 KB raw, +23 KB gzip por artefacto.

## 2. Trabajo por página

- **Código:** solo se colorea lo activo. Un bloque dentro de `[hidden]` (capítulo o pestaña), `template` o `details`
  cerrado espera; se despierta con `MutationObserver` limitado a `hidden`/`open`, `toggle` en captura, `nota:pagina` y un
  `IntersectionObserver` (600 px). Lo visible y pequeño (<12.000 caracteres) se colorea durante `init` con presupuesto
  de 24 ms (sin saltos de maquetación al cargar); lo grande, por tramos de 8 ms. Más de 150.000 caracteres: sin color y
  con aviso; más de 20.000 líneas: ni color ni números. `beforeprint` colorea todo. El observer no reacciona a sus
  propios tokens (no escribe `hidden`/`open`) y vuelve en seguida si no hay pendientes.
  `NotaCodigo.pendientes()` = trabajo en curso; `esperando()` = bloques ocultos.
- **Tokenización síncrona:** Prism no es interrumpible; solo la construcción del DOM va por tramos. Ver «Entradas patológicas».
- **API para otros módulos:** `window.NotaPaginas.visible(el)` y `actual()` en `chapters.js`, más el evento existente
  `nota:pagina`. Chart-core ya difiere por ancho/hidden; no cambié datos ni cálculos de gráficas.
- **Three:** ya no es `<script src>` bloqueante en el contrato. `globe.js`, `scene.js` y `fleet.js` comparten
  `window.NotaTres(el)`: espera a que la figura se acerque a la vista (400 px), inserta Three 0.160.1 una sola vez con
  SRI (`sha512-vnmn…`, verificado contra cdnjs) y `crossorigin`, y sin red cae al respaldo legible que ya existía. No se
  vendoriza (670 KB). Los documentos viejos con la etiqueta síncrona siguen validando.
- **Audio:** `audio.js` (sonidos base64) pesa 213.663 B / 146.183 B gzip y está en CORE: es el mayor coste fijo por
  documento después de las fuentes. No lo cambié (los sonidos fueron pedidos); queda medido.

Deep links a IDs nunca visitados, historial, recarga con hash, `details` abiertos por el destino, impresión y lectura
sin JavaScript siguen a cargo de `chapters.js`/`reader.js`; el atlas lo comprueba (abajo).

## 3. Refresco de históricos

`reader_style.refresh_editorial_reference(content, css, code, pieces, runtime=None)`; `build.py` genera
`portal/static/runtime-refresh.json` con `chapters`, `prototype` (87c5c84), `chart-core`, `charts`, `analytics`,
`reports`, `evidence`, `attention-map`, `geography`, `globe`, `scene`, `fleet` y el CSS de chart-core. Solo se
reemplazan `<script data-nota-modulo>` reales (no `src`, ni `template`/`noscript`, ni módulos propios). Un módulo
requerido que falta (chart-core) se inserta una vez, justo antes del primer módulo refrescado que lo necesita.
Prueba HTMLParser en `portal/test_reader_style.py` (16/16). Root acepta el 5º argumento en `portal/app.py`.

Prueba real: el atlas renderizado en `7e238af` pasado por el refresco y abierto sin red, Chromium y WebKit: estilo de
código insertado 1 vez, chart-core insertado 1 vez, 18 gráficas dibujadas en la página de gráficas, 0 errores de
gráfica, 1.000 líneas coloreadas, 0 errores de página.

## 4. Wiring aplicado

`docs/charts-core-wiring.patch` (ORDER/ATTRS, bloque CHART CORE, library/validate `url(#id)`, globals de developers) y
embeds (ORDER tras editorial-pieces, `ATTRS['data-embed']`, bloque EMBEDS, listas de library/validate, global
`MargenEmbeds`). `scripts/package.py` incluye `packages/core/syntax`. No apliqué el parche final de embeds
(`tests/evidence/atlas-embeds-impl-2026-10-22/wiring.patch`, validación estricta de href/img): root integra desde main.

## Mediciones

Fixture idéntico: las mismas 10 páginas fuente del atlas (98 recetas + 1.000 líneas; hash de fuentes igual) renderizadas
dos veces desde esta rama. **Base** = mismo árbol con `code/chapters/globe/scene/fleet.js` de main `fcdaf2f` y la
etiqueta síncrona de Three; **candidato** = esta rama. 3 cargas frías por configuración (contexto nuevo), servidas desde
127.0.0.1, todo lo demás abortado. Medianas. Arnés: `tests/evidence/atlas-runtime-2026-10-22/measure_atlas.py`;
datos crudos: `measurements.json`. Un intento anterior se colgó por un error del arnés (esperaba `pendientes()==0`
contando bloques ocultos) y se descartó; un tramo de la segunda pasada coincidió con pruebas de navegador en paralelo,
así que las diferencias de pocos ms no son concluyentes.

Bytes: base 2.322.301 B / 968.485 gzip → candidato 2.393.107 B / 993.251 gzip (+70,8 KB, +24,8 KB gzip; casi todo Prism).

| Motor · ancho · CPU | Nodos tras `load` | Líneas de código creadas | `load` ms | Tareas largas (suma / máx ms) | Abrir el `details` de 1.000 líneas hasta reposo, ms |
| --- | --- | --- | --- | --- | --- |
| Chromium 1440 ×1 | 35.699 → **7.364** | 1.063 → 0 | 164 → 131 | 0 → 0 | 20 → 21 |
| Chromium 390 ×1 | 35.696 → **7.361** | 1.063 → 0 | 154 → 124 | 0 → 0 | 20 → 144 |
| Chromium 320 ×1 | 35.696 → 7.361 | 1.063 → 0 | 155 → 125 | 0 → 0 | 23 → 131 |
| Chromium 1440 ×4 | 35.699 → 7.364 | 1.063 → 0 | 690 → **553** | 3 → 2 (262 / 117 → 133 / 77) | 26 → 369 |
| Chromium 390 ×4 | 35.696 → 7.361 | 1.063 → 0 | 654 → **539** | 3 → 2 (256 / 116 → 130 / 76) | 25 → 59 |
| WebKit 1440 | 35.699 → 7.364 | 1.063 → 0 | 234 → 204 | sin API longtask | 30 → 143 |
| WebKit 390 | 35.696 → 7.361 | 1.063 → 0 | 224 → 205 | sin API longtask | 30 → 194 |
| WebKit 320 | 35.696 → 7.361 | 1.063 → 0 | 231 → 204 | sin API longtask | 25 → 199 |

Lectura honesta:
- Lo que baja es el trabajo inicial: −79 % de nodos y ninguna línea de código construida al cargar; con CPU ×4,
  −20 % en `load` y una tarea larga menos. Las dos que quedan (77 ms máx.) no son de código.
- El trabajo **se traslada** a cuando el lector abre algo: abrir el bloque de 1.000 líneas pasa de ~20 ms (ya hecho al
  cargar) a 59–369 ms hasta el reposo, repartido en tramos de 8 ms (no una tarea única). Es el precio elegido.
- Navegación entre capítulos: ~55–70 ms por clic en ambos builds (dos frames incluidos); sin diferencia apreciable.
- Oyentes registrados al cargar: 1.041 → 1.045. Heap JS en Chromium sin cambio apreciable en la API disponible
  (`performance.memory` redondea; no lo uso como evidencia). Nodos al final del recorrido: 37.698 → 21.368.
- Red sin conexión: en ambos solo se intenta Three, y en el candidato solo cuando se visita la página con 3D. 0 errores.

### Entradas patológicas bajo el tope de 150.000 caracteres

`probe_pathological.py`, `NotaCodigo.tokens` (síncrono) y construcción completa forzada (`{inmediato:true}`, sin tramos):

| Entrada | Caracteres | Tokenizar Chromium / WebKit ms | Construcción completa forzada Chromium / WebKit ms | Copia exacta |
| --- | --- | --- | --- | --- |
| JS una sola línea | 78.301 | 16 / 16 | 161 / 232 | sí |
| JS con muchos escapes | 149.000 | 12 / 14 | 394 / 610 | sí |
| HTML anidado sin cerrar | 135.000 | 30 / 23 | 260 / 419 | sí |
| Plantilla JS sin cerrar | 145.001 | 19 / 34 | 477 / 679 | sí |
| Markdown | 125.000 | 43 / **59** | 281 / 583 | sí |

La tokenización sola llega a 59 ms en WebKit (tarea larga) para Markdown cerca del tope; no puedo afirmar «sin tareas
largas» para cualquier entrada. En el camino normal la construcción va por tramos; la forzada solo la usan pruebas e impresión.

## Pruebas

Nuevas: `scripts/test_code_syntax.py` (8 casos; Chromium y WebKit OK; con el code.js de main fallan 5/7 de los
originales y el de anidados falla con el runtime anterior), `scripts/test_deferred_runtime.py` (Three diferido y
respaldo sin red; ambos motores), caso nuevo en `portal/test_reader_style.py`.
Ajustadas, sin debilitar lo verificado: `test_editorial_atlas` espera a que el bloque de 1.000 líneas termine sus tramos;
`test_contract` exige que Three no sea etiqueta bloqueante; `portal/test_developers.py` refleja chart-core antes de
charts/analytics con hash por script.
Pasan: contract, release, portability, automatic_updates, public_assets, validate, editorial_reference, editorial_atlas,
editorial_web, prototype_resize (ambos motores), portal 209 en main según root.

Fallas conocidas fuera de mi alcance (aparecen al registrar las 98 recetas): `test_editorial_flow` en `dated-header`
(root lo corrigió en `88b2ed9`) y `test_developers_runtime_browser`: `youtube` desborda 119 px a 300 y 44 px a 375 en
la vista previa de developers (embeds/root). Portabilidad en Windows: root investiga autocrlf vs hashes de Prism
(sugerencia: `.gitattributes` con `packages/core/syntax/vendor/** -text`).

## Pendiente

- CI: añadir `test_code_syntax.py` y `test_deferred_runtime.py` (Chromium + WebKit) — lo dejo a root.
- La tokenización de un bloque es síncrona: un bloque muy grande pero bajo el tope sí puede producir una tarea larga.
