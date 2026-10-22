# Auditoría de referencia cmrg.me para el atlas — 22 de octubre de 2026

Auditoría de diseño **en solo lectura**. Contrasta `https://www.cmrg.me` (renderizado en vivo) con Margen en la base `d61743a` (PR #47, `docs/editorial-reference.md` y `packages/core/styles/editorial-reference.css`). No se modificó producto ni build. Datos: [`tests/evidence/atlas-reference-2026-10-22/`](../tests/evidence/atlas-reference-2026-10-22/) (`inventory.json`, `measurements.json`, `margen-runtime-d61743a.json`). Las capturas de la referencia y los scripts de sonda están **solo** en el archivo privado `~/.local/share/margen-review/atlas-reference-20261022/` (346 PNG + `scripts/`); no se suben al repositorio.

## 1. Alcance real

| Qué | Cobertura comprobada |
| --- | --- |
| Descubrimiento | `sitemap.xml` (16 URL) + recorrido BFS de todos los `<a href>` de cada ruta visitada, normalizando host (`www`/`v2`/apex), query, hash y barra final. **0 rutas internas nuevas** fuera del sitemap. |
| Identidad del despliegue | `v2.cmrg.me` devolvió la misma lista de chunks `/_next/static` que `www` (diff vacío), Vercel. Se trató como el mismo despliegue; no se sustituyó. `cmrg.me` → 308 a `www`. |
| Rutas visitadas | Las 16, HTTP 200, a 1440×900 y 390×844 (capturas por viewport de desplazamiento, máximo 8 por ruta: los artículos largos quedan parcialmente cubiertos, ver `screens_covered_*` en `inventory.json`). |
| Sonda profunda | `/`, `/blog/react-19-part-2-the-code`, `/blog/programar-e-uma-merda` a **1440×900, 1280×800, 390×844 y 320×640**: estilos computados de ~50 selectores, estados del índice al inicio/medio/final, hit-testing índice↔figuras, hover/focus, cabecera tras scroll, pie. |
| Sondas específicas | Treemap (4 viewports + hover), galerías horizontales (`/work`, `/about`), medios anchos y video (4 artículos), copia de código con portapapeles, hover de enlaces/permalinks/reacciones, orden de tabulación, `prefers-reduced-motion`, `prefers-color-scheme: light`. |
| Margen runtime | Fixture sintético local construido con `scripts/contract_artifact.build` (7 secciones, código ancho, `details.ancho` cerrado y abierto con **Enter**, 120 líneas, galería de `docs/components.md`), tema editorial oscuro a 1440/1280/390/320 y claro a 1440/390. La muestra privada `2104ce89…` **no** se abrió. |

**Excluido y por qué** (también en `inventory.json → excluded`): `/api/*` y `/monitoring` (robots `Disallow`); anclas `#…` y `/shelf#…`/`/work#…` (no son páginas); `v1.cmrg.me`, `htnx.cmrg.me` y la preview de Vercel (aplicaciones aparte); 44 hosts externos; **clic en reacciones, envío del guestbook, newsletter y búsqueda** (mutan datos públicos o envían datos: solo se observaron etiquetas, geometría y hover); reproducción de audio; tema claro (la referencia renderiza el mismo fondo oscuro con `prefers-color-scheme: light`). No se midió Safari/Firefox, ni INP/rendimiento de campo, ni impresión.

### Mapa de rutas

| Tipo | Rutas | Componentes observados (1440) |
| --- | --- | --- |
| Home | `/` | nav superior, h1 serif 44.5, tarjetas `h-32` (hover −1px, portada difuminada `blur(16px) saturate(.5)` al 30 %), **attention map** (treemap SVG), lista de entradas con fecha mono 12.1, anotaciones a mano (Reenie Beanie, rough-notation ×8), pie. |
| Índice blog | `/blog` | 8 `article`, búsqueda (`input` con `backdrop-filter: blur(8px) saturate(2)`), newsletter, canvas 1018×335 (pie), fechas mono. |
| Secciones | `/about`, `/now`, `/work`, `/shelf`, `/thanks`, `/guestbook` | `/about`: canvas globo 728×560 con `aria-label`, lista de vuelos con fade inferior, galería horizontal (9 fotos), timeline; `/work`: galería (13), cronología; `/shelf`: 36 artículos, botones «turn the book» / vinilos, sombras `blur(40px)`; `/now`: listas con fechas; `/thanks`: créditos; `/guestbook`: lienzo de dibujo (Undo/Redo/Pen/Marker/Brush/Eraser/Size/tinta) con `backdrop-filter: blur(8px)`, h1 96 px. |
| Artículos | 8 × `/blog/*` | encabezado con fecha (y bandera de idioma en `programar`), índice con tachado, reacciones, progreso derecho, callouts numerados, código Shiki (lenguajes `ts,tsx,json,css,sh,py,cpp,perl,text`), tweet incrustado, video propio (`htnx`), imágenes anchas 1024, notas al margen, notas al pie, permalinks `#`, pie. |

## 2. Contrato de capas (prioridad para implementar)

### 2.1 Cómo lo resuelve la referencia (medido, 1440, 4 artículos)

| Capa | Regla medida | z efectivo |
| --- | --- | --- |
| Lienzo | `main{position:relative; z-index:10; background:#13110f; box-shadow: 0 20px 25px -5px …}` — contexto de apilamiento de todo el artículo | 10 |
| Carril del índice | `section.blog-toc-rail-mask{position:absolute; z-index:20; left:-28rem; width:448px; padding-left:64px; clip-path:inset(0)}` visible **solo ≥1328 px** (`min-[1328px]:block`). Hijo `section{position:fixed; top:128px; width:384px; padding-right:24px; z-index:0}` | 20 |
| Máscara superior del índice | `mask-image: linear-gradient(#0000 0, #0000001f 12rem, #00000061 24rem, #000000b8 36rem, #000 48rem)` en el carril **absoluto** (anclado al artículo, no al viewport): al cargar, el índice se ve casi invisible y aparece a medida que se baja (captura `…-1440-00-top.png`). | — |
| Carril «back» | `.blog-back-rail-mask{mask-image: linear-gradient(#000 0 calc(100% - 14rem), #0000 100%)}`, `z-index:10`; enlace `position:fixed; top:128px; z-index:10`. | 10 |
| Código | `figure[data-rehype-pretty-code-figure]{position:relative; z-index:50; width:48rem}` + `pre{position:relative; z-index:50; background: gray-900/25; backdrop-filter: blur(12px)}` → **difumina** lo que tenga debajo, incluido el índice. | 50 |
| Imagen / video ancho | `[data-pullsher-root]{position:relative; z-index:40; width:48rem; margin-block:32px}` → `[data-pullsher-stage]{left:50%; translate:-50%; width:64rem}` (1024 px, x=208) → `[data-pullsher-content]{position:relative; z-index:50}` con superficie `bg-gray-950`, `border-radius:28px`. **Opaco**: tapa el índice (captura `pullsher-contentlayer-git-nextjs-1440.png`: «How do you glue it all t» queda cortado por la imagen). | 40 |
| Zoom de imagen | hermano `div{position:fixed; inset:0; z-index:30}` con `backdrop-filter` animado (0 → blur) y `background: color-mix(gray-950 0%→…)`. | 30 |
| Bandas de desenfoque | dos `.blur-overlay{position:fixed; z-index:50; height:clamp(40px,10vh,160px)}` arriba/abajo (ver §3.4). | 50 |
| Cabecera | `header{position:fixed; z-index:50}` | 50 |

Hit-testing de la referencia (`measurements.json → deep_probe → stack_samples`): con el código en pantalla, las 11 filas del índice siguen siendo el elemento superior porque **la geometría evita el solape**: el texto del índice termina antes de x≈336 y el código empieza en x=336. Solo el quinto botón de reacciones queda bajo el código (difuminado). Cuando una imagen de 1024 px pasa, la imagen gana (z 40 > 20) y oculta el índice sin transparencia.

**Regla de la referencia:** ninguna superficie ancha transparente sin `z-index` cruza el carril. Todo lo que lo invade está por encima (z > 20) y es **opaco** (media) o **translúcido con `backdrop-filter: blur(12px)`** (código). Por debajo de 1328 px el índice no existe.

### 2.2 Margen en `d61743a` (runtime, fixture local)

`margen-runtime-d61743a.json`, capturas `margen-fixture-*`:

- `.indice`: `position:fixed; z-index:2`, fondo transparente, x 72→432 a 1440 (24→352 a 1280). Al enfocarlo: `z-index:4` + fondo `--papel` (funciona).
- **Galería** (`.galeria-fotografica`, 1216 px, x=112): `position:relative; z-index:auto`. En las 8 filas del índice `elementFromPoint` devuelve `.indice` → **el índice se pinta encima de las fotos** (1440 y 1280, oscuro y claro). Reproduce la captura del usuario.
- **`details.ancho`** (1024 px, x=208), abierto con teclado (`open === true`): `position:relative; z-index:auto`, transparente. El `pre` interno hereda `.codigo-editorial` (`z-index:3` + `blur(12px)`), así que el **código** sí difumina el índice, pero el `summary` y el párrafo descriptivo cruzan el carril y **sus textos se superponen** al índice (filas 1–2). Con el bloque más abajo (`details_deep`) el código cubre todas las filas (correcto).
- A 1280 px el índice existe y solapa 96 px de código y 328 px de galería; en la referencia no hay índice a ese ancho.
- 390/320: índice estático, sin solape, sin scroll horizontal.

### 2.3 Especificación de cambio (verificable)

1. **Orden de capas explícito.** Variables en `.hoja.lectura-guiada`: `--z-indice: 2`, `--z-pieza-ancha: 3`, `--z-indice-foco: 4`. Toda pieza que pueda cruzar el carril (`.ancho`, `.amplio`, `.galeria-fotografica`, `details.ancho`, `figure` ancha, tablas anchas, embeds) recibe `position:relative; z-index:var(--z-pieza-ancha); isolation:isolate`. No usar `overflow:hidden` global.
2. **Superficie según material.** Medios (galería, imagen, video, embed): superficie opaca detrás de todo el rectángulo, **incluidas** las zonas de padding de 12 px y los bordes con fade de la pista; la máscara de fade no puede dejar ver el índice. Texto/código: fondo `color-mix(var(--panel) 25%, transparent)` + `backdrop-filter: blur(12px)` sobre todo el rectángulo, como `.codigo-editorial pre`.
3. **`details.ancho`.** O bien `summary` y descripción usan la medida de lectura (33rem alineada con la prosa) y solo el código se ensancha a 48rem, o bien todo el `details` lleva la superficie translúcida + blur(12px) de (2). Debe valer cerrado, abierto con ratón y abierto con Enter/Espacio.
4. **Punto de corte del carril.** Mostrar el índice fijo solo cuando su texto no cruce el borde izquierdo de la pieza de 48rem: referencia ≥1328 px. Alternativa admisible: mantener 1280 pero recortar el ancho del carril a `calc((100vw - 48rem)/2 - 24px)`.
5. **Foco.** Mantener `:focus-within → z-index:4` y fondo; añadir prueba de que, enfocado, el índice es el elemento superior aunque haya galería o `details` encima.

**Pruebas de aceptación** (Playwright, oscuro y claro, 1440/1328/1280/390/320): con galería, código ancho y `details.ancho` abierto por teclado bajo el carril, `document.elementFromPoint` en el centro de cada fila del índice **no** devuelve `.indice` salvo con foco dentro del índice; ningún píxel de texto del índice visible sobre la galería (diff de captura con el índice oculto vs visible < 1 % en el rectángulo de la galería); sobre el código la diferencia existe pero está difuminada (comparar con `backdrop-filter:none`, como ya hace `test_code_blur_is_rendered_over_index`); sin scroll horizontal.

## 3. Especificación por componente

Valores de referencia medidos con `getComputedStyle`; «Margen» = estado en `d61743a`. Fuentes: `measurements.json → deep_probe` y `css_rules_screen`.

### 3.1 Tipografía y medida

| Elemento | Referencia | Margen | Brecha |
| --- | --- | --- | --- |
| Prosa | 528 px; Geist 15.5/24.025, `letter-spacing:.05px`, `padding-block:8px` por párrafo | 33rem, 15.5/1.55 | Igualado salvo familia (Margen usa su sans). |
| h1 artículo | serif 44.5/49.44, `letter-spacing:-1.1125px`, `padding-top:24px`; ≤639 px: 36.4/43.68 | 44.5/49.44 y 36.4/43.68 | Falta `letter-spacing:-0.025em`. |
| h2 | serif 36.4/43.68, `-0.91px`, `pt 24 / pb 8`; móvil 28.5/38 | 36.4/43.68, sin variante móvil | Añadir 28.5/38 ≤639 px y tracking −0.025em. |
| h2 home | serif 28.5/38 | — | — |
| Código | 768 px, 13.7/22 Geist Mono | 48rem, 13.7/22 | Igualado. |
| Fuentes | serif **Editorial New** (licencia comercial de Pangram Pangram; no copiar), Geist y Geist Mono (OFL), Reenie Beanie (OFL), **Departure Mono** como «fancy» (OFL) para números de reacciones y `#` de permalink | Instrument Serif (OFL) + sans/mono propios | Sustitución documentada; Departure Mono y Geist se pueden incorporar con su OFL en `licenses/`; Editorial New no. |

### 3.2 Encabezado de artículo con fecha

Referencia: `h1` + fila `flex gap-x-2 text-sm text-gray-500`: [bandera de idioma 20×20 con `aria-label` + `/` en Departure Mono, solo si hay traducción] + `<time class="font-mono" datetime>` en Geist Mono 13.7/19.57, gris 500, minúsculas (`april 8, 2024`). Distancia h1→fecha: 0 px (la fecha empieza en y = fin del h1); fecha→primer párrafo ≈ 16 px. En listas: `time` mono 12.1 px gris 600. Permalink `#` en h1/h2: Departure Mono, `opacity:0; filter:blur(4px); margin-right:-1ch`, con hover o `:target` → `opacity:1; blur(0); padding-right:.5ch` en 150 ms (salida 300 ms con 300 ms de retardo).
**Cambio:** fila de metadatos mono 13.7 gris 3 bajo el título sin separación extra; `<time datetime>` obligatorio; permalink con la misma transición y foco visible.

### 3.3 Índice: tachado, progreso, hover, foco

| Aspecto | Referencia | Margen | Cambio |
| --- | --- | --- | --- |
| Visibilidad | ≥1328 px; fixed `top:128px`, `w:384px`, `pr:24px`, 13.7/24 Geist | fijo ≥1280 px (estático 1200–1279), `w:360` a 1440 / 328 a 1280, 13.7/24 | Ver §2.3-4. |
| Niveles | `padding-left` 0/16/32 px por profundidad | plano | Indentar por nivel (h2/h3/h4). |
| Numeración | span Geist Mono `tabular-nums`, `opacity:.5`, `margin-right:4px` (`01.`) | `::before` mono, opacidad completa | Opacidad .5 solo en el número. |
| Pasado | `data-past` → texto `opacity:.5` (320 ms, `cubic-bezier(.645,.045,.355,1)`) **y** tachado dibujado a mano: `svg.rough-annotation` (rough-notation), trazo 2 px, color gris-500 al 50 %, animado por `stroke-dasharray/offset` (al final del artículo el último trazo aún tenía offset 7.27 px = animación en curso) | `text-decoration: line-through` | Trazo SVG irregular con animación de dibujo; reducido a opacidad sin animación con `prefers-reduced-motion` (no verificado en la referencia: allí la transición siguió en 0.15 s). |
| Activo | `data-active` → color gris-400 | `aria-current` → `--tinta` | Equivalente; usar gris intermedio, no tinta plena. |
| Hover | color gris-400; sin blur ni cambio de opacidad del carril | color `--tinta` | Ajustar color. |
| Foco | `outline: 2px dashed gris-400; outline-offset:2px`, sin cambio de capa | z 4 + fondo + outline 1px offset 8px | Margen es más robusto (eleva capa); conservar, igualar outline. |
| Sombra | `filter: drop-shadow(1px 1px 3px #0003)` en cada enlace | — | Añadir. |
| Máscara | fade anclado al artículo (§2.1) | — | Añadir `mask-image` en un contenedor absoluto del alto del artículo. |
| Back to top | fijo `top:128px`, 13.7/24, con icono; arriba del todo se muestra «back to posts» en otro carril con máscara inferior de 14rem | — | Opcional. |
| Reacciones | ≥1328 px bajo el índice: grupo `role=group` 284×44, 5 botones 56×44, icono pixel + cifra Departure Mono 15.5/20, peso 500, `letter-spacing:-.025em`, gris-600; `aria-label` «Noice: N total reactions. 0 of 5 added this visit.»; <1328 px se mueven al final del artículo con ancho de prosa. Sin tooltip en hover. | No existe | Fuera del alcance de Margen como servicio público; si se adopta, sin contador global por defecto. |
| Progreso derecho | `aside` absoluto z 20, `w:16px` a `right:32px`, `sticky top:128px`, alto `100vh-16rem`; marcas + porcentaje naranja; presente a 1440; a 1280/390/320 el selector no encontró el `aside` (no se determinó el punto de corte exacto) | `.regla-guiada` 44 px a `right:32px` | Verificar a 1280; resto alineado. |

### 3.4 Máscara superior / inferior y cabecera

- `.blur-overlay` fija arriba y abajo, alto `clamp(40px,10vh,160px)`, `margin:-1px 0`: `::before` `backdrop-filter:blur(.5px)` (z 1) + 6 `div` con `blur(1|2|4|6|8|12px)` (z 2–7), cada uno enmascarado a una banda escalonada en tramos de 12.5 %, + `::after` `blur(8px)` (z 8) en 87.5→100 %. Resultado: el texto se difumina progresivamente al acercarse al borde (capturas: título desenfocado bajo la cabecera).
- Margen: `.web-bordes` usa **una** capa `blur(8px)` con máscara lineal, solo en la receta `web-shell`; el lector de documentos no la tiene.
- Cabecera: `fixed z 50`, transición `all 2000ms cubic-bezier(.075,.82,.165,1)`; estado oculto `opacity:0; filter:blur(16px)`. A 1.5–2.5 s de cargar un artículo en `scrollY=0` estaba oculta (también con `reduced-motion`); tras bajar 1200 px y subir 300 px estaba visible. No se determinó la regla exacta de aparición.
**Cambio:** pila de 6–8 capas de `backdrop-filter` con máscaras escalonadas (no una sola), desactivada con `prefers-reduced-transparency` y en impresión.

### 3.5 Callouts numerados

Referencia (`blockquote.blockquote-mask`): `margin:32px 0; padding:16px; border-radius:4px`; fondo `radial-gradient(circle at top left, transparent 0 16px, acento 12 % 16px, acento 8 % 90%)` (el círculo transparente aloja el número); barra izquierda `::before` 3 px desde `top:15px`, alto `calc(100% - 15px)`, `border-radius:0 0 0 2rem`; icono 32×32 en `top/left:-13px`, `fill` acento 80 %; título `blockquote-title` peso 600, acento 80 %, `text-transform:lowercase` + `::first-letter` mayúscula («IMPORTANT:» → «Important:»). Acentos observados: naranja #f1733d (important), gris/azul (note). Ancho = prosa (528).
Margen `.aviso-esquina`: número 32 px a −13 px ✔, `padding:16px`, `radius:4px` ✔, pero **borde completo 1 px** al 25 % en vez de fondo radial + barra izquierda de 3 px.
**Cambio:** reemplazar el borde por fondo radial con hueco de 16 px + barra izquierda 3 px desde 15 px; título 600 en acento 80 %.

### 3.6 Código

| Aspecto | Referencia | Margen | Cambio |
| --- | --- | --- | --- |
| Marco | 768 px; 4 trazos discontinuos 1 px gris-700/80: horizontales salen 64 px (móvil `max(-1.5rem, 50% - 50dvw)`) con máscara 90° 0→15→85→100 %; verticales salen 48 px (móvil 16 px) con máscara 0→35→65→100 % | igualado (`::before/::after`) | — |
| Título/archivo | `figcaption` Geist Mono 13.7/19.57 gris-600, `margin:0 0 8px 16px` («build.ts») | `.cab` 13.7/19.57, lenguaje visible | Permitir nombre de archivo además de lenguaje. |
| Pie | `[data-rehype-pretty-code-caption]` centrado, 13.7 gris-500 itálica, `margin-top:8px` | — | Añadir pie opcional. |
| Copia | botón 40×40 `top:2px right:16px` (−12 px margen), gris-500, hover `brightness(150%)`; icono anima escala/blur; sin tooltip; portapapeles = texto visible exacto (209/209 caracteres) | 44×44, estado `role=status` | Igualado en función. |
| Números | `counter`, `color:#fff2`, `width:1rem` (≤2 cifras) / `2rem` (3 cifras), `margin:0 1rem` | `max(16px, cifras·1ch)` + 32 px | Equivalente; probar 1–1000. |
| Línea resaltada | `background:#ca9e6610; border-left:1px solid #ca9e66`; número en #ca9e66, `margin-right:calc(1rem - 2px)` | `box-shadow: inset 2px 0 naranja`, sin fondo | Añadir tinte 6 % y borde de 1 px; número en acento. |
| Caracteres | `mark`: fondo #ca9e6620, `radius:4px`, `padding:0 .2rem .1rem`, `box-shadow:0 0 0 1px #ca9e6630, 0 0 10px #ca9e6620`, hijos `#ca9e66 !important` | `mark` naranja con borde 22 % | Añadir halo de 10 px. |
| Atenuación de rango | **No existe** regla de atenuación del resto de líneas: misma opacidad/color computado en líneas normales y resaltadas, también en hover. La sensación de «resto atenuado» viene de los colores del tema `quietude` (puntuación `#57554F`). | — | No inventar atenuación como «igual a la referencia»; si se añade, es decisión propia. |
| Tema | Shiki dual `github-light-high-contrast` / `quietude`; variables `--shiki-screen` y `--shiki-print` por token | tokenizador local | Brecha conocida (no es Shiki). |
| Desbordamiento | `pre code` con `mask-image` lateral guiado por `animation-timeline: scroll(self inline)`; fallback `min(12%,40px)`; `scroll-padding:16px` | scroll nativo sin fade | Añadir fade lateral dependiente del scroll. |
| Selección | `code ::selection{background:#ca9e6620}` | — | Añadir. |
| Foco del `pre` | `tabindex=0`; con `.focus()` programático no se observó outline (no se ejercitó `:focus-visible` con teclado real) | `2px dashed` offset 4 | Conservar Margen. |

### 3.7 Tweet / X

Dentro de un callout gris: icono X + texto, tarjeta del tweet (avatar circular, nombre + verificado, `@handle / fecha`, texto, «Show more», medio con «View video on X», acciones con contadores, logo X a la derecha); marcado `[data-blog-tweet]`, `[data-blog-tweet-media]`, `[data-blog-tweet-actions]`; impresión: borde izquierdo y sin medios. Es HTML propio, sin script de X (no se observaron iframes). Ancho = prosa.
**Cambio:** el embed de Margen debe ser HTML estático con enlace de respaldo; detalle de proveedores lo audita `margen-atlas-datos`.

### 3.8 Video y medios anchos

Video (`htnx`): reproductor propio, `[data-video-player]` radio 28 px, `bg-gray-950`; `<video muted playsinline preload="metadata">` sin `autoplay`, sin `poster`, sin `controls` nativos; botón de reproducción que cubre el video; barra `absolute inset-x-2 bottom-2 z 20` con botones de 44 px (play, silencio, pantalla completa) y deslizador `role=group` «Video progress»; `.blur-overlay` de 120 px bajo los controles. 1024×679 a 1440; 342×227 a 390.
Imágenes anchas: ver §2.1 (1024 px, radio 28, z 40, zoom con overlay fijo z 30).

### 3.9 Galerías horizontales (`/about`, `/work`)

`ul` 1024 px, `padding:12px 0`, `gap:12px`, `tabindex=0`, `aria-label`, `cursor:grab`, `overscroll-behavior-x:contain`, sin `scroll-snap`; máscara `linear-gradient(to right, transparent, #000 min(12%,40px), …)` guiada por `animation-timeline: scroll(self inline)` (el fade inicial es 0 en `scrollLeft=0` y aparece al desplazar). `figure` 232 px de alto (ancho según imagen: 232 o 348), `border-radius:28px` con `corner-squircle`, `bg-gray-900`, `box-shadow:3px 4px 10px gray-950/20`, anillo interior `1px white/5` (z 20), degradado inferior `to top, gray-950 → gray-950/40 @45 % → transparente`, pie Geist Mono 12.1 px (`px-4 pb-2.5`) con año 11 px gris-600.
Margen: 232 px, 12 px, fades por variables JS, radio 28 ✔. **Brechas:** apilamiento (§2.2) y que el fade de borde deje ver el índice.

### 3.10 Attention map (treemap)

Contenedor `w:min(100vw - 3rem, 64rem)` (1024 a 1440/1280, 350 a 390), `padding:8px`, 4 trazos discontinuos con fade; SVG 1008×380 (`sm:h-95`), 320 px de alto en móvil. Celdas `rect` relleno gris-800 #2e2821, trazo gris-700 #3b3229 1 px; etiqueta serif 18 px gris-300 y duración Geist Mono 11.5 px gris-500; el formato se abrevia según tamaño («3 days, 10 hours, 36 minutes» → «3d, 10h, 36m» → «S…»). 26 rect a 1440/1280/390, 24 a 320; a 390 la disposición cambia a filas. **Sin** `role`, `aria-label`, `title`, `tabindex` ni tooltip (hover sin efecto medible).
**Cambio en Margen:** mismo lenguaje visual pero con tabla alternativa, foco por celda y valores con unidad (Margen exige accesibilidad que la referencia no tiene).

### 3.11 Pie con redes desenfocadas

`footer` del sitio (también al final de cada artículo): nombre serif; lista `X: / GitHub: / LinkedIn: / email:` con `a.link-default` + descripción `text-gray-600` que **≥1280 px** es gris-700 con `filter: blur(4px)` y `cursor:crosshair`; `li:hover` → `blur(0)`, gris-600, 300 ms; por debajo de 1280 sin blur. Columna derecha con nota editorial; fila inferior con último commit (`time` relativo + `+n −n` mono verde/rojo), licencia y `v1`. Botón de sonido (no se midió ni se reprodujo audio).
Margen: `web-pie` en la receta `web-shell`. **Cambio:** pie configurable por documento/autor (sin identidad de Ángel por defecto), descripciones opcionales con blur 4 px solo en puntero fino ≥1280 y sin blur al enfocar.

### 3.12 Enlaces, iconos, sombras

`.link-default`: `color: color-mix(in srgb, currentColor 50%, gray-950)`, subrayado, hover `brightness(150%)` 150 ms; favicon `img[data-link-favicon]` 16×16, `margin-right:.3em`, `translateY(-1px)`, `referrerpolicy=no-referrer`, lazy, servido desde `/favicons/*.svg` propio. No hay tarjeta de vista previa en hover (no apareció `[data-slot=link-preview-card]` aunque existe CSS para ella). Código en línea: fondo gris-900/60, `backdrop-filter:saturate(1.5)`, `padding:2px 6px`, trazos laterales discontinuos con fade. `strong` con `drop-shadow-md`.

### 3.13 Movimiento (resumen)

| Elemento | Duración / curva |
| --- | --- |
| Cabecera | 2000 ms `cubic-bezier(.075,.82,.165,1)`, opacidad + blur 16 px |
| Índice (color, pasado) | 320 ms `cubic-bezier(.645,.045,.355,1)` |
| Enlaces del carril, copia, links | 150 ms |
| Permalink | entrada 150 ms; salida 300 ms + 300 ms retardo |
| Pie (redes) | 300 ms |
| Tooltip (CSS presente) | 150 ms `cubic-bezier(.175,.885,.32,1.1)` + blur 4 px |
Con `reduced_motion: reduce` la transición del índice midió 0.15 s (no se anula) y la cabecera conservó el estado oculto inicial.

## 4. Inferencias de stack (limitadas)

Evidencia directa: cabecera `server: Vercel`; rutas `/_next/static/immutable/chunks/*` y `turbopack-*.js` (Next.js con Turbopack); clases utilitarias de Tailwind v4 (`--tw-*`, `@layer properties`); atributos `data-rac`/`data-react-aria-pressable` (React Aria Components); `data-rehype-pretty-code-*` y variables `--shiki-*` (rehype-pretty-code + Shiki); `svg.rough-annotation` (rough-notation o derivado); `number-flow-react` en home. No se determinaron versiones ni código fuente; nada de esto se adopta como dependencia por esta auditoría.

## 5. Brechas priorizadas para implementación

1. **Capas** (§2.3): galería y `details.ancho` bajo el índice — bug visible, reproducido.
2. **Punto de corte del índice** (1328) y máscara superior anclada al artículo.
3. **Tachado dibujado** + opacidad .5 de pasados + niveles + número a .5.
4. **Callout** con fondo radial y barra de 3 px.
5. **Código**: línea resaltada con tinte, halo de `mark`, fade lateral de desbordamiento, pie de figura, nombre de archivo.
6. **Bandas de desenfoque** escalonadas arriba/abajo (lector y web-shell).
7. **Encabezado con fecha**, tracking de títulos, h2 móvil 28.5/38.
8. **Pie** configurable con redes desenfocadas opcionales.
9. **Treemap** accesible con la estética medida.

## 6. Reproducción

Python de Playwright: `/Users/angelbotto/orca/workspaces/margen/margen-lector-voz/.venv/bin/python` (Chromium headless, DPR 1, `color_scheme=dark`). Scripts y JSON crudos en `~/.local/share/margen-review/atlas-reference-20261022/scripts/` (`crawl.py`, `probe.py`, `routes2.py`, `treemap.py`, `gal.py`, `wide.py`, `interact.py`, `margen_fixture.py`, `compile.py`). `margen_fixture.py <repo> <salida.json> <dir capturas>` reproduce el bug de capas contra cualquier commit sin red. La referencia cambia con el tiempo (contadores, «latest commit», attention map): las cifras de contenido no son invariantes, la geometría y las reglas sí lo fueron durante esta sesión.
