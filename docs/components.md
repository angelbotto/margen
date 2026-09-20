# Margen components

For new artifacts, compose content from these recipes and use the [artifact contract](artifact-contract.md). The generator includes appearance, comments, sound and reading aids once, detects recipe modules and embeds complete fonts and styles. React and Tailwind are not required. Start with [charts](#recetas-graficas), [heatmaps](#recetas-calor), [tables](#recetas-tablas), [sound](#recetas-sonido), [writing](#recetas-escritura) or [Three.js](#recetas-three). The executable catalog is `examples/generated/template.html`; chapters are in `examples/generated/chapters.html`.

## Document and themes — legacy compatibility

This skeleton explains older documents with a simple selector. Use the artifact contract for new documents: this historical shell omits current controls. Replace embedding comments with complete local files, not remote dependencies. Use `.amplio` instead of `.ancho` for a wider figure; do not widen the entire reading column.

```html
<title>Nota — decisión y evidencia</title>
<meta charset="utf-8">
<style>/* Pegar aquí packages/core/styles/fonts.css y packages/core/styles/artifact.css completos, incluidas las licencias */</style>
<meta name="viewport" content="width=device-width, initial-scale=1">
<a class="salto" href="#contenido">Saltar al contenido</a>
<main class="hoja" data-lectura lang="es">
  <div class="herramientas">
    <span class="firma-editorial"><span>Margen</span><small>Cuadernos</small></span>
    <div class="temas">
      <label for="tema">Papel</label>
      <select id="tema" data-tema>
        <option value="system">Sistema</option>
        <option value="light">Claro</option>
        <option value="dark">Oscuro cálido</option>
        <option value="sea">Dark Sea</option>
      </select>
    </div>
  </div>
  <header class="cabecera" id="contenido" tabindex="-1">
    <p class="ceja">Decisión / septiembre 2026</p>
    <h1>Una fuente de verdad.</h1>
    <p class="bajada">Registrar el movimiento una vez y conservar su trazabilidad.</p>
  </header>
  <!-- Secciones y figuras como hermanos; ver los bloques siguientes. -->
</main>
<script>/* Pegar aquí packages/core/components/reader.js completo */</script>
```

## Hand-drawn underline

Use `.marca` for a short decision-bearing phrase. Its two embedded SVG strokes have distinct curves; `box-decoration-break:clone` handles wrapping. Text remains selectable and retains its contrast. An underline does not replace a link, a status label or a heading.

```html
<p>El estado definitivo debe vivir en <span class="marca">un solo registro</span>.
  El <a href="#evidencia">detalle de la evidencia</a> se puede consultar después.</p>
```

## Handwritten note and bracket

Use a margin note for a complementary perspective, never for a critical condition. The paragraph occupies the central grid cell; from 1184px the note occupies a real cell on the right and below that it follows the paragraph. Reenie Beanie supplies the annotation typography; only bracket decorations use absolute positioning. Use the margin-notes recipe for left/right animated variants.

```html
<div class="con-margen">
  <p>El dato necesita unidad, fecha y origen. Mientras se confirma, debe decir
    <span class="dato">pendiente de medir</span>.</p>
  <aside class="margen" aria-label="Nota al margen">
    ¿se entiende sin estar en la reunión?
  </aside>
</div>
<p class="nota">una buena nota le ahorra contexto a la siguiente persona</p>
```

## Circular callouts

Use for conditions, errors, confirmations and short quotations. The default variant is informational; `ojo`, `bien` and `mal` add semantic emphasis. The 28px circle stays in the grid rather than invading the margin. Static callouts do not need `role="alert"`. Numbering does not make a callout an executable step.

```html
<aside class="aviso ojo" aria-label="Aviso 1: condición">
  <span class="num">1</span>
  <div><p class="titulo">La medición todavía es parcial.</p>
    <p>Falta el volumen de una sede; el total no representa toda la operación.</p></div>
</aside>
<aside class="aviso bien" aria-label="Aviso 2: resultado">
  <span class="num">2</span>
  <div><p class="titulo">La fuente está identificada.</p>
    <p>El registro incluye la fecha de corte y la unidad de cada cifra.</p></div>
</aside>
<aside class="aviso mal" aria-label="Aviso 3: error">
  <span class="num">3</span>
  <div><p class="titulo">El archivo no se pudo leer.</p>
    <p>La última medición válida sigue disponible en el registro.</p></div>
</aside>
<aside class="aviso cita">
  <span class="num" aria-hidden="true">↳</span>
  <div><blockquote>Dejar una buena nota es dejar contexto.</blockquote>
    <p class="secundario">Principio de esta plantilla</p></div>
</aside>
```

## Fixed proportion map

This grid represents exactly 60/25/15: columns 3fr/2fr, then rows 5fr/3fr subdividing the second column. Recalculate proportions when data changes; changing labels alone misrepresents values. Only comparable nonnegative values with a positive total fit this recipe. Check text minimums against actual areas. Use the attention map or bars for other distributions, and disclose any grouped tail separately.

```html
<figure class="ancho">
  <div class="mapa" role="group" aria-label="Reparto ilustrativo de cien horas">
    <div class="bloque destaca"><span class="n">Investigar</span><span class="d">60 h · 60 %</span></div>
    <div class="bloque"><span class="n">Construir</span><span class="d">25 h · 25 %</span></div>
    <div class="bloque"><span class="n">Revisar</span><span class="d">15 h · 15 %</span></div>
  </div>
  <figcaption>Ejemplo de cien horas. Las áreas incluyen el borde interior de cada celda.</figcaption>
</figure>
```

## Status pills, definition lists and meters

Use a `dl` to associate labels and values, a pill for a short labeled state, and `meter` for coverage. An operation in progress needs `progress` instead. Keep units and explicit state words; color is supplementary. Dates and names are not fake controls.

```html
<p>El valor está <span class="dato">pendiente de medir</span>.</p>
<p><span class="pildora p-si">✓ Aplicado</span>
   <span class="pildora p-medio">≈ Parcial</span>
   <span class="pildora p-no">× No disponible</span></p>
<dl class="datos">
  <div><dt>Fuente</dt><dd>CSS publicado de cmrg.me</dd></div>
  <div><dt>Tamaño original</dt><dd>15,5 px</dd></div>
  <div><dt>Interlineado original</dt><dd>1,55</dd></div>
</dl>
<div class="medida">
  <label for="cobertura">Páginas revisadas</label><span class="pct">100 %</span>
  <meter id="cobertura" min="0" max="10" value="10">10 de 10 páginas</meter>
</div>
```

## Reading outline and progress ruler

Use for a document with multiple sections. At 1200px, `lectura-guiada` reserves 200px left and 76px right, with a 160px outline and a 44px ruler. Below that, the outline is in flow and progress is compact. Previous sections are struck through to indicate position, not proof of reading. The ruler supports click, arrows, PageUp/Down and Home/End. Keep IDs unique; never announce every scroll through aria-live.

For chapters, use `hoja multipagina lectura-guiada`, `data-lectura data-progreso-pagina`, one outline per `.pagina`, and one ruler after main. Add `data-historial data-enlaces-internos` for deep links. Load chapters after reader. Progress tracks the visible chapter and excludes footer/pagination. Without JS, navigation remains available. Print removes controls. The older non-guided layout retains its 1600px threshold.

```html
<main class="hoja lectura-guiada" data-lectura lang="es">
  <header class="cabecera"><p class="ceja">Informe</p><h1>Una decisión con evidencia</h1></header>
  <nav class="indice" tabindex="0" aria-label="Índice del documento">
    <p class="ceja">En esta nota</p>
    <ol><li><a href="#criterio">El criterio</a></li>
        <li><a href="#evidencia">La evidencia</a></li></ol>
  </nav>
  <section class="seccion" id="criterio"><h2>El criterio</h2><p>Qué necesitamos resolver.</p></section>
  <section class="seccion" id="evidencia"><h2>La evidencia</h2><p>Qué sostiene la decisión.</p></section>
</main>
<div class="regla regla-guiada" role="slider" tabindex="0" aria-orientation="horizontal"
     aria-label="Progreso de lectura" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0">
  <div class="ticks"></div><div class="cursor"></div><span class="val">0%</span>
</div>
```

## Code with copy control

Use when readers need exact text to inspect or copy. Keep filenames when meaningful; language-only headers are compacted by the interface runtime. Preserve native selection and local scrolling. If clipboard access fails, select the code and explain manual copying. IDs must be unique. Escape &, < and > when inserting source into HTML.

```html
<figure class="ancho">
  <div class="codigo">
    <div class="cab"><span>registro.js · JavaScript</span>
      <button type="button" data-copiar="registro-codigo" aria-label="Copiar registro.js" title="Copiar"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H4v13h4"/></svg></button>
      <span class="copia-estado" role="status" aria-live="polite"></span>
    </div>
    <pre tabindex="0" aria-label="Código de registro"><code id="registro-codigo"><span class="com">// La procedencia forma parte del dato.</span>
<span class="kw">const</span> fuente = <span class="str">"CSS publicado de cmrg.me"</span>;</code></pre>
  </div>
  <figcaption>Ejemplo verificable; la copia conserva el texto, sin los colores del resaltado.</figcaption>
</figure>
```

## Wide tables and diagrams

Tables are wide by default. Do not apply nowrap to every cell; wrap long identifiers and scroll locally where structure needs width. SVG diagrams need a viewBox, title and equivalent text. Protect label readability with a scrollable region or a mobile vertical composition. The example diagram contains exactly three steps; adding steps requires updating geometry, equivalent text and viewBox. It neither simulates a process nor calculates duration.

```html
<figure class="amplio">
  <div class="tabla-caja" tabindex="0" role="region" aria-label="Medidas tipográficas, desplazable">
    <table><caption>Valores observados en cmrg.me</caption>
      <thead><tr><th scope="col">Uso</th><th scope="col">Tamaño</th><th scope="col">Interlineado</th></tr></thead>
      <tbody><tr><th scope="row">Cuerpo</th><td>15,5 px</td><td>1,55</td></tr>
        <tr><th scope="row">Título, escritorio</th><td>44,5 px</td><td>1,1111</td></tr></tbody>
    </table>
  </div>
  <figcaption>Fuente: hoja CSS y estilo calculado a 1639 px de viewport.</figcaption>
</figure>
```

```html
<figure class="ancho">
  <div class="diagrama-caja" tabindex="0" role="region" aria-label="Proceso de revisión, desplazable">
    <svg class="diagrama" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 160" role="img" aria-labelledby="proceso-titulo proceso-desc">
      <title id="proceso-titulo">De la fuente a la decisión</title>
      <desc id="proceso-desc">Observar la fuente, verificar la evidencia y registrar la decisión.</desc>
      <g fill="none" stroke="currentColor"><rect x="10" y="40" width="200" height="80" rx="4"/>
        <rect x="260" y="40" width="200" height="80" rx="4"/><rect x="510" y="40" width="200" height="80" rx="4"/>
        <path d="M210 80h42m-9-7 9 7-9 7M460 80h42m-9-7 9 7-9 7"/></g>
      <g fill="currentColor" text-anchor="middle" font-size="17"><text x="110" y="87">Observar</text><text x="360" y="87">Verificar</text><text x="610" y="87">Registrar</text></g>
    </svg>
  </div>
  <figcaption>Fuente → verificación → decisión registrada. Las flechas indican orden, no duración.</figcaption>
</figure>
```

## Fading excerpt

Use only for an optional teaser. Apply the mask to an aria-hidden decorative copy; complete text remains available in details, through keyboard/screen reader and in print. Never fade the only copy of a conclusion, warning, source or table.

```html
<div class="extracto">
  <p class="desvanece" aria-hidden="true">La forma prepara el terreno; la evidencia sostiene
    lo que decimos. Una nota se termina cuando permite decidir.</p>
  <details><summary>Leer la nota completa</summary>
    <p>La forma prepara el terreno; la evidencia sostiene lo que decimos. Una nota se termina
      cuando permite decidir. Si falta una fuente, debe quedar identificada como pendiente.</p>
  </details>
</div>
```

## Kept cards

Use for selected objects or references with a complete title and a useful personal note. Covers are optional. Adaptive columns have a 240px minimum; hover transforms the cover without moving text and reduced motion removes transitions. Use a real named link for navigation. Embed images as data URIs. Generated sample covers are local illustrations, not commercial artwork.

```html
<div class="kept ancho">
  <article>
    <svg class="portada" viewBox="0 0 180 220" aria-hidden="true">
      <rect x="2" y="2" width="176" height="216" rx="2" fill="#755a42"/>
      <circle cx="90" cy="85" r="48" fill="none" stroke="#fef8f2"/>
      <text x="24" y="166" fill="#fef8f2" font-family="Georgia" font-size="24">La decisión</text>
    </svg>
    <h3>La decisión</h3><p>Qué se eligió y por qué. Un registro al que podamos volver.</p>
    <p class="meta">NOTA / 01 · ejemplo editorial</p>
  </article>
  <article>
    <h3>La evidencia</h3><p>Medidas, fuentes y límites, con el contexto que les da sentido.</p>
    <p class="meta">REGISTRO / 02 · ejemplo editorial</p>
  </article>
</div>
```

## Chapter layout

<!-- nota:ejemplo multipagina -->

```html
<a class="salto" href="#contenido">Saltar al contenido</a>
<div class="barra" tabindex="0" role="region" aria-label="Páginas y tema, desplazable">
  <span class="sello">bottifact</span>
  <nav aria-label="Páginas del informe">
    <button type="button" data-ir="p1" aria-current="page"><span class="n">01</span>El destino</button>
    <button type="button" data-ir="p2"><span class="n">02</span>La evidencia</button>
  </nav>
  <div class="temas">
    <label for="tema" class="sr-only">Papel</label>
    <select id="tema" data-tema>
      <option value="system">Sistema</option><option value="light">Claro</option>
      <option value="dark">Oscuro cálido</option><option value="sea">Dark Sea</option>
    </select>
  </div>
</div>

<main class="hoja multipagina" data-lectura lang="es">
  <article class="pagina viva" id="p1" data-pagina>
    <header class="cabecera" id="contenido" tabindex="-1">
      <p class="ceja">Página 01 / el destino</p>
      <h1>A dónde tenemos que ir.</h1>
      <p class="bajada">Una frase que dice de qué trata el capítulo.</p>
    </header>
    <nav class="indice" aria-label="Índice de esta página">
      <p class="ceja">En esta página</p>
      <ol><li><a href="#criterio">El criterio</a></li></ol>
    </nav>
    <section class="seccion" id="criterio"><h2>El criterio</h2><p>Texto.</p></section>
    <figure class="amplio">
      <div class="tabla-caja" tabindex="0" role="region" aria-label="Criterios del destino, desplazable">
        <table><caption>Criterios ilustrativos</caption>
          <thead><tr><th scope="col">Criterio</th><th scope="col">Resultado esperado</th></tr></thead>
          <tbody><tr><th scope="row">Trazabilidad</th><td>Conservar la fuente y la fecha de cada registro.</td></tr></tbody>
        </table>
      </div><figcaption>Figura hermana de la sección; conserva el ancho amplio.</figcaption>
    </figure>
  </article>

  <article class="pagina" id="p2" data-pagina hidden>
    <header class="cabecera"><p class="ceja">Página 02 / evidencia</p><h1>Qué lo sostiene.</h1></header>
    <nav class="indice" aria-label="Índice de evidencia"><ol><li><a href="#registro">El registro</a></li></ol></nav>
    <section class="seccion" id="registro"><h2>El registro</h2><p>Una muestra ilustrativa conserva su origen y distingue lo medido de lo pendiente.</p></section>
    <figure class="ancho"><div class="codigo"><div class="cab"><span>registro.txt</span>
      <button type="button" data-copiar="registro-p2">Copiar registro</button><span class="copia-estado" role="status"></span></div>
      <pre tabindex="0" aria-label="Registro ilustrativo"><code id="registro-p2">fuente: ejemplo local
fecha: 2026-09-13
estado: pendiente de medir</code></pre></div><figcaption>Datos de ejemplo, sin una medición de producción.</figcaption></figure>
  </article>

  <div class="paginacion" data-paginacion>
    <button type="button" data-nav="prev"><span class="et">Anterior</span><span class="tit"></span></button>
    <button type="button" data-nav="next"><span class="et">Siguiente</span><span class="tit"></span></button>
  </div>
  <footer class="pie">Margen · Dos capítulos de ejemplo.</footer>
</main>
```

**Use and limits:** Use separate chapters when each has its own reading task and contents. Put the grid on `.pagina`, never combine `por-seccion` with `multipagina`. Load reader then chapters once. Active navigation uses `aria-current=page`; hashes identify chapters and `nota:pagina` announces changes. IDs and `data-ir` targets must match. This is local navigation, not a network router. Historical chapter layouts show only the first chapter without JavaScript; print includes all chapters. The standard contract provides its own no-JavaScript fallback.

## Dense table

<!-- nota:ejemplo tabla-densa -->

```html
<figure class="amplio">
  <div class="tabla-caja densa" tabindex="0" role="region" aria-label="Brechas, desplazable">
    <table><caption>Seguimiento ilustrativo de brechas</caption>
      <thead><tr><th scope="col">Brecha</th><th scope="col">Responsable</th><th scope="col">Estado</th><th scope="col">Inicio</th><th scope="col">Revisión</th><th scope="col">Evidencia esperada</th></tr></thead>
      <tbody><tr><th scope="row">Fuente sin fecha de corte</th><td>Equipo de datos</td><td>Pendiente</td><td><time datetime="2026-09-13">13-sep-2026</time></td><td><time datetime="2026-09-18">18-sep-2026</time></td><td>Registro con fecha y criterio de inclusión.</td></tr>
        <tr><th scope="row">Definición de unidad</th><td>Equipo de análisis</td><td>En revisión</td><td><time datetime="2026-09-12">12-sep-2026</time></td><td><time datetime="2026-09-16">16-sep-2026</time></td><td>Diccionario con unidad y denominador.</td></tr></tbody>
    </table>
  </div>
  <figcaption>Ejemplo de seis columnas; desplaza la tabla para consultar la última.</figcaption>
</figure>
```

**Use and limits:** Use for five or more columns. `.tabla-caja table` starts at 34rem; `.densa` raises the local minimum to 58rem. Preserve a focusable, named local scroller instead of compressing cells or making the entire page scroll horizontally. Inspect actual long values at 320/390 px. Do not apply nowrap to every cell.

## Terminal

<!-- nota:ejemplo terminal -->

```html
<figure class="ancho">
  <div class="terminal">
    <div class="cab"><span>saldo por bolsillo · ejemplo ilustrativo</span>
      <button type="button" data-copiar="t-saldos" aria-label="Copiar la salida">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
          <rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/>
        </svg>
      </button>
      <span class="copia-estado" role="status" aria-live="polite"></span>
    </div>
    <div class="cuerpo">
      <pre tabindex="0" aria-label="Distribución del saldo"><code id="t-saldos"><span class="tenue">       rango   bolsillos        total COP</span>
<span class="tenue">  ------------  ---------  ---------------</span>
  menos de $100        349            5.120
    más de $1M          5    <span class="subra">14.434.490</span></code></pre>
    </div>
  </div>
  <figcaption>Datos ilustrativos. La columna que importa va señalada, no en negrita.</figcaption>
</figure>
```

**Use and limits:** Use when exact console output is the evidence, not as a substitute for an analytical table. The terminal intentionally retains a dark surface in light and dark documents, with theme-specific tones. Copy uses the shared `data-copiar` behavior and a manual-selection fallback. Align plain output with monospace spaces inside `pre`. It never executes commands.

## Handwritten note

<!-- nota:ejemplo manuscrita -->

```html
<div class="gesto-escrito">
  <p class="manuscrita" data-mano="fuente" data-escritura-sonora id="nota-decision">de doce frentes, siete están en producción. el cuello de botella ya no es construir: es decidir.</p>
  <button class="gesto-repetir" type="button" data-mano-repetir="nota-decision" data-audio="escritura" aria-label="Volver a escribir la nota" title="Volver a escribir la nota"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 10a9 9 0 1 1 2 8M3 4v6h6"/></svg></button>
</div>
```

**Use and limits:** Use a short secondary observation revealed when seen. `data-mano=fuente` reveals the embedded Reenie Beanie glyphs, with 375 ms character reveals staggered to match the approved pencil sample (about 2.18–3.03 s). Entry triggers once at 30% visibility; replay remains available. Keep complete equivalent text for selection, assistive reading and review. Leaving the viewport, hiding the tab or reduced motion completes the text and cancels sound. `data-escritura-sonora` requests the original recording after a real audio-unlocking gesture; do not loop, normalize or stretch it. No RAF. The older empty `data-mano` SVG alphabet remains compatible (lowercase, 240 characters, words up to 160 px). Prefer `fuente` for new notes. `NotaMano.init/get/destroy` preserves original nodes.

## Route globe

The complete executable example is `examples/generated/globe.html`. Land-mask data is embedded in globe.js; there are no map keys or fetch requests. Load the pinned Three dependency once.

| Input / method | Contract |
|---|---|
| `points` | Unique string id; latitude −90…90, longitude −180…180; optional label. |
| `arcs` | Existing from/to IDs; optional unique id, label and detail. |
| `select(id)` | Selects and centers a route; null selects all; unknown ID throws. |
| `setData({points,arcs})` | Validates before replacing geometry; invalid data throws TypeError and retains prior data. |
| `rotate(dx,dy)` | Radians; tilt is limited to ±1.2. |
| `pause()` / `resume()` | Rotation control; resume respects reduced motion. |
| `destroy()` | Stops RAF, disconnects listeners/observers, frees WebGL and empties the container. |

Coincident points avoid degenerate curves; antipodes use a deterministic axis. Labels enter through textContent. Escape `<` as `\u003c` in embedded JSON. Curves have 64 segments and hide behind the sphere. Time-based rotation is 0.072rad/s; reduced motion makes selection immediate. Buttons and keyboard remain available; touch rotation preserves vertical page scrolling. Without WebGL, retain the complete route list and an explanation. The 256×128 land mask is not a political map or measured distance source. Label invented routes as illustrative.

```html
<figure class="ancho">
  <div id="mi-globo"></div>
  <figcaption>Rutas ilustrativas. La lista permanece disponible sin WebGL.</figcaption>
</figure>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.1/three.min.js"></script>
<script>/* Pegar aquí packages/core/components/globe.js completo, con su licencia MIT */</script>
<script>
const rutas = new NotaGlobo(document.getElementById('mi-globo'), {
  points: [
    {id:'BOG',label:'Bogotá',lat:4.711,lon:-74.0721},
    {id:'MAD',label:'Madrid',lat:40.4168,lon:-3.7038},
    {id:'HND',label:'Tokio',lat:35.5494,lon:139.7798}
  ],
  arcs: [
    {id:'bog-mad',from:'BOG',to:'MAD',label:'BOG → MAD',detail:'Bogotá · Madrid'},
    {id:'mad-hnd',from:'MAD',to:'HND',label:'MAD → HND',detail:'Madrid · Tokio'}
  ]
});
</script>
```

## Evidence modules

Each visualization uses its HTML table as the source of truth. Embed complete fonts/styles and each necessary script once: charts.js for charts/heatmaps and tables.js for sorting/sparklines. These modules are independent of Three. `NotaGraficas.init(root)` and `NotaTablas.init(root)` are idempotent; get(element).destroy() restores the original markup. Destroy, edit source data, then initialize again. No network or framework is required.

Keep wide figures as direct children of `.hoja` or `.pagina`, using por-seccion for nested sections. `data-valor` uses decimal points without thousands separators. Empty means missing; zero is a measured zero. Visible text includes units. Scales include extremes; missing records are not summed or interpolated. Straight line segments between observations do not imply additional measurements. Exact values remain available in the table.

<a id="recetas-graficas"></a>

## Bar chart

<!-- nota:ejemplo barras -->

```html
<figure class="ancho" id="barras-ejemplo" data-grafica="barras" data-unidad="Horas">
  <details open><summary>Ver los datos de balance de horas</summary>
    <div class="tabla-caja" tabindex="0" role="region" aria-label="Balance de horas, tabla desplazable">
      <table><caption>Balance de horas</caption>
        <thead><tr><th scope="col">Actividad</th><th scope="col">Horas</th></tr></thead>
        <tbody><tr><th scope="row">Investigar</th><td data-valor="60">60 h</td></tr>
<tr><th scope="row">Construir</th><td data-valor="25">25 h</td></tr>
<tr><th scope="row">Revisar</th><td data-valor="15">15 h</td></tr>
<tr><th scope="row">Ajuste de registro</th><td data-valor="-10">−10 h</td></tr></tbody>
      </table>
    </div>
  </details>
  <figcaption>Datos ilustrativos; corte 13-sep-2026.</figcaption>
</figure>
```

**Use and limits:** Compare magnitudes in one unit. Zero stays in the domain; negatives and up to four grouped series are supported. Up to 500 rows; for many categories prefer a sortable table. The drawing keeps an 800 px local minimum and wraps long category labels. This is not a stacked or normalized percentage chart.

Bar charts measure their container, wrap category labels and redraw when a hidden chapter opens or the viewport changes. Numeric labels and the original table remain available; extremely narrow containers may scroll locally. The layout keeps a shared zero baseline for positive and negative values.

## Line chart

<!-- nota:ejemplo lineas -->

```html
<figure class="ancho" id="lineas-ejemplo" data-grafica="lineas" data-unidad="Horas">
  <details open><summary>Ver los datos de tiempo de resolución</summary>
    <div class="tabla-caja" tabindex="0" role="region" aria-label="Tiempo de resolución, tabla desplazable">
      <table><caption>Tiempo de resolución</caption>
        <thead><tr><th scope="col">Etapa</th><th scope="col">Equipo A</th><th scope="col">Equipo B</th></tr></thead>
        <tbody><tr><th scope="row">Entrada</th><td data-valor="12">12 h</td><td data-valor="16">16 h</td></tr>
<tr><th scope="row">Revisión</th><td data-valor="8">8 h</td><td data-valor="11">11 h</td></tr>
<tr><th scope="row">Validación</th><td data-valor="">Sin dato</td><td data-valor="9">9 h</td></tr>
<tr><th scope="row">Cierre</th><td data-valor="6">6 h</td><td data-valor="7">7 h</td></tr></tbody>
      </table>
    </div>
  </details>
  <figcaption>Datos ilustrativos; corte 13-sep-2026.</figcaption>
</figure>
```

**Use and limits:** Follow an ordered sequence of comparable categories. X positions are equally spaced, not dated intervals. Missing values break the line instead of becoming zero. Y covers the observed domain and need not start at zero. Up to four series; line styles and legend numbers distinguish them. No smoothing or inferred confidence intervals. Use time-series for irregular dates.

## Time series

<!-- nota:ejemplo temporal -->

```html
<figure class="ancho" id="temporal-ejemplo" data-grafica="temporal" data-unidad="Solicitudes">
  <details open><summary>Ver los datos de solicitudes por día</summary>
    <div class="tabla-caja" tabindex="0" role="region" aria-label="Solicitudes por día, tabla desplazable">
      <table><caption>Solicitudes por día</caption>
        <thead><tr><th scope="col">Día UTC</th><th scope="col">Solicitudes</th></tr></thead>
        <tbody><tr><th scope="row"><time datetime="2026-09-01">1 sep</time></th><td data-valor="80">80 solicitudes</td></tr>
<tr><th scope="row"><time datetime="2026-09-03">3 sep</time></th><td data-valor="100">100 solicitudes</td></tr>
<tr><th scope="row"><time datetime="2026-09-08">8 sep</time></th><td data-valor="90">90 solicitudes</td></tr>
<tr><th scope="row"><time datetime="2026-09-13">13 sep</time></th><td data-valor="120">120 solicitudes</td></tr></tbody>
      </table>
    </div>
  </details>
  <figcaption>Ejemplo: conteos diarios independientes. Último registro frente al registro anterior (13 sep frente a 8 sep), no totales de ventanas de distinta duración.</figcaption>
</figure>
```

**Use and limits:** Compare dated observations with UTC millisecond positions. Dates must be valid, unique, increasing ISO days. Absolute change is current minus previous; relative change divides by the absolute previous value. A zero baseline makes percentage change undefined; missing values prevent comparison. Name the compared records. No aggregation, timezone repair, causal inference or automatic judgment that an increase is good.

## Scatter plot

<!-- nota:ejemplo dispersion -->

```html
<figure class="ancho" id="dispersion-ejemplo" data-grafica="dispersion" >
  <details open><summary>Ver los datos de carga y latencia</summary>
    <div class="tabla-caja" tabindex="0" role="region" aria-label="Carga y latencia, tabla desplazable">
      <table><caption>Carga y latencia</caption>
        <thead><tr><th scope="col">Muestra</th><th scope="col">Carga (solicitudes/s)</th><th scope="col">Latencia (ms)</th></tr></thead>
        <tbody><tr><th scope="row">A</th><td data-valor="10">10</td><td data-valor="80">80 ms</td></tr>
<tr><th scope="row">B</th><td data-valor="20">20</td><td data-valor="95">95 ms</td></tr>
<tr><th scope="row">C</th><td data-valor="35">35</td><td data-valor="140">140 ms</td></tr>
<tr><th scope="row">D</th><td data-valor="50">50</td><td data-valor="170">170 ms</td></tr>
<tr><th scope="row">E</th><td data-valor="65">65</td><td data-valor="165">165 ms</td></tr></tbody>
      </table>
    </div>
  </details>
  <figcaption>Datos ilustrativos; corte 13-sep-2026.</figcaption>
</figure>
```

**Use and limits:** Explore paired numeric X/Y observations with explicit units. Both coordinates must be finite; up to 500 points. Coincident points overlap but remain distinct in the source table. No regression, jitter, uncertainty estimation or causal inference.

## Distribution

<!-- nota:ejemplo distribucion -->

```html
<figure class="ancho" id="distribucion-ejemplo" data-grafica="distribucion">
  <details open><summary>Ver los datos de duración</summary>
    <div class="tabla-caja" tabindex="0" role="region" aria-label="Distribución de duración, tabla desplazable">
      <table><caption>Duración de 30 sesiones</caption>
        <thead><tr><th scope="col">Duración (min)</th><th scope="col">Sesiones</th><th scope="col">Sesiones/min</th></tr></thead>
        <tbody>
          <tr><th scope="row" data-desde="0" data-hasta="10">0 a menos de 10 min</th><td data-valor="5">5</td><td data-valor="">0,5</td></tr>
          <tr><th scope="row" data-desde="10" data-hasta="20">10 a menos de 20 min</th><td data-valor="15">15</td><td data-valor="">1,5</td></tr>
          <tr><th scope="row" data-desde="20" data-hasta="40">20 a 40 min (incluido)</th><td data-valor="10">10</td><td data-valor="">0,5</td></tr>
        </tbody>
      </table>
    </div>
  </details>
  <figcaption>Ejemplo de 30 sesiones. Altura = frecuencia / ancho del intervalo; el área representa la frecuencia. El último intervalo tiene el doble de ancho.</figcaption>
</figure>
```

<a id="recetas-calor"></a>

**Use and limits:** Show continuous-variable frequencies in explicit increasing, non-overlapping bins. Frequencies are nonnegative integers. Density is frequency divided by bin width; with unequal widths, area represents count. Declare boundary inclusion in the table. The module does not bin raw samples or estimate a probability curve.

## Heatmap

<!-- nota:ejemplo calor -->

```html
<figure class="ancho" id="calor-ejemplo" data-grafica="calor" data-umbrales="0,30,60,90,120,150" data-unidad="Minutos">
  <details open><summary>Ver los datos de tiempo por actividad y día</summary>
    <div class="tabla-caja" tabindex="0" role="region" aria-label="Tiempo por actividad y día, tabla desplazable">
      <table><caption>Tiempo por actividad y día</caption>
        <thead><tr><th scope="col">Actividad</th><th scope="col">Lun</th><th scope="col">Mar</th><th scope="col">Mié</th><th scope="col">Jue</th><th scope="col">Vie</th></tr></thead>
        <tbody><tr><th scope="row">Investigar</th><td data-valor="0">0 min</td><td data-valor="30">30 min</td><td data-valor="60">60 min</td><td data-valor="90">90 min</td><td data-valor="120">120 min</td></tr>
<tr><th scope="row">Construir</th><td data-valor="150">150 min</td><td data-valor="120">120 min</td><td data-valor="90">90 min</td><td data-valor="">Sin dato</td><td data-valor="30">30 min</td></tr>
<tr><th scope="row">Revisar</th><td data-valor="10">10 min</td><td data-valor="20">20 min</td><td data-valor="40">40 min</td><td data-valor="80">80 min</td><td data-valor="110">110 min</td></tr></tbody>
      </table>
    </div>
  </details>
  <figcaption>Ejemplo ilustrativo, minutos por día. Límites de clase: [0,30), [30,60), [60,90), [90,120), [120,150]. Ausencia distinta de cero.</figcaption>
</figure>
```

<a id="recetas-tablas"></a>

**Use and limits:** Compare intensity across two discrete dimensions. Five levels use six increasing boundaries, with the maximum included in the final level. Out-of-domain data produces an error while preserving the source table, never silent saturation. Up to 31×31 cells, local scrolling and a minimum column width. Each cell retains its value; no hidden row-specific scales or gradient encoding.

## Comparison

<!-- nota:ejemplo comparacion -->

```html
<figure class="amplio">
  <div class="tabla-caja" tabindex="0" role="region" aria-label="Comparación de fuentes, desplazable">
    <table class="tabla-comparacion"><caption>Fuentes candidatas · ejemplo</caption>
      <thead><tr><th scope="col">Criterio</th><th scope="col" class="elegida">Registro A · elegido</th><th scope="col">Registro B</th></tr></thead>
      <tbody>
        <tr><th scope="row">Fecha de corte</th><td class="elegida">13-sep-2026</td><td>10-sep-2026</td></tr>
        <tr><th scope="row">Trazabilidad</th><td class="elegida">✓ Identificador por movimiento</td><td>≈ Resumen por día</td></tr>
        <tr><th scope="row">Límite</th><td class="elegida">Falta una sede</td><td>Faltan tres días</td></tr>
      </tbody>
    </table>
  </div>
  <figcaption>Datos ilustrativos. «Elegido» expresa la decisión, no una puntuación automática.</figcaption>
</figure>
```

**Use and limits:** Compare shared properties across a few alternatives. State the decision explicitly instead of relying on color. `.elegida` marks cells; it does not calculate a winner. Add `.densa` for five or more columns. The first column is not automatically sticky, preserving mobile comparison space.

## Totals

<!-- nota:ejemplo totales -->

```html
<figure class="ancho">
  <div class="tabla-caja" tabindex="0" role="region" aria-label="Horas por actividad, tabla ordenable y desplazable">
    <table class="tabla-totales" data-tabla><caption>Horas registradas · ejemplo</caption>
      <thead><tr><th scope="col"><button type="button" data-ordenar="texto">Actividad</button></th><th scope="col"><button type="button" data-ordenar="numero">Horas</button></th></tr></thead>
      <tbody>
        <tr><th scope="row">Investigar</th><td class="numero" data-valor="60">60 h</td></tr>
        <tr><th scope="row">Construir</th><td class="numero" data-valor="25">25 h</td></tr>
        <tr><th scope="row">Revisar</th><td class="numero" data-valor="15">15 h</td></tr>
      </tbody>
      <tfoot><tr><th scope="row">Total de horas registradas</th><td class="numero">100 h</td></tr></tfoot>
    </table>
  </div>
  <figcaption>Ejemplo: 60 + 25 + 15 = 100 h. Los botones ordenan sólo las filas de datos; el total permanece al pie.</figcaption>
</figure>
```

**Use and limits:** Show records with a genuinely additive total. The author supplies the total; do not sum percentages, rates or averages. One tbody, no merged cells or subtotal rows inside it. `data-tabla` enables sorting; numeric cells need `data-valor`. Missing values remain last in both directions, ties retain order and tfoot stays fixed. This simple recipe has no filtering or paging.

## Sparkline

<!-- nota:ejemplo sparkline -->

```html
<figure class="ancho">
  <div class="tabla-caja" tabindex="0" role="region" aria-label="Serie semanal de solicitudes, desplazable">
    <table data-tabla data-min="0" data-max="120"><caption>Solicitudes de lunes a jueves · ejemplo</caption>
      <thead><tr><th scope="col">Canal</th><th scope="col">Serie L / M / X / J, dominio común 0–120</th><th scope="col">Último día</th></tr></thead>
      <tbody>
        <tr><th scope="row">Web</th><td data-sparkline><span class="sparkline-datos"><span data-valor="80">80</span>, <span data-valor="100">100</span>, <span data-valor="90">90</span>, <span data-valor="120">120</span></span></td><td class="numero">120</td></tr>
        <tr><th scope="row">App</th><td data-sparkline><span class="sparkline-datos"><span data-valor="40">40</span>, <span data-valor="">sin dato</span>, <span data-valor="70">70</span>, <span data-valor="60">60</span></span></td><td class="numero">60</td></tr>
      </tbody>
    </table>
  </div>
  <figcaption>Valores ilustrativos. Misma escala Y en ambas filas. El dato ausente corta la línea y todos los valores permanecen escritos.</figcaption>
</figure>
```

<a id="recetas-sonido"></a>

**Use and limits:** Add a trend without separating it from its record. Keep all values in text; the SVG is redundant and aria-hidden. X is equally spaced and all rows must use the same periods. Declare shared `data-min`/`data-max`; out-of-range points are rejected. No per-row autoscaling or irregular-time encoding. Text remains when rendering fails.

## Sound

<!-- nota:ejemplo sonido -->

```html
<aside class="nota-sonido" data-canal-sonido aria-labelledby="sonido-titulo">
  <h3 id="sonido-titulo">Una señal breve.</h3>
  <p>Activa el sonido y prueba una señal. Cada acción también se describe en texto.</p>
  <div><button type="button" data-audio-activar aria-pressed="false">Activar sonido</button></div>
  <div>
    <button type="button" data-audio="accion" data-mensaje="Ejemplo de acción seleccionada.">Acción</button>
    <button type="button" data-audio="confirmacion" data-mensaje="Ejemplo de confirmación completada.">Confirmación</button>
    <button type="button" data-audio="atencion" data-mensaje="Ejemplo: revisa el dato antes de continuar.">Atención</button>
  </div>
  <p role="status" aria-live="polite">Sonido apagado.</p>
</aside>
```

<a id="recetas-escritura"></a>

**Use and limits:** The standard base loads `audio.js` before reader and uses the approved embedded cmrg.me recordings. It starts enabled by preference but requires a real interaction to unlock Web Audio; mute and volume are remembered. Click .9, hover .4, pencil .6 and positive/negative .8 are multiplied by initial master volume .65. Hover playback rate is .9; pencil pitch/duration stay original, without loops or normalization. No runtime downloads. Only explicitly marked interactions produce sound; theme changes, focus and generic scrolling remain silent. Hiding the tab pauses/cancels voices. Inspect `NotaAudio.enabled`, `activeVoices`, `plays` and `samples`; `disable()` stops voices. Provenance is in reference-audio/PROVENANCE.md and tests/evidence/sounds-cmrg.json. The older independent sound.js channel starts muted, does not persist preference, and stops when hidden. Its 60 ms sine signals are a legacy fallback, not the reference recording. A digital gain does not establish physical loudness. init/get/destroy clean up contexts and listeners.

## Writing

<!-- nota:ejemplo escritura -->

```html
<figure class="ancho nota-escritura" data-escritura data-escritura-sonora data-al-ver data-canal-sonido data-duracion="2400">
  <div class="escritura-caja" tabindex="0" role="region" aria-label="Escritura a mano, desplazable">
    <svg viewBox="0 0 420 110" aria-hidden="true">
      <path data-trazo d="M55 51 C43 38 27 51 30 68 C34 83 52 69 54 53 L52 76 Q58 78 65 71"/>
      <path data-trazo d="M96 77 L101 48 L99 69 Q111 41 120 52 L117 74 Q132 42 142 54 L140 74 Q142 81 151 73"/>
      <path data-trazo d="M179 53 C167 40 154 55 157 69 C161 84 179 68 180 54 L178 77 Q185 78 193 71"/>
      <path data-trazo d="M207 77 L212 49 L210 68 Q224 41 235 53 L232 74 Q236 81 246 72"/>
      <path data-trazo d="M274 50 C259 44 249 59 254 72 C260 85 280 75 281 61 Q279 50 271 51 Q270 58 289 56"/>
      <path data-trazo d="M28 91 Q123 84 214 91 T293 89"/>
    </svg>
  </div>
  <div class="escritura-controles">
    <button type="button" data-audio-activar aria-pressed="false">Activar sonido</button>
    <button type="button" data-escribir data-audio="escritura" data-mensaje="Repetir escritura con señal breve si el sonido está activado.">Repetir escritura</button>
    <button type="button" data-finalizar>Mostrar trazo completo</button>
  </div>
  <p data-texto-escritura>«a mano»</p><p class="procedencia">Activa el sonido en Apariencia —o en el control local— y pulsa Repetir para escuchar el trazo.</p>
  <p role="status" aria-live="polite">Trazo completo.</p>
  <figcaption>Gesto ilustrativo original de Margen. 2400 ms repartidos por la longitud de cada trazo; la frase siempre permanece escrita debajo.</figcaption>
</figure>
```

<a id="recetas-three"></a>

**Use and limits:** Use ordered SVG centerline paths for a brief secondary handwritten gesture. It does not turn arbitrary text or filled font outlines into handwriting. Update `data-texto-escritura` whenever paths change; permanent equivalent text remains and SVG is aria-hidden. `data-al-ver` starts once at 30% visibility; otherwise readers choose replay. `data-escritura-sonora` requests approved pencil sound only after audio unlock and respects mute. Supported duration is 100–10000 ms. Leaving view, hiding the tab or reduced motion cancels/completes the gesture with no RAF or queued replay. `NotaEscritura.init/get`, `play()`, `finish()` and `destroy()` manage lifecycle. `play()` respects reduced motion.

## Coordinates

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.1/three.min.js"></script>
```

<!-- nota:ejemplo xyz -->

```html
<figure class="ancho" data-escena="xyz" id="xyz-ejemplo">
  <div class="tabla-caja" tabindex="0" role="region" aria-label="Carga, latencia y memoria, tabla desplazable">
    <table><caption>Tres variables de una misma prueba</caption>
      <thead><tr><th scope="col">Prueba</th><th scope="col">Carga (req/s)</th><th scope="col">Latencia (ms)</th><th scope="col">Memoria (MB)</th></tr></thead>
      <tbody>
        <tr><th scope="row">A</th><td data-valor="10">10</td><td data-valor="80">80</td><td data-valor="100">100</td></tr>
        <tr><th scope="row">B</th><td data-valor="20">20</td><td data-valor="95">95</td><td data-valor="120">120</td></tr>
        <tr><th scope="row">C</th><td data-valor="35">35</td><td data-valor="140">140</td><td data-valor="150">150</td></tr>
        <tr><th scope="row">D</th><td data-valor="50">50</td><td data-valor="170">170</td><td data-valor="210">210</td></tr>
      </tbody>
    </table>
  </div>
  <figcaption>Datos ilustrativos. Posiciones X/Y/Z normalizadas por sus dominios, con valores reales en los ejes. Selecciona un registro para identificarlo; proyección ortográfica, sin tamaños por perspectiva.</figcaption>
</figure>
```

**Use and limits:** Use a third dimension only when it adds a meaningful spatial relationship. One pinned Three.js inclusion can serve all scenes/globes. Load scene.js once. Accepts 1–100 finite complete XYZ records; axes have independent domains, so geometric distance across different units is not a common metric. No regression, jitter or correlation claims. Selection reveals an exact record while dimming others. Keep short labels, units in headers, a 600 px local canvas minimum and the permanent source table. Use a 2D scatterplot when two variables suffice.

## Stages

<!-- nota:ejemplo etapas -->

```html
<figure class="ancho" data-escena="etapas" id="etapas-ejemplo">
  <div class="tabla-caja" tabindex="0" role="region" aria-label="Duración por etapa, tabla desplazable">
    <table><caption>Dónde tarda una solicitud</caption>
      <thead><tr><th scope="col">Etapa</th><th scope="col">Tiempo (ms)</th><th scope="col">Qué ocurre</th></tr></thead>
      <tbody>
        <tr><th scope="row">1 · Recibir</th><td data-valor="20">20 ms</td><td>Leer la entrada.</td></tr>
        <tr><th scope="row">2 · Validar</th><td data-valor="40">40 ms</td><td>Comprobar el contrato.</td></tr>
        <tr><th scope="row">3 · Consultar</th><td data-valor="120">120 ms</td><td>Esperar la fuente de datos.</td></tr>
        <tr><th scope="row">4 · Responder</th><td data-valor="30">30 ms</td><td>Entregar la salida.</td></tr>
      </tbody>
    </table>
  </div>
  <figcaption>Ejemplo ilustrativo: 210 ms si las cuatro etapas ocurren en serie. Alturas proporcionales al tiempo, orden horizontal secuencial; anchura y profundidad constantes sin significado cuantitativo.</figcaption>
</figure>
```

**Use and limits:** Explain ordered process stages with durations. Supports 1–12 stages with nonnegative duration; zero height is not inflated. No dependency planning, parallelism, cumulative waterfall or physical simulation. Do not sum overlapping durations as elapsed time. Selection connects a stage to its written explanation; initial rotation is paused. `NotaEscena.init/get`, `select(index|null)`, `rotate(dx,dy)`, `pause/resume` and idempotent `destroy()` manage instances. Rotation is .15 rad/s and runs only while visible, active and requested without reduced motion. Destroy releases RAF, observers, listeners and WebGL resources while restoring the source table. Destroy/reinitialize to replace data.

## Limits of editorial primitives

These rules supplement individual recipes. Keep appearance tokens complete, one control per document, explicit status text and truthful denominators. Margin notes carry secondary context; handwriting is not a replacement for body copy. Fixed proportion grids require recalculated geometry for different data. A reading ruler indicates position, not comprehension. Code and terminals copy text but do not execute it. Dense tables need local scrolling and checks at 320/390px; they are not virtualized databases. Decorative excerpts must have a complete accessible counterpart. Kept cards do not load external covers automatically. Handwriting is static without its animation module. Globes do not supply political boundaries or measured distances. Call destroy when removing enhanced components.

## Current scope

Margen includes portable HTML/CSS/JS recipes, a Python generator and validator, React adapters, an optional hosted portal, and portable agent instructions. The HTML runtime does not require a framework. React adapters are separate and do not provide one-to-one coverage of every recipe. The registry is not a shadcn installation registry. Maps and dashboards need declared data; no sample implies a live feed. Publishing is an explicit action. See architecture.md and react.md for current boundaries.

## Reports, articles and prototypes

Embed complete fonts/styles and reader once. Add reports.js for data-reporte, prototype.js for data-visor, and globe.js plus pinned Three for journey globes. `NotaReportes.init(root)` and `NotaVisores.init(root)` are idempotent; get(element).destroy() removes enhancement and restores source data. To change a source table, destroy, edit and reinitialize; there is no data observer.

## Appearance

<!-- nota:ejemplo apariencia -->

```html
<div class="pieza" id="apariencia-ejemplo">
  <h3>Una llave pequeña, distintas formas de leer</h3>
  <p>Prueba los tres controles. Comparten las preferencias de esta nota.</p>
  <div class="apariencia-variantes">
    <div><p class="variante-nombre">01 · Círculo</p>
<details class="apariencia-menu orbita" data-apariencia-menu>
  <summary aria-label="Apariencia del documento" aria-controls="panel-apariencia-orbita"><span class="apariencia-icono"><svg class="icono-sol" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/></svg><svg class="icono-luna" viewBox="0 0 24 24" aria-hidden="true"><path d="M20.4 14A8.6 8.6 0 0 1 10 3.6 8.6 8.6 0 1 0 20.4 14Z"/></svg></span></summary>
  <div class="apariencia-panel apariencia-explorador" id="panel-apariencia-orbita" tabindex="0" role="region" aria-label="Opciones de apariencia, desplazables">
    <div class="apariencia-encabezado"><p class="apariencia-titulo">Apariencia</p><span data-tema-actual>Sistema</span></div>
<div class="apariencia-pestanas" role="tablist" aria-label="Preferencias del documento"><button type="button" role="tab" id="preferencia-apariencia-orbita-temas" aria-controls="preferencia-panel-apariencia-orbita-temas" aria-selected="true" tabindex="0" data-preferencia-tab="temas">Temas</button><button type="button" role="tab" id="preferencia-apariencia-orbita-letras" aria-controls="preferencia-panel-apariencia-orbita-letras" aria-selected="false" tabindex="-1" data-preferencia-tab="letras">Letras</button><button type="button" role="tab" id="preferencia-apariencia-orbita-sonido" aria-controls="preferencia-panel-apariencia-orbita-sonido" aria-selected="false" tabindex="-1" data-preferencia-tab="sonido">Sonido</button></div><section role="tabpanel" tabindex="0" id="preferencia-panel-apariencia-orbita-temas" aria-labelledby="preferencia-apariencia-orbita-temas" data-preferencia-panel="temas"><fieldset class="apariencia-modos"><legend>Modo</legend><div><label><input type="radio" name="modo-apariencia-orbita" value="light" data-elegir-modo><span>Claro</span></label><label><input type="radio" name="modo-apariencia-orbita" value="dark" data-elegir-modo><span>Oscuro</span></label><label><input type="radio" name="modo-apariencia-orbita" value="system" data-elegir-modo checked><span>Sistema</span></label></div><p data-modo-estado>Se adapta a la apariencia del dispositivo.</p></fieldset><div class="apariencia-filtros"><label>Buscar tema<input type="search" data-buscar-tema placeholder="Nombre o color" autocomplete="off"></label><label>Categoría<select data-familia-tema><option value="">Todas</option><option value="editorial">Editoriales</option><option value="marca">Marcas</option><option value="tecnico">Técnicos</option><option value="producto">Producto</option><option value="editor">Editores</option></select></label></div><fieldset class="apariencia"><legend class="sr-only">Paleta del documento</legend><div class="apariencia-colores" tabindex="0" role="region" aria-label="Temas disponibles, desplazables"><label data-tema-familia="editorial"><input type="radio" name="color-apariencia-orbita" value="editorial" data-elegir-tema checked><span class="paleta-mini" data-muestra-tema="editorial" aria-hidden="true"><i></i><b></b></span><span>Editorial<small>Papel cálido · cobre</small></span></label>
<label data-tema-familia="editorial"><input type="radio" name="color-apariencia-orbita" value="sea" data-elegir-tema><span class="paleta-mini" data-muestra-tema="sea" aria-hidden="true"><i></i><b></b></span><span>Sea<small>Azul oceánico · menta</small></span></label>
<label data-tema-familia="editorial"><input type="radio" name="color-apariencia-orbita" value="oliva" data-elegir-tema><span class="paleta-mini" data-muestra-tema="oliva" aria-hidden="true"><i></i><b></b></span><span>Oliva<small>Botánico · verde</small></span></label>
<label data-tema-familia="editorial"><input type="radio" name="color-apariencia-orbita" value="arcilla" data-elegir-tema><span class="paleta-mini" data-muestra-tema="arcilla" aria-hidden="true"><i></i><b></b></span><span>Arcilla<small>Terracota · arena</small></span></label>
<label data-tema-familia="editorial"><input type="radio" name="color-apariencia-orbita" value="ciruela" data-elegir-tema><span class="paleta-mini" data-muestra-tema="ciruela" aria-hidden="true"><i></i><b></b></span><span>Ciruela<small>Malva · tinta violeta</small></span></label>
<label data-tema-familia="marca"><input type="radio" name="color-apariencia-orbita" value="liftit" data-elegir-tema><span class="paleta-mini" data-muestra-tema="liftit" aria-hidden="true"><i></i><b></b></span><span>Liftit<small>LMS · Ribbon, Bay y coral</small></span></label>
<label data-tema-familia="marca"><input type="radio" name="color-apariencia-orbita" value="tikin" data-elegir-tema><span class="paleta-mini" data-muestra-tema="tikin" aria-hidden="true"><i></i><b></b></span><span>Tikin<small>Blanco y negro · rojo Tikin</small></span></label>
<label data-tema-familia="marca"><input type="radio" name="color-apariencia-orbita" value="catabum" data-elegir-tema><span class="paleta-mini" data-muestra-tema="catabum" aria-hidden="true"><i></i><b></b></span><span>Catabum<small>Comunidad · violeta y magenta</small></span></label>
<label data-tema-familia="tecnico"><input type="radio" name="color-apariencia-orbita" value="blueprint" data-elegir-tema><span class="paleta-mini" data-muestra-tema="blueprint" aria-hidden="true"><i></i><b></b></span><span>Blueprint<small>Plano · cuadrícula</small></span></label>
<label data-tema-familia="tecnico"><input type="radio" name="color-apariencia-orbita" value="hacker" data-elegir-tema><span class="paleta-mini" data-muestra-tema="hacker" aria-hidden="true"><i></i><b></b></span><span>Hacker<small>Terminal · verde</small></span></label>
<label data-tema-familia="producto"><input type="radio" name="color-apariencia-orbita" value="linear" data-elegir-tema><span class="paleta-mini" data-muestra-tema="linear" aria-hidden="true"><i></i><b></b></span><span>Linear<small>Grafito · lavanda</small></span></label>
<label data-tema-familia="editor"><input type="radio" name="color-apariencia-orbita" value="modern" data-elegir-tema><span class="paleta-mini" data-muestra-tema="modern" aria-hidden="true"><i></i><b></b></span><span>Modern<small>VS Code · azul</small></span></label>
<label data-tema-familia="editor"><input type="radio" name="color-apariencia-orbita" value="github" data-elegir-tema><span class="paleta-mini" data-muestra-tema="github" aria-hidden="true"><i></i><b></b></span><span>GitHub<small>Neutros · azul</small></span></label>
<label data-tema-familia="editor"><input type="radio" name="color-apariencia-orbita" value="catppuccin" data-elegir-tema><span class="paleta-mini" data-muestra-tema="catppuccin" aria-hidden="true"><i></i><b></b></span><span>Catppuccin<small>Latte / Mocha · pastel</small></span></label>
<label data-tema-familia="editor"><input type="radio" name="color-apariencia-orbita" value="solarized" data-elegir-tema><span class="paleta-mini" data-muestra-tema="solarized" aria-hidden="true"><i></i><b></b></span><span>Solarized<small>Marfil / petróleo · cian</small></span></label></div></fieldset><p class="apariencia-resultados" data-temas-resultados role="status">15 temas · claro y oscuro</p><button type="button" data-limpiar-temas hidden>Limpiar búsqueda y filtros</button></section><section role="tabpanel" tabindex="0" id="preferencia-panel-apariencia-orbita-letras" aria-labelledby="preferencia-apariencia-orbita-letras" data-preferencia-panel="letras" hidden><fieldset class="apariencia"><legend>Combinaciones de lectura</legend><div class="apariencia-estilos" tabindex="0" role="region" aria-label="Combinaciones tipográficas, desplazables">
      <label><input type="radio" name="estilo-apariencia-orbita" value="editorial" data-elegir-estilo checked><span class="muestra-letra editorial" aria-hidden="true">Aa</span><span>Editorial<small>Instrument · Geist</small></span></label>
      <label><input type="radio" name="estilo-apariencia-orbita" value="sobrio" data-elegir-estilo><span class="muestra-letra sobrio" aria-hidden="true">Aa</span><span>Sobrio<small>Geist · Geist</small></span></label>
      <label><input type="radio" name="estilo-apariencia-orbita" value="tecnico" data-elegir-estilo><span class="muestra-letra tecnico" aria-hidden="true">Aa</span><span>Técnico<small>Mono · Geist</small></span></label>
    <label><input type="radio" name="estilo-apariencia-orbita" value="libro" data-elegir-estilo><span class="muestra-letra libro" aria-hidden="true">Aa</span><span>Libro<small>Literata · Literata</small></span></label>
    <label><input type="radio" name="estilo-apariencia-orbita" value="revista" data-elegir-estilo><span class="muestra-letra revista" aria-hidden="true">Aa</span><span>Revista<small>Instrument · Literata</small></span></label>
    <label><input type="radio" name="estilo-apariencia-orbita" value="bitacora" data-elegir-estilo><span class="muestra-letra bitacora" aria-hidden="true">Aa</span><span>Bitácora<small>Mono · Literata</small></span></label>
    </div></fieldset><div class="apariencia-muestra" aria-label="Vista previa tipográfica"><strong>Una idea merece espacio.</strong><p>Leer, comparar y decidir. El detalle también cuenta: 1.250,50.</p></div><div class="apariencia-ajustes">
      <button type="button" data-comodidad aria-pressed="false">Lectura cómoda <span aria-hidden="true">✓</span></button>
      <button type="button" data-ver-escritura>Ver escritura animada ↗</button>
      <button type="button" data-papel-tramado aria-pressed="false">Grano de papel <span aria-hidden="true">✓</span></button>
    </div></section><section role="tabpanel" tabindex="0" id="preferencia-panel-apariencia-orbita-sonido" aria-labelledby="preferencia-apariencia-orbita-sonido" data-preferencia-panel="sonido" hidden><fieldset class="apariencia-audio"><legend>Sonido</legend>

      <button type="button" data-audio-prueba>Probar sonido</button>
      <label>Volumen <output data-audio-volumen-valor>65 %</output><input type="range" min="0" max="100" value="65" step="5" aria-label="Volumen del sonido" data-audio-volumen></label>
      <p role="status" data-audio-estado>Sonido habilitado. Se activa después del primer clic. Puedes apagarlo abajo.</p>
    </fieldset><p class="apariencia-nota">Clics, lápiz y pequeños gestos. Sin música de fondo. Tu elección de silencio se recuerda en este navegador.</p><div class="apariencia-pie"><button type="button" data-audio-global aria-pressed="true"><span data-audio-etiqueta>Sonidos activados</span><span class="interruptor" aria-hidden="true"></span></button></div></section>
  </div>
</details>
    </div>
    <div><p class="variante-nombre">02 · Con etiqueta</p>
<details class="apariencia-menu etiqueta" data-apariencia-menu>
  <summary aria-label="Apariencia del documento" aria-controls="panel-apariencia-etiqueta"><span class="apariencia-icono"><svg class="icono-sol" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/></svg><svg class="icono-luna" viewBox="0 0 24 24" aria-hidden="true"><path d="M20.4 14A8.6 8.6 0 0 1 10 3.6 8.6 8.6 0 1 0 20.4 14Z"/></svg></span><span>Apariencia</span><svg class="icono-flecha" viewBox="0 0 24 24" aria-hidden="true"><path d="m8 10 4 4 4-4"/></svg></summary>
  <div class="apariencia-panel apariencia-explorador" id="panel-apariencia-etiqueta" tabindex="0" role="region" aria-label="Opciones de apariencia, desplazables">
    <div class="apariencia-encabezado"><p class="apariencia-titulo">Apariencia</p><span data-tema-actual>Sistema</span></div>
<div class="apariencia-pestanas" role="tablist" aria-label="Preferencias del documento"><button type="button" role="tab" id="preferencia-apariencia-etiqueta-temas" aria-controls="preferencia-panel-apariencia-etiqueta-temas" aria-selected="true" tabindex="0" data-preferencia-tab="temas">Temas</button><button type="button" role="tab" id="preferencia-apariencia-etiqueta-letras" aria-controls="preferencia-panel-apariencia-etiqueta-letras" aria-selected="false" tabindex="-1" data-preferencia-tab="letras">Letras</button><button type="button" role="tab" id="preferencia-apariencia-etiqueta-sonido" aria-controls="preferencia-panel-apariencia-etiqueta-sonido" aria-selected="false" tabindex="-1" data-preferencia-tab="sonido">Sonido</button></div><section role="tabpanel" tabindex="0" id="preferencia-panel-apariencia-etiqueta-temas" aria-labelledby="preferencia-apariencia-etiqueta-temas" data-preferencia-panel="temas"><fieldset class="apariencia-modos"><legend>Modo</legend><div><label><input type="radio" name="modo-apariencia-etiqueta" value="light" data-elegir-modo><span>Claro</span></label><label><input type="radio" name="modo-apariencia-etiqueta" value="dark" data-elegir-modo><span>Oscuro</span></label><label><input type="radio" name="modo-apariencia-etiqueta" value="system" data-elegir-modo checked><span>Sistema</span></label></div><p data-modo-estado>Se adapta a la apariencia del dispositivo.</p></fieldset><div class="apariencia-filtros"><label>Buscar tema<input type="search" data-buscar-tema placeholder="Nombre o color" autocomplete="off"></label><label>Categoría<select data-familia-tema><option value="">Todas</option><option value="editorial">Editoriales</option><option value="marca">Marcas</option><option value="tecnico">Técnicos</option><option value="producto">Producto</option><option value="editor">Editores</option></select></label></div><fieldset class="apariencia"><legend class="sr-only">Paleta del documento</legend><div class="apariencia-colores" tabindex="0" role="region" aria-label="Temas disponibles, desplazables"><label data-tema-familia="editorial"><input type="radio" name="color-apariencia-etiqueta" value="editorial" data-elegir-tema checked><span class="paleta-mini" data-muestra-tema="editorial" aria-hidden="true"><i></i><b></b></span><span>Editorial<small>Papel cálido · cobre</small></span></label>
<label data-tema-familia="editorial"><input type="radio" name="color-apariencia-etiqueta" value="sea" data-elegir-tema><span class="paleta-mini" data-muestra-tema="sea" aria-hidden="true"><i></i><b></b></span><span>Sea<small>Azul oceánico · menta</small></span></label>
<label data-tema-familia="editorial"><input type="radio" name="color-apariencia-etiqueta" value="oliva" data-elegir-tema><span class="paleta-mini" data-muestra-tema="oliva" aria-hidden="true"><i></i><b></b></span><span>Oliva<small>Botánico · verde</small></span></label>
<label data-tema-familia="editorial"><input type="radio" name="color-apariencia-etiqueta" value="arcilla" data-elegir-tema><span class="paleta-mini" data-muestra-tema="arcilla" aria-hidden="true"><i></i><b></b></span><span>Arcilla<small>Terracota · arena</small></span></label>
<label data-tema-familia="editorial"><input type="radio" name="color-apariencia-etiqueta" value="ciruela" data-elegir-tema><span class="paleta-mini" data-muestra-tema="ciruela" aria-hidden="true"><i></i><b></b></span><span>Ciruela<small>Malva · tinta violeta</small></span></label>
<label data-tema-familia="marca"><input type="radio" name="color-apariencia-etiqueta" value="liftit" data-elegir-tema><span class="paleta-mini" data-muestra-tema="liftit" aria-hidden="true"><i></i><b></b></span><span>Liftit<small>LMS · Ribbon, Bay y coral</small></span></label>
<label data-tema-familia="marca"><input type="radio" name="color-apariencia-etiqueta" value="tikin" data-elegir-tema><span class="paleta-mini" data-muestra-tema="tikin" aria-hidden="true"><i></i><b></b></span><span>Tikin<small>Blanco y negro · rojo Tikin</small></span></label>
<label data-tema-familia="marca"><input type="radio" name="color-apariencia-etiqueta" value="catabum" data-elegir-tema><span class="paleta-mini" data-muestra-tema="catabum" aria-hidden="true"><i></i><b></b></span><span>Catabum<small>Comunidad · violeta y magenta</small></span></label>
<label data-tema-familia="tecnico"><input type="radio" name="color-apariencia-etiqueta" value="blueprint" data-elegir-tema><span class="paleta-mini" data-muestra-tema="blueprint" aria-hidden="true"><i></i><b></b></span><span>Blueprint<small>Plano · cuadrícula</small></span></label>
<label data-tema-familia="tecnico"><input type="radio" name="color-apariencia-etiqueta" value="hacker" data-elegir-tema><span class="paleta-mini" data-muestra-tema="hacker" aria-hidden="true"><i></i><b></b></span><span>Hacker<small>Terminal · verde</small></span></label>
<label data-tema-familia="producto"><input type="radio" name="color-apariencia-etiqueta" value="linear" data-elegir-tema><span class="paleta-mini" data-muestra-tema="linear" aria-hidden="true"><i></i><b></b></span><span>Linear<small>Grafito · lavanda</small></span></label>
<label data-tema-familia="editor"><input type="radio" name="color-apariencia-etiqueta" value="modern" data-elegir-tema><span class="paleta-mini" data-muestra-tema="modern" aria-hidden="true"><i></i><b></b></span><span>Modern<small>VS Code · azul</small></span></label>
<label data-tema-familia="editor"><input type="radio" name="color-apariencia-etiqueta" value="github" data-elegir-tema><span class="paleta-mini" data-muestra-tema="github" aria-hidden="true"><i></i><b></b></span><span>GitHub<small>Neutros · azul</small></span></label>
<label data-tema-familia="editor"><input type="radio" name="color-apariencia-etiqueta" value="catppuccin" data-elegir-tema><span class="paleta-mini" data-muestra-tema="catppuccin" aria-hidden="true"><i></i><b></b></span><span>Catppuccin<small>Latte / Mocha · pastel</small></span></label>
<label data-tema-familia="editor"><input type="radio" name="color-apariencia-etiqueta" value="solarized" data-elegir-tema><span class="paleta-mini" data-muestra-tema="solarized" aria-hidden="true"><i></i><b></b></span><span>Solarized<small>Marfil / petróleo · cian</small></span></label></div></fieldset><p class="apariencia-resultados" data-temas-resultados role="status">15 temas · claro y oscuro</p><button type="button" data-limpiar-temas hidden>Limpiar búsqueda y filtros</button></section><section role="tabpanel" tabindex="0" id="preferencia-panel-apariencia-etiqueta-letras" aria-labelledby="preferencia-apariencia-etiqueta-letras" data-preferencia-panel="letras" hidden><fieldset class="apariencia"><legend>Combinaciones de lectura</legend><div class="apariencia-estilos" tabindex="0" role="region" aria-label="Combinaciones tipográficas, desplazables">
      <label><input type="radio" name="estilo-apariencia-etiqueta" value="editorial" data-elegir-estilo checked><span class="muestra-letra editorial" aria-hidden="true">Aa</span><span>Editorial<small>Instrument · Geist</small></span></label>
      <label><input type="radio" name="estilo-apariencia-etiqueta" value="sobrio" data-elegir-estilo><span class="muestra-letra sobrio" aria-hidden="true">Aa</span><span>Sobrio<small>Geist · Geist</small></span></label>
      <label><input type="radio" name="estilo-apariencia-etiqueta" value="tecnico" data-elegir-estilo><span class="muestra-letra tecnico" aria-hidden="true">Aa</span><span>Técnico<small>Mono · Geist</small></span></label>
    <label><input type="radio" name="estilo-apariencia-etiqueta" value="libro" data-elegir-estilo><span class="muestra-letra libro" aria-hidden="true">Aa</span><span>Libro<small>Literata · Literata</small></span></label>
    <label><input type="radio" name="estilo-apariencia-etiqueta" value="revista" data-elegir-estilo><span class="muestra-letra revista" aria-hidden="true">Aa</span><span>Revista<small>Instrument · Literata</small></span></label>
    <label><input type="radio" name="estilo-apariencia-etiqueta" value="bitacora" data-elegir-estilo><span class="muestra-letra bitacora" aria-hidden="true">Aa</span><span>Bitácora<small>Mono · Literata</small></span></label>
    </div></fieldset><div class="apariencia-muestra" aria-label="Vista previa tipográfica"><strong>Una idea merece espacio.</strong><p>Leer, comparar y decidir. El detalle también cuenta: 1.250,50.</p></div><div class="apariencia-ajustes">
      <button type="button" data-comodidad aria-pressed="false">Lectura cómoda <span aria-hidden="true">✓</span></button>
      <button type="button" data-ver-escritura>Ver escritura animada ↗</button>
      <button type="button" data-papel-tramado aria-pressed="false">Grano de papel <span aria-hidden="true">✓</span></button>
    </div></section><section role="tabpanel" tabindex="0" id="preferencia-panel-apariencia-etiqueta-sonido" aria-labelledby="preferencia-apariencia-etiqueta-sonido" data-preferencia-panel="sonido" hidden><fieldset class="apariencia-audio"><legend>Sonido</legend>

      <button type="button" data-audio-prueba>Probar sonido</button>
      <label>Volumen <output data-audio-volumen-valor>65 %</output><input type="range" min="0" max="100" value="65" step="5" aria-label="Volumen del sonido" data-audio-volumen></label>
      <p role="status" data-audio-estado>Sonido habilitado. Se activa después del primer clic. Puedes apagarlo abajo.</p>
    </fieldset><p class="apariencia-nota">Clics, lápiz y pequeños gestos. Sin música de fondo. Tu elección de silencio se recuerda en este navegador.</p><div class="apariencia-pie"><button type="button" data-audio-global aria-pressed="true"><span data-audio-etiqueta>Sonidos activados</span><span class="interruptor" aria-hidden="true"></span></button></div></section>
  </div>
</details>
    </div>
    <div><p class="variante-nombre">03 · Cápsula</p>
<details class="apariencia-menu capsula" data-apariencia-menu>
  <summary aria-label="Apariencia del documento" aria-controls="panel-apariencia-capsula"><span class="apariencia-icono"><svg class="icono-sol" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/></svg><svg class="icono-luna" viewBox="0 0 24 24" aria-hidden="true"><path d="M20.4 14A8.6 8.6 0 0 1 10 3.6 8.6 8.6 0 1 0 20.4 14Z"/></svg></span><span class="apariencia-actual" data-tema-actual>Sistema</span><svg class="icono-flecha" viewBox="0 0 24 24" aria-hidden="true"><path d="m8 10 4 4 4-4"/></svg></summary>
  <div class="apariencia-panel apariencia-explorador" id="panel-apariencia-capsula" tabindex="0" role="region" aria-label="Opciones de apariencia, desplazables">
    <div class="apariencia-encabezado"><p class="apariencia-titulo">Apariencia</p><span data-tema-actual>Sistema</span></div>
<div class="apariencia-pestanas" role="tablist" aria-label="Preferencias del documento"><button type="button" role="tab" id="preferencia-apariencia-capsula-temas" aria-controls="preferencia-panel-apariencia-capsula-temas" aria-selected="true" tabindex="0" data-preferencia-tab="temas">Temas</button><button type="button" role="tab" id="preferencia-apariencia-capsula-letras" aria-controls="preferencia-panel-apariencia-capsula-letras" aria-selected="false" tabindex="-1" data-preferencia-tab="letras">Letras</button><button type="button" role="tab" id="preferencia-apariencia-capsula-sonido" aria-controls="preferencia-panel-apariencia-capsula-sonido" aria-selected="false" tabindex="-1" data-preferencia-tab="sonido">Sonido</button></div><section role="tabpanel" tabindex="0" id="preferencia-panel-apariencia-capsula-temas" aria-labelledby="preferencia-apariencia-capsula-temas" data-preferencia-panel="temas"><fieldset class="apariencia-modos"><legend>Modo</legend><div><label><input type="radio" name="modo-apariencia-capsula" value="light" data-elegir-modo><span>Claro</span></label><label><input type="radio" name="modo-apariencia-capsula" value="dark" data-elegir-modo><span>Oscuro</span></label><label><input type="radio" name="modo-apariencia-capsula" value="system" data-elegir-modo checked><span>Sistema</span></label></div><p data-modo-estado>Se adapta a la apariencia del dispositivo.</p></fieldset><div class="apariencia-filtros"><label>Buscar tema<input type="search" data-buscar-tema placeholder="Nombre o color" autocomplete="off"></label><label>Categoría<select data-familia-tema><option value="">Todas</option><option value="editorial">Editoriales</option><option value="marca">Marcas</option><option value="tecnico">Técnicos</option><option value="producto">Producto</option><option value="editor">Editores</option></select></label></div><fieldset class="apariencia"><legend class="sr-only">Paleta del documento</legend><div class="apariencia-colores" tabindex="0" role="region" aria-label="Temas disponibles, desplazables"><label data-tema-familia="editorial"><input type="radio" name="color-apariencia-capsula" value="editorial" data-elegir-tema checked><span class="paleta-mini" data-muestra-tema="editorial" aria-hidden="true"><i></i><b></b></span><span>Editorial<small>Papel cálido · cobre</small></span></label>
<label data-tema-familia="editorial"><input type="radio" name="color-apariencia-capsula" value="sea" data-elegir-tema><span class="paleta-mini" data-muestra-tema="sea" aria-hidden="true"><i></i><b></b></span><span>Sea<small>Azul oceánico · menta</small></span></label>
<label data-tema-familia="editorial"><input type="radio" name="color-apariencia-capsula" value="oliva" data-elegir-tema><span class="paleta-mini" data-muestra-tema="oliva" aria-hidden="true"><i></i><b></b></span><span>Oliva<small>Botánico · verde</small></span></label>
<label data-tema-familia="editorial"><input type="radio" name="color-apariencia-capsula" value="arcilla" data-elegir-tema><span class="paleta-mini" data-muestra-tema="arcilla" aria-hidden="true"><i></i><b></b></span><span>Arcilla<small>Terracota · arena</small></span></label>
<label data-tema-familia="editorial"><input type="radio" name="color-apariencia-capsula" value="ciruela" data-elegir-tema><span class="paleta-mini" data-muestra-tema="ciruela" aria-hidden="true"><i></i><b></b></span><span>Ciruela<small>Malva · tinta violeta</small></span></label>
<label data-tema-familia="marca"><input type="radio" name="color-apariencia-capsula" value="liftit" data-elegir-tema><span class="paleta-mini" data-muestra-tema="liftit" aria-hidden="true"><i></i><b></b></span><span>Liftit<small>LMS · Ribbon, Bay y coral</small></span></label>
<label data-tema-familia="marca"><input type="radio" name="color-apariencia-capsula" value="tikin" data-elegir-tema><span class="paleta-mini" data-muestra-tema="tikin" aria-hidden="true"><i></i><b></b></span><span>Tikin<small>Blanco y negro · rojo Tikin</small></span></label>
<label data-tema-familia="marca"><input type="radio" name="color-apariencia-capsula" value="catabum" data-elegir-tema><span class="paleta-mini" data-muestra-tema="catabum" aria-hidden="true"><i></i><b></b></span><span>Catabum<small>Comunidad · violeta y magenta</small></span></label>
<label data-tema-familia="tecnico"><input type="radio" name="color-apariencia-capsula" value="blueprint" data-elegir-tema><span class="paleta-mini" data-muestra-tema="blueprint" aria-hidden="true"><i></i><b></b></span><span>Blueprint<small>Plano · cuadrícula</small></span></label>
<label data-tema-familia="tecnico"><input type="radio" name="color-apariencia-capsula" value="hacker" data-elegir-tema><span class="paleta-mini" data-muestra-tema="hacker" aria-hidden="true"><i></i><b></b></span><span>Hacker<small>Terminal · verde</small></span></label>
<label data-tema-familia="producto"><input type="radio" name="color-apariencia-capsula" value="linear" data-elegir-tema><span class="paleta-mini" data-muestra-tema="linear" aria-hidden="true"><i></i><b></b></span><span>Linear<small>Grafito · lavanda</small></span></label>
<label data-tema-familia="editor"><input type="radio" name="color-apariencia-capsula" value="modern" data-elegir-tema><span class="paleta-mini" data-muestra-tema="modern" aria-hidden="true"><i></i><b></b></span><span>Modern<small>VS Code · azul</small></span></label>
<label data-tema-familia="editor"><input type="radio" name="color-apariencia-capsula" value="github" data-elegir-tema><span class="paleta-mini" data-muestra-tema="github" aria-hidden="true"><i></i><b></b></span><span>GitHub<small>Neutros · azul</small></span></label>
<label data-tema-familia="editor"><input type="radio" name="color-apariencia-capsula" value="catppuccin" data-elegir-tema><span class="paleta-mini" data-muestra-tema="catppuccin" aria-hidden="true"><i></i><b></b></span><span>Catppuccin<small>Latte / Mocha · pastel</small></span></label>
<label data-tema-familia="editor"><input type="radio" name="color-apariencia-capsula" value="solarized" data-elegir-tema><span class="paleta-mini" data-muestra-tema="solarized" aria-hidden="true"><i></i><b></b></span><span>Solarized<small>Marfil / petróleo · cian</small></span></label></div></fieldset><p class="apariencia-resultados" data-temas-resultados role="status">15 temas · claro y oscuro</p><button type="button" data-limpiar-temas hidden>Limpiar búsqueda y filtros</button></section><section role="tabpanel" tabindex="0" id="preferencia-panel-apariencia-capsula-letras" aria-labelledby="preferencia-apariencia-capsula-letras" data-preferencia-panel="letras" hidden><fieldset class="apariencia"><legend>Combinaciones de lectura</legend><div class="apariencia-estilos" tabindex="0" role="region" aria-label="Combinaciones tipográficas, desplazables">
      <label><input type="radio" name="estilo-apariencia-capsula" value="editorial" data-elegir-estilo checked><span class="muestra-letra editorial" aria-hidden="true">Aa</span><span>Editorial<small>Instrument · Geist</small></span></label>
      <label><input type="radio" name="estilo-apariencia-capsula" value="sobrio" data-elegir-estilo><span class="muestra-letra sobrio" aria-hidden="true">Aa</span><span>Sobrio<small>Geist · Geist</small></span></label>
      <label><input type="radio" name="estilo-apariencia-capsula" value="tecnico" data-elegir-estilo><span class="muestra-letra tecnico" aria-hidden="true">Aa</span><span>Técnico<small>Mono · Geist</small></span></label>
    <label><input type="radio" name="estilo-apariencia-capsula" value="libro" data-elegir-estilo><span class="muestra-letra libro" aria-hidden="true">Aa</span><span>Libro<small>Literata · Literata</small></span></label>
    <label><input type="radio" name="estilo-apariencia-capsula" value="revista" data-elegir-estilo><span class="muestra-letra revista" aria-hidden="true">Aa</span><span>Revista<small>Instrument · Literata</small></span></label>
    <label><input type="radio" name="estilo-apariencia-capsula" value="bitacora" data-elegir-estilo><span class="muestra-letra bitacora" aria-hidden="true">Aa</span><span>Bitácora<small>Mono · Literata</small></span></label>
    </div></fieldset><div class="apariencia-muestra" aria-label="Vista previa tipográfica"><strong>Una idea merece espacio.</strong><p>Leer, comparar y decidir. El detalle también cuenta: 1.250,50.</p></div><div class="apariencia-ajustes">
      <button type="button" data-comodidad aria-pressed="false">Lectura cómoda <span aria-hidden="true">✓</span></button>
      <button type="button" data-ver-escritura>Ver escritura animada ↗</button>
      <button type="button" data-papel-tramado aria-pressed="false">Grano de papel <span aria-hidden="true">✓</span></button>
    </div></section><section role="tabpanel" tabindex="0" id="preferencia-panel-apariencia-capsula-sonido" aria-labelledby="preferencia-apariencia-capsula-sonido" data-preferencia-panel="sonido" hidden><fieldset class="apariencia-audio"><legend>Sonido</legend>

      <button type="button" data-audio-prueba>Probar sonido</button>
      <label>Volumen <output data-audio-volumen-valor>65 %</output><input type="range" min="0" max="100" value="65" step="5" aria-label="Volumen del sonido" data-audio-volumen></label>
      <p role="status" data-audio-estado>Sonido habilitado. Se activa después del primer clic. Puedes apagarlo abajo.</p>
    </fieldset><p class="apariencia-nota">Clics, lápiz y pequeños gestos. Sin música de fondo. Tu elección de silencio se recuerda en este navegador.</p><div class="apariencia-pie"><button type="button" data-audio-global aria-pressed="true"><span data-audio-etiqueta>Sonidos activados</span><span class="interruptor" aria-hidden="true"></span></button></div></section>
  </div>
</details>
    </div>
  </div>
  <p>Color, tipografía, tamaño y trama se pueden combinar. Las tablas y figuras conservan sus anchos.</p>
</div>
```

**Use and limits:** Use one appearance control per document; the catalog shows variants only for comparison. The shared dock hosts the normal control. Themes, typography and sound are separate tabs with arrows/Home/End navigation. Escape closes and returns focus; outside interaction closes. Theme selection stays open for comparison. Family and light/dark/system mode are independent. Search ignores accents; category, favorites and result count narrow a compact scrollable list. The current family remains named in the header. Sound and volume belong only to Sound. Six heading/body pairs are supported: Instrument Serif/Geist, Geist/Geist, Geist Mono/Geist, Literata/Literata, Instrument Serif/Literata and Geist Mono/Literata. Reenie Beanie remains for annotations. Include reader once, preserve unique IDs and radio names, and define complete tokens when adding a family. Preferences are local unless a connected host stores them; without storage they last for the session. Sound enabled does not prove audible output. Paper grain is independent and removed in print. Check typography reflow on real content. This is not a token editor or prototype device emulator.

## Decision

<!-- nota:ejemplo decision -->

```html
<aside class="pieza ficha-decision" id="decision-ejemplo" aria-labelledby="decision-titulo">
  <p class="ceja">Decisión 02 · ejemplo</p>
  <h3 id="decision-titulo">Una revisión al final del registro</h3>
  <p>Validar la información en un único paso antes de enviarla.</p>
  <dl>
    <div><dt>Por qué</dt><dd>Permite detectar omisiones sin pedir a la persona que repita datos.</dd></div>
    <div><dt>Alternativa considerada</dt><dd>Confirmar cada campo por separado; interrumpe la tarea con demasiada frecuencia.</dd></div>
    <div><dt>Qué falta comprobar</dt><dd>Que se detecten los errores antes del envío en una prueba de uso.</dd></div>
    <div><dt>Cuándo revisarla</dt><dd>Si la revisión final se omite o no ayuda a corregir los errores.</dd></div>
  </dl>
</aside>
```

**Use and limits:** Record a decision's reasoning and conditions for revisiting it. Status, owner and date are editorial facts supplied by the author. This is not an urgent alert, approval workflow, signature or automatic audit trail.

## Chronology

<!-- nota:ejemplo cronologia -->

```html
<div class="pieza" id="cronologia-ejemplo">
  <h3>De la observación a la prueba</h3>
  <ol class="cronologia">
    <li><time datetime="2026-09-01">01 sep 2026</time><div><h4>Observar</h4><p>Se registran las dudas al completar un formulario.</p></div></li>
    <li><time datetime="2026-09-04">04 sep 2026</time><div><h4>Prototipar</h4><p>Se reúnen los campos en dos pasos y se añade una revisión final.</p></div></li>
    <li><time datetime="2026-09-14">14 sep 2026</time><div><h4>Contrastar</h4><p>Se prepara una prueba con tareas, criterios de éxito y observaciones.</p></div></li>
  </ol>
  <p class="procedencia">Cronología ilustrativa; no representa una prueba realizada.</p>
</div>
```

**Use and limits:** Order events and explain what changed. Dates stack above their event on mobile. Spacing does not encode elapsed time or establish causality; use duration charts when duration matters.

## Article

<!-- nota:ejemplo articulo -->

```html
<div class="pieza" id="articulo-ejemplo">
  <h3>El contexto antes de empezar</h3>
  <dl class="ficha-articulo">
    <div><dt>Autoría</dt><dd>Equipo editorial</dd></div>
    <div><dt>Publicado</dt><dd><time datetime="2026-09-14">14 sep 2026</time></dd></div>
    <div><dt>Tipo de pieza</dt><dd>Ensayo con ejemplos</dd></div>
    <div><dt>Revisión</dt><dd>Primera edición</dd></div>
  </dl>
  <p>Una propuesta para separar lo observado de lo supuesto al escribir un informe.</p>
</div>
```

**Use and limits:** Present author, date and editorial status without a large cover. Fields are optional metadata, not controls. Do not invent reading time, credentials or peer review. No automatic SEO or social cards.

## References

<!-- nota:ejemplo referencias -->

```html
<div class="pieza" id="referencias-ejemplo">
  <h3>La evidencia queda a un paso</h3>
  <p>Una afirmación debe permitir volver a su origen
    <a id="llamada-fuente-1" href="#fuente-1" aria-label="Consultar referencia 1">[1]</a>.
    Cuando una cifra es ilustrativa, debe decirlo
    <a id="llamada-fuente-2" href="#fuente-2" aria-label="Consultar referencia 2">[2]</a>.</p>
  <ol class="nota-referencias" aria-label="Referencias del ejemplo">
    <li id="fuente-1" tabindex="-1">Nota metodológica del ejemplo: acompañar cada afirmación con su procedencia.
      <a href="#llamada-fuente-1" aria-label="Volver a la llamada de referencia 1">Volver al texto ↑</a></li>
    <li id="fuente-2" tabindex="-1">Los ejemplos de esta biblioteca no representan datos de producción.
      <a href="#llamada-fuente-2" aria-label="Volver a la llamada de referencia 2">Volver al texto ↑</a></li>
  </ol>
</div>
```

**Use and limits:** Keep lengthy citations and clarifications outside the paragraph with links back. Works without JavaScript. Use unique note/return IDs; repeated citations need distinct return links. Real sources require author, title, date and a verifiable destination. Keep references and calls in the same chapter. This is not automatic bibliography management.

## Glossary

<!-- nota:ejemplo glosario -->

```html
<div class="pieza" id="glosario-ejemplo">
  <h3>Palabras que conviene acordar</h3>
  <dl class="nota-glosario">
    <div><dt><dfn>Observación</dfn></dt><dd>Lo que se registró directamente, con su contexto y procedencia.</dd></div>
    <div><dt><dfn>Hipótesis</dfn></dt><dd>Explicación provisional que puede contrastarse con evidencia.</dd></div>
    <div><dt><dfn>Prototipo</dfn></dt><dd>Representación parcial de una solución para explorar una pregunta.</dd></div>
  </dl>
</div>
```

**Use and limits:** Define report-specific vocabulary in visible text. Definitions are editorial, not hover-only help, automatic search or translation.

## Methodology

<!-- nota:ejemplo metodologia -->

```html
<div class="pieza" id="metodologia-ejemplo">
  <h3>Cómo leer esta evidencia</h3>
  <p>El ejemplo compara la duración declarada de una tarea bajo dos supuestos.</p>
  <details class="metodologia">
    <summary>Consultar método, supuestos y exclusiones</summary>
    <dl class="nota-glosario">
      <div><dt>Unidad</dt><dd>Minutos por operación; volumen mensual constante.</dd></div>
      <div><dt>Supuesto</dt><dd>Las tareas comparadas tienen el mismo alcance.</dd></div>
      <div><dt>Exclusión</dt><dd>No incluye capacitación, espera ni fallos de otros sistemas.</dd></div>
      <div><dt>Límite</dt><dd>El resultado estima capacidad, no demuestra ahorro realizado.</dd></div>
    </dl>
  </details>
</div>
```

**Use and limits:** Disclose methodological detail after stating the main limitation in normal text. Do not hide conditions that change the conclusion. Native details works without JavaScript; reader expands and restores it for print. The component neither executes nor verifies the method.

## Before after

<!-- nota:ejemplo antes-despues -->

```html
<figure class="pieza ancho" id="antes-despues-ejemplo">
  <h3>Un cambio que se puede leer</h3>
  <div class="antes-despues">
    <div><h4>Antes · mensaje genérico</h4><p><del>No se pudo completar la acción.</del></p><p>La persona debe adivinar qué falta.</p></div>
    <div class="despues"><h4>Después · siguiente paso concreto</h4><p><ins>Añade la fecha del registro para continuar.</ins></p><p>El mensaje identifica el campo que necesita atención.</p></div>
  </div>
  <figcaption>Ejemplo de redacción. Las dos versiones permanecen completas; en móvil se leen una después de otra.</figcaption>
</figure>
```

**Use and limits:** Explain an editorial correction or interface/content revision with del/ins semantics. It does not compute diffs or compare screenshots with a slider. Use comparison for alternatives without a temporal relationship.

## Waterfall

<!-- nota:ejemplo cascada -->

```html
<figure class="pieza ancho" id="cascada-ejemplo" data-reporte="cascada">
  <h3>Cómo se llega al resultado</h3>
  <p>Horas disponibles, ajustes y trabajo añadido. Cada tramo empieza donde termina el anterior.</p>
  <div class="tabla-caja" tabindex="0" role="region" aria-label="Balance de capacidad en horas, desplazable">
    <table><caption>Balance ilustrativo · eje X en horas</caption>
      <thead><tr><th scope="col">Concepto</th><th scope="col">Cambio (h)</th><th scope="col">Acumulado (h)</th></tr></thead>
      <tbody>
        <tr><th scope="row">Capacidad inicial</th><td data-valor="120">+120</td><td>120</td></tr>
        <tr><th scope="row">Mantenimiento</th><td data-valor="-30">−30</td><td>90</td></tr>
        <tr><th scope="row">Apoyo adicional</th><td data-valor="20">+20</td><td>110</td></tr>
        <tr><th scope="row">Revisión</th><td data-valor="-15">−15</td><td>95</td></tr>
      </tbody>
      <tfoot><tr><th scope="row">Resultado</th><td>Horas netas</td><td>95</td></tr></tfoot>
    </table>
  </div>
  <figcaption>Ejemplo: 120 − 30 + 20 − 15 = 95 h. Signos y tabla distinguen aumentos y reducciones sin depender del color.</figcaption>
</figure>
```

**Use and limits:** Explain a total through positive and negative contributions in one unit. Three columns, 1–60 rows, finite values and running totals within ±10^9. The first row is a change from zero; no intermediate subtotals or resets. The module calculates the third column rather than reading it as input. Zero and every cumulative extreme stay in the domain. Keep the visible table and 860 px local drawing minimum. Do not add rates, percentages or different currencies.

## Small multiples

<!-- nota:ejemplo multiples -->

```html
<figure class="pieza amplio" id="multiples-ejemplo" data-reporte="multiples">
  <h3>La misma pregunta en tres sedes</h3>
  <p>Solicitudes por semana. Los tres paneles comparten el eje Y; el eje X corresponde al orden de la tabla.</p>
  <div class="tabla-caja" tabindex="0" role="region" aria-label="Solicitudes por sede y semana, desplazable">
    <table><caption>Solicitudes semanales · ejemplo · eje Y en solicitudes</caption>
      <thead><tr><th scope="col">Período</th><th scope="col">Bogotá</th><th scope="col">Medellín</th><th scope="col">Cali</th></tr></thead>
      <tbody>
        <tr><th scope="row">1 · Semana 1</th><td data-valor="40">40</td><td data-valor="20">20</td><td data-valor="30">30</td></tr>
        <tr><th scope="row">2 · Semana 2</th><td data-valor="60">60</td><td data-valor="30">30</td><td data-valor="">Sin dato</td></tr>
        <tr><th scope="row">3 · Semana 3</th><td data-valor="50">50</td><td data-valor="35">35</td><td data-valor="40">40</td></tr>
        <tr><th scope="row">4 · Semana 4</th><td data-valor="80">80</td><td data-valor="40">40</td><td data-valor="45">45</td></tr>
      </tbody>
    </table>
  </div>
  <figcaption>Datos ilustrativos. Escala común de 0 a 80; sin dato corta el trazo. La pendiente no demuestra causalidad.</figcaption>
</figure>
```

**Use and limits:** Compare up to four groups without overlapping their lines. Use the same 2–60 equally spaced periods for every group; irregular dates are unsupported. Finite values up to ±10^9, with missing distinct from zero. Each panel retains a 360 px local minimum. An empty series has an explicit 0–1 auxiliary domain and no invented points.

## Reconciliation

<!-- nota:ejemplo conciliacion -->

```html
<figure class="pieza amplio" id="conciliacion-ejemplo" data-reporte="conciliacion">
  <h3>Una diferencia necesita explicación</h3>
  <div class="tabla-caja densa" tabindex="0" role="region" aria-label="Conciliación de operaciones, desplazable">
    <table class="tabla-calculo"><caption>Operaciones esperadas y observadas · ejemplo</caption>
      <thead><tr><th scope="col">Canal</th><th scope="col">Esperadas</th><th scope="col">Observadas</th><th scope="col">Diferencia</th><th scope="col">Explicación</th></tr></thead>
      <tbody>
        <tr><th scope="row">Web</th><td data-valor="120">120</td><td data-valor="118">118</td><td>−2</td><td>Dos operaciones siguen en revisión.</td></tr>
        <tr><th scope="row">App</th><td data-valor="80">80</td><td data-valor="80">80</td><td>0</td><td>Conteos coincidentes.</td></tr>
        <tr><th scope="row">Asistido</th><td data-valor="30">30</td><td data-valor="33">33</td><td>+3</td><td>Tres registros pendientes de clasificar.</td></tr>
      </tbody>
      <tfoot><tr><th scope="row">Total</th><td>230</td><td>231</td><td>1</td><td>El saldo neto no compensa las diferencias por canal.</td></tr></tfoot>
    </table>
  </div>
  <figcaption>Datos ilustrativos. Diferencia = observado − esperado; una diferencia cero no prueba igualdad de los registros individuales.</figcaption>
</figure>
```

**Use and limits:** Compare expected/observed counts while retaining each row's explanation. Exactly five columns, up to 60 rows, nonnegative integer counts up to 10^9. Missing observed counts make the total incomplete with no net balance. This does not join IDs, detect duplicates or demonstrate financial reconciliation. Explanations are supplied, not inferred.

## Scenario

<!-- nota:ejemplo escenario -->

```html
<div class="pieza ancho" id="escenario-ejemplo" data-reporte="escenario">
  <h3>¿Qué cambia si la tarea toma menos tiempo?</h3>
  <p>Explora capacidad mensual con un volumen fijo. Los valores iniciales son ilustrativos.</p>
  <form class="escenario-form" aria-label="Supuestos de capacidad mensual">
    <label>Operaciones al mes<input name="volumen" type="number" min="0" max="1000000" step="1" value="1200" required></label>
    <label>Antes, minutos por operación<input name="antes" type="number" min="0" max="1440" step="0.1" value="8" required></label>
    <label>Después, minutos por operación<input name="despues" type="number" min="0" max="1440" step="0.1" value="5" required></label>
    <button type="reset">Restablecer supuestos</button>
  </form>
  <div class="escenario-resultados">
    <output data-resultado aria-live="polite">60 h/mes liberadas</output>
    <p data-formula>1.200 × (8 − 5) ÷ 60 = 60 h/mes. Es capacidad estimada, no ahorro monetario ni una predicción.</p>
  </div>
</div>
```

**Use and limits:** Explore a linear capacity model with explicit reversible assumptions. Nonnegative minutes, at most one day per operation and one million operations per month; integer volume and time in tenths. Longer after-times show additional hours. Missing/out-of-range inputs invalidate output instead of retaining a stale result. No forecasting, valuation or data submission; without JavaScript the initial calculation remains.

## Journey

<!-- nota:ejemplo recorrido -->

```html
<figure class="pieza ancho" id="recorrido-ejemplo" data-reporte="recorrido">
  <h3>Seguir el viaje de una idea</h3>
  <p>Una ruta por etapa, con contexto escrito. Selecciona anterior o siguiente para orientar el globo.</p>
  <div data-recorrido-globo></div>
  <div class="acciones">
    <button type="button" data-paso="prev">← Etapa anterior</button>
    <button type="button" data-paso="next">Etapa siguiente →</button>
  </div>
  <p data-recorrido-estado role="status">Tres etapas ilustrativas; el recorrido empieza inmóvil.</p>
  <ol class="recorrido-pasos">
    <li data-ruta="idea-bog-mad"><strong><span data-lugar="BOG" data-lat="4.711" data-lon="-74.0721">Bogotá</span> → <span data-lugar="MAD" data-lat="40.4168" data-lon="-3.7038">Madrid</span></strong><p>Se comparte la primera propuesta para revisión.</p></li>
    <li data-ruta="idea-mad-hnd"><strong><span data-lugar="MAD" data-lat="40.4168" data-lon="-3.7038">Madrid</span> → <span data-lugar="HND" data-lat="35.5494" data-lon="139.7798">Tokio</span></strong><p>La propuesta se convierte en una prueba de interacción.</p></li>
    <li data-ruta="idea-hnd-bog"><strong><span data-lugar="HND" data-lat="35.5494" data-lon="139.7798">Tokio</span> → <span data-lugar="BOG" data-lat="4.711" data-lon="-74.0721">Bogotá</span></strong><p>Las observaciones regresan al equipo que decide.</p></li>
  </ol>
  <figcaption>Relato ficticio. Las coordenadas son geográficas; no representan vuelos, distancias ni actividad real.</figcaption>
</figure>
```

**Use and limits:** Use location and sequence together, keeping written stages visible. Load globe before reports and share one Three.js dependency. `data-lugar` identifies a place; repeated IDs require identical coordinates/name. Every route has a unique ID and two locations. No automatic advance, sound, geocoding or network maps. Starts paused; selection aligns the globe and story. Manual rotation does not change the stage. Without WebGL retain the narrative and route list. Respect reduced motion and destroy resources when removed.

## Prototype

<!-- nota:ejemplo visor -->

```html
<figure class="pieza amplio" id="visor-ejemplo" data-visor data-visor-editor>
  <h3>Una interfaz, varios tamaños</h3>
  <p>Explora los estados vacío, revisión y confirmado de un registro ilustrativo.</p>
  <div class="visor-herramientas visor-iconos" role="group" aria-label="Vista del prototipo"><div class="visor-dispositivos" role="group" aria-label="Dispositivo"><button type="button" class="nota-icono" data-ancho-visor="390" aria-pressed="true" aria-label="Móvil · 390 px" title="Móvil · 390 px"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="2" width="12" height="20" rx="2"/><path d="M10 18h4"/></svg></button><button type="button" class="nota-icono" data-ancho-visor="768" aria-pressed="false" aria-label="Tablet · 768 px" title="Tablet · 768 px"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="2" width="18" height="20" rx="2"/><path d="M10 18h4"/></svg></button><button type="button" class="nota-icono" data-ancho-visor="1024" aria-pressed="false" aria-label="Escritorio · 1024 px" title="Escritorio · 1024 px"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M12 17v4M7 21h10"/></svg></button></div><details class="control-menu visor-opciones"><summary class="nota-icono" aria-label="Proporción y otros tamaños" title="Proporción y otros tamaños"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="5" width="20" height="14" rx="2"/><path d="m8 15 8-6"/></svg></summary><div class="control-panel" tabindex="0" role="region" aria-label="Proporción y tamaños del prototipo"><label class="visor-proporcion"><span class="control-etiqueta">Proporción del marco</span><select data-proporcion-visor aria-label="Proporción del marco"><option value="auto">Altura libre</option><option value="9/16">9:16</option><option value="4/3">4:3</option><option value="16/9">16:9</option><option value="1/1">1:1</option></select></label><button type="button" data-ancho-visor="320" data-cerrar-menu aria-pressed="false">Móvil pequeño · 320 px</button><button type="button" data-ancho-visor="auto" data-cerrar-menu aria-pressed="false">Ancho disponible</button></div></details><button type="button" class="nota-icono" data-girar-visor aria-pressed="false" aria-label="Rotar marco" title="Rotar marco"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="5" width="9" height="14" rx="1"/><path d="M18 4a8 8 0 0 1 3 6m0-6v6h-5"/></svg></button><button type="button" class="nota-icono" data-ajustar-visor aria-pressed="false" aria-label="Ajustar al espacio" title="Ajustar al espacio"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5M8 8h8v8H8z"/></svg></button><button type="button" class="nota-icono" data-reiniciar-visor aria-label="Reiniciar prototipo" title="Reiniciar prototipo"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 10a9 9 0 1 1 2 8M3 4v6h6"/></svg></button></div>
  <p data-visor-estado role="status">Vista inicial: 390 px CSS.</p>
  <div class="visor-caja" tabindex="0" role="region" aria-label="Prototipo interactivo, desplazable horizontalmente"></div>
  <details class="visor-importar"><summary>Embeber mi HTML</summary><label>HTML y CSS locales<textarea data-html-visor rows="8" spellcheck="false" placeholder="Pega aquí un fragmento HTML sin scripts ni recursos externos"></textarea></label><button type="button" data-cargar-html>Cargar en el visor</button><p data-importar-estado role="status">Tu HTML se muestra sólo en este navegador. Reiniciar recupera la muestra original.</p></details>
  <template data-prototipo>
    <style>
      .demo { padding: 24px; min-width: 0; }
      .demo nav { display: flex; flex-wrap: wrap; gap: 8px; padding-bottom: 20px; border-bottom: 1px solid var(--pieza-linea); }
      .demo button { min-height: 44px; padding: 8px 12px; color: var(--pieza-tinta); background: var(--pieza-papel); border: 1px solid var(--pieza-linea); border-radius: 4px; font: inherit; cursor: pointer; }
      .demo button[aria-pressed='true'] { background: var(--pieza-suave); border-color: var(--pieza-acento); }
      .demo h2 { font: 400 32px/1.15 var(--serif); margin: 0 0 16px; }
      .demo p { margin: 0 0 18px; overflow-wrap: anywhere; }
      .demo .contexto { margin-top: 24px; font-size: 14px; color: var(--pieza-secundaria); }
      .demo article { padding-top: 28px; }
      .demo dl { margin: 0 0 20px; display: grid; gap: 12px; }
      .demo dt { font-size: 13px; color: var(--pieza-secundaria); }
      .demo dd { margin: 0; }
      .demo .estado { padding: 16px; border: 1px dashed var(--pieza-linea); }
      @container (min-width: 600px) {
        .demo article { display: grid; grid-template-columns: minmax(0,1.5fr) minmax(0,1fr); gap: 32px; }
        .demo .contexto { margin-top: 0; padding-top: 4px; }
      }
    </style>
    <div class="demo">
      <nav aria-label="Estados del prototipo">
        <button type="button" data-demo-ir="vacio" aria-pressed="true">Vacío</button>
        <button type="button" data-demo-ir="revision" aria-pressed="false">Revisión</button>
        <button type="button" data-demo-ir="confirmado" aria-pressed="false">Confirmado</button>
      </nav>
      <article data-demo-pagina="vacio">
        <div><h2>Tu primer registro</h2><p>Todavía no hay registros en este ejemplo.</p><button type="button" data-demo-ir="revision">Crear borrador de ejemplo</button></div>
        <aside class="contexto"><p>Empieza con un nombre, una fecha y una explicación del movimiento.</p><p class="estado">Estado: sin registros</p></aside>
      </article>
      <article data-demo-pagina="revision" hidden>
        <div><h2>Revisa antes de confirmar</h2><dl><div><dt>Nombre</dt><dd>Sesión de revisión</dd></div><div><dt>Fecha</dt><dd>14 de septiembre de 2026</dd></div><div><dt>Duración</dt><dd>30 minutos</dd></div></dl><button type="button" data-demo-ir="confirmado">Confirmar ejemplo</button></div>
        <aside class="contexto"><p>Comprueba los datos del borrador. Este prototipo usa un registro fijo para explorar la interacción.</p><p class="estado">Estado: pendiente de confirmar</p></aside>
      </article>
      <article data-demo-pagina="confirmado" hidden>
        <div><h2>Registro confirmado</h2><p>La sesión de revisión aparece en el ejemplo con su fecha y duración.</p><button type="button" data-demo-ir="vacio">Volver al inicio</button></div>
        <aside class="contexto"><p class="estado">Estado: confirmado en el prototipo</p><p>No se envió ni se guardó información.</p></aside>
      </article>
    </div>
  </template>
  <div class="visor-fuente"><h4>Estados del ejemplo</h4><ol><li>Vacío: crear un borrador de ejemplo.</li><li>Revisión: sesión del 14-sep-2026, 30 minutos, pendiente de confirmar.</li><li>Confirmado: resultado ilustrativo; no se envían datos.</li></ol></div>
  <figcaption>Vista interactiva local. El ancho conserva píxeles CSS reales; en una pantalla pequeña se desplaza la región completa.</figcaption>
</figure>
```

**Use and limits:** Preview trusted declarative component states at 320, 390, 768, 1024 px or available width. Named icon controls choose device, aspect, rotation and fit; report CSS dimensions and visual scale. Uses Shadow DOM and @container, not a remote iframe or hardware emulator; @media(width) measures the outer window. No scripts, inline event handlers, submissions or arbitrary remote resources. loadHTML accepts up to 100000 characters of trusted local HTML/CSS with raster data images, rejecting scripts, iframes, external URLs and CSS imports. This is not a sanitizer for hostile content. `NotaVisores.get().setWidth()`, `setAspect(auto|9/16|4/3|16/9|1/1)`, `reset()` and `destroy()` preserve the textual/print alternative. Fit can shrink text; use 100% to judge readability.

## Choose and copy from the catalog

The executable template searches recipe names and purposes and exposes each exact snippet in details. Search filters the recipe index, not document sections or reading progress, and ignores case/accents. Without JS the full index remains. Clipboard failure offers manual selection. catalog.js is needed only for data-buscador-recetas. A copied snippet is a content component with documented dependencies; complete generated examples are self-contained documents.

## Tabs

<!-- nota:ejemplo pestanas -->

```html
<div class="pieza pestanas" id="pestanas-ejemplo" data-pestanas>
  <h3>La afirmación, sus datos y su límite</h3>
  <div class="pestanas-caja" tabindex="0" role="region" aria-label="Vistas de la evidencia, desplazables">
    <div class="pestanas-nav" data-tabs-nav aria-label="Vistas de la evidencia">
      <button type="button" id="tab-hallazgo" data-tab="panel-hallazgo">Hallazgo</button>
      <button type="button" id="tab-datos" data-tab="panel-datos">Evidencia</button>
      <button type="button" id="tab-limites" data-tab="panel-limites">Límites</button>
    </div>
  </div>
  <section id="panel-hallazgo" data-tab-panel><h4>Una hipótesis para probar</h4><p>Un resumen antes de confirmar podría reducir las correcciones posteriores.</p><p>Esta es una hipótesis de diseño, no un resultado medido.</p></section>
  <section id="panel-datos" data-tab-panel><h4>Qué necesitamos observar</h4><p>Tiempo hasta confirmar, correcciones posteriores y errores detectados antes del envío.</p><p>Comparar tareas del mismo alcance y conservar los registros de cada sesión.</p></section>
  <section id="panel-limites" data-tab-panel><h4>Qué no se puede concluir</h4><p>Una mejora en velocidad no demuestra menor tasa de error ni ahorro económico.</p><p>El ejemplo no contiene observaciones de personas reales.</p></section>
</div>
```

**Use and limits:** Switch short alternative views of one question. Load tabs after reader. Arrows/Home/End move focus; native Enter/Space and clicks activate. Keep one active tab, named panels, matching unique IDs and source order. Do not hide mandatory steps or essential warnings. No fetching, URL synchronization, persistence or nested instances. All sections remain visible without JavaScript and in print. init/get/destroy preserves original content.

## Finding

<!-- nota:ejemplo hallazgo -->

```html
<aside class="pieza hallazgo" id="hallazgo-ejemplo" aria-labelledby="hallazgo-titulo">
  <p class="ceja">Ficha 01 · hipótesis pendiente</p>
  <h3 id="hallazgo-titulo">Revisar todo antes de confirmar</h3>
  <dl>
    <div><dt>Afirmación</dt><dd>Un resumen final podría facilitar la revisión de los datos antes del envío.</dd></div>
    <div><dt>Evidencia disponible</dt><dd>Existe un prototipo navegable. Todavía no hay sesiones observadas que prueben la hipótesis.</dd></div>
    <div><dt>Límite</dt><dd>La existencia del prototipo no acredita usabilidad ni ahorro de tiempo.</dd></div>
    <div><dt>Siguiente prueba</dt><dd>Observar tareas comparables y registrar duración, errores y correcciones sin cambiar el alcance.</dd></div>
  </dl>
</aside>
```

**Use and limits:** Separate an observed finding, supporting evidence and implication. Use verified data, sources and limits; label hypotheses before presenting them. Static HTML with no hidden state. Avoid repeating this card for every paragraph.

## Report layout

<!-- nota:ejemplo informe -->

```html
<a class="salto" href="#contenido">Saltar al contenido</a>
<header class="edicion-cabecera" id="inicio">
  <div class="edicion-franja"><a class="firma-editorial" href="#resumen" aria-label="Primer capítulo"><span>Margen</span><small>Estudios de producto</small></a><div class="edicion-acciones"><span>Edición 02</span></div></div>
  <div class="edicion-contexto"><span>Una revisión antes de confirmar</span><span>Septiembre de 2026 · ejemplo ilustrativo</span></div>
</header>
<div class="barra capitulos" tabindex="0" role="region" aria-label="Capítulos del informe, desplazables">
  <nav aria-label="Capítulos">
    <button type="button" data-ir="resumen" aria-current="page"><span class="n">01</span>Resumen</button>
    <button type="button" data-ir="evidencia"><span class="n">02</span>Evidencia</button>
    <button type="button" data-ir="prototipo"><span class="n">03</span>Prototipo</button>
    <button type="button" data-ir="siguientes"><span class="n">04</span>Próximos pasos</button>
  </nav>
</div>
<main class="hoja multipagina edicion" data-lectura data-historial lang="es">
<article class="pagina viva" id="resumen" data-pagina>
  <header class="cabecera" id="contenido" tabindex="-1"><p class="ceja">Capítulo 01 / 04</p><h1>Confirmar sin repetir el trabajo.</h1><p class="bajada">Un informe para explorar una decisión de interfaz, consultar sus supuestos y probar la interacción.</p></header>
<section class="seccion"><h2>La decisión que queremos probar</h2><p>Reunir los datos en un resumen editable antes de confirmar una sesión. La persona revisa fecha, duración y estado en un mismo lugar.</p><p>Este documento muestra un formato de informe. Sus cifras son supuestos ilustrativos; no son resultados de producción.</p></section><aside class="pieza hallazgo" id="hallazgo-ejemplo" aria-labelledby="hallazgo-titulo">
  <p class="ceja">Ficha 01 · hipótesis pendiente</p>
  <h3 id="hallazgo-titulo">Revisar todo antes de confirmar</h3>
  <dl>
    <div><dt>Afirmación</dt><dd>Un resumen final podría facilitar la revisión de los datos antes del envío.</dd></div>
    <div><dt>Evidencia disponible</dt><dd>Existe un prototipo navegable. Todavía no hay sesiones observadas que prueben la hipótesis.</dd></div>
    <div><dt>Límite</dt><dd>La existencia del prototipo no acredita usabilidad ni ahorro de tiempo.</dd></div>
    <div><dt>Siguiente prueba</dt><dd>Observar tareas comparables y registrar duración, errores y correcciones sin cambiar el alcance.</dd></div>
  </dl>
</aside><dl class="datos"><div><dt>Pregunta</dt><dd>¿Se detectan errores antes de confirmar?</dd></div><div><dt>Estado</dt><dd>Hipótesis por validar</dd></div><div><dt>Alcance</dt><dd>Una tarea de registro</dd></div><div><dt>Entregable</dt><dd>Prototipo y plan de observación</dd></div></dl>
</article>
<article class="pagina" id="evidencia" data-pagina hidden>
  <header class="cabecera"><p class="ceja">Capítulo 02 / 04</p><h1>Qué sabemos y qué falta medir.</h1><p class="bajada">Separar una hipótesis de sus datos evita presentar una intención como un resultado.</p></header>
<div class="pieza pestanas" id="pestanas-ejemplo" data-pestanas>
  <h3>La afirmación, sus datos y su límite</h3>
  <div class="pestanas-caja" tabindex="0" role="region" aria-label="Vistas de la evidencia, desplazables">
    <div class="pestanas-nav" data-tabs-nav aria-label="Vistas de la evidencia">
      <button type="button" id="tab-hallazgo" data-tab="panel-hallazgo">Hallazgo</button>
      <button type="button" id="tab-datos" data-tab="panel-datos">Evidencia</button>
      <button type="button" id="tab-limites" data-tab="panel-limites">Límites</button>
    </div>
  </div>
  <section id="panel-hallazgo" data-tab-panel><h4>Una hipótesis para probar</h4><p>Un resumen antes de confirmar podría reducir las correcciones posteriores.</p><p>Esta es una hipótesis de diseño, no un resultado medido.</p></section>
  <section id="panel-datos" data-tab-panel><h4>Qué necesitamos observar</h4><p>Tiempo hasta confirmar, correcciones posteriores y errores detectados antes del envío.</p><p>Comparar tareas del mismo alcance y conservar los registros de cada sesión.</p></section>
  <section id="panel-limites" data-tab-panel><h4>Qué no se puede concluir</h4><p>Una mejora en velocidad no demuestra menor tasa de error ni ahorro económico.</p><p>El ejemplo no contiene observaciones de personas reales.</p></section>
</div><figure class="ancho" id="tiempos-ejemplo" data-grafica="barras" data-unidad="Minutos por operación">
  <details open><summary>Ver los supuestos de duración</summary><div class="tabla-caja" tabindex="0" role="region" aria-label="Supuestos de duración, desplazables"><table><caption>Duración supuesta por operación · no medida</caption><thead><tr><th scope="col">Escenario</th><th scope="col">Minutos</th></tr></thead><tbody><tr><th scope="row">Actual supuesto</th><td data-valor="8">8 min</td></tr><tr><th scope="row">Propuesto supuesto</th><td data-valor="5">5 min</td></tr></tbody></table></div></details><figcaption>La gráfica compara dos supuestos con una escala común desde cero. No representa un experimento.</figcaption>
</figure><div class="pieza ancho" id="escenario-ejemplo" data-reporte="escenario">
  <h3>¿Qué cambia si la tarea toma menos tiempo?</h3>
  <p>Explora capacidad mensual con un volumen fijo. Los valores iniciales son ilustrativos.</p>
  <form class="escenario-form" aria-label="Supuestos de capacidad mensual">
    <label>Operaciones al mes<input name="volumen" type="number" min="0" max="1000000" step="1" value="1200" required></label>
    <label>Antes, minutos por operación<input name="antes" type="number" min="0" max="1440" step="0.1" value="8" required></label>
    <label>Después, minutos por operación<input name="despues" type="number" min="0" max="1440" step="0.1" value="5" required></label>
    <button type="reset">Restablecer supuestos</button>
  </form>
  <div class="escenario-resultados">
    <output data-resultado aria-live="polite">60 h/mes liberadas</output>
    <p data-formula>1.200 × (8 − 5) ÷ 60 = 60 h/mes. Es capacidad estimada, no ahorro monetario ni una predicción.</p>
  </div>
</div>
</article>
<article class="pagina" id="prototipo" data-pagina hidden>
  <header class="cabecera"><p class="ceja">Capítulo 03 / 04</p><h1>Recorrer la propuesta.</h1><p class="bajada">Prueba vacío, revisión y confirmación. El visor cambia de ancho sin salir del informe.</p></header>
<figure class="pieza amplio" id="visor-ejemplo" data-visor data-visor-editor>
  <h3>Una interfaz, varios tamaños</h3>
  <p>Explora los estados vacío, revisión y confirmado de un registro ilustrativo.</p>
  <div class="visor-herramientas visor-iconos" role="group" aria-label="Vista del prototipo"><div class="visor-dispositivos" role="group" aria-label="Dispositivo"><button type="button" class="nota-icono" data-ancho-visor="390" aria-pressed="true" aria-label="Móvil · 390 px" title="Móvil · 390 px"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="2" width="12" height="20" rx="2"/><path d="M10 18h4"/></svg></button><button type="button" class="nota-icono" data-ancho-visor="768" aria-pressed="false" aria-label="Tablet · 768 px" title="Tablet · 768 px"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="2" width="18" height="20" rx="2"/><path d="M10 18h4"/></svg></button><button type="button" class="nota-icono" data-ancho-visor="1024" aria-pressed="false" aria-label="Escritorio · 1024 px" title="Escritorio · 1024 px"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M12 17v4M7 21h10"/></svg></button></div><details class="control-menu visor-opciones"><summary class="nota-icono" aria-label="Proporción y otros tamaños" title="Proporción y otros tamaños"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="5" width="20" height="14" rx="2"/><path d="m8 15 8-6"/></svg></summary><div class="control-panel" tabindex="0" role="region" aria-label="Proporción y tamaños del prototipo"><label class="visor-proporcion"><span class="control-etiqueta">Proporción del marco</span><select data-proporcion-visor aria-label="Proporción del marco"><option value="auto">Altura libre</option><option value="9/16">9:16</option><option value="4/3">4:3</option><option value="16/9">16:9</option><option value="1/1">1:1</option></select></label><button type="button" data-ancho-visor="320" data-cerrar-menu aria-pressed="false">Móvil pequeño · 320 px</button><button type="button" data-ancho-visor="auto" data-cerrar-menu aria-pressed="false">Ancho disponible</button></div></details><button type="button" class="nota-icono" data-girar-visor aria-pressed="false" aria-label="Rotar marco" title="Rotar marco"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="5" width="9" height="14" rx="1"/><path d="M18 4a8 8 0 0 1 3 6m0-6v6h-5"/></svg></button><button type="button" class="nota-icono" data-ajustar-visor aria-pressed="false" aria-label="Ajustar al espacio" title="Ajustar al espacio"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5M8 8h8v8H8z"/></svg></button><button type="button" class="nota-icono" data-reiniciar-visor aria-label="Reiniciar prototipo" title="Reiniciar prototipo"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 10a9 9 0 1 1 2 8M3 4v6h6"/></svg></button></div>
  <p data-visor-estado role="status">Vista inicial: 390 px CSS.</p>
  <div class="visor-caja" tabindex="0" role="region" aria-label="Prototipo interactivo, desplazable horizontalmente"></div>
  <template data-prototipo>
    <style>
      .demo { padding: 24px; min-width: 0; }
      .demo nav { display: flex; flex-wrap: wrap; gap: 8px; padding-bottom: 20px; border-bottom: 1px solid var(--pieza-linea); }
      .demo button { min-height: 44px; padding: 8px 12px; color: var(--pieza-tinta); background: var(--pieza-papel); border: 1px solid var(--pieza-linea); border-radius: 4px; font: inherit; cursor: pointer; }
      .demo button[aria-pressed='true'] { background: var(--pieza-suave); border-color: var(--pieza-acento); }
      .demo h2 { font: 400 32px/1.15 var(--serif); margin: 0 0 16px; }
      .demo p { margin: 0 0 18px; overflow-wrap: anywhere; }
      .demo .contexto { margin-top: 24px; font-size: 14px; color: var(--pieza-secundaria); }
      .demo article { padding-top: 28px; }
      .demo dl { margin: 0 0 20px; display: grid; gap: 12px; }
      .demo dt { font-size: 13px; color: var(--pieza-secundaria); }
      .demo dd { margin: 0; }
      .demo .estado { padding: 16px; border: 1px dashed var(--pieza-linea); }
      @container (min-width: 600px) {
        .demo article { display: grid; grid-template-columns: minmax(0,1.5fr) minmax(0,1fr); gap: 32px; }
        .demo .contexto { margin-top: 0; padding-top: 4px; }
      }
    </style>
    <div class="demo">
      <nav aria-label="Estados del prototipo">
        <button type="button" data-demo-ir="vacio" aria-pressed="true">Vacío</button>
        <button type="button" data-demo-ir="revision" aria-pressed="false">Revisión</button>
        <button type="button" data-demo-ir="confirmado" aria-pressed="false">Confirmado</button>
      </nav>
      <article data-demo-pagina="vacio">
        <div><h2>Tu primer registro</h2><p>Todavía no hay registros en este ejemplo.</p><button type="button" data-demo-ir="revision">Crear borrador de ejemplo</button></div>
        <aside class="contexto"><p>Empieza con un nombre, una fecha y una explicación del movimiento.</p><p class="estado">Estado: sin registros</p></aside>
      </article>
      <article data-demo-pagina="revision" hidden>
        <div><h2>Revisa antes de confirmar</h2><dl><div><dt>Nombre</dt><dd>Sesión de revisión</dd></div><div><dt>Fecha</dt><dd>14 de septiembre de 2026</dd></div><div><dt>Duración</dt><dd>30 minutos</dd></div></dl><button type="button" data-demo-ir="confirmado">Confirmar ejemplo</button></div>
        <aside class="contexto"><p>Comprueba los datos del borrador. Este prototipo usa un registro fijo para explorar la interacción.</p><p class="estado">Estado: pendiente de confirmar</p></aside>
      </article>
      <article data-demo-pagina="confirmado" hidden>
        <div><h2>Registro confirmado</h2><p>La sesión de revisión aparece en el ejemplo con su fecha y duración.</p><button type="button" data-demo-ir="vacio">Volver al inicio</button></div>
        <aside class="contexto"><p class="estado">Estado: confirmado en el prototipo</p><p>No se envió ni se guardó información.</p></aside>
      </article>
    </div>
  </template>
  <div class="visor-fuente"><h4>Estados del ejemplo</h4><ol><li>Vacío: crear un borrador de ejemplo.</li><li>Revisión: sesión del 14-sep-2026, 30 minutos, pendiente de confirmar.</li><li>Confirmado: resultado ilustrativo; no se envían datos.</li></ol></div>
  <figcaption>Vista interactiva local. El ancho conserva píxeles CSS reales; en una pantalla pequeña se desplaza la región completa.</figcaption>
</figure>
</article>
<article class="pagina" id="siguientes" data-pagina hidden>
  <header class="cabecera"><p class="ceja">Capítulo 04 / 04</p><h1>La siguiente prueba tiene un propósito.</h1><p class="bajada">Antes de construir más, necesitamos observar si la propuesta resuelve el problema.</p></header>
<section class="seccion"><h2>Observar, comparar, decidir</h2><ol><li>Definir una tarea y mantener el mismo alcance en ambas versiones.</li><li>Registrar duración, errores detectados y correcciones posteriores.</li><li>Conservar el contexto de cada sesión y explicar las exclusiones.</li><li>Revisar la hipótesis con esos datos antes de afirmar una mejora.</li></ol></section><div class="pieza" id="metodologia-ejemplo">
  <h3>Cómo leer esta evidencia</h3>
  <p>El ejemplo compara la duración declarada de una tarea bajo dos supuestos.</p>
  <details class="metodologia">
    <summary>Consultar método, supuestos y exclusiones</summary>
    <dl class="nota-glosario">
      <div><dt>Unidad</dt><dd>Minutos por operación; volumen mensual constante.</dd></div>
      <div><dt>Supuesto</dt><dd>Las tareas comparadas tienen el mismo alcance.</dd></div>
      <div><dt>Exclusión</dt><dd>No incluye capacitación, espera ni fallos de otros sistemas.</dd></div>
      <div><dt>Límite</dt><dd>El resultado estima capacidad, no demuestra ahorro realizado.</dd></div>
    </dl>
  </details>
</div><aside class="aviso ojo"><span class="num">!</span><div><p class="titulo">El prototipo no confirma la hipótesis.</p><p>Este ejemplo no ha registrado sesiones ni enviado datos. El siguiente entregable debe aportar evidencia.</p></div></aside>
</article>
<div class="paginacion" data-paginacion><button type="button" data-nav="prev"><span class="et">Anterior</span><span class="tit"></span></button><button type="button" data-nav="next"><span class="et">Siguiente</span><span class="tit"></span></button></div>
<footer class="pie"><span>Margen · Estudios de producto</span><p>Cuatro capítulos, una pregunta. Datos ilustrativos, sin solicitudes ni registros reales.</p></footer>
</main>
```

**Use and limits:** Compose a report with distinct tasks: understand the decision, inspect evidence, try a proposal and review next steps. Chapter controls are page navigation; local tabs are a tablist. Wide figures belong directly to each `.pagina`. Include reader, chapters, charts, reports, prototype and tabs once; this example does not need Three. `data-historial` enables chapter history; share chapter IDs for deep links. No remote routing. Historical layout shows the first chapter without JavaScript and all chapters in print; use the standard generator for new reports.

## Extended palettes

Oliva, Arcilla and Ciruela are library adaptations rather than colors measured from cmrg.me. Each palette defines evidence, semantic state and WebGL tokens. Color alone does not express certainty or status. Typography and theme are independently selectable. See themes.md for the current family/mode registry; do not infer supported families from this historical example.

## Archive

<!-- nota:ejemplo archivo -->

```html
<section class="pieza ancho" id="archivo-ejemplo" data-archivo>
  <h3>El cuaderno abierto</h3><p>Artículos de ejemplo sobre cómo investigar, explicar y construir.</p>
  <form class="editorial-controles" role="search" aria-label="Buscar publicaciones locales">
    <label>Buscar<input type="search" name="buscar" placeholder="Título o descripción"></label>
    <label>Tema<select name="tema"><option value="">Todos los temas</option><option>Diseño</option><option>Investigación</option><option>Producto</option></select></label>
    <button type="reset">Limpiar filtros</button>
  </form><p data-archivo-estado role="status">3 publicaciones disponibles.</p>
  <div class="publicaciones" data-publicaciones>
    <article data-publicacion data-publicacion-tema="Diseño"><p class="ceja">Diseño · <time datetime="2026-09-14">14 sep 2026</time></p><h4><a href="examples/generated/report.html#resumen">Una revisión antes de confirmar</a></h4><p data-extracto>El recorrido desde una hipótesis hasta una propuesta que se puede probar.</p><p class="procedencia" data-meta>Equipo editorial · Estudio de ejemplo</p></article>
    <article data-publicacion data-publicacion-tema="Investigación"><p class="ceja">Investigación · <time datetime="2026-09-12">12 sep 2026</time></p><h4><a href="examples/generated/report.html#evidencia">Lo que una cifra todavía no demuestra</a></h4><p data-extracto>Separar el dato observado, el supuesto y la siguiente pregunta.</p><p class="procedencia" data-meta>Equipo editorial · Ensayo de ejemplo</p></article>
    <article data-publicacion data-publicacion-tema="Producto"><p class="ceja">Producto · <time datetime="2026-09-10">10 sep 2026</time></p><h4><a href="examples/generated/report.html#prototipo">Probar antes de publicar</a></h4><p data-extracto>Una interfaz local con estados explícitos y varios anchos de lectura.</p><p class="procedencia" data-meta>Equipo editorial · Guía de ejemplo</p></article>
  </div><p data-archivo-vacio hidden>No encontramos publicaciones. Borra la búsqueda o elige otro tema.</p>
</section>
```

**Use and limits:** Filter a short local publication archive by text/topic with editorial.js. Matching ignores accents and supports reset. It is not CMS search, server pagination or an index of thousands of records. Without JavaScript all entries remain visible. Replace example destinations with real links and do not invent dates or reading times.

## Author

<!-- nota:ejemplo autor -->

```html
<aside class="pieza autor-editorial" id="autor-ejemplo" aria-labelledby="autor-nombre">
  <span class="autor-inicial" aria-hidden="true">t</span><div><p class="ceja">Acerca de esta edición</p><h3 id="autor-nombre">Equipo editorial</h3><p>Investigación, producto y documentación. Esta identidad ilustra la ficha; reemplázala por la autoría real del artículo.</p><a href="examples/generated/report.html">Leer el estudio completo →</a></div>
</aside>
```

**Use and limits:** Close an article with author identity and relevant context. Static HTML does not verify identity or contributions. Decorative initials repeat the visible name; an optional photograph needs an embedded data URI and appropriate alternative text.

## Related reading

<!-- nota:ejemplo relacionados -->

```html
<nav class="pieza" id="relacionados-ejemplo" aria-labelledby="relacionados-titulo"><h3 id="relacionados-titulo">Seguir el hilo</h3><ol class="lecturas-relacionadas"><li><span class="ceja">01 · Evidencia</span><a href="examples/generated/report.html#evidencia">Qué sabemos y qué falta medir</a><p>Los supuestos que sostienen la propuesta.</p></li><li><span class="ceja">02 · Práctica</span><a href="examples/generated/report.html#prototipo">Recorrer el prototipo</a><p>Explorar los estados de una tarea.</p></li></ol></nav>
```

**Use and limits:** Suggest deliberately selected next readings with specific reasons and real destinations. No automatic recommendation or personalization. Do not hide primary navigation here.

## Annotations

<!-- nota:ejemplo anotaciones -->

```html
<figure class="pieza ancho" id="anotaciones-ejemplo">
<h3>Tres momentos de una confirmación</h3><div class="diagrama-caja" tabindex="0" role="region" aria-label="Flujo anotado de 720 píxeles, desplazable">
<svg class="plano-anotado" viewBox="0 0 720 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="anotaciones-titulo anotaciones-desc"><title id="anotaciones-titulo">Crear, revisar y confirmar</title><desc id="anotaciones-desc">Uno: crear borrador. Dos: revisar datos. Tres: confirmar. Las tres notas siguientes explican cada paso.</desc><g fill="none" stroke="currentColor"><rect x="10" y="45" width="200" height="110" rx="6"/><rect x="260" y="45" width="200" height="110" rx="6"/><rect x="510" y="45" width="200" height="110" rx="6"/><path d="M210 100h45m-9-7 9 7-9 7M460 100h45m-9-7 9 7-9 7"/></g><g text-anchor="middle" fill="currentColor"><text x="110" y="85">01</text><text x="110" y="120">Crear borrador</text><text x="360" y="85">02</text><text x="360" y="120">Revisar datos</text><text x="610" y="85">03</text><text x="610" y="120">Confirmar</text></g></svg></div>
<ol class="notas-anotadas"><li><strong>Crear.</strong> Los datos permanecen editables; todavía no hay envío.</li><li><strong>Revisar.</strong> Se presenta fecha, duración y nombre en un resumen.</li><li><strong>Confirmar.</strong> La interfaz debe explicar qué se guardó y ofrecer un siguiente paso.</li></ol><figcaption>Flujo conceptual; las distancias no representan tiempo ni cantidad. Las notas contienen toda la explicación del dibujo.</figcaption>
</figure>
```

**Use and limits:** Explain numbered parts of a flow or embedded capture without relying on hover. Keep note numbering aligned with drawing order. Wide diagrams retain scale with local scrolling. No attention measurement or click tracking.

## Revision history

<!-- nota:ejemplo revisiones -->

```html
<section class="pieza" id="revisiones-ejemplo"><h3>Qué cambió en el documento</h3><p class="procedencia">Historial ficticio para mostrar el formato; no describe commits del repositorio.</p><ol class="revisiones-editoriales"><li><p class="ceja"><time datetime="2026-09-14">14 sep 2026</time> · v0.2 · Equipo editorial</p><h4>Se explican las exclusiones</h4><p>El cálculo ahora distingue capacidad estimada de ahorro realizado.</p></li><li><p class="ceja"><time datetime="2026-09-12">12 sep 2026</time> · v0.1 · Equipo editorial</p><h4>Primera propuesta</h4><p>Hipótesis, prototipo y preguntas por observar.</p></li></ol></section>
```

**Use and limits:** Record material changes and corrections using real dates and owners. This is an editorial history, not automatic version control, an audit log or a signature. A build timestamp is not a publication date.

## Criteria

<!-- nota:ejemplo criterios -->

```html
<figure class="pieza amplio" id="criterios-ejemplo"><h3>Comparar sin esconder el criterio</h3><div class="tabla-caja" tabindex="0" role="region" aria-label="Matriz de criterios, desplazable"><table class="matriz-criterios"><caption>Opciones de revisión · comparación conceptual</caption><thead><tr><th scope="col">Criterio</th><th scope="col">Resumen final</th><th scope="col">Revisión por paso</th><th scope="col">Cómo comprobarlo</th></tr></thead><tbody><tr><th scope="row">Ver todo en contexto</th><td>Reúne los campos</td><td>Los reparte entre pantallas</td><td>Observar errores detectados</td></tr><tr><th scope="row">Editar cerca del dato</th><td>Requiere acceso desde el resumen</td><td>Edición dentro de cada paso</td><td>Contar pasos de corrección</td></tr><tr><th scope="row">Tiempo total</th><td>Pendiente de medir</td><td>Pendiente de medir</td><td>Misma tarea, alcance comparable</td></tr></tbody></table></div><figcaption>No hay puntuación agregada: las compensaciones y los datos faltantes quedan visibles.</figcaption></figure>
```

**Use and limits:** Compare alternatives against explicit evidence-based criteria. Missing observations remain pending. Do not invent weights, scores or winners, or turn ordinal labels into numerical precision.

## Risks

<!-- nota:ejemplo riesgos -->

```html
<figure class="pieza amplio" id="riesgos-ejemplo"><h3>Lo que podría salir mal</h3><div class="tabla-caja" tabindex="0" role="region" aria-label="Registro de riesgos, desplazable"><table><caption>Riesgos ilustrativos de un flujo de confirmación</caption><thead><tr><th scope="col">Causa y consecuencia</th><th scope="col">Responsable propuesto</th><th scope="col">Mitigación</th><th scope="col">Señal para revisar</th></tr></thead><tbody><tr><th scope="row">Un resumen incompleto permite confirmar un dato incorrecto</th><td>Diseño de producto</td><td>Mostrar todos los campos críticos y su edición</td><td>Correcciones posteriores a confirmar</td></tr><tr><th scope="row">Un fallo de guardado parece un envío exitoso</th><td>Ingeniería</td><td>Confirmar sólo tras respuesta válida y ofrecer reintento</td><td>Discrepancia entre interfaz y registro</td></tr></tbody></table></div><figcaption>Ejemplo sin probabilidades estimadas. Asigna personas y señales verificables en el proyecto real.</figcaption></figure>
```

**Use and limits:** Describe cause, impact, owner, mitigation and observable warning signals. No automatic probability/severity estimates or multiplication of ordinal scales. The component neither assigns real work nor replaces operational tracking.

## Configuration

<!-- nota:ejemplo configuracion -->

```html
<section class="pieza" id="configuracion-ejemplo" data-config-editorial><h3>La misma publicación, otra edición</h3><p>Elige cómo se presentan las publicaciones del archivo. Los cambios se aplican en este documento.</p><form class="editorial-controles" aria-label="Configuración del archivo"><label>Presentación<select name="disposicion"><option value="rejilla">Rejilla editorial</option><option value="lista">Lista de lectura</option></select></label><label class="editorial-check"><input type="checkbox" name="extractos" checked> Mostrar extractos</label><label class="editorial-check"><input type="checkbox" name="metadatos" checked> Mostrar autoría y formato</label><button type="reset">Restablecer edición</button></form><p data-config-estado role="status">Rejilla editorial con extractos y metadatos.</p><div class="codigo"><div class="cab"><span>Configuración local · JSON</span><button type="button" data-copiar="config-editorial-json">Copiar configuración</button><span class="copia-estado" role="status"></span></div><pre tabindex="0" aria-label="Configuración editorial JSON, desplazable"><code id="config-editorial-json" data-config-json>{"version":1,"disposicion":"rejilla","extractos":true,"metadatos":true}</code></pre></div><p class="procedencia">Configuración de presentación, independiente de la paleta y tipografía del botón de apariencia. No instala un tema de Ghost.</p><p><a href="#archivo-ejemplo">Ver el archivo con esta configuración →</a></p></section>
```

**Use and limits:** Change archive list/grid presentation and information density with editorial.js, producing copyable JSON. Scope is the current document: use one configurator. No preference persistence, JSON import, content changes or Ghost connection. Appearance continues to own palette and typography. Without JavaScript preserve the initial state.

## Component library and local registry

`examples/generated/library.html` groups recipes into navigable chapters with guidance and dependencies. template.html is the continuous catalog; report.html is a narrative example. Use the generated registry for current counts.

`data-enlaces-internos` enables descendant deep links and history in the multipage library. Navigation activates and focuses the target outside the fixed bar; link to the recipe rather than a hidden inner tab. Each chapter has its own outline/progress. Printing includes all chapters; without JS all content remains.

The library is a local HTML catalog, not an installable CMS theme. The optional portal supplies separate authentication/collaboration. registry.json contains versioned HTML, chapter, modules and documentation; it is not the shadcn schema and should not be fetched at reader runtime. `NotaEditorial.init(root)` and get(element).destroy() manage archive/configurator lifecycle. Do not nest archives or duplicate IDs. A Ghost integration would additionally require CMS templates, context and GScan validation.

## Data explorer

<!-- nota:ejemplo explorador -->

```html
<section class="pieza amplio" id="explorador-ejemplo" data-explorador>
<h3>Explorar el registro</h3><p>Seis registros ficticios. Ordena por encabezado, filtra y agrupa sin perder el detalle.</p>
<form class="tabla-herramientas" aria-label="Explorar registros">
<label class="tabla-busqueda"><span class="control-etiqueta">Buscar registros</span><svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><circle cx="10" cy="10" r="6"/><path d="m15 15 5 5"/></svg><input type="search" name="buscar" placeholder="Buscar registros…"></label>
<details class="control-menu"><summary>Filtros <span data-filtros-cuenta></span>⌄</summary><div class="control-panel" tabindex="0" role="region" aria-label="Filtros de registros"><label>Estado<select name="estado"><option value="">Todos los estados</option><option>En revisión</option><option>Confirmado</option></select></label><button type="reset">Limpiar filtros</button></div></details>
<details class="control-menu"><summary>Agrupar ⌄</summary><div class="control-panel" tabindex="0" role="region" aria-label="Agrupar registros"><label>Agrupar por<select name="grupo"><option value="">Sin grupos</option><option value="1">Equipo</option><option value="2">Estado</option></select></label></div></details>
<details class="control-menu"><summary>Columnas ⌄</summary><div class="control-panel" tabindex="0" role="region" aria-label="Columnas visibles"><label><input type="checkbox" data-columna="1" checked> Equipo</label><label><input type="checkbox" data-columna="2" checked> Estado</label><label><input type="checkbox" data-columna="3" checked> Importe COP</label></div></details>
</form>
<p data-explorador-estado role="status">6 registros de ejemplo.</p><div class="tabla-caja" tabindex="0" role="region" aria-label="Registros ordenables y agrupables, desplazables"><table><caption>Movimientos ilustrativos · importes en COP</caption><thead><tr><th scope="col"><details class="control-menu tabla-orden"><summary>Nombre <span data-indicador-orden aria-hidden="true">↕</span></summary><div class="control-panel" tabindex="0" role="region" aria-label="Ordenar por Nombre"><button type="button" data-orden-col="0" data-direccion="1" data-cerrar-menu>↑ Ascendente</button><button type="button" data-orden-col="0" data-direccion="-1" data-cerrar-menu>↓ Descendente</button><button type="button" data-orden-col="0" data-direccion="0" data-cerrar-menu>Restablecer orden</button></div></details></th><th scope="col"><details class="control-menu tabla-orden"><summary>Equipo <span data-indicador-orden aria-hidden="true">↕</span></summary><div class="control-panel" tabindex="0" role="region" aria-label="Ordenar por Equipo"><button type="button" data-orden-col="1" data-direccion="1" data-cerrar-menu>↑ Ascendente</button><button type="button" data-orden-col="1" data-direccion="-1" data-cerrar-menu>↓ Descendente</button><button type="button" data-orden-col="1" data-direccion="0" data-cerrar-menu>Restablecer orden</button></div></details></th><th scope="col"><details class="control-menu tabla-orden"><summary>Estado <span data-indicador-orden aria-hidden="true">↕</span></summary><div class="control-panel" tabindex="0" role="region" aria-label="Ordenar por Estado"><button type="button" data-orden-col="2" data-direccion="1" data-cerrar-menu>↑ Ascendente</button><button type="button" data-orden-col="2" data-direccion="-1" data-cerrar-menu>↓ Descendente</button><button type="button" data-orden-col="2" data-direccion="0" data-cerrar-menu>Restablecer orden</button></div></details></th><th scope="col"><details class="control-menu tabla-orden"><summary>Importe COP <span data-indicador-orden aria-hidden="true">↕</span></summary><div class="control-panel" tabindex="0" role="region" aria-label="Ordenar por Importe COP"><button type="button" data-orden-col="3" data-direccion="1" data-cerrar-menu>↑ Ascendente</button><button type="button" data-orden-col="3" data-direccion="-1" data-cerrar-menu>↓ Descendente</button><button type="button" data-orden-col="3" data-direccion="0" data-cerrar-menu>Restablecer orden</button></div></details></th></tr></thead><tbody>
<tr><th scope="row">Sesión de diseño</th><td>Producto</td><td>En revisión</td><td data-valor="120000">120.000</td></tr>
<tr><th scope="row">Prueba de lectura</th><td>Investigación</td><td>Confirmado</td><td data-valor="80000">80.000</td></tr>
<tr><th scope="row">Revisión móvil</th><td>Producto</td><td>Confirmado</td><td data-valor="60000">60.000</td></tr>
<tr><th scope="row">Entrevista inicial</th><td>Investigación</td><td>En revisión</td><td data-valor="95000">95.000</td></tr>
<tr><th scope="row">Control de calidad</th><td>Ingeniería</td><td>Confirmado</td><td data-valor="140000">140.000</td></tr>
<tr><th scope="row">Ajuste de interfaz</th><td>Ingeniería</td><td>En revisión</td><td data-valor="75000">75.000</td></tr>
</tbody></table></div></section>
```

**Use and limits:** Explore 1–16 columns and up to 2000 local rows. Load table-model before data-explorer and include controls.js. Search stays visible; Filters, Display, Views and More form one action group. Table/Cards changes presentation while preserving source cells and IDs; auto uses cards at 640 px or below. Use stable table/row/cell identifiers for review anchors. Text, finite numbers (`data-valor`, header `data-tipo=numero`) and ISO dates (`data-tipo=fecha`) are supported. State/total column indexes are zero-based and default to 2/3; declare the additive unit and never mix currencies. Facets, AND/OR conditions, empty values, numeric/date ranges, chips, multi-sort, grouping, visibility, density and local saved views share one query model. Incomplete ranges match nothing. Paging offers 10/25/50/100 rows; totals cover all filtered rows while group counters cover the page. Selection persists across pages; selection export includes selected rows outside the filter using visible columns, otherwise exports the filtered set. CSV neutralizes formulas. Printing restores the complete source. No editing, virtualization or remote fetching. `NotaExplorador.init/get/destroy`, `.visible`, `.selected` and `.exportCSV()` preserve original data. The detail action exposes all fields with keyboard access. Fixed columns and widths are open-table adjustments; saved views retain query/grouping/visibility/density/presentation. See docs/mobile-and-tables.md. React uses its native adapter; standalone does not download React/TanStack. The administrator queries the authorized server collection with progressive scrolling.


### Review and presentation update

The reader dock exposes Appearance, one writing action, counted Comments, and Share. Privacy is selected inside the composer; existing thread types stay immutable. The count includes open threads visible to the current reader, including their own private notes, and excludes replies/resolved threads. Nearby pins group by position and open every contained thread. Share owns link/access and creator management; there is no generic More dock.

Record explorers support Table, List, Cards and Board. List reduces per-record spacing; Board groups the existing rows by the selected field (preferring a categorical status/team field initially). The portable board shows the current filtered page, with per-lane counts explicitly scoped to that page. React uses its supplied filtered dataset. Both preserve source records and selection. This is a read-only presentation, not drag-and-drop state editing or an inferred workflow. Saved portable views include presentation. Horizontal scrolling stays local to the board; print returns to a table.

## Rich records and column ordering

See [rich table composition](https://github.com/angelbotto/margen/blob/main/docs/rich-tables.md) for reordered columns, persisted layouts, avatars, media, nested cards and mobile behavior. Scalar values remain authoritative for filtering and CSV.

## Cards

<!-- nota:ejemplo cards -->

```html
<section class="pieza ancho" id="cards-ejemplo"><h3>Tarjetas con un propósito</h3><div class="cards-editoriales">
<article class="card-editorial"><p class="ceja">Lectura / 01</p><h4><a href="examples/generated/report.html#evidencia">De la hipótesis a la evidencia</a></h4><p>Una tarjeta editorial con título, extracto y destino concreto.</p><p class="procedencia">Ensayo de ejemplo · Investigación</p></article>
<article class="card-editorial card-dato"><p class="ceja">Indicador / 02</p><h4>Sesiones revisadas</h4><p class="card-valor">12 <span>de 20</span></p><meter min="0" max="20" value="12" aria-label="12 de 20 sesiones revisadas">60 %</meter><p class="procedencia">60 % · cifras ficticias para mostrar cobertura, no progreso en tiempo real.</p></article>
<article class="card-editorial"><p class="ceja">Proyecto / 03</p><h4>Confirmar con contexto</h4><p><span class="pildora p-medio">Propuesta por validar</span></p><dl><dt>Siguiente paso</dt><dd>Observar una tarea completa.</dd></dl><a href="examples/generated/report.html#prototipo">Probar el prototipo →</a></article>
</div></section>
```

**Use and limits:** Group distinct entities such as articles, metrics or projects in a responsive grid. Link through an explicit title/action. Do not use one card per paragraph or conceal a comparison better served by a table. Values/states need sources; avoid overlapping clicks, fixed heights and truncation. Prototype embedding belongs to the prototype recipe and its trusted-local-content restrictions.

## Review

<!-- nota:ejemplo revision -->

```html
<section class="pieza" id="revision-ejemplo" data-revision>
<h3>Revisar sin perder el contexto</h3><p>Activa Comentar y elige un párrafo, título, figura o card. También puedes seleccionar texto antes de pulsar Comentar.</p><div class="acciones"><button type="button" data-revision-modo aria-pressed="false">Comentar documento</button><button type="button" data-revision-lista>Ver comentarios</button></div><p data-revision-estado role="status">Comentarios locales con exportación para compartir.</p>
<dialog class="revision-dialogo revision-ui" data-revision-editor aria-labelledby="revision-editor-titulo"><form><h2 class="sr-only" id="revision-editor-titulo">Añadir comentario</h2><details class="revision-contexto"><summary title="Ver contexto del punto"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/></svg><span class="sr-only">Contexto del punto</span></summary><p data-revision-contexto tabindex="0" aria-label="Contexto completo del comentario"></p></details><label for="revision-texto">Ajuste que propones</label><textarea id="revision-texto" data-revision-texto rows="1" maxlength="4000" required placeholder="Escribe un comentario…"></textarea><div class="acciones"><button type="button" class="nota-icono" data-revision-guardar aria-label="Guardar comentario" title="Guardar comentario"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 19V5m-6 6 6-6 6 6"/></svg></button><button type="button" class="nota-icono" data-revision-cancelar aria-label="Cerrar comentario" title="Cerrar comentario"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 6 12 12M6 18 18 6"/></svg></button></div></form></dialog>
<dialog class="revision-dialogo revision-ui" data-revision-panel aria-labelledby="revision-panel-titulo"><h2 id="revision-panel-titulo">Comentarios del documento</h2><p class="procedencia">Revisión local: exporta el archivo para compartir los hilos.</p><ol data-revision-notas></ol><div class="codigo"><div class="cab"><span>Prompt de ajustes</span><button type="button" data-copiar="revision-prompt">Copiar prompt</button><span class="copia-estado" role="status"></span></div><pre tabindex="0" aria-label="Prompt con comentarios, desplazable"><code id="revision-prompt" data-revision-prompt>No hay comentarios todavía.</code></pre></div><button type="button" data-revision-cerrar>Cerrar comentarios</button></dialog>
</section>
```

**Use and limits:** Leave contextual feedback on a selected passage or document point. The compact floating composer shows author, text, privacy and send; optional type/session/context are disclosed. Pins are outside document flow. Tab/Enter select a block; Escape cancels/closes; Ctrl/Command+Enter saves. Keep the same document ID across revisions. Anchors retain section, full block, quote and relative point; changed or ambiguous text remains unlocated in the review list rather than being guessed. Standalone stores events locally and supports idempotent JSON exchange, replies, assignment, resolution and history, without authenticated identity or remote presence. Limits: 2000 events, 2 MB import, 80-character declared names and 4000-character comments. Export retains archived/private text and is not redaction. Storage failure reports memory-only persistence. Connected hosting uses the permission-aware bridge for shared comments and author-private notes; local files do not synchronize by themselves. Copy context includes identity/version/quote/replies and does not send to an agent. `NotaRevision.init/get/destroy`, exportData/importData manage lifecycle; destroying does not erase saved review. Treat imported text as untrusted proposals. Multipage fragment links need `data-enlaces-internos`.


### Review and presentation update

The reader dock exposes Appearance, one writing action, counted Comments, and Share. Privacy is selected inside the composer; existing thread types stay immutable. The count includes open threads visible to the current reader, including their own private notes, and excludes replies/resolved threads. Nearby pins group by position and open every contained thread. Share owns link/access and creator management; there is no generic More dock.

Record explorers support Table, List, Cards and Board. List reduces per-record spacing; Board groups the existing rows by the selected field (preferring a categorical status/team field initially). The portable board shows the current filtered page, with per-lane counts explicitly scoped to that page. React uses its supplied filtered dataset. Both preserve source records and selection. This is a read-only presentation, not drag-and-drop state editing or an inferred workflow. Saved portable views include presentation. Horizontal scrolling stays local to the board; print returns to a table.

## Polyglot code

<!-- nota:ejemplo codigo-poliglota -->

```html
<section class="pieza ancho" id="codigo-poliglota"><h3>Código que también se puede leer</h3><p>Elige un lenguaje. El coloreado conserva exactamente el texto que copias.</p><div class="pestanas" data-pestanas><div class="pestanas-caja" tabindex="0" role="region" aria-label="Lenguajes de código, desplazables"><div class="pestanas-nav" data-tabs-nav aria-label="Lenguajes"><button type="button" id="codigo-tab-html" data-tab="codigo-panel-html">HTML</button><button type="button" id="codigo-tab-css" data-tab="codigo-panel-css">CSS</button><button type="button" id="codigo-tab-javascript" data-tab="codigo-panel-javascript">JavaScript</button><button type="button" id="codigo-tab-typescript" data-tab="codigo-panel-typescript">TypeScript</button><button type="button" id="codigo-tab-json" data-tab="codigo-panel-json">JSON</button><button type="button" id="codigo-tab-python" data-tab="codigo-panel-python">Python</button><button type="button" id="codigo-tab-sql" data-tab="codigo-panel-sql">SQL</button><button type="button" id="codigo-tab-shell" data-tab="codigo-panel-shell">Shell</button><button type="button" id="codigo-tab-salida" data-tab="codigo-panel-salida">Salida</button></div></div><section id="codigo-panel-html" data-tab-panel><div class="codigo"><div class="cab"><span>HTML</span><button type="button" data-copiar="muestra-html" aria-label="Copiar HTML" title="Copiar"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H4v13h4"/></svg></button><span class="copia-estado" role="status"></span></div><pre tabindex="0" aria-label="Código HTML, desplazable"><code id="muestra-html" data-lenguaje="html">&lt;article class=&quot;nota&quot;&gt;
  &lt;h2&gt;Una decisión con contexto&lt;/h2&gt;
  &lt;p&gt;La evidencia se conserva completa.&lt;/p&gt;
&lt;/article&gt;</code></pre></div></section><section id="codigo-panel-css" data-tab-panel><div class="codigo"><div class="cab"><span>CSS</span><button type="button" data-copiar="muestra-css" aria-label="Copiar CSS" title="Copiar"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H4v13h4"/></svg></button><span class="copia-estado" role="status"></span></div><pre tabindex="0" aria-label="Código CSS, desplazable"><code id="muestra-css" data-lenguaje="css">:root {
  --espacio: 24px;
}
.nota {
  display: grid;
  gap: var(--espacio);
  color: var(--tinta);
}</code></pre></div></section><section id="codigo-panel-javascript" data-tab-panel><div class="codigo"><div class="cab"><span>JavaScript</span><button type="button" data-copiar="muestra-javascript" aria-label="Copiar JavaScript" title="Copiar"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H4v13h4"/></svg></button><span class="copia-estado" role="status"></span></div><pre tabindex="0" aria-label="Código JavaScript, desplazable"><code id="muestra-javascript" data-lenguaje="javascript">// Datos de ejemplo, sin solicitudes
const registros = [12, 8, 5];
const total = registros.reduce((suma, n) =&gt; suma + n, 0);
console.log(&quot;Total:&quot;, total);</code></pre></div></section><section id="codigo-panel-typescript" data-tab-panel><div class="codigo"><div class="cab"><span>TypeScript</span><button type="button" data-copiar="muestra-typescript" aria-label="Copiar TypeScript" title="Copiar"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H4v13h4"/></svg></button><span class="copia-estado" role="status"></span></div><pre tabindex="0" aria-label="Código TypeScript, desplazable"><code id="muestra-typescript" data-lenguaje="typescript">type Registro = { nombre: string; valor: number };
const ejemplo: Registro = { nombre: &quot;Diseño&quot;, valor: 12 };
function leer(r: Registro): number {
  return r.valor;
}</code></pre></div></section><section id="codigo-panel-json" data-tab-panel><div class="codigo"><div class="cab"><span>JSON</span><button type="button" data-copiar="muestra-json" aria-label="Copiar JSON" title="Copiar"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H4v13h4"/></svg></button><span class="copia-estado" role="status"></span></div><pre tabindex="0" aria-label="Código JSON, desplazable"><code id="muestra-json" data-lenguaje="json">{
  &quot;edicion&quot;: &quot;cuaderno&quot;,
  &quot;paginas&quot;: 9,
  &quot;sonido&quot;: false,
  &quot;fuente&quot;: null
}</code></pre></div></section><section id="codigo-panel-python" data-tab-panel><div class="codigo"><div class="cab"><span>Python</span><button type="button" data-copiar="muestra-python" aria-label="Copiar Python" title="Copiar"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H4v13h4"/></svg></button><span class="copia-estado" role="status"></span></div><pre tabindex="0" aria-label="Código Python, desplazable"><code id="muestra-python" data-lenguaje="python"># Ejemplo local
registros = [12, 8, 5]
def total(valores):
    return sum(valores)
print(&quot;Total:&quot;, total(registros))</code></pre></div></section><section id="codigo-panel-sql" data-tab-panel><div class="codigo"><div class="cab"><span>SQL</span><button type="button" data-copiar="muestra-sql" aria-label="Copiar SQL" title="Copiar"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H4v13h4"/></svg></button><span class="copia-estado" role="status"></span></div><pre tabindex="0" aria-label="Código SQL, desplazable"><code id="muestra-sql" data-lenguaje="sql">-- Consulta ilustrativa
SELECT equipo, SUM(importe) AS total
FROM movimientos
WHERE estado = &#x27;confirmado&#x27;
GROUP BY equipo
ORDER BY total DESC;</code></pre></div></section><section id="codigo-panel-shell" data-tab-panel><div class="codigo"><div class="cab"><span>Shell</span><button type="button" data-copiar="muestra-shell" aria-label="Copiar Shell" title="Copiar"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H4v13h4"/></svg></button><span class="copia-estado" role="status"></span></div><pre tabindex="0" aria-label="Código Shell, desplazable"><code id="muestra-shell" data-lenguaje="shell"># Comprobaciones locales
python3 scripts/build.py
python3 scripts/validate.py
echo &quot;Listo para revisar&quot;</code></pre></div></section><section id="codigo-panel-salida" data-tab-panel><div class="codigo"><div class="cab"><span>Salida</span><button type="button" data-copiar="muestra-salida" aria-label="Copiar Salida" title="Copiar"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H4v13h4"/></svg></button><span class="copia-estado" role="status"></span></div><pre tabindex="0" aria-label="Código Salida, desplazable"><code id="muestra-salida" data-lenguaje="salida">OK     documento generado     44 recetas
WARN   fuente pendiente       2 registros
ERROR  ejemplo rechazado      1 recurso externo</code></pre></div></section></div></section>
```

**Use and limits:** Declare HTML, CSS, JavaScript, TypeScript, JSON, Python, SQL, shell or output with `data-lenguaje`. Load code.js and tabs.js for this example. The lightweight lexer preserves original copy text and editorial spans; it never executes code, compiles, validates or downloads language grammars. Keep local scrolling and theme-aware token contrast.

## Contribution calendar

<!-- nota:ejemplo calendario -->

```html
<figure class="ancho" id="analitica-calendario" data-analitica="calendario" data-unidad="conciliaciones">
  <details><summary>Consultar los 109 días registrados</summary>
  <div class="tabla-caja" tabindex="0" role="region" aria-label="Datos de Calendario de actividad, desplazables">
    <table><caption>Calendario de actividad</caption>
      <thead><tr><th scope="col">Fecha UTC</th><th scope="col">Conciliaciones</th></tr></thead>
      <tbody>
        <tr><th scope="row">2026-05-25</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-05-26</th><td data-valor="7">7</td></tr>
        <tr><th scope="row">2026-05-27</th><td data-valor="14">14</td></tr>
        <tr><th scope="row">2026-05-28</th><td data-valor="21">21</td></tr>
        <tr><th scope="row">2026-05-29</th><td data-valor="3">3</td></tr>
        <tr><th scope="row">2026-05-30</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-05-31</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-06-01</th><td data-valor="2">2</td></tr>
        <tr><th scope="row">2026-06-02</th><td data-valor="9">9</td></tr>
        <tr><th scope="row">2026-06-03</th><td data-valor="16">16</td></tr>
        <tr><th scope="row">2026-06-04</th><td data-valor="23">23</td></tr>
        <tr><th scope="row">2026-06-05</th><td data-valor="5">5</td></tr>
        <tr><th scope="row">2026-06-06</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-06-07</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-06-08</th><td data-valor="4">4</td></tr>
        <tr><th scope="row">2026-06-09</th><td data-valor="11">11</td></tr>
        <tr><th scope="row">2026-06-10</th><td data-valor="18">18</td></tr>
        <tr><th scope="row">2026-06-11</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-06-12</th><td data-valor="7">7</td></tr>
        <tr><th scope="row">2026-06-13</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-06-14</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-06-15</th><td data-valor="6">6</td></tr>
        <tr><th scope="row">2026-06-16</th><td data-valor="13">13</td></tr>
        <tr><th scope="row">2026-06-17</th><td data-valor="20">20</td></tr>
        <tr><th scope="row">2026-06-18</th><td data-valor="2">2</td></tr>
        <tr><th scope="row">2026-06-19</th><td data-valor="9">9</td></tr>
        <tr><th scope="row">2026-06-20</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-06-21</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-06-22</th><td data-valor="8">8</td></tr>
        <tr><th scope="row">2026-06-23</th><td data-valor="15">15</td></tr>
        <tr><th scope="row">2026-06-24</th><td data-valor="22">22</td></tr>
        <tr><th scope="row">2026-06-27</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-06-28</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-06-29</th><td data-valor="10">10</td></tr>
        <tr><th scope="row">2026-06-30</th><td data-valor="17">17</td></tr>
        <tr><th scope="row">2026-07-01</th><td data-valor="24">24</td></tr>
        <tr><th scope="row">2026-07-02</th><td data-valor="6">6</td></tr>
        <tr><th scope="row">2026-07-03</th><td data-valor="13">13</td></tr>
        <tr><th scope="row">2026-07-04</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-07-05</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-07-06</th><td data-valor="12">12</td></tr>
        <tr><th scope="row">2026-07-07</th><td data-valor="19">19</td></tr>
        <tr><th scope="row">2026-07-08</th><td data-valor="1">1</td></tr>
        <tr><th scope="row">2026-07-09</th><td data-valor="8">8</td></tr>
        <tr><th scope="row">2026-07-10</th><td data-valor="15">15</td></tr>
        <tr><th scope="row">2026-07-11</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-07-12</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-07-13</th><td data-valor="14">14</td></tr>
        <tr><th scope="row">2026-07-14</th><td data-valor="21">21</td></tr>
        <tr><th scope="row">2026-07-15</th><td data-valor="3">3</td></tr>
        <tr><th scope="row">2026-07-16</th><td data-valor="10">10</td></tr>
        <tr><th scope="row">2026-07-17</th><td data-valor="17">17</td></tr>
        <tr><th scope="row">2026-07-18</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-07-19</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-07-20</th><td data-valor="16">16</td></tr>
        <tr><th scope="row">2026-07-21</th><td data-valor="23">23</td></tr>
        <tr><th scope="row">2026-07-22</th><td data-valor="5">5</td></tr>
        <tr><th scope="row">2026-07-23</th><td data-valor="12">12</td></tr>
        <tr><th scope="row">2026-07-24</th><td data-valor="19">19</td></tr>
        <tr><th scope="row">2026-07-25</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-07-26</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-07-27</th><td data-valor="18">18</td></tr>
        <tr><th scope="row">2026-07-28</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-07-29</th><td data-valor="7">7</td></tr>
        <tr><th scope="row">2026-07-30</th><td data-valor="14">14</td></tr>
        <tr><th scope="row">2026-07-31</th><td data-valor="21">21</td></tr>
        <tr><th scope="row">2026-08-01</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-08-02</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-08-03</th><td data-valor="20">20</td></tr>
        <tr><th scope="row">2026-08-04</th><td data-valor="2">2</td></tr>
        <tr><th scope="row">2026-08-05</th><td data-valor="9">9</td></tr>
        <tr><th scope="row">2026-08-06</th><td data-valor="16">16</td></tr>
        <tr><th scope="row">2026-08-07</th><td data-valor="23">23</td></tr>
        <tr><th scope="row">2026-08-08</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-08-09</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-08-10</th><td data-valor="22">22</td></tr>
        <tr><th scope="row">2026-08-11</th><td data-valor="4">4</td></tr>
        <tr><th scope="row">2026-08-12</th><td data-valor="11">11</td></tr>
        <tr><th scope="row">2026-08-14</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-08-15</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-08-16</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-08-17</th><td data-valor="24">24</td></tr>
        <tr><th scope="row">2026-08-18</th><td data-valor="6">6</td></tr>
        <tr><th scope="row">2026-08-19</th><td data-valor="13">13</td></tr>
        <tr><th scope="row">2026-08-20</th><td data-valor="20">20</td></tr>
        <tr><th scope="row">2026-08-21</th><td data-valor="2">2</td></tr>
        <tr><th scope="row">2026-08-22</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-08-23</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-08-24</th><td data-valor="1">1</td></tr>
        <tr><th scope="row">2026-08-25</th><td data-valor="8">8</td></tr>
        <tr><th scope="row">2026-08-26</th><td data-valor="15">15</td></tr>
        <tr><th scope="row">2026-08-27</th><td data-valor="22">22</td></tr>
        <tr><th scope="row">2026-08-28</th><td data-valor="4">4</td></tr>
        <tr><th scope="row">2026-08-29</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-08-30</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-08-31</th><td data-valor="3">3</td></tr>
        <tr><th scope="row">2026-09-01</th><td data-valor="10">10</td></tr>
        <tr><th scope="row">2026-09-02</th><td data-valor="17">17</td></tr>
        <tr><th scope="row">2026-09-03</th><td data-valor="24">24</td></tr>
        <tr><th scope="row">2026-09-04</th><td data-valor="6">6</td></tr>
        <tr><th scope="row">2026-09-05</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-09-06</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-09-07</th><td data-valor="5">5</td></tr>
        <tr><th scope="row">2026-09-08</th><td data-valor="12">12</td></tr>
        <tr><th scope="row">2026-09-09</th><td data-valor="19">19</td></tr>
        <tr><th scope="row">2026-09-10</th><td data-valor="1">1</td></tr>
        <tr><th scope="row">2026-09-11</th><td data-valor="8">8</td></tr>
        <tr><th scope="row">2026-09-12</th><td data-valor="0">0</td></tr>
        <tr><th scope="row">2026-09-13</th><td data-valor="0">0</td></tr>
      </tbody>
    </table>
  </div>
  </details>
  <figcaption>Datos ficticios, 25 may–13 sep 2026. Intensidad diaria, cero distinto de ausencia.</figcaption>
</figure>
```

**Use and limits:** Show continuity and gaps in daily activity. analytics.js accepts 1–366 unique UTC ISO dates over at most 366 consecutive days, with nonnegative integer counts. Missing rows use a diagonal rather than implied zero. Weeks start Monday; thresholds derive from the observed maximum, not percentiles. A selector exposes every day's values. No GitHub connection or productivity inference.

## Pie chart

<!-- nota:ejemplo torta -->

```html
<figure class="ancho" id="analitica-torta" data-analitica="torta" data-unidad="millones COP">
  <div class="tabla-caja" tabindex="0" role="region" aria-label="Datos de Torta y donut de composición, desplazables">
    <table><caption>Torta y donut de composición</caption>
      <thead><tr><th scope="col">Destino</th><th scope="col">Millones COP</th></tr></thead>
      <tbody>
        <tr><th scope="row">Operación</th><td data-valor="48">48</td></tr>
        <tr><th scope="row">Reserva</th><td data-valor="24">24</td></tr>
        <tr><th scope="row">Tecnología</th><td data-valor="18">18</td></tr>
        <tr><th scope="row">Comisiones</th><td data-valor="10">10</td></tr>
      </tbody>
    </table>
  </div>
  <figcaption>Distribución ficticia de 100 millones COP. El botón cambia torta ↔ donut sin cambiar cifras.</figcaption>
</figure>
```

**Use and limits:** Show parts of a positive whole with 1–6 unique nonnegative categories. Zero remains in legend/table without an invented sector. Percentages use the row total, not an external denominator. No negatives or double counting. Names/values remain authoritative where colors repeat. Prefer bars for close comparisons or many categories.

## Area chart

<!-- nota:ejemplo areas -->

```html
<figure class="ancho" id="analitica-areas" data-analitica="areas" data-unidad="millones COP">
  <div class="tabla-caja" tabindex="0" role="region" aria-label="Datos de Áreas apiladas de ingresos, desplazables">
    <table><caption>Áreas apiladas de ingresos</caption>
      <thead><tr><th scope="col">Fecha UTC</th><th scope="col">Servicios</th><th scope="col">Suscripciones</th><th scope="col">Comisiones</th></tr></thead>
      <tbody>
        <tr><th scope="row">2026-04-01</th><td data-valor="24">24</td><td data-valor="12">12</td><td data-valor="4">4</td></tr>
        <tr><th scope="row">2026-05-01</th><td data-valor="28">28</td><td data-valor="16">16</td><td data-valor="6">6</td></tr>
        <tr><th scope="row">2026-06-01</th><td data-valor="26">26</td><td data-valor="20">20</td><td data-valor="7">7</td></tr>
        <tr><th scope="row">2026-07-01</th><td data-valor="35">35</td><td data-valor="24">24</td><td data-valor="9">9</td></tr>
        <tr><th scope="row">2026-08-01</th><td data-valor="40">40</td><td data-valor="28">28</td><td data-valor="12">12</td></tr>
      </tbody>
    </table>
  </div>
  <figcaption>Ingresos ficticios en millones COP; cada banda suma al total. No representan utilidades.</figcaption>
</figure>
```

**Use and limits:** Show a total and its composition over time. Exactly three additive series in one unit, 2–60 unique ISO dates and nonnegative values. Real date spacing and linear segments connect observations without creating transactions or missing-day data. No mixed currencies. An all-zero total has an explicit auxiliary 0–1 domain. Use lines/small multiples for precise comparison of middle bands.

## Box plot

<!-- nota:ejemplo caja -->

```html
<figure class="ancho" id="analitica-caja" data-analitica="caja" data-unidad="minutos">
  <div class="tabla-caja densa" tabindex="0" role="region" aria-label="Datos de Caja y bigotes de entrega, desplazables">
    <table><caption>Caja y bigotes de entrega</caption>
      <thead><tr><th scope="col">Zona</th><th scope="col">Mínimo</th><th scope="col">Q1</th><th scope="col">Mediana</th><th scope="col">Q3</th><th scope="col">Máximo</th></tr></thead>
      <tbody>
        <tr><th scope="row">Norte</th><td data-valor="20">20</td><td data-valor="32">32</td><td data-valor="40">40</td><td data-valor="55">55</td><td data-valor="90">90</td></tr>
        <tr><th scope="row">Centro</th><td data-valor="15">15</td><td data-valor="25">25</td><td data-valor="32">32</td><td data-valor="45">45</td><td data-valor="72">72</td></tr>
        <tr><th scope="row">Sur</th><td data-valor="25">25</td><td data-valor="42">42</td><td data-valor="55">55</td><td data-valor="68">68</td><td data-valor="110">110</td></tr>
      </tbody>
    </table>
  </div>
  <figcaption>Resumen ficticio de tiempos de entrega. Bigotes = mínimo y máximo, no 1,5 IQR.</figcaption>
</figure>
```

**Use and limits:** Compare dispersion and median using five ordered statistics per group. Up to 24 groups, same units and calculation method. Does not derive quartiles from raw samples or identify outliers. Constant groups receive a domain expanded by one on each side. Use distribution for bin counts.

## Candlestick

<!-- nota:ejemplo velas -->

```html
<figure class="ancho" id="analitica-velas" data-analitica="velas" data-unidad="índice base 100">
  <div class="tabla-caja densa" tabindex="0" role="region" aria-label="Datos de Velas financieras OHLC, desplazables">
    <table><caption>Velas financieras OHLC</caption>
      <thead><tr><th scope="col">Fecha UTC</th><th scope="col">Apertura</th><th scope="col">Máximo</th><th scope="col">Mínimo</th><th scope="col">Cierre</th></tr></thead>
      <tbody>
        <tr><th scope="row">2026-09-07</th><td data-valor="100">100</td><td data-valor="112">112</td><td data-valor="96">96</td><td data-valor="108">108</td></tr>
        <tr><th scope="row">2026-09-08</th><td data-valor="108">108</td><td data-valor="115">115</td><td data-valor="101">101</td><td data-valor="103">103</td></tr>
        <tr><th scope="row">2026-09-09</th><td data-valor="103">103</td><td data-valor="111">111</td><td data-valor="99">99</td><td data-valor="109">109</td></tr>
        <tr><th scope="row">2026-09-10</th><td data-valor="109">109</td><td data-valor="118">118</td><td data-valor="106">106</td><td data-valor="115">115</td></tr>
        <tr><th scope="row">2026-09-11</th><td data-valor="115">115</td><td data-valor="119">119</td><td data-valor="108">108</td><td data-valor="111">111</td></tr>
      </tbody>
    </table>
  </div>
  <figcaption>Serie sintética, no cotización de un activo. Hueca = sube o no cambia; rellena = baja.</figcaption>
</figure>
```

**Use and limits:** Show open, high, low and close for 1–60 unique ISO dates in one unit. Low must not exceed open/close, which must not exceed high. Real temporal positions; constant data uses an auxiliary ±10% or ±1 domain. No market feed or technical indicators. Do not use for undefined opening/closing balances.

## Route map

<!-- nota:ejemplo mapa-rutas -->

```html
<figure class="ancho" id="analitica-mapa-rutas" data-analitica="rutas" data-unidad="viajes">
  <div class="tabla-caja densa" tabindex="0" role="region" aria-label="Datos de Mapa de rutas y volumen, desplazables">
    <table><caption>Mapa de rutas y volumen</caption>
      <thead><tr><th scope="col">Conexión</th><th scope="col">Lat. origen</th><th scope="col">Lon. origen</th><th scope="col">Lat. destino</th><th scope="col">Lon. destino</th><th scope="col">Viajes</th></tr></thead>
      <tbody>
        <tr><th scope="row">Bogotá → Medellín</th><td data-valor="4.711">4.711</td><td data-valor="-74.072">-74.072</td><td data-valor="6.244">6.244</td><td data-valor="-75.582">-75.582</td><td data-valor="80">80</td></tr>
        <tr><th scope="row">Bogotá → Cali</th><td data-valor="4.711">4.711</td><td data-valor="-74.072">-74.072</td><td data-valor="3.452">3.452</td><td data-valor="-76.532">-76.532</td><td data-valor="50">50</td></tr>
        <tr><th scope="row">Bogotá → Barranquilla</th><td data-valor="4.711">4.711</td><td data-valor="-74.072">-74.072</td><td data-valor="10.969">10.969</td><td data-valor="-74.781">-74.781</td><td data-valor="30">30</td></tr>
      </tbody>
    </table>
  </div>
  <figcaption>Datos ficticios de logística; no son operaciones de Liftit. Ubicaciones urbanas aproximadas. Contorno: <a href="https://www.naturalearthdata.com/about/terms-of-use/">Natural Earth</a>, dominio público, escala 1:110m.</figcaption>
</figure>
```

**Use and limits:** Compare up to 24 corridors with a shared linear width scale and nonnegative trip counts. Load geography before analytics. Colombia view is latitude −5…14, longitude −80…−66, with equirectangular projection and schematic curves. Zero trips draws no route. No roads, provider routing, geodesic distances, driver guidance or ETA.

## Bubble map

<!-- nota:ejemplo mapa-burbujas -->

```html
<figure class="ancho" id="analitica-mapa-burbujas" data-analitica="burbujas" data-unidad="entregas">
  <div class="tabla-caja" tabindex="0" role="region" aria-label="Datos de Mapa de volumen por sede, desplazables">
    <table><caption>Mapa de volumen por sede</caption>
      <thead><tr><th scope="col">Sede</th><th scope="col">Latitud</th><th scope="col">Longitud</th><th scope="col">Entregas</th></tr></thead>
      <tbody>
        <tr><th scope="row">Bogotá</th><td data-valor="4.711">4.711</td><td data-valor="-74.072">-74.072</td><td data-valor="240">240</td></tr>
        <tr><th scope="row">Medellín</th><td data-valor="6.244">6.244</td><td data-valor="-75.582">-75.582</td><td data-valor="180">180</td></tr>
        <tr><th scope="row">Cali</th><td data-valor="3.452">3.452</td><td data-valor="-76.532">-76.532</td><td data-valor="120">120</td></tr>
        <tr><th scope="row">Barranquilla</th><td data-valor="10.969">10.969</td><td data-valor="-74.781">-74.781</td><td data-valor="60">60</td></tr>
      </tbody>
    </table>
  </div>
  <figcaption>Datos ficticios de logística; no son operaciones de Liftit. Ubicaciones urbanas aproximadas. Contorno: <a href="https://www.naturalearthdata.com/about/terms-of-use/">Natural Earth</a>, dominio público, escala 1:110m.</figcaption>
</figure>
```

**Use and limits:** Compare absolute values at up to 24 Colombian locations. Area, not radius, encodes volume; radius is proportional to the square root of the ratio to the maximum. Zero has zero area. No clustering, territorial coverage or choropleth. Overlap remains accessible through selector/table. Rates need explicit denominators.

## Map columns

<!-- nota:ejemplo columnas-mapa -->

```html
<figure class="ancho" id="analitica-columnas-mapa" data-escena="columnas" data-unidad="entregas">
  <div class="tabla-caja" tabindex="0" role="region" aria-label="Datos de Columnas geográficas 3D, desplazables">
    <table><caption>Columnas geográficas 3D</caption>
      <thead><tr><th scope="col">Sede</th><th scope="col">Latitud</th><th scope="col">Longitud</th><th scope="col">Entregas</th></tr></thead>
      <tbody>
        <tr><th scope="row">Bogotá</th><td data-valor="4.711">4.711</td><td data-valor="-74.072">-74.072</td><td data-valor="240">240</td></tr>
        <tr><th scope="row">Medellín</th><td data-valor="6.244">6.244</td><td data-valor="-75.582">-75.582</td><td data-valor="180">180</td></tr>
        <tr><th scope="row">Cali</th><td data-valor="3.452">3.452</td><td data-valor="-76.532">-76.532</td><td data-valor="120">120</td></tr>
        <tr><th scope="row">Barranquilla</th><td data-valor="10.969">10.969</td><td data-valor="-74.781">-74.781</td><td data-valor="60">60</td></tr>
      </tbody>
    </table>
  </div>
  <figcaption>Datos ficticios de logística; no son operaciones de Liftit. Ubicaciones urbanas aproximadas. Contorno: <a href="https://www.naturalearthdata.com/about/terms-of-use/">Natural Earth</a>, dominio público, escala 1:110m.</figcaption>
</figure>
```

**Use and limits:** Explore location and volume when perspective is useful. Up to 12 nonnegative Colombian locations, constant footprints and a shared height scale from zero. Equirectangular projection, no terrain elevation. Load one Three.js dependency, geography and scene. Starts without rotation, pauses outside view and respects reduced motion; destroy releases resources. Keep the permanent table. Prefer bars for close height comparisons.

## Map arcs

<!-- nota:ejemplo arcos-mapa -->

```html
<figure class="ancho" id="analitica-arcos-mapa" data-escena="arcos" data-unidad="viajes">
  <div class="tabla-caja densa" tabindex="0" role="region" aria-label="Datos de Arcos logísticos 3D, desplazables">
    <table><caption>Arcos logísticos 3D</caption>
      <thead><tr><th scope="col">Conexión</th><th scope="col">Lat. origen</th><th scope="col">Lon. origen</th><th scope="col">Lat. destino</th><th scope="col">Lon. destino</th><th scope="col">Viajes</th></tr></thead>
      <tbody>
        <tr><th scope="row">Bogotá → Medellín</th><td data-valor="4.711">4.711</td><td data-valor="-74.072">-74.072</td><td data-valor="6.244">6.244</td><td data-valor="-75.582">-75.582</td><td data-valor="80">80</td></tr>
        <tr><th scope="row">Bogotá → Cali</th><td data-valor="4.711">4.711</td><td data-valor="-74.072">-74.072</td><td data-valor="3.452">3.452</td><td data-valor="-76.532">-76.532</td><td data-valor="50">50</td></tr>
        <tr><th scope="row">Bogotá → Barranquilla</th><td data-valor="4.711">4.711</td><td data-valor="-74.072">-74.072</td><td data-valor="10.969">10.969</td><td data-valor="-74.781">-74.781</td><td data-valor="30">30</td></tr>
      </tbody>
    </table>
  </div>
  <figcaption>Datos ficticios de logística; no son operaciones de Liftit. Ubicaciones urbanas aproximadas. Contorno: <a href="https://www.naturalearthdata.com/about/terms-of-use/">Natural Earth</a>, dominio público, escala 1:110m.</figcaption>
</figure>
```

**Use and limits:** Explain up to 12 origin/destination connections in Colombia. Tube cross-section is proportional to trips; constant arc height is visual separation, not altitude or duration. Zero has zero cross-section. No road routing, ETA, animated vehicles or live tracking. Share Three/geography/scene lifecycle; selector and table retain exact data.

## Warehouse

<!-- nota:ejemplo almacen -->

```html
<figure class="ancho" id="analitica-almacen" data-escena="almacen" data-unidad="posiciones">
  <div class="tabla-caja densa" tabindex="0" role="region" aria-label="Datos de Capacidad de almacén 3D, desplazables">
    <table><caption>Capacidad de almacén 3D</caption>
      <thead><tr><th scope="col">Ubicación</th><th scope="col">X (m)</th><th scope="col">Z (m)</th><th scope="col">Ocupados</th><th scope="col">Capacidad</th></tr></thead>
      <tbody>
        <tr><th scope="row">A1</th><td data-valor="0">0</td><td data-valor="0">0</td><td data-valor="8">8</td><td data-valor="12">12</td></tr>
        <tr><th scope="row">A2</th><td data-valor="4">4</td><td data-valor="0">0</td><td data-valor="11">11</td><td data-valor="12">12</td></tr>
        <tr><th scope="row">B1</th><td data-valor="0">0</td><td data-valor="6">6</td><td data-valor="5">5</td><td data-valor="10">10</td></tr>
        <tr><th scope="row">B2</th><td data-valor="4">4</td><td data-valor="6">6</td><td data-valor="9">9</td><td data-valor="10">10</td></tr>
        <tr><th scope="row">C1</th><td data-valor="0">0</td><td data-valor="12">12</td><td data-valor="2">2</td><td data-valor="8">8</td></tr>
        <tr><th scope="row">C2</th><td data-valor="4">4</td><td data-valor="12">12</td><td data-valor="6">6</td><td data-valor="8">8</td></tr>
      </tbody>
    </table>
  </div>
  <figcaption>Almacén ficticio. Coordenadas en planta; sólido = posiciones ocupadas, contorno = capacidad total.</figcaption>
</figure>
```

**Use and limits:** Show available capacity across 1–12 locations with finite X/Z coordinates in metres, positive capacity and occupancy between zero and capacity. X/Z share scale; constant box footprints are not actual shelf dimensions. Height represents position count, not metres. Duplicate coordinates can overlap. No structural-safety, evacuation or digital-twin claims. Keep table and scene lifecycle cleanup.

## Shared analytics contract

Embed dependencies named in the registry once. Original tables remain the data source. `NotaAnalitica.init(root)` returns new or existing instances; get(figure).destroy() removes controls/SVG and preserves the source. Retry init after fixing invalid data; destroy first when changing initialized data. Keep axis labels short and explanations in captions. Selection reveals exact values without filtering/recalculating totals. Calendar details expand in print.

NotaEscena adds columnas/arcos/almacen to its XYZ/stage contract and shares pinned Three with globes. Scenes start stationary; manual controls work with reduced motion and resume cannot bypass it. Colors use theme tokens. No analytics view needs audio, external shaders or third-party map data at reading time.

## Margin notes

<!-- nota:ejemplo apuntes -->

```html
<div class="apuntes ancho" id="apuntes-ejemplo">
  <section class="apunte izquierda">
    <div class="apunte-cuerpo"><h3>Una decisión necesita contexto.</h3><p>La evidencia sirve cuando nos ayuda a <span data-subrayar="referencia">decidir mejor</span>. Un reporte puede dejar una pregunta breve al margen sin interrumpir el argumento.</p></div>
    <aside class="apunte-nota" aria-label="Apunte a la izquierda"><p class="manuscrita" data-mano="fuente" data-escritura-sonora id="apunte-izquierdo">menos ruido, más criterio.</p><button class="gesto-repetir" type="button" data-mano-repetir="apunte-izquierdo" data-audio="escritura" aria-label="Repetir apunte izquierdo" title="Repetir apunte izquierdo"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 10a9 9 0 1 1 2 8M3 4v6h6"/></svg></button></aside>
  </section>
  <section class="apunte">
    <div class="apunte-cuerpo"><h3>Explicar también es editar.</h3><p>Antes de agregar otra gráfica, prueba a <span data-subrayar="referencia">quitar lo que sobra</span>. La anotación acompaña al párrafo; el subrayado se dibuja cuando aparece.</p><p>Corrección ilustrativa: <del data-subrayar="tachado">cinco días</del> <ins>tres días</ins>. Conserva visible el cambio y explica su motivo.</p></div>
    <aside class="apunte-nota" aria-label="Apunte a la derecha"><p class="manuscrita" data-mano="fuente" data-escritura-sonora id="apunte-derecho">¿se entiende sin explicarlo?</p><button class="gesto-repetir" type="button" data-mano-repetir="apunte-derecho" data-audio="escritura" aria-label="Repetir apunte derecho" title="Repetir apunte derecho"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 10a9 9 0 1 1 2 8M3 4v6h6"/></svg></button></aside>
  </section>
</div>
```

**Use and limits:** Place a brief secondary question beside the claim it qualifies. Left/right variants use reserved grid space; reading order keeps the argument first. Below 1000 px notes follow the paragraph. Replay floats on the bracket with no reserved height, appearing on hover/focus and remaining available on touch. Handwriting, underline and `del[data-subrayar=tachado]` start once at 30% visibility; leaving completes the gesture and stops audio. Reentry does not auto-repeat. Keep complete equivalent text and correction semantics. Use brief one-line underlines and approved handwriting/audio; no essential conditions or long prose in the margin.

## Outlined cards

<!-- nota:ejemplo cards-trazadas -->

```html
<section class="ancho" id="cards-trazadas-ejemplo">
  <h3>Escrito recientemente</h3><p>Lecturas de ejemplo para volver sobre una idea.</p>
  <div class="cards-trazadas cards-abiertas marco-difuso">
    <a href="examples/generated/report.html#resumen" data-audio-hover><h4>Una revisión antes de confirmar</h4><p>La pregunta, la evidencia disponible y la decisión que sigue.</p><span class="procedencia">ENSAYO · 8 min · ejemplo</span></a>
    <a href="examples/generated/report.html#evidencia" data-audio-hover><h4>La escala también cuenta una historia</h4><p>Qué podemos afirmar con los datos y qué necesita otra prueba.</p><span class="procedencia">INVESTIGACIÓN · 6 min · ejemplo</span></a>
    <a href="examples/generated/report.html#prototipo" data-audio-hover><h4>Del documento a una experiencia que se puede probar</h4><p>Una propuesta local con estados, dispositivo y contexto.</p><span class="procedencia">PROTOTIPO · 4 min · ejemplo</span></a>
    <a href="examples/generated/report.html#siguientes" data-audio-hover><h4>Hacer visibles los supuestos</h4><p>Una calculadora pequeña para discutir capacidad sin inventar certezas.</p><span class="procedencia">REPORTE · 5 min · ejemplo</span></a>
    <a href="examples/generated/report.html#resumen" data-audio-hover><h4>Lo que una buena nota deja claro</h4><p>Una conclusión que conserve la pregunta y sus límites.</p><span class="procedencia">CUADERNO · 3 min · ejemplo</span></a>
    <a href="examples/generated/report.html#siguientes" data-audio-hover><h4>La siguiente pregunta también importa</h4><p>Cómo cerrar un informe dejando una prueba concreta por hacer.</p><span class="procedencia">MÉTODO · 5 min · ejemplo</span></a>
  </div>
  <p class="procedencia">El hover tiene una señal breve sólo si activas Sonidos en Apariencia. Sin sonido también se ve la selección.</p>
</section>
```

**Use and limits:** Use a publication/document grid with shared outlines, subtle surface and short hover shadow. Each card is one real keyboard-accessible link; do not nest buttons inside it. Preserve full titles/excerpts without fixed-height clipping. Optional `data-audio-hover` requires actual pointer motion and unlocked sound, never focus, loading or scrolling. The original embedded hover sample respects master volume and rate limiting. Mobile requires no hover or sound to understand the link.

## Attention map

<!-- nota:ejemplo atencion -->

```html
<figure class="ancho" id="atencion-ejemplo" data-atencion data-unidad="horas">
  <div class="tabla-caja" tabindex="0" role="region" aria-label="Datos del attention map, desplazables">
    <table><caption>Dónde se fue la atención</caption><thead><tr><th scope="col">Actividad</th><th scope="col">Horas</th></tr></thead><tbody>
      <tr><th scope="row">Investigar</th><td data-valor="125">125<small data-contexto>Entrevistas y revisión de fuentes durante cuatro semanas ficticias.</small></td></tr>
      <tr><th scope="row">Construir</th><td data-valor="34">34</td></tr>
      <tr><th scope="row">Conversar</th><td data-valor="20">20</td></tr>
      <tr><th scope="row">Documentar</th><td data-valor="12">12</td></tr>
      <tr><th scope="row">Revisar</th><td data-valor="8">8</td></tr>
      <tr><th scope="row">Planear</th><td data-valor="6">6</td></tr>
      <tr><th scope="row">Administrar</th><td data-valor="4">4</td></tr>
      <tr><th scope="row">Otros</th><td data-valor="3">3</td></tr>
    </tbody></table>
  </div>
  <figcaption>212 horas ficticias. El área representa la proporción del total; no es un registro real de actividad. Selecciona una celda o una categoría para consultar su valor.</figcaption>
</figure>
```

**Use and limits:** Partition a positive total across 1–40 unique categories with finite nonnegative values up to 10^9. Binary area partitioning, not fixed placeholder positions or hierarchical squarification. Zero remains in controls/table with no area. Tiny cells may show a number while full names/values remain outside the map. A 1000×380 viewBox uses a 900 px readable local minimum. Hover, focus and touch expose value, share, total and optional plain-text `data-contexto`; Escape dismisses a hoverable tooltip. The table/selector expose equivalent data. No productivity measurement or app connection. init/get/destroy preserves source; destroy/reinitialize after data changes. Prefer bars for precise rankings.

## Frame

<!-- nota:ejemplo marco -->

```html
<aside class="ancho marco-difuso" id="marco-ejemplo">
  <div class="marco-contenido"><h3>Una pausa para mirar la evidencia.</h3><p>Las líneas se cruzan en las esquinas y se pierden hacia los extremos. El contenido permanece completo.</p></div>
</aside>
```

**Use and limits:** Frame a wide composition once. `marco-difuso` reserves 12–32 px inside its box for fading dotted extensions without page overflow. Only decorative pseudo-elements fade; never mask evidence, focus or state borders. Do not compete with a component's existing pseudo-elements. Without masking, a dashed frame remains. No negative-margin imitation.

## Bookshelf

<!-- nota:ejemplo estanteria -->

```html
<section class="ancho marco-difuso" id="estanteria-ejemplo" aria-label="Lecturas guardadas">
  <ul class="estanteria">
    <li><div class="estante-portada" aria-hidden="true"><small>CUADERNO / 01</small><span>Observar antes de medir</span><small>ESTUDIO EDITORIAL</small></div><div><span class="estante-estado">Por leer</span><h3>Observar antes de medir</h3><p class="procedencia">Cuaderno de campo · Edición ilustrativa · 2026</p><p>Una colección de preguntas para registrar el contexto de una cifra antes de compararla. Lo guardamos para preparar la siguiente investigación.</p><p><a href="examples/generated/report.html#evidencia">Ver el ejemplo de evidencia →</a></p></div></li>
    <li><div class="estante-portada" aria-hidden="true"><small>CUADERNO / 02</small><span>El oficio de quitar</span><small>NOTAS DE PRODUCTO</small></div><div><span class="estante-estado">En lectura</span><h3>El oficio de quitar</h3><p class="procedencia">Ensayo · Edición ilustrativa · 2026</p><p>Sobre decisiones que hacen una interfaz más clara. Nos interesa porque una pantalla puede crecer sin que la tarea se vuelva más fácil.</p><p><a href="examples/generated/report.html#prototipo">Recorrer la propuesta →</a></p></div></li>
    <li><div class="estante-portada" aria-hidden="true"><small>CUADERNO / 03</small><span>Volver a preguntar</span><small>CONVERSACIONES</small></div><div><span class="estante-estado">Consultado</span><h3>Volver a preguntar</h3><p class="procedencia">Entrevistas · Edición ilustrativa · 2026</p><p>Una referencia para separar lo que sabemos de lo que suponemos. Cada lectura conserva la razón para volver a ella.</p><p><a href="examples/generated/report.html#siguientes">Leer las preguntas pendientes →</a></p></div></li>
  </ul>
</section>
```

**Use and limits:** Curate books, documents or resources with title, status and a reason to keep them. Example covers are original CSS illustrations with fictional titles. Authorized replacements need embedded data images and alternative text. No fabricated commercial links or remote cover downloads. The visible title repeats any cover information. Mobile stacks each row with a 120 px cover; no automatic animation.

## Invitation

<!-- nota:ejemplo invitacion -->

```html
<section class="ancho marco-difuso" id="invitacion-ejemplo">
  <div class="invitacion" data-invitacion id="invitacion-idea">
    <div><h3>¿Qué sumarías?</h3><p>Una lectura, una pregunta o una idea que merezca entrar en la siguiente versión.</p></div>
    <form aria-label="Preparar una recomendación"><label for="invitacion-texto">Tu idea</label><textarea id="invitacion-texto" name="idea" maxlength="1000" required placeholder="Un título, un enlace o una nota…" aria-describedby="invitacion-estado"></textarea><button type="button" data-invitacion-copiar>Copiar mi idea ↗</button><p role="status" id="invitacion-estado">Borrador local; copia antes de cerrar.</p></form>
  </div>
</section>
```

**Use and limits:** End a reading with a concrete invitation and a static halftone treatment. invitation.js copies up to 1000 nonempty characters plus document title and block reference; clipboard denial selects text and explains manual copy. It does not submit, store or synchronize messages. init/get/destroy supports mounting. Without JavaScript it is a writing surface, not a working send form. The decorative pattern is not a chart or paper-grain setting.

## Status list

<!-- nota:ejemplo lista-estados -->

```html
<section id="lista-estados-ejemplo">
  <h3>En qué estamos</h3><p class="procedencia">Instantánea ilustrativa · <time datetime="2026-09-14">14 sep 2026</time></p>
  <ul class="lista-estados" aria-label="Estado de los frentes">
    <li class="hecho"><span class="estado-signo" aria-hidden="true">[x]</span><span class="estado-texto"><span class="sr-only">Completado: </span>Definir la pregunta del informe</span></li>
    <li><span class="estado-signo" aria-hidden="true">[-]</span><span class="estado-texto"><span class="sr-only">En curso: </span>Contrastar las cifras con su fuente</span></li>
    <li><span class="estado-signo" aria-hidden="true">[ ]</span><span class="estado-texto"><span class="sr-only">Pendiente: </span>Probar la propuesta con lectores</span></li>
    <li><span class="estado-signo" aria-hidden="true">[ ]</span><span class="estado-texto"><span class="sr-only">Pendiente: </span>Publicar lo que cambió y por qué</span></li>
  </ul>
</section>
```

**Use and limits:** Show a dated snapshot of completed and pending work. Symbols, text and strike-through distinguish status; color is supplementary. It is not an editable task manager or checkbox list. Do not derive percentages from qualitative states. Update date and content together.

## Project list

<!-- nota:ejemplo lista-proyectos -->

```html
<section id="lista-proyectos-ejemplo"><h3>Tres preguntas abiertas</h3>
  <ul class="lista-proyectos">
    <li><h4>Qué vale la pena medir</h4><p>Elegir indicadores que respondan a la decisión del equipo y explicitar qué queda fuera.</p></li>
    <li><h4>Cómo se entiende la propuesta</h4><p>Recorrer el prototipo con una tarea concreta antes de añadir otra pantalla.</p></li>
    <li><h4>Cuándo volver a revisar</h4><p>Acordar una fecha y una señal para retomar la decisión con evidencia nueva.</p></li>
  </ul>
</section>
```

**Use and limits:** Describe parallel projects or research directions with a short title and paragraph. Use a table when comparing common attributes. Numbering must not imply priority unless an order is real. Preserve complete names and real destinations.

## Conversation

<!-- nota:ejemplo conversacion -->

```html
<section id="conversacion-ejemplo"><h3>Aclarar la pregunta</h3>
  <ol class="conversacion" aria-label="Diálogo ilustrativo">
    <li><strong>Investigación</strong>¿Qué queremos aprender con este informe?</li>
    <li class="respuesta"><strong>Producto</strong>Si la propuesta ayuda a decidir con menos dudas.</li>
    <li><strong>Investigación</strong>Entonces necesitamos observar una decisión, además de contar clics.</li>
    <li class="respuesta"><strong>Producto</strong>Dejemos esa pregunta al comienzo.</li>
  </ol>
</section>
```

**Use and limits:** Use a dialogue to explain an idea, with explicit participants and natural reading order. The fixture is fictional, not a quote. Real quotations need provenance. No connected chat, simulated typing, presence or fabricated replies.

## Navigation

<!-- nota:ejemplo navegacion -->

```html
<div class="ancho navegacion-muestra" id="navegacion-ejemplo">
  <a class="firma-editorial" href="examples/generated/report.html#resumen"><span>Margen</span></a>
  <nav aria-label="Recorrer el informe"><a href="examples/generated/report.html#resumen">inicio</a><span class="nav-separador" aria-hidden="true">/</span><a href="examples/generated/report.html#evidencia">evidencia</a><span class="nav-separador" aria-hidden="true">/</span><a href="examples/generated/report.html#prototipo">propuesta</a><span class="nav-separador" aria-hidden="true">/</span><a href="examples/generated/report.html#siguientes">siguiente</a></nav>
</div>
```

**Use and limits:** Use ordinary links for documents and `data-ir` buttons for local chapters. `data-capitulos-scroll` scrolls only chapter navigation; appearance stays separate. Preserve contents/progress for long documents and use one chapter navigation instance. Decorative separators do not replace accessible names. Below 700 px chapters move to a second row.

## Editorial footer

<!-- nota:ejemplo pie-editorial -->

```html
<footer class="ancho pie-editorial" id="pie-editorial-ejemplo">
  <div><h3>Margen</h3><nav aria-label="Más del cuaderno"><a href="examples/generated/report.html#resumen">El informe</a><a href="examples/generated/report.html#evidencia">Las fuentes y sus límites</a><a href="examples/generated/report.html#siguientes">Lo que sigue</a></nav></div>
  <div class="pie-carta"><h3>Una nota para quien viene después.</h3><p>Dejamos las preguntas, las fuentes y las decisiones a la vista. Que la siguiente versión pueda comenzar desde aquí.</p><p><em>Este cuaderno sigue abierto.</em></p></div>
  <div class="pie-colofon"><span>Edición ilustrativa · <time datetime="2026-09-14">14 sep 2026</time></span><span>Lectura · evidencia · conversación</span></div>
</footer>
```

**Use and limits:** Close with identity, useful links, editorial context and a real date where known. Two columns stack on mobile. An optional global sound button is appropriate only when another sound control is absent. Do not invent contact details, commit statistics or licensing. The main footer follows content and does not cover the final section.

## Compose a standard artifact

Use the [artifact contract](artifact-contract.md) for new documents. Appearance, optional sound, floating comments and navigation are embedded once; do not insert duplicates in content. Appearance separates Themes, Typography and Sound. The sound tab owns preview, volume (initially 65%) and state. Preview activates the reference click; toggling preference alone does not play audio. Browser activation failure keeps audio inactive and explains retry. Pencil sound tracks its stroke and cancels with it. Enabled preference is not proof of audible output.

Choose components for editorial usefulness. Structural validation does not prove hearing, screen-reader output or responsive layout, and building does not update already published HTML. Standalone comments persist locally when storage is available, with a memory-only fallback; connected comments follow portal permissions.

## Activity

<!-- nota:ejemplo actividad-editorial -->

```html
<section class="pieza amplio actividad-editorial" id="actividad-editorial-ejemplo" data-actividad data-actividad-tabla="actividad-editorial-datos">
  <div><p class="ceja">Actividad de ejemplo / ocho semanas</p><h3>Pequeños avances,<br>una historia visible.</h3><p>Cada cuadrado representa una semana. La intensidad indica cuántas acciones se registraron; no mide calidad ni productividad.</p><a class="enlace-icono" href="https://www.cmrg.me/now">Ver la referencia editorial ↗</a></div>
  <div><div class="actividad-mosaico" data-actividad-mapa role="group" aria-label="Acciones por semana"></div><div class="actividad-escala" data-actividad-escala aria-label="Escala de acciones"></div><p data-actividad-estado role="status">Los conteos completos están en la tabla.</p></div>
</section>
<details class="actividad-datos" id="actividad-editorial-datos"><summary>Datos ilustrativos completos</summary><div class="tabla-caja" tabindex="0" role="region" aria-label="Actividad semanal, desplazable"><table><caption>Acciones de ejemplo, no actividad real de GitHub</caption><thead><tr><th scope="col">Semana</th><th scope="col">Acciones</th></tr></thead><tbody>
    <tr><th scope="row">1–7 junio</th><td data-valor="0">0</td></tr><tr><th scope="row">8–14 junio</th><td data-valor="2">2</td></tr><tr><th scope="row">15–21 junio</th><td data-valor="3">3</td></tr><tr><th scope="row">22–28 junio</th><td data-valor="5">5</td></tr><tr><th scope="row">29 junio–5 julio</th><td data-valor="1">1</td></tr><tr><th scope="row">6–12 julio</th><td data-valor="7">7</td></tr><tr><th scope="row">13–19 julio</th><td data-valor="4">4</td></tr><tr><th scope="row">20–26 julio</th><td data-valor="8">8</td></tr>
  </tbody></table></div></details>
```

**Use and limits:** Introduce recent activity with contextual counts derived from the source table. 1–52 periods, integer counts 0–1000000. Equal cell size represents equal periods; intensity represents count, not area or productivity. Zero has its own legend sample; positive bins derive from the observed maximum. Hover, focus and click expose detail. `data-actividad-tabla` points to a sibling table outside the frame: copy both blocks and update IDs together. The table prints in full; missing targets show an error. No GitHub feed.

## Code lines

<!-- nota:ejemplo codigo-lineas -->

```html
<figure class="ancho" id="codigo-lineas-ejemplo"><div class="codigo codigo-editorial"><div class="cab"><span>preparar_resumen.py · Python</span><button class="boton-icono-copia" type="button" data-copiar="codigo-lineas-fuente" aria-label="Copiar código Python" title="Copiar código"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M8 8h12v13H8zM16 8V3H4v13h4"/></svg></button><span class="copia-estado" role="status"></span></div><pre tabindex="0" aria-label="Código Python con líneas 3 y 6 destacadas, desplazable"><code id="codigo-lineas-fuente" data-lenguaje="python" data-lineas data-destacar="3,6">def resumir(registros):
    cantidades = [fila["cantidad"] for fila in registros]
    total = sum(cantidades)
    if not cantidades:
        return {"total": 0, "promedio": None}
    return {"total": total, "promedio": total / len(cantidades)}</code></pre></div><figcaption>Ejemplo ilustrativo. Las líneas 3 y 6 explican el cálculo; el botón copia el código sin números de línea.</figcaption></figure>
```

**Use and limits:** Explain precise code lines with code.js and `data-destacar`, such as `3,6-8`. `data-lineas` starts from plain code text; do not add manual token spans. CSS line numbers never enter copied text. Unhighlighted lines remain readable. Copy has an accessible name and result state. This is lexical highlighting, not an editor/compiler; wide code scrolls locally.

## Icon links

<!-- nota:ejemplo enlaces-icono -->

```html
<section class="pieza" id="enlaces-icono-ejemplo"><h3>Una referencia en medio del argumento.</h3><p>Consulta <a class="enlace-icono" href="https://www.cmrg.me/blog/react-19-part-2-the-code"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M8 4H4v16h16v-4M13 3h8v8M21 3 10 14"/></svg>el artículo de referencia</a> antes de interpretar <code class="codigo-en-linea">data-lineas</code>. Para una ruta local, <code class="codigo-en-linea">scripts/validate.py</code> nombra exactamente qué ejecutar.</p></section>
```

**Use and limits:** Add a small decorative SVG beside a complete source/repository/file link label. Icons do not replace the name or promise a different action. No external logo fetch. Allow long URLs/paths to wrap. Multiline code belongs in a code block, not an inline chip.

## Animated callouts

<!-- nota:ejemplo avisos-animados -->

```html
<div class="pieza" id="avisos-animados-ejemplo">
  <aside class="aviso aviso-esquina mal" data-aviso-animado aria-labelledby="aviso-cuidado-titulo"><span class="num" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M12 4v10M12 17v2"/></svg></span><div><p class="titulo" id="aviso-cuidado-titulo">Cuidado</p><p>Estos conteos son ilustrativos. Antes de tomar una decisión, reemplázalos por una fuente verificable.</p></div></aside>
  <aside class="aviso aviso-esquina" data-aviso-animado aria-labelledby="aviso-nota-titulo"><span class="num" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M7 3h11v16H7zM4 6v16h11"/></svg></span><div><p class="titulo" id="aviso-nota-titulo">Nota</p><p>Los comentarios de revisión se conservan mientras esta pestaña permanezca abierta. Copia el prompt antes de recargar.</p></div></aside>
</div>
```

**Use and limits:** Mark brief caution or context with a corner icon that reserves its own space. editorial-pieces.js adds two 1000 ms pulses on entry and optional replay on hover/focus. Motion stops when hidden, outside view, reduced or destroyed. No RAF or sound. Static notices must not use role=alert; meaning does not depend on animation. Existing notice variants remain compatible.

## Timeline

<!-- nota:ejemplo trayectoria -->

```html
<section class="pieza" id="trayectoria-ejemplo"><h3>La trayectoria de una idea.</h3><p class="procedencia">Proyecto ficticio · hitos de ejemplo, del más reciente al más antiguo.</p><ol class="cronologia cronologia-vertical">
<li class="actual"><h3>Una prueba con lectores</h3><p class="periodo"><time datetime="2026-09">Septiembre de 2026</time> · etapa actual</p><p>Observar dónde se pierde el contexto y qué hace falta para decidir con confianza.</p></li>
<li><h3>Un prototipo que se puede recorrer</h3><p class="periodo"><time datetime="2026-08">Agosto de 2026</time></p><p>Dar forma a las preguntas y mantener visibles las limitaciones de cada alternativa.</p></li>
<li><h3>Las primeras preguntas</h3><p class="periodo"><time datetime="2026-07">Julio de 2026</time></p><p>Definir el problema, su evidencia disponible y la siguiente observación necesaria.</p></li>
</ol></section>
```

**Use and limits:** Present actual milestones with date, title and explanation on one axis. Distinguish the current point with words and color. Vertical spacing is editorial, not proportional time. The line fades from accent to secondary ink at the end; evidence and older entries remain fully legible. Use duration/time charts when elapsed time matters.

## Gallery

<!-- nota:ejemplo galeria -->

```html
<section class="pieza amplio galeria-fotografica" id="galeria-ejemplo" data-galeria><div class="galeria-pista" data-galeria-pista tabindex="0" role="region" aria-label="Galería de cuatro ilustraciones, desplazable horizontalmente">
<figure><img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA2MDAgNDAwIj48cmVjdCB3aWR0aD0iNjAwIiBoZWlnaHQ9IjQwMCIgZmlsbD0iIzI2M2IzNyIvPjxjaXJjbGUgY3g9IjEzMCIgY3k9IjEwMCIgcj0iNjIiIGZpbGw9IiNkOGI5ODgiLz48cGF0aCBkPSJNMCAzMzAgMTYwIDE0MCAzMTAgMzAwIDQ1NSAxMzAgNjAwIDI3MFY0MDBIMFoiIGZpbGw9IiNhY2MzYTQiLz48cGF0aCBkPSJNMCAzNzUgMTgwIDMwMCAzNDAgMzcwIDUwMCAyNjUgNjAwIDMxMFY0MDBIMFoiIGZpbGw9IiMyNjNiMzciIG9wYWNpdHk9Ii42Ii8+PC9zdmc+" alt="Relieve: ilustración geométrica de paisaje" width="600" height="400" loading="lazy"><figcaption>Relieve · ilustración, 2026</figcaption></figure>
<figure><img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA2MDAgNDAwIj48cmVjdCB3aWR0aD0iNjAwIiBoZWlnaHQ9IjQwMCIgZmlsbD0iIzIwMzU0NyIvPjxjaXJjbGUgY3g9IjIxMCIgY3k9IjEwMCIgcj0iNjIiIGZpbGw9IiNlZWQzYTUiLz48cGF0aCBkPSJNMCAzMzAgMTYwIDE0MCAzMTAgMzAwIDQ1NSAxMzAgNjAwIDI3MFY0MDBIMFoiIGZpbGw9IiM4MGE2YWIiLz48cGF0aCBkPSJNMCAzNzUgMTgwIDMwMCAzNDAgMzcwIDUwMCAyNjUgNjAwIDMxMFY0MDBIMFoiIGZpbGw9IiMyMDM1NDciIG9wYWNpdHk9Ii42Ii8+PC9zdmc+" alt="Horizonte: ilustración geométrica de paisaje" width="600" height="400" loading="lazy"><figcaption>Horizonte · ilustración, 2026</figcaption></figure>
<figure><img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA2MDAgNDAwIj48cmVjdCB3aWR0aD0iNjAwIiBoZWlnaHQ9IjQwMCIgZmlsbD0iIzM5MzQ0MyIvPjxjaXJjbGUgY3g9IjI5MCIgY3k9IjEwMCIgcj0iNjIiIGZpbGw9IiNlYWQ4YmQiLz48cGF0aCBkPSJNMCAzMzAgMTYwIDE0MCAzMTAgMzAwIDQ1NSAxMzAgNjAwIDI3MFY0MDBIMFoiIGZpbGw9IiNhZTk3YTciLz48cGF0aCBkPSJNMCAzNzUgMTgwIDMwMCAzNDAgMzcwIDUwMCAyNjUgNjAwIDMxMFY0MDBIMFoiIGZpbGw9IiMzOTM0NDMiIG9wYWNpdHk9Ii42Ii8+PC9zdmc+" alt="Ciudad: ilustración geométrica de paisaje" width="600" height="400" loading="lazy"><figcaption>Ciudad · ilustración, 2026</figcaption></figure>
<figure><img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA2MDAgNDAwIj48cmVjdCB3aWR0aD0iNjAwIiBoZWlnaHQ9IjQwMCIgZmlsbD0iIzQ0MzkyZCIvPjxjaXJjbGUgY3g9IjM3MCIgY3k9IjEwMCIgcj0iNjIiIGZpbGw9IiNlMGM5YTQiLz48cGF0aCBkPSJNMCAzMzAgMTYwIDE0MCAzMTAgMzAwIDQ1NSAxMzAgNjAwIDI3MFY0MDBIMFoiIGZpbGw9IiNiOWFkODgiLz48cGF0aCBkPSJNMCAzNzUgMTgwIDMwMCAzNDAgMzcwIDUwMCAyNjUgNjAwIDMxMFY0MDBIMFoiIGZpbGw9IiM0NDM5MmQiIG9wYWNpdHk9Ii42Ii8+PC9zdmc+" alt="Sendero: ilustración geométrica de paisaje" width="600" height="400" loading="lazy"><figcaption>Sendero · ilustración, 2026</figcaption></figure>
</div><p class="sr-only" data-galeria-estado role="status">Desliza para recorrer las cuatro ilustraciones.</p></section>
```

**Use and limits:** Show embedded photos/captures with native horizontal scrolling via trackpad, touch or focused keyboard arrows. The photographic variant has no internal heading, controls or autoplay; short captions overlay a full-image gradient, subtle outline and shadow. Pointer drag uses grab/capture; touch stays native. Superellipse(1.6) corners use 28 px with an 18 px circular fallback. Position announcements enhance rather than replace native scrolling. Use data images and alt text; fixtures are illustrations, not the user's photos. Cover crops may hide edges; use contain for evidence requiring the full image. Long explanations belong outside. No zoom/360 viewer. Reduced motion also disables legacy smooth controls. init/get/destroy preserves content.

## Liftit, Blueprint and Hacker examples

Theme family and light/dark/system mode are independent. Components inherit tokens rather than needing separate markup per theme. Use the generator options below for initial appearance. Liftit supports logistics, Blueprint architectural specifications, and Hacker code/runbooks. Color never replaces status words; a Blueprint grid is not a chart scale. Do not attribute fictional data to a company.

Blueprint uses a static 24/120px grid omitted in print; Hacker does not execute commands or blink. Brand sources and current token choices live in brands.md and themes.md. Declared initial presentation is overridden by later route-local preferences; changing the route starts from declared defaults. Without an initial presentation, global preferences remain. Complete examples are in examples/generated/{liftit,blueprint,hacker,guide}.html.

```bash
python3 scripts/create_artifact.py --contenido operacion.html --titulo 'Lectura de operación' --tema liftit --modo system --estilo sobrio --salida examples/generated/report.html
python3 scripts/create_artifact.py --contenido especificacion.html --titulo 'Plano del sistema' --tema blueprint --modo dark --estilo tecnico --salida plano.html
python3 scripts/create_artifact.py --contenido runbook.html --titulo 'Diagnóstico y recuperación' --tema hacker --modo dark --estilo tecnico --salida diagnostico.html
```

```json
{
  "titulo": "Plano del sistema",
  "tema": "blueprint",
  "estilo": "tecnico",
  "paginas": [
    {"id": "contrato", "titulo": "Contrato", "contenido": "contrato.html"},
    {"id": "evidencia", "titulo": "Evidencia", "contenido": "examples/generated/evidence.html"}
  ]
}
```

## Fleet globe

<!-- nota:ejemplo globo-flota -->

```html
<figure class="amplio" id="flota-colombia" data-flota>
  <div class="tabla-caja densa" tabindex="0" role="region" aria-label="Corte de flota de ejemplo, desplazable">
    <table><caption>Flota ficticia · 15 septiembre 2026, 08:00 COT · posiciones iniciales de demostración</caption>
      <thead><tr><th scope="col">Vehículo</th><th scope="col">Origen</th><th scope="col">Destino</th><th scope="col">Avance ilustrativo %</th><th scope="col">Pedidos</th><th scope="col">Estado al corte</th><th scope="col">Actualización</th><th scope="col">Contexto</th><th scope="col">Siguiente acción</th></tr></thead>
      <tbody>
        <tr><th scope="row">LFT-021</th><td data-lat="4.711" data-lon="-74.072">Bogotá</td><td data-lat="6.244" data-lon="-75.582">Medellín</td><td data-valor="35">35</td><td data-valor="18">18</td><td>En ruta</td><td><time datetime="2026-09-15T08:00:00-05:00">08:00 COT</time></td><td>Salida confirmada; sin novedades reportadas en este ejemplo.</td><td>Próximo hito: llegada al punto de distribución.</td></tr>
        <tr><th scope="row">LFT-034</th><td data-lat="4.711" data-lon="-74.072">Bogotá</td><td data-lat="3.452" data-lon="-76.532">Cali</td><td data-valor="62">62</td><td data-valor="12">12</td><td>Con novedad</td><td><time datetime="2026-09-15T07:58:00-05:00">07:58 COT</time></td><td>Congestión reportada. La demo no estima cuánto retrasará la llegada.</td><td>Acción: confirmar situación con el transportista antes de informar una nueva hora.</td></tr>
        <tr><th scope="row">LFT-056</th><td data-lat="4.711" data-lon="-74.072">Bogotá</td><td data-lat="10.969" data-lon="-74.781">Barranquilla</td><td data-valor="18">18</td><td data-valor="9">9</td><td>En ruta</td><td><time datetime="2026-09-15T07:59:00-05:00">07:59 COT</time></td><td>Documentos verificados; nueve pedidos asociados al vehículo de ejemplo.</td><td>Próximo hito: confirmar recepción en destino.</td></tr>
      </tbody>
    </table>
  </div>
  <figcaption>Ejemplo ficticio, no una operación real de Liftit. Coordenadas urbanas aproximadas WGS84. Colombia: Natural Earth 1:110m, dominio público; máscara terrestre COBE. Los arcos no son vías terrestres.</figcaption>
</figure>
```

**Use and limits:** Explore a declared operational snapshot across Colombian cities with selectable vehicles. Load one Three 0.160.1, geography, globe and fleet. One instance; 1–12 vehicles with unique IDs, distinct endpoints, valid Colombian coordinates, progress 0–100, nonnegative integer orders and a zoned ISO timestamp. Routes are schematic arcs, never streets, GPS, ETA or measured distance. Drag rotates; Shift+drag pans; focused wheel/buttons and pinch zoom. Arrows rotate, Shift+arrows pan, +/- zoom and Home resets. No inertia/camera animation. Rear-hemisphere labels/vehicles hide; collision-prone labels remain accessible in route focus and list. Manual exploration can move endpoints out of view; reset restores framing. Playback demonstrates positions for 45 seconds without sound or delivery-state updates, pausing when hidden and respecting reduced motion/manual progress. A historical snapshot must not be labeled live. Without WebGL retain list/detail/table. `NotaFlota.init/get`, seek(0…100), select(id) and destroy manage lifecycle; destroy/update/reinitialize for another snapshot.

## Delivery summary

<!-- nota:ejemplo ficha-entrega -->

```html
<section class="pieza" id="ficha-entrega-ejemplo">
  <p class="ceja">Pedido de ejemplo / DEMO-018</p><h3>Estar cerca no es haber entregado.</h3>
  <p>Vehículo LFT-021 · Bogotá → Medellín. Estado ilustrativo: en tránsito.</p>
  <ol class="cronologia cronologia-vertical">
    <li><h3>Recogida confirmada</h3><p class="periodo"><time datetime="2026-09-15T06:30:00-05:00">06:30 COT</time></p><p>18 pedidos asociados al vehículo. La cantidad pertenece al corte de ejemplo.</p></li>
    <li class="actual"><h3>En tránsito</h3><p class="periodo"><time datetime="2026-09-15T08:00:00-05:00">08:00 COT</time> · último evento conocido</p><p>El movimiento en el mapa no confirma recepción ni prueba de entrega.</p></li>
    <li><h3>Recepción pendiente</h3><p>Sin hora confirmada. No se fabrica una estimación a partir de la animación.</p></li>
    <li><h3>Evidencia pendiente</h3><p>Registrar fecha, receptor y prueba autorizada de entrega cuando existan. No se incluyen firmas ni fotos ficticias como si fueran evidencia real.</p></li>
  </ol>
</section>
```

**Use and limits:** Explain a delivery's last known event and missing evidence. Use real zoned timestamps and stable IDs; unknown receipt/signature/time remains pending. Static HTML does not track, upload files or store signatures. A nearby vehicle is not proof of delivery. Keep a few milestones and one current status.

## Incident queue

<!-- nota:ejemplo cola-novedades -->

```html
<section class="pieza amplio" id="cola-novedades-ejemplo" data-explorador data-unidad="pedidos">
<h3>Despacho y novedades</h3><p>Tres vehículos ficticios del corte. Filtra Con novedad, agrupa por ciudad y ordena los pedidos para revisar a quién contactar.</p>
<form class="tabla-herramientas" aria-label="Explorar registros">
<label class="tabla-busqueda"><span class="control-etiqueta">Buscar registros</span><svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><circle cx="10" cy="10" r="6"/><path d="m15 15 5 5"/></svg><input type="search" name="buscar" placeholder="Buscar registros…"></label>
<details class="control-menu"><summary>Filtros <span data-filtros-cuenta></span>⌄</summary><div class="control-panel" tabindex="0" role="region" aria-label="Filtros de registros"><label>Estado<select name="estado"><option value="">Todos los estados</option><option>Con novedad</option><option>En ruta</option></select></label><button type="reset">Limpiar filtros</button></div></details>
<details class="control-menu"><summary>Agrupar ⌄</summary><div class="control-panel" tabindex="0" role="region" aria-label="Agrupar registros"><label>Agrupar por<select name="grupo"><option value="">Sin grupos</option><option value="1">Ciudad</option><option value="2">Estado</option></select></label></div></details>
<details class="control-menu"><summary>Columnas ⌄</summary><div class="control-panel" tabindex="0" role="region" aria-label="Columnas visibles"><label><input type="checkbox" data-columna="1" checked> Ciudad</label><label><input type="checkbox" data-columna="2" checked> Estado</label><label><input type="checkbox" data-columna="3" checked> Pedidos</label></div></details>
</form>
<p data-explorador-estado role="status">3 vehículos de ejemplo.</p><div class="tabla-caja" tabindex="0" role="region" aria-label="Registros ordenables y agrupables, desplazables"><table><caption>Vehículos de ejemplo · pedidos asociados al corte</caption><thead><tr><th scope="col"><details class="control-menu tabla-orden"><summary>Vehículo <span data-indicador-orden aria-hidden="true">↕</span></summary><div class="control-panel" tabindex="0" role="region" aria-label="Ordenar por Vehículo"><button type="button" data-orden-col="0" data-direccion="1" data-cerrar-menu>↑ Ascendente</button><button type="button" data-orden-col="0" data-direccion="-1" data-cerrar-menu>↓ Descendente</button><button type="button" data-orden-col="0" data-direccion="0" data-cerrar-menu>Restablecer orden</button></div></details></th><th scope="col"><details class="control-menu tabla-orden"><summary>Ciudad <span data-indicador-orden aria-hidden="true">↕</span></summary><div class="control-panel" tabindex="0" role="region" aria-label="Ordenar por Ciudad"><button type="button" data-orden-col="1" data-direccion="1" data-cerrar-menu>↑ Ascendente</button><button type="button" data-orden-col="1" data-direccion="-1" data-cerrar-menu>↓ Descendente</button><button type="button" data-orden-col="1" data-direccion="0" data-cerrar-menu>Restablecer orden</button></div></details></th><th scope="col"><details class="control-menu tabla-orden"><summary>Estado <span data-indicador-orden aria-hidden="true">↕</span></summary><div class="control-panel" tabindex="0" role="region" aria-label="Ordenar por Estado"><button type="button" data-orden-col="2" data-direccion="1" data-cerrar-menu>↑ Ascendente</button><button type="button" data-orden-col="2" data-direccion="-1" data-cerrar-menu>↓ Descendente</button><button type="button" data-orden-col="2" data-direccion="0" data-cerrar-menu>Restablecer orden</button></div></details></th><th scope="col"><details class="control-menu tabla-orden"><summary>Pedidos <span data-indicador-orden aria-hidden="true">↕</span></summary><div class="control-panel" tabindex="0" role="region" aria-label="Ordenar por Pedidos"><button type="button" data-orden-col="3" data-direccion="1" data-cerrar-menu>↑ Ascendente</button><button type="button" data-orden-col="3" data-direccion="-1" data-cerrar-menu>↓ Descendente</button><button type="button" data-orden-col="3" data-direccion="0" data-cerrar-menu>Restablecer orden</button></div></details></th></tr></thead><tbody><tr><th scope="row">LFT-021</th><td>Medellín</td><td>En ruta</td><td data-valor="18">18</td></tr><tr><th scope="row">LFT-034</th><td>Cali</td><td>Con novedad</td><td data-valor="12">12</td></tr><tr><th scope="row">LFT-056</th><td>Barranquilla</td><td>En ruta</td><td data-valor="9">9</td></tr></tbody></table></div></section>
```

**Use and limits:** Filter operational exceptions, group by city and sort orders using the shared data explorer. `data-unidad=pedidos` declares the total; legacy financial examples default to COP. This is a static snapshot, not updated by fleet playback. Keep units and explicit status text. Explorer limits, mobile cards, selection and export semantics apply; no dispatch or assignment actions are executed.

## Compact interface conventions

Replay, copy, device, rotate and fit actions use icons with accessible names, tooltips and visible focus. Decorative SVG is aria-hidden. Preserve usable touch targets and reduced-motion behavior. Prototype presets include 390/768/1024px; 320px and available width remain in the menu. Filename headers stay visible; language-only code headers are compacted without changing copied text.

The comment composer prioritizes author, draft and send, with context/type/session under an optional disclosure. Draft text grows before scrolling locally. Appearance is a searchable compact list with favorites/category and an independent mode control. Sound belongs exclusively to the Sound tab. Table tools share a button group while retaining named actions. Compactness never permits removing accessible labels.

## Visual story

<!-- nota:ejemplo relato-visual -->

```html
<figure class="amplio" id="evidencia-relato" data-evidencia="relato" data-unidad="horas">
<div class="tabla-caja densa" role="region" tabindex="0" aria-label="Cien horas de trabajo, datos desplazables">
<table data-evidencia-datos><caption>Cien horas de trabajo</caption><thead><tr><th scope="col">Paso</th><th scope="col">Horas</th><th scope="col">Lectura</th></tr></thead><tbody>
<tr><th scope="row">Investigar</th><td data-valor="60">60</td><td>La mayor parte del tiempo se dedicó a comprender el problema.</td></tr>
<tr><th scope="row">Construir</th><td data-valor="25">25</td><td>La implementación parte de lo aprendido durante la investigación.</td></tr>
<tr><th scope="row">Revisar</th><td data-valor="15">15</td><td>La revisión reserva tiempo para contrastar el resultado con la pregunta.</td></tr>
</tbody></table>
</div>
<figcaption>Datos ilustrativos: distribución de 100 horas, no productividad medida.</figcaption>
</figure>
```

**Use and limits:** Connect a narrative to one shared figure with 2–8 rows: name, nonnegative magnitude and explanation, each text up to 100 characters. Desktop scroll selects a step; controls allow explicit selection. Mobile restores normal flow and written values. Shared zero-based scale, no data mutation or scroll hijacking. Without JavaScript retain the table. IntersectionObserver is cleaned up; no animation loop. Source data stays in one table (or the image zone list). Declare data-unidad (1–40 characters); numeric magnitude is limited to 10^12. Views round to eight significant digits while source values remain. Load evidence.js; NotaEvidencia.init/get/destroy owns lifecycle. Destroy before changing the source. No network or external libraries; data remains if enhancement fails.

## Sankey

<!-- nota:ejemplo sankey -->

```html
<figure class="amplio" id="evidencia-sankey" data-evidencia="sankey" data-unidad="millones COP">
<div class="tabla-caja densa" role="region" tabindex="0" aria-label="Destino de ingresos de ejemplo, datos desplazables">
<table data-evidencia-datos><caption>Destino de ingresos de ejemplo</caption><thead><tr><th scope="col">Origen</th><th scope="col">Destino</th><th scope="col">Millones COP</th></tr></thead><tbody>
<tr><th scope="row">Carga urbana</th><td>Operación</td><td data-valor="65">65</td></tr>
<tr><th scope="row">Carga urbana</th><td>Soporte</td><td data-valor="10">10</td></tr>
<tr><th scope="row">Carga urbana</th><td>Margen</td><td data-valor="15">15</td></tr>
<tr><th scope="row">Última milla</th><td>Operación</td><td data-valor="20">20</td></tr>
<tr><th scope="row">Última milla</th><td>Soporte</td><td data-valor="5">5</td></tr>
<tr><th scope="row">Última milla</th><td>Margen</td><td data-valor="5">5</td></tr>
</tbody></table>
</div>
<figcaption>Datos ficticios, total 120 millones COP. No representan estados financieros de Liftit o Tikin.</figcaption>
</figure>
```

**Use and limits:** Compare nonnegative flows with a common thickness scale. Two columns only, 1–24 connections, at most eight nodes per column and positive total. Nodes derive from connections; zero has no thickness. No intermediate stages, cycles, negative values, mixed currencies or crossing optimization. Use the table when dense. Conceptual reference: https://github.com/d3/d3-sankey ; the implementation is local and does not load D3. Source data stays in one table (or the image zone list). Declare data-unidad (1–40 characters); numeric magnitude is limited to 10^12. Views round to eight significant digits while source values remain. Load evidence.js; NotaEvidencia.init/get/destroy owns lifecycle. Destroy before changing the source. No network or external libraries; data remains if enhancement fails.

## Cohorts

<!-- nota:ejemplo cohortes -->

```html
<figure class="amplio" id="evidencia-cohortes" data-evidencia="cohortes" data-unidad="clientes">
<div class="tabla-caja densa" role="region" tabindex="0" aria-label="Clientes activos por cohorte, datos desplazables">
<table data-evidencia-datos><caption>Clientes activos por cohorte</caption><thead><tr><th scope="col">Cohorte</th><th scope="col">Base</th><th scope="col">Mes 0</th><th scope="col">Mes 1</th><th scope="col">Mes 2</th><th scope="col">Mes 3</th></tr></thead><tbody>
<tr><th scope="row">Marzo</th><td data-valor="120">120</td><td data-valor="120">120</td><td data-valor="96">96</td><td data-valor="84">84</td><td data-valor="72">72</td></tr>
<tr><th scope="row">Abril</th><td data-valor="100">100</td><td data-valor="100">100</td><td data-valor="83">83</td><td data-valor="70">70</td><td data-estado="pendiente">Pendiente de observar</td></tr>
<tr><th scope="row">Mayo</th><td data-valor="80">80</td><td data-valor="80">80</td><td data-valor="60">60</td><td data-estado="pendiente">Pendiente de observar</td><td data-estado="pendiente">Pendiente de observar</td></tr>
<tr><th scope="row">Junio</th><td data-valor="60">60</td><td data-valor="60">60</td><td data-estado="pendiente">Pendiente de observar</td><td data-estado="pendiente">Pendiente de observar</td><td data-estado="pendiente">Pendiente de observar</td></tr>
</tbody></table>
</div>
<figcaption>Datos ficticios. Corte: 30 junio 2026. Cada celda cuenta personas activas ese mes; pueden regresar.</figcaption>
</figure>
```

**Use and limits:** Compare recurrence using 1–20 cohorts and 1–12 periods with labels up to 24 characters. Positive integer bases; integer counts between zero and base. Pending cells (`data-estado=pendiente`) must trail each row and are not zero. Exact count/base/percentage remain visible. Five intensity ranges: [0,20), [20,40), [40,60), [60,80), [80,100]%. No event-to-cohort calculation or incompatible period comparisons. Source data stays in one table (or the image zone list). Declare data-unidad (1–40 characters); numeric magnitude is limited to 10^12. Views round to eight significant digits while source values remain. Load evidence.js; NotaEvidencia.init/get/destroy owns lifecycle. Destroy before changing the source. No network or external libraries; data remains if enhancement fails.

## Sensitivity

<!-- nota:ejemplo sensibilidad -->

```html
<figure class="amplio" id="evidencia-sensibilidad" data-evidencia="sensibilidad" data-unidad="millones COP">
<p>Resultado base: <strong data-evidencia-base data-valor="100">100</strong> millones COP.</p>
<div class="tabla-caja densa" role="region" tabindex="0" aria-label="Resultado ante cambios de un supuesto, datos desplazables">
<table data-evidencia-datos><caption>Resultado ante cambios de un supuesto</caption><thead><tr><th scope="col">Supuesto</th><th scope="col">Escenario A</th><th scope="col">Resultado A</th><th scope="col">Escenario B</th><th scope="col">Resultado B</th></tr></thead><tbody>
<tr><th scope="row">Volumen</th><td>−10 %</td><td data-valor="91">91</td><td>+10 %</td><td data-valor="109">109</td></tr>
<tr><th scope="row">Precio</th><td>−5 %</td><td data-valor="92">92</td><td>+5 %</td><td data-valor="108">108</td></tr>
<tr><th scope="row">Combustible</th><td>−10 %</td><td data-valor="106">106</td><td>+10 %</td><td data-valor="94">94</td></tr>
</tbody></table>
</div>
<figcaption>Escenarios ilustrativos independientes. No son una proyección financiera ni combinan efectos.</figcaption>
</figure>
```

**Use and limits:** Compare assumption changes against one visible baseline with declared A/B outcomes. 1–16 rows sorted by absolute B−A range; A need not be the smaller outcome. Shapes distinguish extremes and selection exposes absolute change. No financial modeling, probabilities, interpolation or combined effects. Reset changes inspection, not source data. Source data stays in one table (or the image zone list). Declare data-unidad (1–40 characters); numeric magnitude is limited to 10^12. Views round to eight significant digits while source values remain. Load evidence.js; NotaEvidencia.init/get/destroy owns lifecycle. Destroy before changing the source. No network or external libraries; data remains if enhancement fails.

## Gantt

<!-- nota:ejemplo gantt -->

```html
<figure class="amplio" id="evidencia-gantt" data-evidencia="gantt" data-unidad="días">
<div class="tabla-caja densa" role="region" tabindex="0" aria-label="Hoja de ruta de una revisión, datos desplazables">
<table data-evidencia-datos><caption>Hoja de ruta de una revisión</caption><thead><tr><th scope="col">ID</th><th scope="col">Tarea</th><th scope="col">Inicio</th><th scope="col">Fin</th><th scope="col">Responsable</th><th scope="col">Estado</th><th scope="col">Depende de</th></tr></thead><tbody>
<tr><th scope="row">A</th><td>Diagnóstico</td><td>2026-09-01</td><td>2026-09-03</td><td>Operación</td><td>Completada</td><td>—</td></tr>
<tr><th scope="row">B</th><td>Ensayo</td><td>2026-09-03</td><td>2026-09-08</td><td>Producto</td><td>En curso</td><td>A</td></tr>
<tr><th scope="row">C</th><td>Revisión</td><td>2026-09-08</td><td>2026-09-10</td><td>Diseño</td><td>Plan</td><td>B</td></tr>
<tr><th scope="row">D</th><td>Evidencia</td><td>2026-09-03</td><td>2026-09-06</td><td>Operación</td><td>Completada</td><td>A</td></tr>
<tr><th scope="row">E</th><td>Decisión</td><td>2026-09-10</td><td>2026-09-10</td><td>Equipo</td><td>Plan</td><td>C, D</td></tr>
</tbody></table>
</div>
<figcaption>Calendario ficticio. Fechas UTC. Las barras representan intervalos inicio→fin; igualdad indica un hito.</figcaption>
</figure>
```

**Use and limits:** Show 1–24 tasks with actual dates, owners and finish-to-start dependencies. Unique ASCII IDs up to 12 characters; valid ISO dates over at most ten years. Comma-separated dependency IDs or an em dash for none. Reject cycles, absent IDs and dependencies ending after their successor starts. Explicit text/symbol status, never inferred from today. Duration is elapsed time, not inclusive working days. No holiday calendar, critical-path calculation or scheduler. Source data stays in one table (or the image zone list). Declare data-unidad (1–40 characters); numeric magnitude is limited to 10^12. Views round to eight significant digits while source values remain. Load evidence.js; NotaEvidencia.init/get/destroy owns lifecycle. Destroy before changing the source. No network or external libraries; data remains if enhancement fails.

## Funnel

<!-- nota:ejemplo embudo -->

```html
<figure class="amplio" id="evidencia-embudo" data-evidencia="embudo" data-unidad="pedidos">
<div class="tabla-caja densa" role="region" tabindex="0" aria-label="Del pedido a la entrega, datos desplazables">
<table data-evidencia-datos><caption>Del pedido a la entrega</caption><thead><tr><th scope="col">Etapa</th><th scope="col">Pedidos</th><th scope="col">Definición</th></tr></thead><tbody>
<tr><th scope="row">Solicitudes</th><td data-valor="1000">1000</td><td>Pedidos de una misma cohorte de ejemplo.</td></tr>
<tr><th scope="row">Validadas</th><td data-valor="800">800</td><td>Solicitudes con datos completos.</td></tr>
<tr><th scope="row">Programadas</th><td data-valor="500">500</td><td>Solicitudes validadas con programación.</td></tr>
<tr><th scope="row">Completadas</th><td data-valor="450">450</td><td>Programadas con recepción registrada.</td></tr>
</tbody></table>
</div>
<figcaption>Datos ilustrativos: misma cohorte y ventana de seguimiento para las cuatro etapas.</figcaption>
</figure>
```

**Use and limits:** Show counts, conversion and drop-off for the same population across 2–12 stages. Non-increasing nonnegative integer counts with a positive first stage. Conversion from a zero stage is undefined. No mixed populations, reentry or causal claims about loss. Bars start at zero and detail names the denominator. Source data stays in one table (or the image zone list). Declare data-unidad (1–40 characters); numeric magnitude is limited to 10^12. Views round to eight significant digits while source values remain. Load evidence.js; NotaEvidencia.init/get/destroy owns lifecycle. Destroy before changing the source. No network or external libraries; data remains if enhancement fails.

## Uncertainty

<!-- nota:ejemplo incertidumbre -->

```html
<figure class="amplio" id="evidencia-incertidumbre" data-evidencia="incertidumbre" data-unidad="pedidos">
<p data-evidencia-metodo>Los límites son escenarios declarados por el equipo de ejemplo. No hay un nivel de confianza ni una probabilidad asignada.</p>
<div class="tabla-caja densa" role="region" tabindex="0" aria-label="Escenarios de demanda, datos desplazables">
<table data-evidencia-datos><caption>Escenarios de demanda</caption><thead><tr><th scope="col">Fecha</th><th scope="col">Inferior</th><th scope="col">Central</th><th scope="col">Superior</th></tr></thead><tbody>
<tr><th scope="row">2026-10-01</th><td data-valor="80">80</td><td data-valor="100">100</td><td data-valor="125">125</td></tr>
<tr><th scope="row">2026-11-01</th><td data-valor="85">85</td><td data-valor="112">112</td><td data-valor="145">145</td></tr>
<tr><th scope="row">2026-12-01</th><td data-valor="90">90</td><td data-valor="120">120</td><td data-valor="160">160</td></tr>
<tr><th scope="row">2027-01-01</th><td data-valor="100">100</td><td data-valor="132">132</td><td data-valor="180">180</td></tr>
</tbody></table>
</div>
<figcaption>Datos ficticios de escenarios; no constituyen previsión de Liftit ni intervalo estadístico.</figcaption>
</figure>
```

**Use and limits:** Show a central trajectory with explicit lower/upper values across 2–48 strictly increasing ISO dates. All values finite and lower ≤ central ≤ upper. A visible `data-evidencia-metodo` explanation is required. The domain covers actual extremes; zero is not mandatory for a series. No inferred confidence, imputation or invented scenarios. Line/dash style supplements band color. Source data stays in one table (or the image zone list). Declare data-unidad (1–40 characters); numeric magnitude is limited to 10^12. Views round to eight significant digits while source values remain. Load evidence.js; NotaEvidencia.init/get/destroy owns lifecycle. Destroy before changing the source. No network or external libraries; data remains if enhancement fails.

## Zoomable evidence

<!-- nota:ejemplo evidencia-ampliable -->

```html
<figure class="amplio" id="evidencia-imagen" data-evidencia="imagen">
<h3>Revisar una evidencia en detalle</h3>
<div data-evidencia-imagen><img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMjAwIiBoZWlnaHQ9IjcyMCIgdmlld0JveD0iMCAwIDEyMDAgNzIwIj48cmVjdCB3aWR0aD0iMTIwMCIgaGVpZ2h0PSI3MjAiIGZpbGw9IiNmYWY1ZWQiLz48ZyBmaWxsPSIjMjgyYjM2IiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiI+PHRleHQgeD0iNzIiIHk9IjkwIiBmb250LXNpemU9IjM4Ij5SZWdpc3RybyBkZSB1bmEgcmV2aXNpw7NuPC90ZXh0Pjx0ZXh0IHg9IjcyIiB5PSIxMzYiIGZvbnQtc2l6ZT0iMjIiPklMVVNUUkFDScOTTiDCtyBOTyBFUyBVTkEgRkFDVFVSQSBOSSBVTiBSRUdJU1RSTyBSRUFMPC90ZXh0PjxwYXRoIGQ9Ik03MiAxNzJIMTEyOE03MiA1MDBIMTEyOCIgc3Ryb2tlPSIjOWE4YzdkIi8+PHRleHQgeD0iNzIiIHk9IjIzMCIgZm9udC1zaXplPSIyNCI+RG9jdW1lbnRvPC90ZXh0Pjx0ZXh0IHg9IjY2MCIgeT0iMjMwIiBmb250LXNpemU9IjI0Ij5SRVYtMDQyIMK3IDE1IHNlcHRpZW1icmUgMjAyNjwvdGV4dD48dGV4dCB4PSI3MiIgeT0iMzA2IiBmb250LXNpemU9IjI0Ij5FbnRyZWdhcyByZXZpc2FkYXM8L3RleHQ+PHRleHQgeD0iOTcwIiB5PSIzMDYiIGZvbnQtc2l6ZT0iMzIiPjI0PC90ZXh0Pjx0ZXh0IHg9IjcyIiB5PSIzODIiIGZvbnQtc2l6ZT0iMjQiPlBlbmRpZW50ZXMgZGUgZXZpZGVuY2lhPC90ZXh0Pjx0ZXh0IHg9Ijk3MCIgeT0iMzgyIiBmb250LXNpemU9IjMyIj4zPC90ZXh0Pjx0ZXh0IHg9IjcyIiB5PSI1NzIiIGZvbnQtc2l6ZT0iMjQiPlNpZ3VpZW50ZSBwYXNvPC90ZXh0Pjx0ZXh0IHg9IjcyIiB5PSI2MjAiIGZvbnQtc2l6ZT0iMjgiPlJldmlzYXIgbG9zIHRyZXMgc29wb3J0ZXMgYW50ZXMgZGUgY2VycmFyLjwvdGV4dD48L2c+PC9zdmc+" width="1200" height="720" alt="Ilustración de REV-042: 24 entregas revisadas, tres pendientes de evidencia. Se propone revisar soportes antes de cerrar."></div>
<ol data-evidencia-zonas>
  <li data-x="92" data-y="26">Fecha y referencia: REV-042, 15 septiembre 2026.</li>
  <li data-x="91" data-y="52">Tres entregas todavía requieren evidencia.</li>
  <li data-x="89" data-y="86">Siguiente acción: revisar los tres soportes antes de cerrar.</li>
</ol>
<figcaption>Ilustración creada para esta receta; reemplazar por una captura o imagen autorizada.</figcaption>
</figure>
```

**Use and limits:** Inspect one embedded data image with 1–12 numbered zones. Percentage `data-x/data-y` coordinates range 0–100; labels up to 100 characters. Zoom/fit supports 100–400%, local two-axis scrolling and keyboard/selector access. Overlapping zones remain accessible in the list. Place markers beside evidence. This does not increase image resolution or perform OCR. Author annotations are separate from reader comments; print preserves the original. Source data stays in one table (or the image zone list). Declare data-unidad (1–40 characters); numeric magnitude is limited to 10^12. Views round to eight significant digits while source values remain. Load evidence.js; NotaEvidencia.init/get/destroy owns lifecycle. Destroy before changing the source. No network or external libraries; data remains if enhancement fails.

## Relationship map

<!-- nota:ejemplo relationship-map -->

```html
<section class="pieza amplio" id="relationship-map-example" data-relationship-map>
<p class="ceja">Relaciones de ejemplo · datos sintéticos</p><h3>Del proyecto a la decisión</h3><p>Empieza en una pieza, sigue una conexión y vuelve atrás. Buscar encuentra piezas incluso fuera de la vecindad visible. Los filtros cambian el alcance, no la fuente.</p>
<details><summary>Fuente completa y alternativa sin JavaScript</summary>
<div class="tabla-caja" tabindex="0" role="region" aria-label="Piezas del mapa"><table data-map-nodes><caption>Piezas de ejemplo</caption><thead><tr><th scope="col">Nombre</th><th scope="col">Tipo</th><th scope="col">Contexto</th></tr></thead><tbody>
<tr data-node="project"><th scope="row">Piloto Horizonte</th><td>Proyecto</td><td>Determinar si existe evidencia suficiente para una prueba acotada.</td></tr>
<tr data-node="session"><th scope="row">Evaluar capacidad</th><td>Sesión</td><td>Conversación sintética; sin historial importado ni agente conectado.</td></tr>
<tr data-node="report"><th scope="row">Informe de capacidad · v2</th><td>Artefacto</td><td>Borrador ilustrativo con un supuesto de demanda pendiente de validar.</td></tr>
<tr data-node="source"><th scope="row">Registro de restricciones</th><td>Artefacto</td><td>Ejemplo de fuente relacionada; no contiene métricas de negocio reales.</td></tr>
<tr data-node="decision"><th scope="row">Alcance del piloto</th><td>Decisión</td><td>Propuesta condicionada a comprobar el supuesto. No hay aprobación registrada.</td></tr>
<tr data-node="review"><th scope="row">Verificar la demanda</th><td>Revisión</td><td>Comentario ilustrativo sobre la fuente de una afirmación.</td></tr>
</tbody></table></div>
<div class="tabla-caja" tabindex="0" role="region" aria-label="Relaciones del mapa"><table data-map-edges><caption>Relaciones declaradas y sugeridas del ejemplo</caption><thead><tr><th scope="col">Relación</th><th scope="col">Razón / fuente</th><th scope="col">Estado</th></tr></thead><tbody>
<tr data-source="project" data-target="session"><th scope="row">contiene</th><td>El objetivo de esta sesión pertenece al piloto de ejemplo.</td><td>Declarada</td></tr>
<tr data-source="session" data-target="report"><th scope="row">produjo</th><td>El informe representa el resultado declarado de la sesión sintética.</td><td>Declarada</td></tr>
<tr data-source="report" data-target="decision"><th scope="row">informa</th><td>La propuesta cita el informe; citarlo no demuestra que el supuesto sea válido.</td><td>Declarada</td></tr>
<tr data-source="review" data-target="report"><th scope="row">cuestiona</th><td>El comentario solicita la fuente de la demanda en la versión 2.</td><td>Declarada</td></tr>
<tr data-source="source" data-target="decision"><th scope="row">podría informar</th><td>Propuesta manual de conexión por una restricción compartida. Falta revisión.</td><td>Sugerida</td></tr>
</tbody></table></div></details></section>
```

**Use and limits:** Explore a declared local graph with node/edge tables, unique node IDs, type/context and directed links with reason and declared/suggested status. Both endpoints must exist. Search includes nodes beyond the current neighborhood; one/two-hop scope includes incoming/outgoing edges. Filters, history, zoom, fit, inspector and equivalent tables remain keyboard-accessible. Fit can shrink text; 100% restores it. Up to 100 nodes/250 edges, deterministic type-based layout. No AI inference, confidence scores, force simulation, persistent project editing or portal/session connection. Filter permissions before generating HTML; hidden browser nodes are not private. `BottifactRelationships.init/get/destroy` preserves source tables; invalid input does not mount a partial graph.

## Session brief

<!-- nota:ejemplo session-brief -->

```html
<section class="pieza ancho" id="session-brief-example"><p class="ceja">Sesión de ejemplo · pendiente de continuar</p><h3>Evaluar el alcance del piloto</h3><p>Objetivo: identificar la evidencia necesaria antes de recomendar una prueba.</p><dl class="datos"><div><dt>Agente / dispositivo</dt><dd>Codex · equipo de ejemplo</dd></div><div><dt>Origen</dt><dd>No conectado · muestra sintética</dd></div><div><dt>Resultado</dt><dd>Borrador del informe · versión 2</dd></div><div><dt>Siguiente paso</dt><dd>Validar la fuente del supuesto de demanda</dd></div></dl><details><summary>Qué conservar para retomar</summary><p>Pregunta inicial, restricciones conocidas, versiones producidas, decisiones abiertas y referencia real de la conversación cuando exista. Esta ficha no abre ni importa sesiones.</p></details></section>
```

**Use and limits:** Resume work using its actual objective, outputs and next step. Supply known document, version, quote, source, audience and state; explicitly mark unknowns. Semantic reading and keyboard disclosures reflow on mobile. Synthetic examples are not a portal session entity or conversation import. Reference real sessions only when available.

## Context bundle

<!-- nota:ejemplo context-bundle -->

```html
<section class="pieza ancho" id="context-bundle-example"><p class="ceja">Contexto de ejemplo · preparado, no enviado</p><h3>Verificar un supuesto antes de editar</h3><dl class="datos"><div><dt>Documento / versión</dt><dd>Informe del piloto · v2 ilustrativa</dd></div><div><dt>Audiencia</dt><dd>Creador y agente elegido</dd></div><div><dt>Incluido</dt><dd>Comentario, cita y objetivo del cambio</dd></div><div><dt>Excluido</dt><dd>Notas privadas no seleccionadas e historial completo</dd></div></dl><blockquote>«¿Cuál es la fuente de la demanda prevista?»</blockquote><div class="codigo codigo-editorial"><div class="cab"><span>Instrucción revisable</span><button type="button" data-copiar="context-bundle-prompt" aria-label="Copiar contexto de ejemplo">Copiar</button><span class="copia-estado" role="status"></span></div><pre tabindex="0" aria-label="Contexto de ejemplo"><code id="context-bundle-prompt">Documento: Informe del piloto. Versión: v2 (ejemplo).
Cita comentada: “La demanda prevista permite iniciar un piloto”.
Comentario: verificar la fuente de la demanda.
Objetivo: separar datos observados de supuestos. Si falta evidencia, indicarlo.
Entrega: proponer una revisión; no marcar el comentario como resuelto.
Origen: sin sesión conectada; no inventar una referencia.</code></pre></div><p class="procedencia">Copiar no entrega el paquete a un agente. Sustituye los datos ilustrativos antes de usarlo.</p></section>
```

**Use and limits:** Review and copy a task with quote, version, audience and objective. Supply verified provenance and explicit unknowns. Copying local text neither sends a message nor resumes an agent. Exclude private information inappropriate for the recipient. Preserve semantic reading, keyboard disclosures and mobile flow.

## Evidence ledger

<!-- nota:ejemplo evidence-ledger -->

```html
<figure class="ancho" id="evidence-ledger-example"><div class="tabla-caja" tabindex="0" role="region" aria-label="Registro de evidencia, tabla desplazable"><table><caption>Afirmaciones del piloto · ejemplo sin datos de negocio</caption><thead><tr><th scope="col">Afirmación</th><th scope="col">Estado</th><th scope="col">Fuente y alcance</th><th scope="col">Qué falta</th></tr></thead><tbody><tr><th scope="row">Existe demanda suficiente</th><td>Hipótesis</td><td>Sin fuente adjunta</td><td>Definir ventana, unidad y denominador</td></tr><tr><th scope="row">La interfaz permite revisar el informe</th><td>Propuesta verificable</td><td>Prototipo ilustrativo, no prueba de usuarios</td><td>Observar la tarea y registrar errores</td></tr><tr><th scope="row">La revisión reduce retrabajo</th><td>Pendiente de medir</td><td>No se infiere desde actividad</td><td>Establecer comparación y criterio de éxito</td></tr></tbody></table></div><figcaption>Distingue evidencia, interpretación y vacío. No asigna porcentajes de confianza inventados.</figcaption></figure>
```

**Use and limits:** Contrast claims with evidence and identify gaps before deciding. Supply real source/version/quote and explicit unknowns. No automatic confidence score or source verification. Preserve semantic headers, local table scrolling and accessible copyable text.

## Review queue

<!-- nota:ejemplo review-queue -->

```html
<section class="pieza ancho" id="review-queue-example"><p class="ceja">Revisión de ejemplo</p><h3>Dos pendientes, contextos diferentes</h3><div class="cards-trazadas cards-abiertas"><article><p class="ceja">Comentario compartido · abierto</p><h4>Validar la fuente de demanda</h4><blockquote>«La demanda permite iniciar un piloto»</blockquote><p>Informe · v2 · sección Supuestos. La cita sigue pendiente de comprobar.</p><details><summary>Qué se necesita para resolver</summary><p>Una fuente verificable y una versión revisada. Exportar el comentario no lo resuelve.</p></details></article><article><p class="ceja">Nota privada · ejemplo</p><h4>Preparar una pregunta para el agente</h4><p>Comparar el escenario conservador antes de recomendar.</p><details><summary>Audiencia del contexto</summary><p>Una interfaz debe filtrar esta nota por permisos antes de renderizarla. Ocultarla con CSS no la hace privada.</p></details></article></div><p class="procedencia">Muestra estática. Los hilos reales se crean desde los comentarios flotantes; esta receta no sincroniza ni administra permisos.</p></section>
```

**Use and limits:** Demonstrate shared comments and personal notes with their distinct context. This is a sample composition, not a connected manager. Use verified references and filter permissions server-side before creating HTML. Preserve mobile reading and keyboard disclosure; do not expose private notes in a public example.

## Version comparison

<!-- nota:ejemplo version-comparison -->

```html
<section class="pieza ancho" id="version-comparison-example"><p class="ceja">Revisión editorial · ejemplo</p><h3>De una afirmación a un supuesto explícito</h3><div class="cards-trazadas cards-abiertas"><article><p class="ceja">Antes · v2 ilustrativa</p><blockquote>La demanda permite iniciar el piloto.</blockquote><p>Problema: presenta una conclusión sin fuente.</p></article><article><p class="ceja">Propuesta · v3 ilustrativa</p><blockquote>El piloto depende de validar la demanda prevista. Todavía falta una fuente con período y denominador.</blockquote><p>El cambio aclara el límite; no fabrica evidencia.</p></article></div><details><summary>Revisión y trazabilidad</summary><p>Motivo: comentario sobre el supuesto. Estado: propuesta, no aceptada. Una comparación real debe enlazar versiones inmutables y conservar la cita original.</p></details></section>
```

**Use and limits:** Explain a manual editorial correction and its reason without hiding uncertainty. Use real source versions and quotes; examples are synthetic. Not an automatic diff or version-control engine. Keep Before/Proposal labels clear on mobile and retain keyboard-readable/copyable text.
