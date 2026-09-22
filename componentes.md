# Componentes de Bottifact

Para **nuevos artefactos**, escribe contenido con estas recetas y usa el generador de
[estandar.md](estandar.md): incorpora la llave sol/luna, comentarios, sonido y ayudas de lectura.
No reconstruyas esa base copiando el esqueleto histórico de abajo. Cada receta indica sus
módulos; el generador los detecta e incrusta junto con `fuentes.css` y `estilo.css` completos.
Las piezas no requieren React ni clases de Tailwind.

Para empezar por una pieza: [gráficas](#recetas-graficas),
[calor](#recetas-calor), [tablas](#recetas-tablas),
[sonido](#recetas-sonido), [escritura](#recetas-escritura),
[Three.js](#recetas-three). `plantilla.html` es el catálogo ejecutable;
`multipagina.html` muestra capítulos completos. Las recetas marcadas son sus fuentes.

## Documento y temas — compatibilidad histórica

Este esqueleto explica documentos anteriores con selector simple. **No es la base de nuevos
artefactos**: omite los controles que Angel pidió estandarizar. Para crear uno consulta
[estandar.md](estandar.md); la receta `apariencia` documenta la llave vigente con nueve paletas.


```html
<title>Nota — decisión y evidencia</title>
<meta charset="utf-8">
<style>/* Pegar aquí fuentes.css y estilo.css completos, incluidas las licencias */</style>
<meta name="viewport" content="width=device-width, initial-scale=1">
<a class="salto" href="#contenido">Saltar al contenido</a>
<main class="hoja" data-lectura lang="es">
  <div class="herramientas">
    <span class="firma-editorial"><span>Bottifact</span><small>Cuadernos</small></span>
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
<script>/* Pegar aquí interacciones.js completo */</script>
```

La plantilla ejecutable ya contiene los archivos incrustados. Los comentarios de este ejemplo
se sustituyen por los archivos indicados; no son dependencias remotas. Para una figura aún más
ancha, cambia `.ancho` por `.amplio`, nunca el ancho de todo el documento.

## Subrayado a mano

```html
<p>El estado definitivo debe vivir en <span class="marca">un solo registro</span>.
  El <a href="#evidencia">detalle de la evidencia</a> se puede consultar después.</p>
```

**Cuándo:** una frase que contiene la decisión. `.marca` usa dos trazos SVG incrustados, de
`1.7px`, con curvas distintas; `background-size:100% .32em` y `box-decoration-break:clone`
permiten saltar de línea. El tema Sea cambia el trazo a verde. El texto conserva su tinta,
selección y contraste; el trazo no pretende reemplazar enlaces o negritas.

## Nota manuscrita y corchete

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

**Cuándo:** una perspectiva complementaria, no una condición que cambia la decisión principal.
El párrafo ocupa la celda central; a partir de `1184px` la nota usa una celda real a su derecha.
Debajo, sigue al párrafo. La nota usa Reenie Beanie `26px / 1.18`; el corchete es CSS de `1px`
con remates de `9px`. Solo los remates decorativos son absolutos.

## Avisos con círculo

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

**Cuándo:** condiciones, errores, confirmaciones o citas breves. Omite la variante para una nota
informativa azul. Círculo `28px`, dos columnas `30px minmax(0,1fr)`, borde izquierdo `3px`;
el número pertenece al flujo y no invade un margen. No uses `role="alert"` para avisos estáticos.
El original usa símbolos dentro de un círculo; la numeración es la adaptación pedida por Angel.

## Mapa de proporción

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

**Cuándo:** participación sobre un total positivo y comparable. Las columnas `3fr 2fr` dan
60/40; las filas `5fr 3fr` subdividen el 40 en 25/15. Esta receta corresponde **solo a esos
pesos**. Al cambiar datos, calcula nuevas fracciones o genera un treemap con sus valores; no
cambies únicamente las etiquetas. Las filas tienen mínimos para proteger texto; con otros
idiomas o texto mucho más largo, verifica el reparto o usa un gráfico de barras y una tabla.

Para más de tres grupos, ordena por peso y considera agrupar la cola como «Otros», desglosada
aparte. No omitas cifras pequeñas ni sustituyas un porcentaje por una celda arbitraria. El
original calcula un treemap squarify; esta receta de rejilla es una versión explícita sin D3.

## Pastillas, lista mono y medida

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

**Cuándo:** la lista `dl` asocia etiquetas y valores; una pastilla representa un estado o dato
breve. La barra usa `meter` porque mide cobertura, no una operación en curso. No conviertas
fechas o nombres en controles falsos. Las pastillas saltan de línea si hace falta.

## Índice lateral y regla de lectura

Patrón por defecto para nuevos artefactos de Angel con varias secciones. Pega `fuentes.css` y
`estilo.css` inline, este HTML y `interacciones.js` una vez al final.

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

**Cuándo:** orientar un documento de varias secciones. Desde 1200 px, `lectura-guiada` reserva
200 px a la izquierda y 76 px a la derecha; el índice fijo mide 160 px y la regla 44 px.
Son decisiones de esta variante, no medidas de cmrg. Figuras y texto siguen calculando sus
anchos dentro del espacio disponible. Debajo, el índice se lee en el flujo y el progreso aparece
como control compacto en la esquina inferior izquierda; no tapa el control de comentarios.
El índice marca la sección actual y tacha las anteriores. El tachado indica posición, no prueba de lectura.
La regla admite clic, flechas, PageUp/Down y Home/End; actualiza su orientación accesible al cambiar de tamaño.

**Multipágina:** conserva las pestañas y añade un `nav.indice` dentro de cada `.pagina`, con enlaces
sólo a sus secciones. El contenedor usa `class="hoja multipagina lectura-guiada" data-lectura data-progreso-pagina`.
Para enlaces profundos con historial añade `data-historial data-enlaces-internos`, como en la biblioteca.
Coloca una sola `.regla.regla-guiada` después de `main`. Incluye `multipagina.js` después de
`interacciones.js`. El porcentaje corresponde al capítulo visible, excluye el pie y la paginación,
y se recalcula al cambiar de capítulo o abrir contenido. Si un capítulo cabe completo, indica 100 % al quedar visible entero.

**Cuándo no / límite:** una pieza aislada sin secciones no necesita un índice vacío. Los enlaces
exigen IDs únicos y existentes; no añadas `aria-live` al porcentaje porque anunciaría cada scroll.
No anides los componentes anchos dentro del índice ni alteres sus contenedores de rejilla.
El HTML funciona como navegación sin JS; el seguimiento y el porcentaje requieren el módulo.
Al imprimir se ocultan controles y se recupera el ancho. El patrón anterior `.hoja` + `.indice` +
`.regla`, sin las nuevas clases, conserva su comportamiento y el umbral de 1600 px.

## Código con encabezado y copia

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

**Cuándo:** la persona necesita inspeccionar, comparar o copiar una entrada exacta. El encabezado
usa mono `12px`; el código `13px / 1.65`, con desplazamiento y selección nativos. Si la API del
portapapeles está bloqueada, el script selecciona el contenido y explica cómo copiarlo. Usa
identificadores únicos por bloque. Escapa `&`, `<` y `>` al insertar código dentro del HTML.

## Tablas y diagramas anchos

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

Las tablas son anchas por defecto. No apliques `white-space:nowrap` a toda la tabla. Si una
columna contiene identificadores largos, permite partirlos; si la estructura necesita más
ancho, conserva el desplazamiento local. Los diagramas SVG deben tener `viewBox`, título y
una descripción equivalente en texto. El tamaño del dibujo debe proteger la lectura de sus
etiquetas; usa una región desplazable para figuras densas, o una composición vertical en móvil.

Diagrama completo, sin dependencias:

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

**Cuándo:** una relación o secuencia concreta se entiende mejor como dibujo. Para registros
comparables usa la tabla; para magnitudes, una gráfica a escala.

**Límite:** esta composición contiene tres pasos. Cambiar sólo las etiquetas no añade nodos
ni rutas; para más pasos ajusta SVG, texto equivalente y viewBox. Conserva los IDs únicos,
el mínimo de 640 px y su región desplazable. No simula procesos ni calcula tiempos.

## Texto que se desvanece

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

**Cuándo:** un anticipo opcional. La máscara `35% → 100%` afecta solo una copia decorativa;
el contenido íntegro siempre está disponible por teclado, lector de pantalla e impresión.
No apliques `.desvanece` al cierre de una conclusión, una alerta, una tabla o un pie con la fuente.

## Tarjetas «kept»

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

**Cuándo:** objetos o referencias seleccionados, no un catálogo exhaustivo. Portada opcional,
título completo y una nota personal o útil. `auto-fit` con mínimo adaptable de `240px`; el hover
inclina la portada `−2deg` y la eleva `3px` durante `320ms`, sin mover el texto. Con movimiento
reducido no hay transición. Si toda la tarjeta debe navegar, usa un enlace real con nombre;
no añadas un `onclick` a un `div`. Las portadas con `<img>` deben ser `data:` URI, como las de
`plantilla.html`, que se generan localmente y no reproducen carátulas comerciales.

## Multipágina

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
  <footer class="pie">Bottifact · Dos capítulos de ejemplo.</footer>
</main>
```

**Cuándo:** un informe con capítulos que se leen por separado y merecen cada uno su temario. No
para una nota de tres secciones: ahí la página única con índice lateral es mejor.

**La rejilla va en `.pagina`, no en `.hoja`.** Por eso la clase es `multipagina` y no
`por-seccion`: con las páginas de por medio, el selector `>` de `por-seccion` ya no alcanza a las
secciones y todo termina del ancho del párrafo.

**Instalación:** pega `interacciones.js` y después `multipagina.js`, completos dentro de
sendos `<script>` al final. El primero delega el índice cuando ve `.multipagina`; el segundo
mantiene `aria-current`, `aqui-visto` y `aqui-actual` únicamente en la página visible.
`multipagina.html` contiene la receta completa con ambos guiones y el CSS incrustados.

**Límite:** no carga páginas por red ni implementa un router de aplicación. Un enlace de
capítulo usa su ID (`#p2`); los enlaces a secciones son internos a la página ya abierta.
Sin JS sólo se ve el primer capítulo en pantalla; imprime todos los capítulos. No combines
`por-seccion` con `multipagina`. Cada ID y cada `data-ir` debe ser único y corresponderse.

El botón activo lleva `aria-current="page"`; el hash conserva la página abierta, así que un enlace
a un capítulo concreto funciona. Al cambiar de página se emite `nota:pagina` por si hay que
arrancar un lienzo o recalcular una figura.

## Tablas densas

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

**Cuándo:** desde cinco columnas. `.tabla-caja table` ya trae `min-width: 34rem`; `densa` lo sube a
`58rem`. Sin ese mínimo la tabla no se desplaza, se comprime: medido a 390 px, seis columnas daban
celdas de 50 px y filas de **581 px de alto**. Con `densa`, celdas de 139–285 px y filas de 140 px.
El desplazamiento es local —la página nunca se mueve de lado— y la caja es alcanzable por teclado.

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

**Cuándo:** una salida de consola, una consulta y su resultado, un volcado — cuando la evidencia
*es* el texto tal como se vio. No para código fuente de ejemplo: para eso está `.codigo`.

Se queda **oscura en los dos temas** a propósito: una terminal clara no se lee como una terminal.
La variante Sea sí cambia sus tonos, porque ahí el documento entero es oscuro y una caja con otro
negro se vería sucia. El botón de copia usa el mismo `data-copiar` del sistema. Alinea las columnas
con espacios dentro del `<pre>`; no uses una tabla disfrazada.

## Nota manuscrita señalada

<!-- nota:ejemplo manuscrita -->
```html
<div class="gesto-escrito">
  <p class="manuscrita" data-mano="fuente" data-escritura-sonora id="nota-decision">de doce frentes, siete están en producción. el cuello de botella ya no es construir: es decidir.</p>
  <button class="gesto-repetir" type="button" data-mano-repetir="nota-decision" data-audio="escritura" aria-label="Volver a escribir la nota" title="Volver a escribir la nota"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 10a9 9 0 1 1 2 8M3 4v6h6"/></svg></button>
</div>
```

**Cuándo:** destacar una observación breve con escritura que aparece al llegar a ella. Incluye
mano.js: `data-mano="fuente"` revela Reenie Beanie por caracteres, como cmrg.me; no sustituye
sus glifos por dibujos. Cada carácter aparece en 375 ms, escalonado para terminar con una
muestra original de lápiz de aproximadamente 2,18–3,03 s. El ejemplo se anima una vez al
entrar un 30 %; el botón permite repetirlo. `.manuscrita` sin atributo conserva texto estático.

**Límite:** notas breves, con fuente incrustada; no animar párrafos extensos ni información
crítica. Admite mayúsculas y puntuación de la fuente; palabras largas pueden partirse sin
comprimir letras. Texto equivalente completo para lectores y comentarios. Sin JS se lee completo.
Al salir, ocultar la pestaña o reducir movimiento se cancela la animación y se completa el texto.
No hay RAF. `data-escritura-sonora` reproduce una grabación original sólo tras activar Sonidos;
se corta al salir. No se normaliza, estira ni repite el audio. Sin el atributo permanece silenciosa.
La variante anterior `data-mano` sin valor sigue disponible con su alfabeto SVG y sus límites
(minúsculas, 240 caracteres, palabras de hasta 160 px). Para nuevas notas elige `fuente`.
`NotaMano.init/get/destroy` permite insertar o retirar la mejora preservando los nodos originales.

## Globo de rutas

```html
<figure class="ancho">
  <div id="mi-globo"></div>
  <figcaption>Rutas ilustrativas. La lista permanece disponible sin WebGL.</figcaption>
</figure>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.1/three.min.js"></script>
<script>/* Pegar aquí globo.js completo, con su licencia MIT */</script>
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

`globo.html` es la versión completa ejecutable de ese contrato, sin comentarios por sustituir.
La máscara terrestre está incrustada dentro de `globo.js`. No necesita APIs, claves, imágenes
externas ni solicitudes `fetch`.

| Entrada / método | Contrato |
|---|---|
| `points` | Array; `id` string único, `lat` número entre −90 y 90, `lon` entre −180 y 180; `label` opcional. |
| `arcs` | Array; `from` y `to` son IDs existentes; `id` opcional pero único, `label` y `detail` opcionales. Las coordenadas y unidades son geográficas. |
| `select(id)` | Selecciona y centra una ruta; `select(null)` vuelve a todas. Error si el ID no existe. |
| `setData({points,arcs})` | Reemplaza los datos validados, libera geometrías anteriores y reconstruye la lista. Datos inválidos lanzan `TypeError` y conservan el conjunto anterior. |
| `rotate(dx,dy)` | Radianes; giro horizontal e inclinación limitada a ±1,2. |
| `pause()` / `resume()` | Controlan el giro; `resume()` sigue respetando movimiento reducido. |
| `destroy()` | Detiene RAF, desconecta listeners/observers, libera WebGL y vacía el contenedor. |

Los puntos coincidentes no dibujan una curva degenerada; los antípodas usan un eje determinista.
Las etiquetas entran por `textContent`, no por HTML. Cuando serialices JSON dentro de un script,
escapa `<` como `\u003c`; nunca interpoles datos sin escapar dentro de `innerHTML`.

La proyección y la atmósfera siguen COBE; los arcos son bandas cuadráticas con 64 segmentos,
con ocultación tras la esfera. El giro es `0.072rad/s`, equivalente a los `0.0012rad/cuadro`
originales a 60 Hz, pero estable a otras frecuencias. El suavizado conserva el factor original
`0.09` a 60 Hz. En modo reducido el cambio de selección se resuelve inmediatamente; hay
botones y flechas de teclado. Con touch se puede girar horizontalmente y conservar el scroll
vertical de la página. Sin WebGL queda un mensaje y la lista completa de rutas.

El globo no es un mapa político ni una medición de distancias. La máscara de 256×128 describe
masas terrestres; no añade fronteras. No inventes kilómetros, vuelos o sedes: recibe datos reales
o identifica el ejemplo como ilustrativo. Los arcos y marcadores se han aclarado frente al
original, una decisión deliberada para informes, no una afirmación de igualdad píxel a píxel.


## Librería de evidencia: instalación por pieza

La fuente de cada visualización es **su tabla HTML**, no una segunda copia de los datos.
Pega `fuentes.css` y `estilo.css` completos y, al final del documento, los módulos necesarios dentro de
`<script>`: [graficas.js](graficas.js) para gráficas/calor y [tablas.js](tablas.js) para
ordenación/sparkline. Son independientes de Three.js. Cada módulo se pega una sola vez.
Se inicializan al cargar; para HTML insertado después usa `NotaGraficas.init(contenedor)`
o `NotaTablas.init(contenedor)`. Repetir `init` devuelve la instancia existente.
`get(elemento).destroy()` devuelve el HTML original; para nuevos datos, destruye la
instancia, modifica la tabla y vuelve a inicializar. No hay red, almacenamiento ni framework.

Los siguientes bloques son también la fuente del catálogo ejecutable: el ensamblador
extrae las recetas marcadas `nota:ejemplo`. Las figuras se copian **como hijas de `.hoja`**.
Para secciones anidadas usa `por-seccion`; para capítulos usa `multipagina` y coloca las
figuras como hijas de `.pagina`. No envuelvas el bloque en otra sección angosta.

`data-valor` usa punto decimal, sin separadores de miles; su texto visible incluye la
unidad y el formato humano. Vacío significa ausencia, `0` es un cero medido. Los ejemplos
son ilustrativos y lo dicen en su pie. Los nombres y los datos se insertan como texto.
Las unidades de los ejes se escriben completas junto al dibujo (`X`, `Y`) para permitir
que envuelvan en varias líneas. El SVG mantiene los ticks y sus valores en la misma escala.
Las gráficas no tienen animación ni tooltip imprescindible: la tabla permite consultar
cada punto por teclado. Las escalas se calculan con los datos, sin recortar extremos.
No se suman ni se interpolan registros ausentes. Los intervalos entre puntos de una línea
son segmentos rectos, no observaciones adicionales.

<a id="recetas-graficas"></a>

## Barras: cantidades y diferencias

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

**Cuándo:** comparar magnitudes en la misma unidad; admite negativos y hasta cuatro series agrupadas. Cero siempre está en la escala. Usa línea si importa la continuidad temporal.

**Límite:** hasta 500 filas y cuatro series. Muchas barras requieren una figura alta: para centenares de registros, prefiere tabla ordenable. El ancho mínimo del dibujo es 800 px con desplazamiento local; las categorías largas saltan de línea. No son barras apiladas ni porcentajes normalizados.

## Líneas: secuencia y datos ausentes

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

**Cuándo:** seguir una secuencia ordenada de categorías comparables. Trazo y número en la leyenda distinguen series incluso en Sea. Para fechas con separaciones distintas, usa temporal; para categorías independientes, barras.

**Límite:** los intervalos en X son categóricos y equidistantes. La ausencia corta el trazo, no se convierte en cero. El eje Y muestra el dominio completo observado; no tiene que comenzar en cero porque codifica posición. Hasta cuatro series; no calcula suavizados ni intervalos de confianza.

## Serie temporal con variación

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

**Cuándo:** comparar observaciones fechadas. La posición usa milisegundos UTC: dos días y cinco días no ocupan el mismo espacio. El delta compara los dos últimos registros y nombra ambos.

**Límite:** fechas ISO diarias válidas, únicas y crecientes; no agrega días ni corrige zonas horarias. El delta absoluto es actual − anterior y el relativo divide por |anterior|; base 0 indica porcentaje no definido, ausente indica sin comparación. Si tus registros representan ventanas, deben tener duración/composición comparables. No infiere causalidad ni si subir es bueno.

## Dispersión: relación entre dos variables

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

**Cuándo:** explorar pares X/Y medidos en la misma observación. Las dos variables tienen ejes numéricos con unidades. Para una sola secuencia de tiempo usa temporal.

**Límite:** cada punto exige ambos valores finitos. Hasta 500 puntos; coincidentes se superponen y siguen separados en la tabla. No ajusta regresiones, no aplica jitter, no representa incertidumbre ni permite inferir causalidad.

## Distribución: histograma con intervalos reales

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

**Cuándo:** mostrar la distribución de una variable continua agrupada en intervalos explícitos. Los bordes de las barras corresponden a los bordes del intervalo.

**Límite:** frecuencias enteras no negativas; intervalos crecientes sin solapamientos. La densidad se calcula como frecuencia/ancho; con intervalos desiguales es el área la que representa el conteo. La tabla declara inclusión/exclusión de extremos; el módulo no agrupa muestras individuales ni inventa bins. No es una curva de probabilidad ni un gráfico de categorías.

<a id="recetas-calor"></a>

## Attention map: matriz de intensidad

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

**Cuándo:** buscar concentraciones entre dos dimensiones discretas. Cada celda muestra su valor y la leyenda tiene intervalos explícitos. Para partes de un total usa `.mapa`, que conserva el treemap original.

**Límite:** cinco niveles, definidos por seis límites crecientes; máximo incluido en el último nivel. Un valor fuera del dominio produce error visible y conserva la tabla, nunca se satura en secreto. Hasta 31 × 31 celdas con ancho mínimo por columna y scroll local. No usa degradado ni escala implícita por fila. Las cifras mantienen el significado con colores forzados.

<a id="recetas-tablas"></a>

## Tabla de comparación

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

**Cuándo:** comparar las mismas propiedades de pocas alternativas. Escribe la decisión en la cabecera además de señalarla con color. No uses un ranking si los criterios son cualitativos.

**Límite:** la clase `.elegida` se aplica a cada celda de la columna; no calcula ganadores. Para cinco columnas o más añade `densa`. No vuelve sticky la primera columna, para que el espacio útil del teléfono quede disponible al desplazar.

## Tabla de totales y ordenación

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

**Cuándo:** consultar registros y su total aditivo; ofrece ordenación cuando ayuda a encontrar extremos. Sin `data-tabla` funciona como tabla estática.

**Límite:** el total lo calcula quien prepara los datos, no el DOM. No sumar porcentajes, tasas o promedios. Un solo `tbody`, sin celdas combinadas ni filas de subtotal dentro de él; no hay paginación o filtrado. La ordenación numérica requiere `data-valor`; ausencias quedan al final en ambos sentidos. Repetidos conservan su orden, `tfoot` no se mueve.

## Tabla con serie embebida

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

**Cuándo:** añadir tendencia a una tabla sin apartarse del registro. El texto de la celda nombra cada valor; el SVG es redundante y lleva `aria-hidden`.

**Límite:** X equidistante; todas las filas deben describir los mismos períodos. Exige `data-min`/`data-max` comunes y rechaza dibujar puntos fuera de ellos. No autoescala por fila, no es una gráfica con ejes ni codifica tiempo irregular; para eso usa la serie temporal. El texto sigue disponible si el dibujo no se puede generar.

<a id="recetas-sonido"></a>

## Sonido: control central y canal independiente

En la biblioteca, Apariencia controla todo el audio con [audio.js](audio.js), incluido antes de `interacciones.js`. Para copiar sólo un canal independiente usa [sonido.js](sonido.js). En nuevos artefactos, el control central empieza habilitado y espera el primer clic real para abrir Web Audio; recuerda el silencio elegido. El canal independiente conserva su inicio apagado y su botón de activación. El control central oculta los interruptores locales cuando está presente.

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

**Cuándo:** confirmar una acción explícita y breve, en una experiencia donde la persona
puede apagarlo siempre. No añade sonido a gráficos, scroll genérico, foco ni cambios de tema. El botón de activación no emite una señal. El canal independiente no recuerda la preferencia y vuelve a apagado al ocultar la pestaña; la base central recuerda el silencio y pausa al ocultarse. Sólo los elementos con atributos de escritura o hover autorizan esos gestos sonoros.

**Límite:** Web Audio y gesto real de botón; eventos sintéticos no activan ni reproducen.
El canal independiente de `sonido.js` usa seno, ganancia pico 0,025, ataque 3 ms y caída a 0,0001 en 55 ms;
acción 660→440 Hz, confirmación 520→780 Hz, atención 440→360→440 Hz. Cada nota dura 60 ms,
separada por 5 ms; total 125 o 190 ms. Son decisiones de Nota, no mediciones del sitio.
Una nueva señal interrumpe la anterior. No son alarmas, sonificación de series ni audio de
fondo, y la ganancia digital no garantiza un nivel acústico en el dispositivo.
`NotaSonido.get(contenedor).disable()` apaga; `.destroy()` cierra el contexto y listeners.
`NotaSonido.init(contenedor)` inicializa HTML nuevo. No hay método público de reproducción
automática. Sin `audio.js`, `[data-sonido]` conserva el comportamiento anterior.

Con la base estándar, `audio.js` usa los MP3 originales de cmrg.me, incrustados en base64 y
decodificados por Web Audio al activar Sonidos. Clic, hover, confirmación, atención y tres
lápices; sin descargas durante la lectura. Conserva los niveles de la referencia (clic .9,
hover .4, lápiz .6, positivo/negativo .8) multiplicados por el volumen maestro inicial .65.
Hover usa playbackRate .9; el lápiz mantiene su tono y duración original, sin bucle ni normalización.
El canal independiente anterior se conserva sólo cuando falta `audio.js`; con él, sus botones
usan las mismas grabaciones y el mismo interruptor de la cabecera.
`NotaAudio.enabled`, `activeVoices`, `plays` y `samples` permiten inspeccionar el estado;
`NotaAudio.disable()` apaga y cancela las voces. `data-audio="accion|confirmacion|atencion|escritura"`
en botones conserva su resultado textual. Procedencia y hashes en `assets/sonidos-cmrg/PROCEDENCIA.md`
y `auditoria/sonidos-cmrg.json`. La sustitución de síntesis por grabaciones fue pedida por Angel.

<a id="recetas-escritura"></a>

## Escritura: trazo a trazo

Pega [escritura.js](escritura.js) una vez al final. La frase de ejemplo está dibujada con
paths originales; la animación recorre **su longitud**, no un rectángulo que descubre texto.

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
  <figcaption>Gesto ilustrativo original de Bottifact. 2400 ms repartidos por la longitud de cada trazo; la frase siempre permanece escrita debajo.</figcaption>
</figure>
```

**Cuándo:** una anotación corta y secundaria que gana significado con el gesto del trazo.
Con `data-al-ver` se escribe una vez al entrar al menos un 30 % de su caja en pantalla; sin ese atributo empieza completa y la persona decide repetirla. En la base estándar el sonido está habilitado y espera un primer clic real; si estaba silenciado, actívalo en Apariencia. En un canal independiente pulsa Activar sonido y después Repetir escritura. Con `data-escritura-sonora`, y sólo después de que un clic habilite el contexto de audio, el lápiz acompaña la animación al entrar y se detiene al salir. Sin el atributo la entrada es silenciosa. Incluye `audio.js` con Apariencia para el sonido de lápiz; si copias la escritura sola, `sonido.js` ofrece el mismo gesto de lápiz desde su botón local. El acceso «Ver escritura animada» aparece sólo en documentos que incluyen un trazo. Conserva `.manuscrita` para texto corriente
que deba seleccionarse, traducirse o cambiar con datos.

**Límite:** recibe paths SVG ordenados, no transforma automáticamente cualquier fuente
en escritura cursiva. Cada path es un trazo continuo; separa levantamientos de lápiz en
paths distintos. No uses contornos de glifos rellenos si esperas un trazo central de pluma.
Al cambiar la frase, dibuja paths correspondientes y actualiza `data-texto-escritura`.
El SVG es redundante (`aria-hidden`), el texto equivalente es permanente. Admite 100–10000 ms,
no música sincronizada. Web Animations se cancela y completa al salir de pantalla, ocultar
la pestaña o activar movimiento reducido; no hay RAF ni colas que se reanuden al volver. La entrada automática ocurre una sola vez por instancia; Repetir permite verla de nuevo.
`NotaEscritura.get(elemento).play()`, `.finish()` y `.destroy()` controlan la instancia;
`.play()` respeta movimiento reducido. `NotaEscritura.init(elemento)` admite inserción tardía.

<a id="recetas-three"></a>

## Three.js: dispersión XYZ

Usa **una sola** inclusión externa para toda la nota (compartida con `NotaGlobo`):

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.1/three.min.js"></script>
```

Después pega [escena.js](escena.js) completo dentro de `<script>`, una vez, al final.
No necesita `globo.js`, `graficas.js`, controles externos ni importaciones adicionales.

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

**Cuándo:** la tercera variable aporta una relación espacial que conviene explorar. Los
controles giran la vista e identifican registros sin depender de arrastrar ni acertar a un punto.
Si dos variables bastan, la dispersión SVG es más fácil de leer y comparar.

**Límite:** 1–100 registros finitos; sin ausencias, regresión, jitter ni inferencias de
correlación. Cada eje tiene dominio propio, por lo que distancia geométrica no equivale
a una métrica entre variables de unidades distintas. Los puntos pueden ocluirse: elegir
uno atenúa los demás y escribe su valor. El lienzo conserva 600 px de ancho mínimo con
scroll local; las etiquetas de ejes deben ser breves, con las unidades en las cabeceras.
La tabla siempre queda visible, con o sin WebGL. Ningún dato existe sólo en una textura.

## Three.js: etapas con duración

Misma instalación de `escena.js` y la misma inclusión única de Three.js.

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

**Cuándo:** explicar etapas de un proceso junto con su duración. Seleccionar una etapa
conecta su caja con la explicación escrita. Empieza inmóvil; el giro continuo es optativo.
Usa las barras SVG para comparar muchas categorías o cuando girar no aporte información.

**Límite:** 1–12 etapas en orden, duraciones no negativas. La altura cero no se infla para
hacer visible una caja. No representa dependencias, paralelismo, un waterfall acumulado
ni una simulación física. No sumes duraciones como tiempo total si las etapas se solapan.
Los números 1…N identifican las filas de la tabla. Rotar puede superponer etiquetas; los
valores exactos permanecen en la tabla y «Vista inicial» devuelve la composición inicial.

### Ciclo de vida de NotaEscena

| Operación | Contrato |
|---|---|
| `NotaEscena.init(raíz)` | Inicializa `data-escena` una vez por figura; el segundo llamado devuelve la instancia existente. |
| `new NotaEscena(figura)` | Alternativa manual; rechaza una segunda instancia para el mismo contenedor. |
| `NotaEscena.get(figura)` | Recupera la instancia automática. |
| `select(índice)` / `select(null)` | Selecciona una fila, índice desde cero, o muestra todas. Rechaza índices inexistentes. |
| `rotate(dx,dy)` | Giro manual inmediato, en radianes. |
| `pause()` / `resume()` | Desactiva/solicita giro. `resume()` respeta movimiento reducido, visibilidad y estado WebGL. |
| `destroy()` | Cancela RAF, aborta listeners, desconecta observers, libera geometrías/materiales/texturas/renderer y devuelve la tabla original. Es idempotente. |

El giro es 0,15 rad/s, limitado por tiempo, no por cuadros. Sólo hay RAF mientras la vista
es visible, la pestaña está activa, se pidió girar y no hay movimiento reducido. Cambiar
esa preferencia cancela el RAF pendiente; el giro manual sigue siendo instantáneo.
Colores leídos de los tokens claros/oscuros/Sea; los rótulos son canvas locales. Al retirar
la figura de una aplicación llama `destroy()`. Para reemplazar datos: destruye, modifica
la tabla e inicializa otra vez. No hay `fetch`, modelos, mapas ni imágenes externas.

## Límites de las piezas editoriales base

Estas condiciones complementan el HTML y el criterio de cada receta anterior. No cambian
las clases existentes; ayudan a elegir una pieza antes de copiarla.

| Pieza | Cuándo no usarla / qué no hace / qué puede romperla |
|---|---|
| Documento y temas | No reemplaza un formato solicitado distinto de HTML. Un solo selector y `data-theme` en la raíz; mezclar CSS parciales puede dejar tokens sin definir. |
| `.marca` | No señalar un párrafo entero ni expresar un estado sólo con el trazo. No transforma texto en enlace ni dibuja escritura animada. |
| `.con-margen` / `.margen` / `.nota` | No esconder una condición crítica al margen. Varias páginas de texto manuscrito desbordan el propósito de la anotación; el bloque base de margen es hijo directo de `.hoja`. |
| `.aviso` ×4 | No asignar urgencia a todos los párrafos. Una numeración no implica pasos ejecutables; para alertas dinámicas se necesita gestionar el anuncio sin duplicarlo. |
| `.mapa` | No negativos, ausencias ni datos nuevos con proporciones viejas. Esta receta fija sólo representa 60/25/15; usa barras si no vas a recalcular la rejilla. |
| `.dato` / `.datos` / `.pildora` | No falsear controles ni eliminar unidades para que quepan. No calculan ni validan datos; el texto debe incluir el estado además del color. |
| `.medida` | No representar una tarea en ejecución: usa `progress` para eso. `min/max/value`, porcentaje y texto deben describir el mismo denominador. |
| `.indice` / `.regla` | No en una nota breve. IDs duplicados, destinos inexistentes o falta de `data-lectura` rompen seguimiento; el tachado indica posición, no lectura demostrada. |
| `.codigo` | No sustituye un editor ni ejecuta código. Portapapeles puede estar denegado; conserva selección manual y estado. Resaltado escrito a mano, no detección automática de sintaxis. |
| `.tabla-caja` / `.densa` | No grandes bases de datos virtualizadas. Cinco o más columnas usan `densa`; alterar mínimos sin verificar 320/390 puede comprimir las celdas. |
| `.terminal` | No usar para una tabla analítica que necesite ordenar o cabeceras semánticas. Sólo copia texto, no ejecuta comandos. Las columnas dependen de mono y espacios; el ancho se desplaza dentro del `pre`. |
| `.extracto` | No degradar datos críticos ni aplicar máscara al único ejemplar del texto. La copia decorativa debe ser `aria-hidden`; la versión completa vive en `details`. |
| `.kept` | No envoltorio universal para el informe. No carga portadas ni convierte tarjetas en enlaces; añade un `a` real si hay navegación y datos de imagen incrustados. |
| `.manuscrita` / `.senalado` | No instrucciones críticas ni frases llenas de corchetes. Sin atributos es tipografía estática y seleccionable. Para texto breve animado usa `data-mano` con `mano.js`; para paths propios usa `NotaEscritura`. |
| `NotaGlobo` | No topografía, fronteras políticas ni distancias medidas. Una instancia por contenedor, IDs de puntos/rutas únicos; `destroy()` al retirarlo. Sin Three/WebGL conserva lista y mensaje. |

## Alcance de esta versión

Es una librería de recetas HTML/CSS/JS copiables, sin instalación de framework. No incluye
un CLI de generación, React, una dependencia de shadcn, un constructor de consultas,
streaming, mapas políticos o conversión automática de fuentes a caligrafía. Cualquier pieza
nueva debe conservar los tres temas, los datos accesibles, los mínimos locales y el ciclo
de vida documentado. Los ejemplos no se publican ni envían datos.

## Segunda tanda: reportes, artículos y prototipos

Las siguientes recetas amplían el sistema; no cambian los anchos ni los estilos de documentos
previos. Incluye `fuentes.css`, `estilo.css` e `interacciones.js`. Añade [reportes.js](reportes.js)
para `data-reporte`, [visor.js](visor.js) para `data-visor`. El recorrido necesita además
`globo.js` y la única inclusión de Three 0.160.1. Los módulos son independientes de
`graficas.js`; no cargan red. `NotaReportes.init(raíz)` y `NotaVisores.init(raíz)` se pueden
repetir; `get(elemento).destroy()` retira la mejora y restaura los datos originales.
Para cambiar una tabla destruye, edita y vuelve a inicializar. No hay observador de datos.

## Apariencia y lectura cómoda

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
    <div class="apariencia-encabezado"><p class="apariencia-titulo">Tu espacio</p><span data-tema-actual>Sistema</span></div>
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
    <div class="apariencia-encabezado"><p class="apariencia-titulo">Tu espacio</p><span data-tema-actual>Sistema</span></div>
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
    <div class="apariencia-encabezado"><p class="apariencia-titulo">Tu espacio</p><span data-tema-actual>Sistema</span></div>
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

**Cuándo:** un control discreto de lectura en la cabecera. El círculo sol/luna es la opción
principal; la etiqueta hace explícita su función y la cápsula muestra la preferencia elegida.
Copia un solo `details` en una nota. El ejemplo reúne tres variantes para compararlas.
La cabecera del catálogo reutiliza exactamente el primer control con IDs/nombres propios.

**Interacción:** Temas, Letras y Sonido son pestañas con flechas izquierda/derecha, Home y End.
Escape cierra y devuelve el foco a la llave; pulsar o enfocar fuera cierra. Un solo panel abierto.
Los radios conservan la selección; elegir una familia no cierra el panel para poder comparar.
Claro, Oscuro y Sistema son modos independientes: cambiar de familia mantiene el modo.
El tema actual se nombra arriba aunque un filtro lo oculte. Búsqueda sin tildes por nombre o
 descripción, categoría, contador y restablecimiento. Las muestras tienen scroll local con foco y nombre.
El silencio y volumen están sólo en Sonido. Sin JS el disclosure abre, pero los ajustes
no cambian el documento: no es una configuración persistida en el propio HTML.

**Tipografía:** seis combinaciones, independientes de los colores. Editorial: Instrument Serif / Geist;
Sobrio: Geist / Geist; Técnico: Geist Mono / Geist. Libro: Literata / Literata; Revista: Instrument Serif /
Literata; Bitácora: Geist Mono / Literata. El primer nombre corresponde a títulos y el segundo a lectura.
Literata normal e itálica, pesos 400–700, latín y latín extendido, están incrustados; OFL y procedencia en
`licencias/literata-OFL.txt` y `auditoria/literata-fuentes.json`. Reenie Beanie sigue reservada a notas;
código y controles conservan sus familias. Instrument Serif es de títulos, no se usa como cuerpo largo.

**Cuándo no / límite:** no modifica prototipos ni emula preferencias del sistema. Los temas son opciones
predefinidas, no un editor de tokens ni una descarga de temas. Para ampliar, copia una etiqueta con radio,
muestra y `data-tema-familia`; define todos los tokens, registra su clave en interacciones.js/contrato y
actualiza validación. La búsqueda descubre las etiquetas disponibles sin una lista de resultados duplicada.
No inserta controles dinámicamente. Cada copia necesita IDs, aria-controls, aria-labelledby y nombres de
radio únicos. Incluir interacciones.js una vez. Tipografía puede cambiar altura y saltos: revisar contenido real.
Las preferencias se guardan por origen, o por archivo cuando hay presentación inicial; el silencio se comparte
por origen. Sin localStorage funcionan durante la sesión. Sin Web Audio se explica el fallo; habilitado no
significa que el navegador o dispositivo ya esté reproduciendo. El grano incrustado es independiente de la
paleta; se retira al imprimir. Lectura cómoda sigue siendo 18 px/1,7, sin comprimir datos.

## Ficha de decisión

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

**Cuándo:** conservar el razonamiento de una decisión con sus condiciones de revisión.
**Cuándo no / límite:** no es un aviso urgente ni un registro de aprobación. El estado,
responsables y fechas son contenido editorial; no guarda aceptación, firmas ni historial.

## Cronología anotada

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

**Cuándo:** ordenar eventos y explicar qué cambió. En móvil la fecha queda sobre su evento.
**Cuándo no / límite:** no codifica duración ni distancia temporal; el espacio entre filas no
representa días. Para comparar duraciones usa etapas. No afirma causalidad por proximidad.

## Ficha de artículo

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

**Cuándo:** artículos que necesitan autoría, fecha y estado editorial sin ocupar una portada.
**Cuándo no / límite:** no inventa tiempo de lectura, credenciales ni revisión por pares. Los
campos son opcionales y no son botones. No genera metadatos SEO ni tarjetas para redes.

## Referencias con regreso al texto

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

**Cuándo:** citas, aclaraciones o fuentes extensas que interrumpirían el párrafo. Funcionan sin JS.
**Cuándo no / límite:** no es una bibliografía automática. IDs únicos por nota y una llamada
por retorno; si una fuente se cita varias veces, añade retornos distintos y explícitos. Las
fuentes reales requieren autor, título, fecha y enlace verificable. Estas dos son aclaraciones
internas, no citas bibliográficas. Mantén llamada y referencia en la misma página multipágina.

## Glosario editorial

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

**Cuándo:** vocabulario propio de un informe o artículo que necesita definiciones compartidas.
**Cuándo no / límite:** no es una ayuda que aparece sólo al pasar el cursor; las definiciones
permanecen visibles. No incluye búsqueda ni traduce términos. Las definiciones son editoriales.

## Metodología desplegable

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

**Cuándo:** explicar detalles del método después de un resumen que ya declara el límite principal.
**Cuándo no / límite:** no ocultes condiciones que cambian la conclusión. `details` funciona sin
JS; `interacciones.js` abre y restaura el método al imprimir. No verifica ni ejecuta el método.

## Antes y después editorial

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

**Cuándo:** mostrar una corrección de texto, una decisión de interfaz o una revisión de contenido.
**Cuándo no / límite:** no calcula un diff, ni compara capturas con un deslizador. `del`/`ins`
identifican cambios editoriales; para alternativas sin relación temporal usa comparación.

## Cascada de cantidades

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

**Cuándo:** explicar un total como suma de aportes positivos y negativos en la misma unidad.
**Cuándo no / límite:** no sumar tasas, porcentajes ni monedas distintas. Tres columnas,
1–60 filas; valores y acumulados finitos de hasta ±10⁹. La primera fila también es un cambio
desde cero; no admite subtotales intermedios ni reinicios. El módulo calcula acumulados y
resultado, nunca toma la tercera columna como entrada. Tabla visible y dibujo de 860px con
scroll local. Cero y todos los acumulados están en la escala. Sin animación.

## Pequeños múltiples con escala común

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

**Cuándo:** comparar patrones de hasta cuatro grupos sin superponer sus líneas.
**Cuándo no / límite:** los períodos son equidistantes y deben ser los mismos para todos los
grupos; no codifica fechas irregulares. Entre 2 y 60 filas. Valores finitos de hasta ±10⁹,
vacío distinto de cero. Cada panel conserva 360px mínimos dentro de su región desplazable.
Sin valores, el dominio convencional es 0–1 y no hay puntos; no se inventan observaciones.

## Conciliación de registros

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

**Cuándo:** comparar conteos esperados/observados y conservar la explicación por fila.
**Cuándo no / límite:** requiere conteos enteros no negativos (≤10⁹), no importes monetarios.
No cruza IDs, no detecta duplicados ni demuestra conciliación contable. Si falta un observado,
el total indica incompleto y no da un saldo neto. Cinco columnas exactas, hasta 60 filas.
Las explicaciones son editoriales: el módulo no las infiere de la diferencia.

## Calculadora de escenarios

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

**Cuándo:** explicar la sensibilidad de un resultado a supuestos explícitos y reversibles.
**Cuándo no / límite:** modelo lineal de capacidad, sin simulación, predicción ni valoración
financiera. Minutos no negativos, hasta un día por operación y un millón de operaciones al mes;
volumen entero y tiempos en décimas. Si después es mayor, muestra horas adicionales. Vacíos y
entradas fuera de límites invalidan el resultado; no conserva silenciosamente una cifra previa.
Sin JS se ve el cálculo inicial; no usar los controles como formulario de recolección.

## Globo narrado por etapas

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

**Cuándo:** la ubicación y el orden de una historia importan. Las etapas escritas siempre están
visibles; el mapa orienta una ruta a la vez. Incluye Three una sola vez y `globo.js` antes de
`reportes.js`. Comparte la dependencia con todos los demás globos/escenas del documento.

**Cuándo no / límite:** no convierte etapas abstractas en geografía. `data-lugar` identifica
un lugar; repetir un ID exige las mismas coordenadas y nombre. Cada ruta necesita un ID único
y dos lugares. No autoavanza ni añade sonido. Empieza pausado; conserva controles de NotaGlobo,
reduce, pausa por visibilidad y destroy. Sin Three queda mensaje y relato; sin WebGL queda
además la lista de rutas. No añade mapas, texturas ni geocodificación remota.
La lista del globo también cambia la etapa del relato. Una ruta seleccionada mantiene su
orientación: para giro libre usa «Vista inicial» y «Reanudar giro»; anterior/siguiente vuelve
a orientar la etapa. No interpreta el giro manual como un cambio de etapa.

## Visor de prototipos con estados

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

**Cuándo:** documentar estados de un componente o recorrer un prototipo pequeño dentro de un
artículo. El lienzo cambia entre 320, 390, 768, 1024 y el espacio disponible. Reiniciar reconstruye
la muestra original. El menú de dispositivo elige el ancho; la proporción fija la altura del marco, Rotar intercambia sus dimensiones y Ajustar escala la vista para caber. El estado muestra dimensiones CSS y porcentaje visual. Incluye `controles.js` y `visor.js`. El texto alternativo aparece sin JS y al imprimir. No carga archivos.

**Cuándo no / límite:** no es un emulador de iPhone, una captura ni un navegador remoto. No
modifica la densidad de píxeles, el motor o el viewport del documento. Usa **Shadow DOM y
`@container`**, por eso las reglas responsivas del prototipo deben consultar el contenedor;
`@media (width)` seguiría midiendo la ventana exterior. No hay iframe porque la CSP lo bloquea.
El template contiene HTML/CSS de confianza, sin guiones ni manejadores `on…`; no es un sandbox
para HTML ajeno. Los botones `data-demo-ir` activan un `data-demo-pagina` del mismo visor;
no envían formularios, calculan datos ni persisten cambios. Los IDs, si se usan, viven dentro
del shadow. Los estilos del documento no entran, pero sí se heredan sus tokens y fuentes.
El contenido del prototipo debe respetar reduce; el visor no inicia RAF ni transiciones.
`NotaVisores.get(figura).setWidth('768')` permite controlar el ancho; `setAspect('9/16')` fija la proporción (`auto`, `9/16`, `4/3`, `16/9`, `1/1`). Ajustar reduce visualmente también los textos: usa 100 % para valorar legibilidad. `reset()` reinicia y
`destroy()` devuelve la alternativa textual y retira listeners/observer.

## Elegir y copiar desde el catálogo

`plantilla.html` ofrece búsqueda por nombre/propósito y el HTML exacto de cada receta en un
`details` junto al ejemplo. La búsqueda filtra **el índice de recetas**, no borra secciones de
la nota ni altera su progreso. Acentos y mayúsculas no cambian los resultados. El índice
completo sigue disponible sin JS. El botón usa el mismo contrato de copia y alternativa por
selección de `interacciones.js`. El módulo [catalogo.js](catalogo.js) sólo hace falta en un
catálogo que incluya `data-buscador-recetas`; no se necesita en artículos normales.

Las muestras son componentes de documento, no un constructor de aplicaciones. Cada snippet
requiere las fuentes y módulos indicados arriba; el botón copia el componente, no toda la
biblioteca. La plantilla y los ejemplos completos sí son autocontenidos.

## Pestañas dentro de una pieza

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

**Cuándo:** alternar vistas cortas de una misma pregunta: hallazgo/evidencia/límite, diseño/datos
u otras vistas relacionadas. Incluye `pestanas.js` después de `interacciones.js`.
Flechas, Inicio y Fin mueven el foco; Enter o Espacio activan (comportamiento nativo del botón).
El ratón activa al pulsar. Hay un solo tabulador activo; cada panel tiene nombre y foco.

**Cuándo no / límite:** no uses pestañas para ocultar pasos obligatorios o avisos esenciales.
Para capítulos largos usa navegación multipágina. No carga datos, no sincroniza la URL, no
ofrece pestañas deshabilitadas ni persistencia. Mantén botones y paneles en el mismo orden,
con IDs únicos. No anides instancias. Sin JS se ven todas las secciones; al imprimir también.
`NotaPestanas.init(raíz)`, `get(elemento).select(índice)` y `destroy()` siguen el ciclo habitual.
`select` no mueve foco; se emite `nota:pestana` al cambiar para que otras piezas puedan medir.

## Ficha de hallazgo

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

**Cuándo:** separar una afirmación de la evidencia que la sostiene y de lo que aún falta
comprobar. Sirve para investigación, reportes, revisiones de prototipo y artículos técnicos.
**Cuándo no / límite:** no genera conclusiones ni grados de confianza. Una hipótesis pendiente
no se vuelve un hallazgo confirmado por presentarla aquí. Reemplaza las frases de ejemplo
por datos, fuentes y límites verificables; no repitas la ficha por cada párrafo del informe.
HTML estático, sin estado ni eventos; funciona con todos los papeles y al imprimir.

## Informe de cuatro capítulos

El ejemplo [informe.html](informe.html) reúne piezas existentes como una lectura coherente.
Los botones superiores son navegación de capítulos (`aria-current="page"`), no tabs ARIA;
las pestañas locales de Evidencia sí son un tablist. Cada capítulo sigue la rejilla multipágina.

<!-- nota:ejemplo informe -->
```html
<a class="salto" href="#contenido">Saltar al contenido</a>
<header class="edicion-cabecera" id="inicio">
  <div class="edicion-franja"><a class="firma-editorial" href="#resumen" aria-label="Primer capítulo"><span>Bottifact</span><small>Estudios de producto</small></a><div class="edicion-acciones"><span>Edición 02</span></div></div>
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
<footer class="pie"><span>Bottifact · Estudios de producto</span><p>Cuatro capítulos, una pregunta. Datos ilustrativos, sin solicitudes ni registros reales.</p></footer>
</main>
```

**Cuándo:** un reporte con varias tareas de lectura: comprender la decisión, consultar datos,
probar una propuesta y revisar los próximos pasos. La cabecera conserva una firma editorial
compacta. Añade una sola llave de apariencia de su receta en `.edicion-acciones` si se necesita;
el ensamblador del ejemplo ya lo hace. No copies las tres variantes del control.

**Instalación:** `interacciones.js`, `multipagina.js`, `graficas.js`, `reportes.js`, `visor.js`
y `pestanas.js`, incrustados al final; fuentes y CSS completos. Este ejemplo no necesita Three.
`data-historial` activa historial de capítulos para Atrás/Adelante; sin ese atributo sigue el
contrato anterior con replaceState. Los enlaces `#evidencia` y `#prototipo` abren esos capítulos.

**Cuándo no / límite:** no es un router ni carga HTML remoto. Los enlaces a secciones no abren
otros capítulos; comparte el ID del capítulo. Sin JS sólo se ve el primero en pantalla;
impresión incluye los cuatro. Si el informe es corto, usa página única. Para alternar sólo
vistas de una figura, usa la receta de pestañas. Los anchos grandes son hijos de `.pagina`.

## Paletas adicionales

`oliva`, `arcilla` y `ciruela` son opciones explícitas en `data-theme`. Oliva usa papel verde
claro; Arcilla, papel durazno y tinta terracota; Ciruela, fondo oscuro y acentos malva.
Son decisiones nuevas de esta librería, no colores medidos en cmrg.me. Todas incluyen escalas
de gráficas/calor, estados y tonos de WebGL; los tres papeles anteriores permanecen intactos.
Una paleta no comunica por sí sola estado, certeza o calidad. Mantén palabras y símbolos.
El color y el estilo tipográfico se eligen por separado. El terminal conserva su superficie
oscura deliberada, como en los papeles originales.

## Archivo de publicaciones

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
    <article data-publicacion data-publicacion-tema="Diseño"><p class="ceja">Diseño · <time datetime="2026-09-14">14 sep 2026</time></p><h4><a href="informe.html#resumen">Una revisión antes de confirmar</a></h4><p data-extracto>El recorrido desde una hipótesis hasta una propuesta que se puede probar.</p><p class="procedencia" data-meta>Equipo editorial · Estudio de ejemplo</p></article>
    <article data-publicacion data-publicacion-tema="Investigación"><p class="ceja">Investigación · <time datetime="2026-09-12">12 sep 2026</time></p><h4><a href="informe.html#evidencia">Lo que una cifra todavía no demuestra</a></h4><p data-extracto>Separar el dato observado, el supuesto y la siguiente pregunta.</p><p class="procedencia" data-meta>Equipo editorial · Ensayo de ejemplo</p></article>
    <article data-publicacion data-publicacion-tema="Producto"><p class="ceja">Producto · <time datetime="2026-09-10">10 sep 2026</time></p><h4><a href="informe.html#prototipo">Probar antes de publicar</a></h4><p data-extracto>Una interfaz local con estados explícitos y varios anchos de lectura.</p><p class="procedencia" data-meta>Equipo editorial · Guía de ejemplo</p></article>
  </div><p data-archivo-vacio hidden>No encontramos publicaciones. Borra la búsqueda o elige otro tema.</p>
</section>
```

**Cuándo:** Una portada o archivo corto de artículos ya incluidos en el documento. Requiere editorial.js; combina texto y tema, ignora acentos y permite limpiar filtros.

**Cuándo no / límite:** No sustituye búsqueda de un CMS, paginación de servidor ni índice de miles de entradas. Sólo filtra el HTML local; sin JS muestra todo. Los enlaces del ejemplo llevan a capítulos reales de informe.html; reemplázalos al copiar. No inventa fechas ni tiempos de lectura.

## Ficha de autor

<!-- nota:ejemplo autor -->
```html
<aside class="pieza autor-editorial" id="autor-ejemplo" aria-labelledby="autor-nombre">
  <span class="autor-inicial" aria-hidden="true">t</span><div><p class="ceja">Acerca de esta edición</p><h3 id="autor-nombre">Equipo editorial</h3><p>Investigación, producto y documentación. Esta identidad ilustra la ficha; reemplázala por la autoría real del artículo.</p><a href="informe.html">Leer el estudio completo →</a></div>
</aside>
```

**Cuándo:** Cerrar un artículo con autoría y contexto, o abrir una página de autor. HTML estático.

**Cuándo no / límite:** No acredita identidad ni contribuciones. La inicial es decorativa porque el nombre ya está escrito; una foto deberá ir incrustada como data: con el alt adecuado.

## Lecturas relacionadas

<!-- nota:ejemplo relacionados -->
```html
<nav class="pieza" id="relacionados-ejemplo" aria-labelledby="relacionados-titulo"><h3 id="relacionados-titulo">Seguir el hilo</h3><ol class="lecturas-relacionadas"><li><span class="ceja">01 · Evidencia</span><a href="informe.html#evidencia">Qué sabemos y qué falta medir</a><p>Los supuestos que sostienen la propuesta.</p></li><li><span class="ceja">02 · Práctica</span><a href="informe.html#prototipo">Recorrer el prototipo</a><p>Explorar los estados de una tarea.</p></li></ol></nav>
```

**Cuándo:** Proponer siguientes lecturas seleccionadas por su relación con el argumento.

**Cuándo no / límite:** No recomienda automáticamente ni personaliza. Usa destinos existentes y descripciones específicas; no sirve para esconder la navegación principal.

## Diagrama anotado

<!-- nota:ejemplo anotaciones -->
```html
<figure class="pieza ancho" id="anotaciones-ejemplo">
<h3>Tres momentos de una confirmación</h3><div class="diagrama-caja" tabindex="0" role="region" aria-label="Flujo anotado de 720 píxeles, desplazable">
<svg class="plano-anotado" viewBox="0 0 720 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="anotaciones-titulo anotaciones-desc"><title id="anotaciones-titulo">Crear, revisar y confirmar</title><desc id="anotaciones-desc">Uno: crear borrador. Dos: revisar datos. Tres: confirmar. Las tres notas siguientes explican cada paso.</desc><g fill="none" stroke="currentColor"><rect x="10" y="45" width="200" height="110" rx="6"/><rect x="260" y="45" width="200" height="110" rx="6"/><rect x="510" y="45" width="200" height="110" rx="6"/><path d="M210 100h45m-9-7 9 7-9 7M460 100h45m-9-7 9 7-9 7"/></g><g text-anchor="middle" fill="currentColor"><text x="110" y="85">01</text><text x="110" y="120">Crear borrador</text><text x="360" y="85">02</text><text x="360" y="120">Revisar datos</text><text x="610" y="85">03</text><text x="610" y="120">Confirmar</text></g></svg></div>
<ol class="notas-anotadas"><li><strong>Crear.</strong> Los datos permanecen editables; todavía no hay envío.</li><li><strong>Revisar.</strong> Se presenta fecha, duración y nombre en un resumen.</li><li><strong>Confirmar.</strong> La interfaz debe explicar qué se guardó y ofrecer un siguiente paso.</li></ol><figcaption>Flujo conceptual; las distancias no representan tiempo ni cantidad. Las notas contienen toda la explicación del dibujo.</figcaption>
</figure>
```

**Cuándo:** Explicar partes numeradas de un flujo o una captura incrustada sin depender de hover.

**Cuándo no / límite:** No mide atención ni registra clics. Las notas deben mantener numeración y orden del dibujo. Un diagrama ancho conserva escala con desplazamiento local, no se comprime para caber.

## Historial de revisiones

<!-- nota:ejemplo revisiones -->
```html
<section class="pieza" id="revisiones-ejemplo"><h3>Qué cambió en el documento</h3><p class="procedencia">Historial ficticio para mostrar el formato; no describe commits del repositorio.</p><ol class="revisiones-editoriales"><li><p class="ceja"><time datetime="2026-09-14">14 sep 2026</time> · v0.2 · Equipo editorial</p><h4>Se explican las exclusiones</h4><p>El cálculo ahora distingue capacidad estimada de ahorro realizado.</p></li><li><p class="ceja"><time datetime="2026-09-12">12 sep 2026</time> · v0.1 · Equipo editorial</p><h4>Primera propuesta</h4><p>Hipótesis, prototipo y preguntas por observar.</p></li></ol></section>
```

**Cuándo:** Reportes que cambian tras una revisión y artículos con correcciones materiales.

**Cuándo no / límite:** No es auditoría automática, control de versiones ni firma verificable. Escribe cambios reales y responsables reales; no uses la fecha de compilación como fecha de publicación.

## Matriz de criterios

<!-- nota:ejemplo criterios -->
```html
<figure class="pieza amplio" id="criterios-ejemplo"><h3>Comparar sin esconder el criterio</h3><div class="tabla-caja" tabindex="0" role="region" aria-label="Matriz de criterios, desplazable"><table class="matriz-criterios"><caption>Opciones de revisión · comparación conceptual</caption><thead><tr><th scope="col">Criterio</th><th scope="col">Resumen final</th><th scope="col">Revisión por paso</th><th scope="col">Cómo comprobarlo</th></tr></thead><tbody><tr><th scope="row">Ver todo en contexto</th><td>Reúne los campos</td><td>Los reparte entre pantallas</td><td>Observar errores detectados</td></tr><tr><th scope="row">Editar cerca del dato</th><td>Requiere acceso desde el resumen</td><td>Edición dentro de cada paso</td><td>Contar pasos de corrección</td></tr><tr><th scope="row">Tiempo total</th><td>Pendiente de medir</td><td>Pendiente de medir</td><td>Misma tarea, alcance comparable</td></tr></tbody></table></div><figcaption>No hay puntuación agregada: las compensaciones y los datos faltantes quedan visibles.</figcaption></figure>
```

**Cuándo:** Decisiones entre opciones con criterios explícitos y evidencia comparable.

**Cuándo no / límite:** No inventa pesos, puntuaciones ni ganador. Si un criterio no se observó, marca pendiente; no conviertas etiquetas ordinales en precisión numérica.

## Registro de riesgos

<!-- nota:ejemplo riesgos -->
```html
<figure class="pieza amplio" id="riesgos-ejemplo"><h3>Lo que podría salir mal</h3><div class="tabla-caja" tabindex="0" role="region" aria-label="Registro de riesgos, desplazable"><table><caption>Riesgos ilustrativos de un flujo de confirmación</caption><thead><tr><th scope="col">Causa y consecuencia</th><th scope="col">Responsable propuesto</th><th scope="col">Mitigación</th><th scope="col">Señal para revisar</th></tr></thead><tbody><tr><th scope="row">Un resumen incompleto permite confirmar un dato incorrecto</th><td>Diseño de producto</td><td>Mostrar todos los campos críticos y su edición</td><td>Correcciones posteriores a confirmar</td></tr><tr><th scope="row">Un fallo de guardado parece un envío exitoso</th><td>Ingeniería</td><td>Confirmar sólo tras respuesta válida y ofrecer reintento</td><td>Discrepancia entre interfaz y registro</td></tr></tbody></table></div><figcaption>Ejemplo sin probabilidades estimadas. Asigna personas y señales verificables en el proyecto real.</figcaption></figure>
```

**Cuándo:** Acompañar decisiones con causa, impacto, dueño, mitigación y señal observable.

**Cuándo no / límite:** No estima probabilidad ni severidad automáticamente, y no multiplica escalas ordinales. No sustituye seguimiento operativo ni asigna trabajo a personas reales.

## Configuración editorial

<!-- nota:ejemplo configuracion -->
```html
<section class="pieza" id="configuracion-ejemplo" data-config-editorial><h3>La misma publicación, otra edición</h3><p>Elige cómo se presentan las publicaciones del archivo. Los cambios se aplican en este documento.</p><form class="editorial-controles" aria-label="Configuración del archivo"><label>Presentación<select name="disposicion"><option value="rejilla">Rejilla editorial</option><option value="lista">Lista de lectura</option></select></label><label class="editorial-check"><input type="checkbox" name="extractos" checked> Mostrar extractos</label><label class="editorial-check"><input type="checkbox" name="metadatos" checked> Mostrar autoría y formato</label><button type="reset">Restablecer edición</button></form><p data-config-estado role="status">Rejilla editorial con extractos y metadatos.</p><div class="codigo"><div class="cab"><span>Configuración local · JSON</span><button type="button" data-copiar="config-editorial-json">Copiar configuración</button><span class="copia-estado" role="status"></span></div><pre tabindex="0" aria-label="Configuración editorial JSON, desplazable"><code id="config-editorial-json" data-config-json>{"version":1,"disposicion":"rejilla","extractos":true,"metadatos":true}</code></pre></div><p class="procedencia">Configuración de presentación, independiente de la paleta y tipografía del botón de apariencia. No instala un tema de Ghost.</p><p><a href="#archivo-ejemplo">Ver el archivo con esta configuración →</a></p></section>
```

**Cuándo:** Variar lista/rejilla y cantidad de información sin cambiar el contenido. Requiere editorial.js; actualiza los archivos [data-archivo] del mismo documento y genera JSON copiable.

**Cuándo no / límite:** No guarda preferencias ni importa JSON, no cambia el contenido y no conecta Ghost. El alcance es todo el documento; usa un solo configurador. Sin JS conserva el estado inicial. La paleta, tipografía y lectura cómoda siguen en apariencia.

## Biblioteca completa y registro local

[biblioteca.html](biblioteca.html) reúne **44 recetas en nueve capítulos**: inicio,
publicaciones, artículos, reportes, gráficas, tablas, prototipos, espacio y gesto, y edición.
Cada pieza se genera desde el HTML anterior, con su criterio, límites y dependencias al lado.
El estudio narrativo sigue en [informe.html](informe.html); el cuaderno continuo, en
[plantilla.html](plantilla.html). Son tres composiciones del mismo sistema.

**Cuándo:** explorar y copiar piezas, evaluar temas con contenidos distintos o compartir
un componente concreto. `data-enlaces-internos` en `.hoja.multipagina` habilita enlaces a
IDs descendientes y su historial, por ejemplo `biblioteca.html#receta-calor`. Es optativo:
las notas anteriores conservan su contrato. La barra navega capítulos, no es un tablist. Cada capítulo conserva además su índice de secciones y la regla muestra su progreso; en portátil ambos disponen de espacio reservado.
El destino se muestra, recibe foco al navegar y queda fuera de la barra fija. Para enlazar
vistas de pestañas usa el ID de la receta, no un panel oculto de la pieza.

**Límite:** es una biblioteca HTML local, no un CMS ni un tema Ghost instalable. No crea
usuarios, comentarios, pagos o suscripciones. La búsqueda encuentra recetas locales y el
archivo filtra las publicaciones que ya contiene. Al imprimir se incluyen todos los capítulos;
la búsqueda y la configuración son controles de pantalla. Sin JS se muestran todos los
capítulos de esta edición, con los datos originales y las alternativas de cada componente.

[registro.json](registro.json) contiene HTML, capítulo, dependencias y documentación de cada
receta. Es un formato local versionado, **no el esquema de instalación de shadcn**. No lo
cargues por fetch dentro de un artefacto. El ensamblador lo construye junto al HTML, sin red.
`NotaEditorial.init(raíz)` y `get(elemento).destroy()` permiten inicializar y desmontar archivo
/configurador. No anides archivos ni dupliques configuradores; los IDs de copiado son únicos.

La configuración de Ghost inspira la separación entre contenido y presentación. Una futura
integración necesita plantillas Handlebars, contexto del CMS, `package.json` y validación
GScan; copiar este HTML no cumple ese contrato. La comparación y sus fuentes están en
[edicion-completa.md](auditoria/edicion-completa.md).

## Tabla interactiva

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

**Cuándo:** Investigar una tabla corta: buscar, filtrar un estado, agrupar y ordenar dentro de cada grupo. Incluye `controles.js` y `explorador.js`. Buscar queda visible; Filtros, Agrupar y Columnas abren paneles compactos. Cada encabezado ofrece ascendente, descendente y restablecer. Escape cierra el menú y devuelve el foco. Las columnas ocultas se pueden recuperar; Nombre permanece. Los encabezados indican `aria-sort`; el total corresponde sólo a las filas visibles.

**Cuándo no / límite:** tabla local de 1–16 columnas y hasta 2000 filas. Admite texto, números con `data-valor` y fechas ISO mediante `data-tipo="fecha"` en el encabezado; declara `data-tipo="numero"` cuando corresponda. La receta de cuatro columnas mantiene equipo, estado e importe, pero el motor no exige ese esquema. `data-columna-estado` y `data-columna-total` usan índices desde cero (por defecto 2 y 3); declara la unidad de la suma. No mezcla monedas ni conecta un servidor.

Incluye filtro por columna (texto, rango numérico o fecha), búsqueda, grupos plegables de la página, columnas visibles, selección de filas entre páginas, paginación 10/25/50/100, espaciado y encabezado fijo. Mayús al elegir otro orden agrega un criterio. El total corresponde a la vista filtrada completa; el contador de grupo corresponde a la página. Exportar selección incluye filas seleccionadas aunque estén fuera del filtro, usando columnas visibles; sin selección exporta toda la vista filtrada. CSV neutraliza fórmulas. Impresión muestra la fuente completa. No hay edición de celdas ni virtualización. `NotaExplorador.init/get/destroy`, `instance.visible`, `instance.selected` e `instance.exportCSV()` conservan los valores originales.

## Tabla jerárquica desplegable

<!-- nota:ejemplo tabla-jerarquica -->
```html
<figure class="amplio" id="jerarquia-ejemplo" data-jerarquia>
<div class="jerarquia-filtros" role="group" data-jerarquia-filtros aria-label="Filtrar por estado">
<button type="button" data-filtro="" aria-pressed="true">Todos</button>
<button type="button" data-filtro="Usado" aria-pressed="false">Usado</button>
<button type="button" data-filtro="Sin usar" aria-pressed="false">Sin usar</button>
</div>
<p class="jerarquia-cuenta" data-jerarquia-cuenta role="status"></p>
<div class="tabla-caja densa" tabindex="0" role="region" aria-label="Entregas por fecha, tabla desplazable">
<table data-columna-filtro="3"><caption>Entregas por fecha · ejemplo</caption>
<thead><tr><th scope="col">Fecha / destinatario</th><th scope="col">Detalle</th><th scope="col">Monto</th><th scope="col">Estado</th></tr></thead>
<tbody>
<tr data-grupo="g1"><th scope="row">14 ago 2026</th><td>2 personas</td><td class="numero">$300</td><td>50 % usado</td></tr>
<tr data-de="g1"><th scope="row">Persona de ejemplo</th><td>$etiqueta</td><td class="numero">$200</td><td>Usado</td></tr>
<tr data-de="g1"><th scope="row">Otra persona</th><td>$etiqueta2</td><td class="numero">$100</td><td>Sin usar</td></tr>
<tr data-grupo="g2"><th scope="row">6 ago 2026</th><td>1 persona</td><td class="numero">$500</td><td>100 % usado</td></tr>
<tr data-de="g2"><th scope="row">Tercera persona</th><td>$etiqueta3</td><td class="numero">$500</td><td>Usado</td></tr>
</tbody></table></div>
<figcaption>Datos ilustrativos. Las filas de resumen llevan <code>data-grupo</code>; sus hijas, <code>data-de</code> con el mismo identificador.</figcaption>
</figure>
```

**Cuándo:** un resumen por grupo que se despliega a su detalle sin salir de la tabla — fechas con sus destinatarios, lotes con sus filas, categorías con sus partidas. Incluye `jerarquia.js`. Las columnas se mantienen alineadas entre el resumen y su detalle, que es lo que lo vuelve legible: el monto del grupo cae sobre los montos de sus hijas. Empieza plegado y cada fila de resumen es un botón con `aria-expanded`; la flecha gira y el detalle aparece debajo, indentado.

**Filtro optativo:** declara `data-jerarquia-filtros` con pastillas `data-filtro` dentro de la figura y, si quieres un contador vivo, `data-jerarquia-cuenta`. `data-columna-filtro` elige la columna comparada (por defecto, la última). Al filtrar, los grupos con coincidencias se abren solos y los que no tienen desaparecen: buscar un estado no debería obligar a abrir todos los grupos a mano. La comparación es por texto exacto de la celda.

**Cuándo no / límite:** no reemplaza `explorador` cuando hace falta búsqueda libre, orden por columna o exportación. Todo el contenido existe en el HTML, así que sin JavaScript la tabla se lee completa —plegar es una mejora, no un requisito—. Cada `data-grupo` necesita un identificador único y sus hijas el mismo valor en `data-de`; un grupo sin hijas no se convierte en botón. No pagina, no ordena ni carga datos por demanda: con centenares de grupos conviene una tabla filtrable. `NotaJerarquia.init/get`, más `abrirTodo()`, `cerrarTodo()`, `filtrar(valor)` y `destroy()` por instancia.

## Familia de cards

<!-- nota:ejemplo cards -->
```html
<section class="pieza ancho" id="cards-ejemplo"><h3>Tarjetas con un propósito</h3><div class="cards-editoriales">
<article class="card-editorial"><p class="ceja">Lectura / 01</p><h4><a href="informe.html#evidencia">De la hipótesis a la evidencia</a></h4><p>Una tarjeta editorial con título, extracto y destino concreto.</p><p class="procedencia">Ensayo de ejemplo · Investigación</p></article>
<article class="card-editorial card-dato"><p class="ceja">Indicador / 02</p><h4>Sesiones revisadas</h4><p class="card-valor">12 <span>de 20</span></p><meter min="0" max="20" value="12" aria-label="12 de 20 sesiones revisadas">60 %</meter><p class="procedencia">60 % · cifras ficticias para mostrar cobertura, no progreso en tiempo real.</p></article>
<article class="card-editorial"><p class="ceja">Proyecto / 03</p><h4>Confirmar con contexto</h4><p><span class="pildora p-medio">Propuesta por validar</span></p><dl><dt>Siguiente paso</dt><dd>Observar una tarea completa.</dd></dl><a href="informe.html#prototipo">Probar el prototipo →</a></article>
</div></section>
```

**Cuándo:** Agrupar entidades distintas: artículo, indicador y proyecto. La rejilla se adapta al ancho; el enlace está en el título o acción, no en toda la tarjeta.

**Cuándo no / límite:** No uses una tarjeta por párrafo ni escondas una comparación que necesita tabla. Los valores y estados requieren fuente. No hay clics superpuestos, carrusel ni alturas fijas que corten textos. HTML estático con tokens de las seis paletas.

### Pegar un prototipo propio

El visor ofrece **Embeber mi HTML** y `NotaVisores.get(elemento).loadHTML(texto)`. Conserva el ancho elegido y Reiniciar vuelve al template original. Acepta hasta 100.000 caracteres de HTML declarativo con CSS local; rechaza scripts, eventos inline, iframes, envíos, recursos externos y CSS con url()/@import. No es un navegador remoto ni un sanitizador para contenido hostil. Usa HTML de confianza, imágenes raster data: y consultas @container para adaptar el prototipo a su ancho. No modifica ni guarda la fuente del documento.

## Comentarios sobre el documento

<!-- nota:ejemplo revision -->
```html
<section class="pieza" id="revision-ejemplo" data-revision>
<h3>Revisar sin perder el contexto</h3><p>Activa Comentar y elige un párrafo, título, figura o card. También puedes seleccionar texto antes de pulsar Comentar.</p><div class="acciones"><button type="button" data-revision-modo aria-pressed="false">Comentar documento</button><button type="button" data-revision-lista>Ver comentarios</button></div><p data-revision-estado role="status">Comentarios locales con exportación para compartir.</p>
<dialog class="revision-dialogo revision-ui" data-revision-editor aria-labelledby="revision-editor-titulo"><form><h2 class="sr-only" id="revision-editor-titulo">Añadir comentario</h2><details class="revision-contexto"><summary title="Ver contexto del punto"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/></svg><span class="sr-only">Contexto del punto</span></summary><p data-revision-contexto tabindex="0" aria-label="Contexto completo del comentario"></p></details><label for="revision-texto">Ajuste que propones</label><textarea id="revision-texto" data-revision-texto rows="1" maxlength="4000" required placeholder="Escribe un comentario…"></textarea><div class="acciones"><button type="button" class="nota-icono" data-revision-guardar aria-label="Guardar comentario" title="Guardar comentario"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 19V5m-6 6 6-6 6 6"/></svg></button><button type="button" class="nota-icono" data-revision-cancelar aria-label="Cerrar comentario" title="Cerrar comentario"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 6 12 12M6 18 18 6"/></svg></button></div></form></dialog>
<dialog class="revision-dialogo revision-ui" data-revision-panel aria-labelledby="revision-panel-titulo"><h2 id="revision-panel-titulo">Comentarios del documento</h2><p class="procedencia">Revisión local: exporta el archivo para compartir los hilos.</p><ol data-revision-notas></ol><div class="codigo"><div class="cab"><span>Prompt de ajustes</span><button type="button" data-copiar="revision-prompt">Copiar prompt</button><span class="copia-estado" role="status"></span></div><pre tabindex="0" aria-label="Prompt con comentarios, desplazable"><code id="revision-prompt" data-revision-prompt>No hay comentarios todavía.</code></pre></div><button type="button" data-revision-cerrar>Cerrar comentarios</button></dialog>
</section>
```

**Cuándo:** dejar observaciones concretas en un artefacto y copiarlas como prompt con capítulo, referencia, fragmento y ajuste. Incluye revision.js después de interacciones.js. La herramienta es una burbuja fija con icono y contador. Activa Comentar y pulsa el punto del documento: el editor pequeño se abre al lado, sin bloquear la página. Guardar añade un pin flotante fuera del flujo, sin desplazar ni reservar espacio. Tab y Enter permiten elegir un bloque por teclado; Escape cierra o cancela y ⌘/Ctrl+Enter guarda. Ver comentarios abre una lista con contexto y prompt copiable. Puedes seleccionar texto, editar o borrar cada comentario.

**Cuándo no / límite:** revisión asíncrona: guarda eventos en este navegador, comparte un JSON e importa respuestas sin duplicarlas. No hay cuentas verificadas, envío remoto ni presencia entre equipos. Permite responder, asignar un nombre, resolver/reabrir y ver actividad. El prompt sólo incluye abiertos y preserva cita, autor y respuestas. No entra en Shadow DOM: comenta la figura exterior. Los pines flotan y siguen el bloque; si su texto cambió o hay varios candidatos, el hilo queda sin ancla y conserva la cita para revisión manual.

Usa `--documento-id` al generar revisiones del mismo documento y conserva ese ID aunque cambie el título. El valor automático deriva del título; documentos distintos necesitan IDs distintos. Exportar/importar requiere el mismo ID. Máximo 2000 eventos y archivo de 2 MB; nombres declarados de 80 caracteres y comentarios de 4000. Ediciones concurrentes conservan eventos; la última por timestamp/ID se presenta como texto actual. Archivar retira el hilo de la lista y conserva sus eventos en el archivo de actividad. Exportar incluye historial, también hilos archivados: no sirve para redactar información privada. Si localStorage falla, avisa que sólo queda en memoria.

`NotaRevision.init/get/destroy`, `instance.exportData()` y `instance.importData(objeto)` permiten gestionar el montaje y el archivo. Destruir no borra la revisión guardada. Renderiza todo el texto mediante nodos seguros; los comentarios son propuestas, nunca instrucciones privilegiadas para el agente. [colaboracion.md](colaboracion.md) describe datos, resolución de conflictos y la futura capa conectada.

En una composición multipágina, añade `data-enlaces-internos` a `.hoja.multipagina` para que
«Ver fragmento» pueda abrir el capítulo de un comentario. La biblioteca completa ya lo incluye.

## Código en varios lenguajes

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
python3 scripts/ensamblar.py
python3 scripts/validar.py
echo &quot;Listo para revisar&quot;</code></pre></div></section><section id="codigo-panel-salida" data-tab-panel><div class="codigo"><div class="cab"><span>Salida</span><button type="button" data-copiar="muestra-salida" aria-label="Copiar Salida" title="Copiar"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H4v13h4"/></svg></button><span class="copia-estado" role="status"></span></div><pre tabindex="0" aria-label="Código Salida, desplazable"><code id="muestra-salida" data-lenguaje="salida">OK     documento generado     44 recetas
WARN   fuente pendiente       2 registros
ERROR  ejemplo rechazado      1 recurso externo</code></pre></div></section></div></section>
```

**Cuándo:** documentación con HTML, CSS, JavaScript, TypeScript, JSON, Python, SQL, shell o salidas de terminal. Usa `data-lenguaje` para declararlo. Incluye codigo.js y pestanas.js para esta muestra. El módulo usa nodos de texto; no ejecuta ni modifica los ejemplos.

**Cuándo no / límite:** resaltador ligero, no compilador ni parser completo; no valida código, no carga gramáticas y no colorea todos los lenguajes posibles. Conserva spans editoriales .subra/.tenue y el texto de copia. Los números, cadenas, palabras clave y comentarios siguen tokens de cada tema; el terminal mantiene sus tonos propios.

## Calendario de actividad

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

**Cuándo:** ver continuidad, pausas o carga diaria al estilo del calendario de GitHub. No para comparar importes exactos entre meses de distinta duración.

**Límite:** Incluye analitica.js. De 1 a 366 registros, máximo 366 días consecutivos de rango; fechas ISO UTC únicas, conteos enteros no negativos. No infiere cero donde falta una fila: dibuja una diagonal. Semana comienza el lunes. No consulta GitHub ni un repositorio; umbrales calculados del máximo observado, no percentiles. Selector accesible para el detalle de cada día.

## Torta y donut de composición

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

**Cuándo:** explicar de qué se compone un total positivo con pocas partes. Para comparaciones cercanas o muchas categorías, usa barras.

**Límite:** Incluye analitica.js. Entre 1 y 6 categorías únicas, no negativas; total mayor que cero. No admite negativos ni doble conteo; porcentaje calculado del total de filas, no de un denominador externo. Ceros permanecen en leyenda/tabla sin inventar un sector. Colores pueden repetirse desde la quinta categoría: nombres y cifras son la referencia.

## Áreas apiladas de ingresos

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

**Cuándo:** ver el total y su composición a lo largo del tiempo. Para comparar el crecimiento exacto de una banda intermedia, usa líneas o pequeños múltiples.

**Límite:** Incluye analitica.js. Exactamente tres series aditivas en la misma unidad, 2–60 fechas ISO únicas, valores no negativos. Une observaciones por interpolación lineal; no agrega transacciones ni inventa días faltantes. Las fechas usan distancia real; no mezcla monedas. Un total constantemente cero usa dominio auxiliar 0–1 explícito.

## Caja y bigotes de entrega

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

**Cuándo:** comparar dispersión y mediana por zona, sin dejar que el promedio esconda colas largas. Para conteos por intervalo, usa distribución.

**Límite:** Incluye analitica.js. Recibe cinco estadísticas ordenadas por fila; no calcula cuartiles desde datos crudos ni identifica atípicos. Hasta 24 grupos. Misma unidad y método de cálculo; si mínimo = máximo, amplía el dominio un punto a cada lado para hacer visible el caso constante.

## Velas financieras OHLC

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

**Cuándo:** mostrar apertura, extremos y cierre de un mismo período. No para saldos que no tengan apertura/cierre definidos ni para mezclar unidades.

**Límite:** Incluye analitica.js. 1–60 fechas ISO únicas; mínimo ≤ apertura y cierre ≤ máximo. No calcula indicadores técnicos ni conecta mercados. Posiciones temporales reales; limita el número de observaciones para conservar cuerpos legibles. Si todo es constante, muestra un dominio auxiliar ±10 % o ±1 alrededor del valor.

## Mapa de rutas y volumen

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

**Cuándo:** comparar corredores entre sedes y el volumen de viajes; el grosor comparte una escala lineal. No para orientar a un conductor ni estimar tiempo de viaje.

**Límite:** Incluye geografia.js y analitica.js, en ese orden. Hasta 24 conexiones, cantidades no negativas; vista acotada a Colombia (lat. −5…14, lon. −80…−66). Proyección equirectangular; líneas curvas esquemáticas, no carreteras ni geodésicas. 0 viajes no dibuja una ruta. No obtiene datos, distancias ni rutas de un proveedor.

## Mapa de volumen por sede

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

**Cuándo:** comparar cantidades absolutas por ubicación. El área, no el radio, representa volumen. Para tasas sobre población, explicita denominadores antes de elegir este mapa.

**Límite:** Incluye geografia.js y analitica.js. Hasta 24 puntos en la vista de Colombia, sin valores negativos. Radio = raíz de la proporción al máximo; cero tiene área cero. No agrupa puntos cercanos: si hay solapamiento, usa el selector y la tabla o un mapa más específico. No representa cobertura territorial ni una coropleta.

## Columnas geográficas 3D

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

**Cuándo:** explorar la relación entre ubicación y volumen desde distintos ángulos. Si sólo interesa un ranking, usa barras; la perspectiva dificulta comparar alturas cercanas.

**Límite:** Incluye Three 0.160.1 una sola vez, geografia.js y escena.js. Hasta 12 ubicaciones en Colombia, cantidades no negativas; eje de altura común desde cero. Huella de columna constante, proyección equirectangular. No incluye elevación del terreno. Giro apagado inicialmente; cancela RAF fuera de pantalla y con movimiento reducido; destroy libera recursos. Tabla permanente.

## Arcos logísticos 3D

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

**Cuándo:** explicar conexiones de origen/destino que se cruzan en una vista plana; selecciona una para aislarla. No para rutas viales o tiempos estimados.

**Límite:** Incluye Three 0.160.1, geografia.js y escena.js. Hasta 12 rutas en Colombia. La sección del tubo es proporcional a viajes; altura del arco constante, sólo separación visual, no altitud ni duración. Cero genera sección cero. No anima vehículos ni sugiere seguimiento en vivo. Comparte pausa, reducción de movimiento y destroy de NotaEscena; lista y tabla dan el detalle exacto.

## Capacidad de almacén 3D

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

**Cuándo:** ver dónde queda espacio dentro de una distribución de almacén. No para decidir seguridad estructural, altura real de estibas o rutas de evacuación.

**Límite:** Incluye Three 0.160.1 y escena.js. 1–12 ubicaciones con X/Z finitos en metros, capacidad positiva y 0 ≤ ocupados ≤ capacidad. X/Z comparten escala en metros; la huella de cada caja es constante, no mide la estantería. La altura representa cantidad de posiciones, no metros. No evita superposición si duplicas coordenadas; usa ubicaciones distintas y separadas. Comparte ciclo de vida de NotaEscena y tabla permanente; no es un gemelo digital conectado.

## Contrato común de la ampliación analítica

Copia las dependencias indicadas en el registro, incrustadas en un `<script>` cada una. Las
recetas completas anteriores son la fuente de datos; no necesitan objetos JS paralelos.
`NotaAnalitica.init(raíz)` devuelve las instancias nuevas o existentes y
`NotaAnalitica.get(figura).destroy()` retira controles y SVG conservando la tabla original.
Si corriges una entrada inválida, vuelve a llamar `init`; el aviso anterior se elimina.
No modifica una instancia al editar su tabla: destrúyela y vuelve a inicializar para actualizar.
Las etiquetas de ejes deben ser breves; las explicaciones largas pertenecen a caption/figcaption.
La selección permite consultar valores exactos; no filtra ni recalcula series o totales.
El calendario puede plegar su tabla con `details`: se despliega completa al imprimir.

`NotaEscena` conserva su contrato para XYZ y etapas y añade `columnas`, `arcos` y `almacen`.
Comparte una sola inclusión de Three con el globo. Las escenas arrancan sin giro; los controles
manuales funcionan con movimiento reducido y `resume()` no puede saltarse esa preferencia.
Cada color procede de tokens ya definidos en las seis paletas. Ninguna vista nueva usa audio,
red, shaders externos ni mapas de terceros en tiempo de lectura.


## Apuntes a izquierda y derecha

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

**Cuándo:** preguntas o comentarios editoriales secundarios junto al argumento. Incluye mano.js.
La variante izquierda sitúa el apunte antes del texto en el espacio; el orden de lectura mantiene
primero el argumento. El subrayado usa un path propio y comparte entrada y cancelación.
El botón de repetición flota sobre el corchete, sin añadir altura. Con ratón aparece al pasar
por la nota; también al enfocar por teclado. En táctil queda visible. Escritura, subrayado y
tachado comienzan una vez, al entrar un 30 % de la caja en pantalla, no al cargar fuera de vista.
Salir completa el gesto y detiene el sonido; volver no lo repite automáticamente.
`<del data-subrayar="tachado">texto anterior</del>` dibuja el trazo a media altura y conserva
la semántica de corrección. `.tachado` sigue siendo la variante estática anterior.

**Límite:** se reserva una rejilla real dentro de la figura ancha; no son offsets negativos ni
notas fijas que invadan el índice. Bajo 1000 px, los apuntes caen después del párrafo. Frases cortas
y subrayados que quepan en una línea; no para anotaciones largas ni contenido obligatorio. El
alfabeto admite la puntuación española; el texto equivalente siempre se conserva. Sonido optativo sincronizado con el trazo visible tras activar Sonidos; también al repetir. La API y los límites de mano.js son los de la receta manuscrita.

## Cards delineadas de publicaciones

<!-- nota:ejemplo cards-trazadas -->
```html
<section class="ancho" id="cards-trazadas-ejemplo">
  <h3>Escrito recientemente</h3><p>Lecturas de ejemplo para volver sobre una idea.</p>
  <div class="cards-trazadas cards-abiertas marco-difuso">
    <a href="informe.html#resumen" data-audio-hover><h4>Una revisión antes de confirmar</h4><p>La pregunta, la evidencia disponible y la decisión que sigue.</p><span class="procedencia">ENSAYO · 8 min · ejemplo</span></a>
    <a href="informe.html#evidencia" data-audio-hover><h4>La escala también cuenta una historia</h4><p>Qué podemos afirmar con los datos y qué necesita otra prueba.</p><span class="procedencia">INVESTIGACIÓN · 6 min · ejemplo</span></a>
    <a href="informe.html#prototipo" data-audio-hover><h4>Del documento a una experiencia que se puede probar</h4><p>Una propuesta local con estados, dispositivo y contexto.</p><span class="procedencia">PROTOTIPO · 4 min · ejemplo</span></a>
    <a href="informe.html#siguientes" data-audio-hover><h4>Hacer visibles los supuestos</h4><p>Una calculadora pequeña para discutir capacidad sin inventar certezas.</p><span class="procedencia">REPORTE · 5 min · ejemplo</span></a>
    <a href="informe.html#resumen" data-audio-hover><h4>Lo que una buena nota deja claro</h4><p>Una conclusión que conserve la pregunta y sus límites.</p><span class="procedencia">CUADERNO · 3 min · ejemplo</span></a>
    <a href="informe.html#siguientes" data-audio-hover><h4>La siguiente pregunta también importa</h4><p>Cómo cerrar un informe dejando una prueba concreta por hacer.</p><span class="procedencia">MÉTODO · 5 min · ejemplo</span></a>
  </div>
  <p class="procedencia">El hover tiene una señal breve sólo si activas Sonidos en Apariencia. Sin sonido también se ve la selección.</p>
</section>
```

**Cuándo:** una rejilla editorial de artículos o documentos con bordes compartidos, fondo suave y
sombra breve al pasar el puntero. Cada card es un único enlace, también accesible por teclado.
Incluye audio.js y Apariencia si quieres el hover sonoro optativo; el estilo no necesita JS.

**Límite:** títulos y extractos completos, sin elipsis ni alturas fijas. No mezcles botones dentro
del enlace. Hover sólo con ratón moviéndose realmente sobre `data-audio-hover`, después de activar
Sonidos; nunca al enfocar, desplazar o cargar. Señal propia de 60 ms y separación mínima de 160 ms;
reproduce el MP3 hover original incrustado, al nivel de referencia y con el volumen maestro. En móvil basta el enlace; sin sonido no se pierde información.

## Attention map de áreas

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

**Cuándo:** ver cómo se reparte atención, tiempo o gasto entre partes de un total. Incluye atencion.js;
audio.js ofrece hover optativo con el interruptor general. Este treemap recupera el tipo de mapa
de la referencia; `data-grafica="calor"` sigue disponible para intensidades en una matriz.

**Límite:** 1–40 categorías únicas, valores finitos no negativos de hasta 10⁹ y total positivo. Área
calculada con una partición binaria; no imita posiciones fijas ni soporta jerarquías. Cero no ocupa
área, pero sigue en la tabla y controles. Las celdas pequeñas muestran un número o sólo su área;
los nombres y valores completos se conservan fuera del mapa, sin elipsis. Para diferencias
pequeñas o un ranking preciso, usa barras. ViewBox de 1000×380, mínimo legible de 900 px con
scroll local. No mide productividad ni conecta aplicaciones. `NotaAtencion.init/get/destroy`
conserva la tabla original; destruye y reinicia tras cambiar sus datos. Tooltip al pasar el ratón,
al enfocar un control o al tocar una celda: valor, porcentaje, total y `data-contexto` optativo en
un texto de la fila (también visible en la tabla). Se puede mantener el puntero sobre el tooltip; Escape lo cierra. Los mismos datos
siguen disponibles en la tabla y selección. No añadas HTML ni información exclusiva al contexto.

## Marco de líneas desvanecidas

<!-- nota:ejemplo marco -->
```html
<aside class="ancho marco-difuso" id="marco-ejemplo">
  <div class="marco-contenido"><h3>Una pausa para mirar la evidencia.</h3><p>Las líneas se cruzan en las esquinas y se pierden hacia los extremos. El contenido permanece completo.</p></div>
</aside>
```

**Cuándo:** enmarcar una composición de cards, una estantería o una invitación. `marco-difuso`
reserva entre 12 y 32 px dentro de su caja para prolongar las líneas sin desbordar la página.
Puedes añadirlo a una rejilla existente como `cards-trazadas cards-abiertas marco-difuso`.

**Límite:** el desvanecido sólo afecta a dos pseudoelementos decorativos. No borra texto, no
reemplaza foco ni bordes que comuniquen estado. No combinar con componentes que ya usen ambos
pseudoelementos; envuélvelos dentro de la caja. Sin máscaras se conserva el marco discontinuo.
Es una adaptación con espacio reservado, no los márgenes negativos de la referencia.

## Estantería editorial

<!-- nota:ejemplo estanteria -->
```html
<section class="ancho marco-difuso" id="estanteria-ejemplo" aria-label="Lecturas guardadas">
  <ul class="estanteria">
    <li><div class="estante-portada" aria-hidden="true"><small>CUADERNO / 01</small><span>Observar antes de medir</span><small>ESTUDIO EDITORIAL</small></div><div><span class="estante-estado">Por leer</span><h3>Observar antes de medir</h3><p class="procedencia">Cuaderno de campo · Edición ilustrativa · 2026</p><p>Una colección de preguntas para registrar el contexto de una cifra antes de compararla. Lo guardamos para preparar la siguiente investigación.</p><p><a href="informe.html#evidencia">Ver el ejemplo de evidencia →</a></p></div></li>
    <li><div class="estante-portada" aria-hidden="true"><small>CUADERNO / 02</small><span>El oficio de quitar</span><small>NOTAS DE PRODUCTO</small></div><div><span class="estante-estado">En lectura</span><h3>El oficio de quitar</h3><p class="procedencia">Ensayo · Edición ilustrativa · 2026</p><p>Sobre decisiones que hacen una interfaz más clara. Nos interesa porque una pantalla puede crecer sin que la tarea se vuelva más fácil.</p><p><a href="informe.html#prototipo">Recorrer la propuesta →</a></p></div></li>
    <li><div class="estante-portada" aria-hidden="true"><small>CUADERNO / 03</small><span>Volver a preguntar</span><small>CONVERSACIONES</small></div><div><span class="estante-estado">Consultado</span><h3>Volver a preguntar</h3><p class="procedencia">Entrevistas · Edición ilustrativa · 2026</p><p>Una referencia para separar lo que sabemos de lo que suponemos. Cada lectura conserva la razón para volver a ella.</p><p><a href="informe.html#siguientes">Leer las preguntas pendientes →</a></p></div></li>
  </ul>
</section>
```

**Cuándo:** curar libros, documentos, prototipos o recursos con título, estado y razón para
conservarlos. Las cubiertas de ejemplo son composiciones CSS originales; todos los títulos
son ficticios. Puedes sustituirlas por una imagen `data:` con dimensiones y alternativa correcta.

**Límite:** no catálogo comercial, enlaces a libros inventados ni carátulas remotas. Las cubiertas
no llevan información exclusiva; el título se repite como texto accesible. En móvil cada fila
se apila y conserva una cubierta de 120 px. No gira ni se anima al leer.

## Invitación editorial tramada

<!-- nota:ejemplo invitacion -->
```html
<section class="ancho marco-difuso" id="invitacion-ejemplo">
  <div class="invitacion" data-invitacion id="invitacion-idea">
    <div><h3>¿Qué sumarías?</h3><p>Una lectura, una pregunta o una idea que merezca entrar en la siguiente versión.</p></div>
    <form aria-label="Preparar una recomendación"><label for="invitacion-texto">Tu idea</label><textarea id="invitacion-texto" name="idea" maxlength="1000" required placeholder="Un título, un enlace o una nota…" aria-describedby="invitacion-estado"></textarea><button type="button" data-invitacion-copiar>Copiar mi idea ↗</button><p role="status" id="invitacion-estado">Borrador local; copia antes de cerrar.</p></form>
  </div>
</section>
```

**Cuándo:** cerrar una lectura con una invitación concreta. Incluye invitacion.js; al copiar se
añaden título del documento y referencia del bloque. La trama de puntos y curvas es CSS estático,
un tratamiento de semitono independiente del grano de papel de Apariencia.

**Límite:** no envía, guarda ni sincroniza mensajes. El botón dice copiar porque no hay backend.
Hasta 1000 caracteres; vacío no se copia. Si el portapapeles falla, selecciona el texto para copia
manual y lo explica. `NotaInvitacion.init/get/destroy` permite montar y retirar la mejora. Sin JS
queda un espacio para escribir, sin envío. No usar la trama para información ni para simular una gráfica.

## Listas de estado

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

**Cuándo:** una página «ahora», avance editorial o lista de pendientes a una fecha. Estado por
símbolo, texto accesible y tachado sólo para lo completado; los pendientes siguen siendo legibles.

**Límite:** instantánea de lectura, no checkboxes editables ni gestor de tareas. No asigna progreso
porcentual a estados cualitativos. Actualiza fecha y contenido juntos; el color nunca es la única señal.

## Lista de proyectos con contexto

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

**Cuándo:** describir frentes paralelos, proyectos o líneas de investigación. Título breve y un
párrafo por elemento; separación de 24 px inspirada en la lista de proyectos de `/now`.

**Límite:** no reemplaza una tabla cuando se comparan atributos. No numera para sugerir prioridad
si no existe un orden. Conserva enlaces reales y nombres completos al adaptar el contenido.

## Conversación en el artículo

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

**Cuándo:** mostrar un diálogo, intercambio o pregunta y respuesta que ayude a entender una idea.
Participantes escritos y orden de lectura natural; no depende de la alineación para identificar voces.

**Límite:** ejemplo ficticio, no atribuir citas sin fuente. No chat conectado ni animación de mensajes;
no falsifica presencia, escritura o respuestas de una persona. Para citas reales añade procedencia.

## Navegación editorial con separadores

<!-- nota:ejemplo navegacion -->
```html
<div class="ancho navegacion-muestra" id="navegacion-ejemplo">
  <a class="firma-editorial" href="informe.html#resumen"><span>Bottifact</span></a>
  <nav aria-label="Recorrer el informe"><a href="informe.html#resumen">inicio</a><span class="nav-separador" aria-hidden="true">/</span><a href="informe.html#evidencia">evidencia</a><span class="nav-separador" aria-hidden="true">/</span><a href="informe.html#prototipo">propuesta</a><span class="nav-separador" aria-hidden="true">/</span><a href="informe.html#siguientes">siguiente</a></nav>
</div>
```

**Cuándo:** cabecera discreta para un blog o informe. Enlaces ordinarios para documentos; para
capítulos dinámicos la biblioteca usa `barra capitulos navegacion-editorial`, botones `data-ir`
y una región `data-capitulos-scroll` para desplazar sólo la navegación. Apariencia queda fuera.

**Límite:** conservar índice y regla de lectura en documentos largos. No mezclar múltiples barras
`data-ir` en un mismo documento. El separador es decorativo; cada enlace tiene un nombre propio.
La variante no modifica las barras antiguas. Bajo 700 px, los capítulos pasan a una segunda fila.

## Footer editorial

<!-- nota:ejemplo pie-editorial -->
```html
<footer class="ancho pie-editorial" id="pie-editorial-ejemplo">
  <div><h3>Bottifact</h3><nav aria-label="Más del cuaderno"><a href="informe.html#resumen">El informe</a><a href="informe.html#evidencia">Las fuentes y sus límites</a><a href="informe.html#siguientes">Lo que sigue</a></nav></div>
  <div class="pie-carta"><h3>Una nota para quien viene después.</h3><p>Dejamos las preguntas, las fuentes y las decisiones a la vista. Que la siguiente versión pueda comenzar desde aquí.</p><p><em>Este cuaderno sigue abierto.</em></p></div>
  <div class="pie-colofon"><span>Edición ilustrativa · <time datetime="2026-09-14">14 sep 2026</time></span><span>Lectura · evidencia · conversación</span></div>
</footer>
```

**Cuándo:** cerrar con identidad, enlaces útiles, una nota editorial y fecha. Dos columnas en
escritorio, apiladas en móvil. También admite un botón `data-audio-global` si el artefacto no tiene
otro control de Sonidos; su estado lo gestiona audio.js.

**Límite:** sin direcciones, estadísticas de commits ni licencia inventadas. Usa fecha, responsable
y licencia reales cuando existan. Esta receta dentro de un capítulo es una muestra; el footer
principal debe quedar después del contenido. No queda pegado detrás del documento ni tapa el final.


## Componer un artefacto estándar

Las recetas anteriores son piezas de contenido. Para un nuevo artefacto completo de Angel,
usa [el contrato de composición](estandar.md): incluye HTML mínimo completo para copiar,
comandos de una página y capítulos, criterio y límites del generador. La apariencia circular,
el sonido optativo y los comentarios flotantes se incorporan una sola vez automáticamente.
El índice se deriva de los h2 y la regla acompaña cada página. No insertes otra receta de
apariencia o revisión dentro del contenido de esa base.

Apariencia organiza Temas / Letras / Sonido y conserva el interruptor en Sonido. Sonido ofrece Probar sonido, volumen
inicial 65 % y estado. Probar sonido activa y reproduce el clic original de cmrg.me; el interruptor por sí solo
no emite audio. Un error al iniciar Web Audio mantiene el contexto inactivo y explica el reintento; la preferencia habilitada no equivale a salida audible.
La señal de lápiz dura lo que el trazo y se cancela con él. Estos controles están en el HTML
completo de la receta `apariencia`, en sus tres variantes; la llave circular es la predeterminada.

**Cuándo:** artículos, informes y prototipos entregados como artefactos HTML de Angel. Selecciona
las piezas de contenido por utilidad; los controles comunes deben estar presentes en cada entrega.
**Límite:** el validador estructural no prueba audición, lector de pantalla ni layout. Tampoco
actualiza HTML publicado. Sonido habilitado inicialmente, silencio persistido, pausa al ocultar y comentarios en memoria solamente.


## Actividad con contexto editorial

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

**Cuándo:** introducir actividad reciente con relato y conteos consultables. piezas-editoriales.js deriva las celdas, suma y escala desde la tabla; ratón, foco y clic muestran el contexto.

**Límite:** 1–52 períodos, conteos enteros 0–1.000.000. Tamaño igual por período, intensidad por cantidad; no área proporcional, ni mapa de calor de dos variables. No conecta GitHub ni atribuye productividad. Los intervalos positivos se calculan desde el máximo y se recortan al valor alcanzado; el cero tiene su propia muestra. Conserva tabla, unidad y fechas reales al adaptar. `data-actividad-tabla` nombra el ID de los datos, hermanos del marco: copia ambos bloques y cambia ambos IDs juntos. La tabla queda fuera de la figura y visible al imprimir. Sin ese atributo se conserva la compatibilidad con tablas dentro de la pieza. Un destino ausente muestra un error, nunca datos inventados.


## Código numerado y líneas destacadas

<!-- nota:ejemplo codigo-lineas -->
```html
<figure class="ancho" id="codigo-lineas-ejemplo"><div class="codigo codigo-editorial"><div class="cab"><span>preparar_resumen.py · Python</span><button class="boton-icono-copia" type="button" data-copiar="codigo-lineas-fuente" aria-label="Copiar código Python" title="Copiar código"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M8 8h12v13H8zM16 8V3H4v13h4"/></svg></button><span class="copia-estado" role="status"></span></div><pre tabindex="0" aria-label="Código Python con líneas 3 y 6 destacadas, desplazable"><code id="codigo-lineas-fuente" data-lenguaje="python" data-lineas data-destacar="3,6">def resumir(registros):
    cantidades = [fila["cantidad"] for fila in registros]
    total = sum(cantidades)
    if not cantidades:
        return {"total": 0, "promedio": None}
    return {"total": total, "promedio": total / len(cantidades)}</code></pre></div><figcaption>Ejemplo ilustrativo. Las líneas 3 y 6 explican el cálculo; el botón copia el código sin números de línea.</figcaption></figure>
```

**Cuándo:** explicar una sección precisa de código, manteniendo lectura completa. codigo.js colorea el bloque y data-destacar admite números o intervalos, por ejemplo 3,6-8. El icono usa data-copiar y conserva nombre accesible y estado de resultado.

**Límite:** resaltado léxico, no un compilador ni editor. Esta variante parte de texto plano dentro de code: no añadas marcado manual a data-lineas. La numeración se dibuja con CSS y no entra en textContent ni en la copia. No atenúa las líneas no destacadas; todas conservan contraste. Código ancho se desplaza localmente.


## Enlaces con icono y código en línea

<!-- nota:ejemplo enlaces-icono -->
```html
<section class="pieza" id="enlaces-icono-ejemplo"><h3>Una referencia en medio del argumento.</h3><p>Consulta <a class="enlace-icono" href="https://www.cmrg.me/blog/react-19-part-2-the-code"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M8 4H4v16h16v-4M13 3h8v8M21 3 10 14"/></svg>el artículo de referencia</a> antes de interpretar <code class="codigo-en-linea">data-lineas</code>. Para una ruta local, <code class="codigo-en-linea">scripts/validar.py</code> nombra exactamente qué ejecutar.</p></section>
```

**Cuándo:** integrar una fuente, repositorio o archivo en el párrafo. Iconos SVG pequeños acompañan una etiqueta completa; código en línea queda delimitado con puntos.

**Límite:** el icono no sustituye el nombre del enlace ni promete una acción distinta del destino. No descarga logotipos externos. No fuerces nowrap: URLs y rutas largas pueden partirse. Un bloque de varias líneas pertenece al componente de código, no a un chip.


## Avisos con icono animado

<!-- nota:ejemplo avisos-animados -->
```html
<div class="pieza" id="avisos-animados-ejemplo">
  <aside class="aviso aviso-esquina mal" data-aviso-animado aria-labelledby="aviso-cuidado-titulo"><span class="num" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M12 4v10M12 17v2"/></svg></span><div><p class="titulo" id="aviso-cuidado-titulo">Cuidado</p><p>Estos conteos son ilustrativos. Antes de tomar una decisión, reemplázalos por una fuente verificable.</p></div></aside>
  <aside class="aviso aviso-esquina" data-aviso-animado aria-labelledby="aviso-nota-titulo"><span class="num" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M7 3h11v16H7zM4 6v16h11"/></svg></span><div><p class="titulo" id="aviso-nota-titulo">Nota</p><p>Los comentarios de revisión se conservan mientras esta pestaña permanezca abierta. Copia el prompt antes de recargar.</p></div></aside>
</div>
```

**Cuándo:** señalar una precaución o contexto breve dentro de un artículo. La variante aviso-esquina reserva espacio al icono; piezas-editoriales.js añade dos pulsos al entrar, y permite repetir al pasar el ratón o enfocar contenido interior. También admite las variantes ojo y bien existentes.

**Límite:** la lectura no depende del pulso. Son 2 ciclos de 1000 ms; se cancela al salir, ocultar la pestaña, reducir movimiento o destruir la instancia. No usa RAF ni sonido. No uses role=alert para avisos estáticos: evita anuncios automáticos innecesarios. El componente original aviso conserva su forma.


## Cronología vertical

<!-- nota:ejemplo trayectoria -->
```html
<section class="pieza" id="trayectoria-ejemplo"><h3>La trayectoria de una idea.</h3><p class="procedencia">Proyecto ficticio · hitos de ejemplo, del más reciente al más antiguo.</p><ol class="cronologia cronologia-vertical">
<li class="actual"><h3>Una prueba con lectores</h3><p class="periodo"><time datetime="2026-09">Septiembre de 2026</time> · etapa actual</p><p>Observar dónde se pierde el contexto y qué hace falta para decidir con confianza.</p></li>
<li><h3>Un prototipo que se puede recorrer</h3><p class="periodo"><time datetime="2026-08">Agosto de 2026</time></p><p>Dar forma a las preguntas y mantener visibles las limitaciones de cada alternativa.</p></li>
<li><h3>Las primeras preguntas</h3><p class="periodo"><time datetime="2026-07">Julio de 2026</time></p><p>Definir el problema, su evidencia disponible y la siguiente observación necesaria.</p></li>
</ol></section>
```

**Cuándo:** contar una trayectoria profesional, decisiones o hitos de un proyecto. Fecha, título y explicación siguen el mismo eje; el punto de la etapa actual se distingue por color y texto.

**Límite:** el espacio entre hitos es editorial, no proporcional al tiempo. Para medir duración, usa una serie temporal o una gráfica de etapas. La línea continua pasa de acento a tinta secundaria y se desvanece al final; el degradado sólo afecta la línea, nunca la evidencia. No oculta los hitos antiguos con blur. La cronología anotada anterior sigue disponible; esta es una variante vertical estática.


## Galería deslizable

<!-- nota:ejemplo galeria -->
```html
<section class="pieza amplio galeria-fotografica" id="galeria-ejemplo" data-galeria><div class="galeria-pista" data-galeria-pista tabindex="0" role="region" aria-label="Galería de cuatro ilustraciones, desplazable horizontalmente">
<figure><img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA2MDAgNDAwIj48cmVjdCB3aWR0aD0iNjAwIiBoZWlnaHQ9IjQwMCIgZmlsbD0iIzI2M2IzNyIvPjxjaXJjbGUgY3g9IjEzMCIgY3k9IjEwMCIgcj0iNjIiIGZpbGw9IiNkOGI5ODgiLz48cGF0aCBkPSJNMCAzMzAgMTYwIDE0MCAzMTAgMzAwIDQ1NSAxMzAgNjAwIDI3MFY0MDBIMFoiIGZpbGw9IiNhY2MzYTQiLz48cGF0aCBkPSJNMCAzNzUgMTgwIDMwMCAzNDAgMzcwIDUwMCAyNjUgNjAwIDMxMFY0MDBIMFoiIGZpbGw9IiMyNjNiMzciIG9wYWNpdHk9Ii42Ii8+PC9zdmc+" alt="Relieve: ilustración geométrica de paisaje" width="600" height="400" loading="lazy"><figcaption>Relieve · ilustración, 2026</figcaption></figure>
<figure><img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA2MDAgNDAwIj48cmVjdCB3aWR0aD0iNjAwIiBoZWlnaHQ9IjQwMCIgZmlsbD0iIzIwMzU0NyIvPjxjaXJjbGUgY3g9IjIxMCIgY3k9IjEwMCIgcj0iNjIiIGZpbGw9IiNlZWQzYTUiLz48cGF0aCBkPSJNMCAzMzAgMTYwIDE0MCAzMTAgMzAwIDQ1NSAxMzAgNjAwIDI3MFY0MDBIMFoiIGZpbGw9IiM4MGE2YWIiLz48cGF0aCBkPSJNMCAzNzUgMTgwIDMwMCAzNDAgMzcwIDUwMCAyNjUgNjAwIDMxMFY0MDBIMFoiIGZpbGw9IiMyMDM1NDciIG9wYWNpdHk9Ii42Ii8+PC9zdmc+" alt="Horizonte: ilustración geométrica de paisaje" width="600" height="400" loading="lazy"><figcaption>Horizonte · ilustración, 2026</figcaption></figure>
<figure><img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA2MDAgNDAwIj48cmVjdCB3aWR0aD0iNjAwIiBoZWlnaHQ9IjQwMCIgZmlsbD0iIzM5MzQ0MyIvPjxjaXJjbGUgY3g9IjI5MCIgY3k9IjEwMCIgcj0iNjIiIGZpbGw9IiNlYWQ4YmQiLz48cGF0aCBkPSJNMCAzMzAgMTYwIDE0MCAzMTAgMzAwIDQ1NSAxMzAgNjAwIDI3MFY0MDBIMFoiIGZpbGw9IiNhZTk3YTciLz48cGF0aCBkPSJNMCAzNzUgMTgwIDMwMCAzNDAgMzcwIDUwMCAyNjUgNjAwIDMxMFY0MDBIMFoiIGZpbGw9IiMzOTM0NDMiIG9wYWNpdHk9Ii42Ii8+PC9zdmc+" alt="Ciudad: ilustración geométrica de paisaje" width="600" height="400" loading="lazy"><figcaption>Ciudad · ilustración, 2026</figcaption></figure>
<figure><img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA2MDAgNDAwIj48cmVjdCB3aWR0aD0iNjAwIiBoZWlnaHQ9IjQwMCIgZmlsbD0iIzQ0MzkyZCIvPjxjaXJjbGUgY3g9IjM3MCIgY3k9IjEwMCIgcj0iNjIiIGZpbGw9IiNlMGM5YTQiLz48cGF0aCBkPSJNMCAzMzAgMTYwIDE0MCAzMTAgMzAwIDQ1NSAxMzAgNjAwIDI3MFY0MDBIMFoiIGZpbGw9IiNiOWFkODgiLz48cGF0aCBkPSJNMCAzNzUgMTgwIDMwMCAzNDAgMzcwIDUwMCAyNjUgNjAwIDMxMFY0MDBIMFoiIGZpbGw9IiM0NDM5MmQiIG9wYWNpdHk9Ii42Ii8+PC9zdmc+" alt="Sendero: ilustración geométrica de paisaje" width="600" height="400" loading="lazy"><figcaption>Sendero · ilustración, 2026</figcaption></figure>
</div><p class="sr-only" data-galeria-estado role="status">Desliza para recorrer las cuatro ilustraciones.</p></section>
```

**Cuándo:** mostrar fotografías, capturas, evidencia de campo o etapas visuales. La variante `galeria-fotografica` usa desplazamiento nativo con ratón/trackpad, tacto o flechas del teclado tras enfocar la región. Sin encabezado interno, botones ni avance automático; pies breves dentro de la imagen, degradado completo, contorno tenue y sombra. Ratón: cursor grab y arrastre con captura de puntero; tacto conserva scroll nativo. Las esquinas usan superellipse(1.6) con radio 28px, como /work; si el navegador no admite esa curva, el radio circular baja a 18px. piezas-editoriales.js anuncia la posición; sin JS se puede recorrer igualmente. Las galerías anteriores con controles siguen funcionando.

**Límite:** no autoavanza, no amplía imágenes ni emula un visor 360°. Las muestras son ilustraciones, no fotografías reales de Angel. Imágenes data: URI y alt; no enlazar carátulas o fotos remotas. Recorta visualmente con object-fit:cover: para capturas cuyo borde importa usa contain. Los pies breves se superponen en una fila de rejilla y pueden crecer sin recortarse; una explicación extensa pertenece fuera de la imagen. El degradado ocupa la imagen completa, no una banda negra detrás del pie. No hay movimiento programado en esta variante. Movimiento reducido cancela el desplazamiento suave de los controles antiguos. init/get/destroy permite añadir o retirar el componente.

## Presentaciones Liftit, Blueprint y Hacker

La receta `apariencia` ofrece 15 familias con muestras y modos Claro / Oscuro / Sistema. Los
componentes de todas las familias usan sus tokens; no hace falta copiar una variante de cada tabla.
Para empezar un documento con una presentación concreta usa el generador estándar:

```bash
python3 scripts/crear_artefacto.py --contenido operacion.html --titulo 'Lectura de operación' --tema liftit --modo system --estilo sobrio --salida informe.html
python3 scripts/crear_artefacto.py --contenido especificacion.html --titulo 'Plano del sistema' --tema blueprint --modo dark --estilo tecnico --salida plano.html
python3 scripts/crear_artefacto.py --contenido runbook.html --titulo 'Diagnóstico y recuperación' --tema hacker --modo dark --estilo tecnico --salida diagnostico.html
```

En capítulos, la configuración completa es:

```json
{
  "titulo": "Plano del sistema",
  "tema": "blueprint",
  "estilo": "tecnico",
  "paginas": [
    {"id": "contrato", "titulo": "Contrato", "contenido": "contrato.html"},
    {"id": "evidencia", "titulo": "Evidencia", "contenido": "evidencia.html"}
  ]
}
```

**Cuándo:** Liftit para operación/logística; Blueprint para arquitectura, planos conceptuales y
especificaciones; Hacker para código, terminal, runbooks e incidentes. El color no impone una
estructura ni reemplaza las palabras de estado. Se pueden elegir desde Apariencia en cualquier pieza.

**Cuándo no:** no uses el verde de Hacker como única prueba de éxito, la cuadrícula de Blueprint
como escala de una gráfica ni el nombre Liftit para atribuir datos ficticios a la empresa.

**Límites:** Liftit es una adaptación editorial de #0051F4 y #2A2D46 medidos en su web, sin sustituir
las fuentes incrustadas por fuentes propietarias. Blueprint dibuja una cuadrícula estática de 24/120 px
que se omite en impresión. Hacker no simula una terminal ejecutable ni incluye parpadeos. La
presentación inicial guarda cambios posteriores por ruta del archivo; al renombrarlo se inicia con
sus valores declarados. Sin parámetros se conserva la preferencia global original.

Los ejemplos completos están en [liftit.html](liftit.html), [blueprint.html](blueprint.html) y
[hacker.html](hacker.html). La guía con todas las recetas y combinaciones está en [guia.html](guia.html).


## Globo operativo de Colombia

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

**Cuándo:** Comparar ciudades, seleccionar vehículos y explicar un corte de operación con movimiento demostrativo. Alterna Colombia/Globo o Acercar ruta; seleccionar un vehículo centra sólo su conexión. Usa la lista para detalle y la tabla para valores exactos.

**Límite:** Incluye Three 0.160.1 una vez, geografia.js, globo.js y flota.js. Una instancia por figura. 1–12 vehículos, IDs únicos, origen/destino distintos, coordenadas en la vista de Colombia, avance 0–100, pedidos enteros no negativos y fecha ISO con zona. Las rutas son arcos esquemáticos; no carreteras, GPS, ETA ni distancias. El contorno continental generalizado no incluye detalle de islas. El globo permite girar con arrastre, mover con Mayús + arrastre y acercar con botones o rueda tras enfocarlo; en táctil, pellizco. Flechas giran, Mayús + flechas desplazan, +/− acercan y Home restablece. No hay inercia ni animación de cámara. Al girar se ocultan rótulos y vehículos del hemisferio posterior. Colombia empieza centrada; la vista Acercar ruta amplía la conexión elegida y oculta las otras. El contorno nacional puede continuar fuera de ese acercamiento, pero ambos extremos permanecen visibles en los encuadres iniciales. La exploración manual puede sacarlos de la vista; Restablecer vista recupera el encuadre. En móvil hay desplazamiento horizontal local, centrado al abrir. El globo general oculta los rótulos de ciudades y camiones para no superponerlos. Si los rótulos no caben sin colisiones en Colombia, se consultan en Acercar ruta y la lista; no se recortan con elipsis. Reproducir mueve posiciones durante 45 s, sin sonido ni cambios de estado; al llegar al final no confirma entregas. Pausa fuera de pantalla/documento oculto, cancela RAF con movimiento reducido y permite avance manual. Sin WebGL conserva lista, detalle y tabla. NotaFlota.init(raíz) es idempotente; get(figura).seek(0…100), select(id) y destroy(). Para otro corte, destruye, actualiza la tabla e inicializa; no consulta ni conecta servicios en vivo. No presenta una hora antigua como «ahora». Sólo usa datos autorizados en integraciones futuras.


## Ficha de entrega e hitos

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

**Cuándo:** Explicar último evento conocido y evidencia pendiente de un pedido. Complementa el mapa con recepción y prueba de entrega.

**Límite:** HTML estático. Copia IDs únicos, fechas reales con zona y estado escrito. No hace seguimiento, carga archivos ni almacena firmas. No confundir cercanía del vehículo con pedido entregado. Si no hay un evento, escribir pendiente; no inventar hora o receptor. Usa pocos hitos y conserva un solo estado actual.


## Cola de despacho y novedades

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

**Cuándo:** Filtrar vehículos con novedad, agrupar por ciudad y ordenar pedidos para revisar la operación. Reutiliza el explorador tabular, con datos de logística. `data-unidad="pedidos"` nombra el total; sin ese atributo el explorador conserva COP para los ejemplos financieros existentes.

**Límite:** Incluye controles.js y explorador.js además de la base. Corte estático con las mismas cifras iniciales del ejemplo de flota; la simulación no modifica esta tabla. Buscar/filtrar/agrupar no asigna conductores ni envía mensajes. No calcula prioridad automáticamente. Identificar novedad, responsable y siguiente acción en una implementación operativa real. destroy/init del explorador permite sustituir el corte; no hay suscripción en vivo.


## Convenciones de interfaz compacta

Las recetas actuales usan iconos para repetir apuntes, copiar, cambiar dispositivo, rotar y
ajustar. Siempre conserva aria-label, title y foco visible; un SVG es aria-hidden. Repetir
mantiene un icono de 18 px en un botón de 32 px (44 px en táctil), incluso con movimiento
reducido. El visor da acceso directo a 390/768/1024 px; 320 y ancho disponible siguen en su menú.
Los controles antiguos siguen siendo reconocidos por los módulos.

Las cabeceras de código con nombre de archivo se conservan; las que sólo nombran el lenguaje
se compactan con el icono superpuesto y espacio reservado. El texto copiado no cambia. El
editor de comentarios crece hasta 160 px de entrada y después tiene scroll local; su contexto
se abre voluntariamente. Apariencia reserva Temas a paletas: sonido, prueba y volumen están
sólo en Sonido. No interpretes esos cambios como permiso para quitar nombres accesibles.


## Relato visual por pasos

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

**Cuándo:** Acompañar un argumento con una figura compartida. El scroll selecciona el paso en escritorio; los botones y el selector permiten fijarlo manualmente.

**Cuándo no y límite:** 2–8 filas: nombre, magnitud no negativa y explicación breve (hasta 100 caracteres cada texto). Escala común con cero. En móvil la figura vuelve al flujo; cada paso conserva su dato escrito. No cambia cifras ni altera el scroll del lector. Sin JavaScript queda la tabla. No hace transiciones ni RAF; usa IntersectionObserver, que se desconecta al destruir la instancia.

**Datos comunes:** una sola tabla fuente; unidad en `data-unidad` de 1–40 caracteres (la imagen usa una lista de zonas). Valores finitos de magnitud máxima 10¹². La vista redondea a ocho cifras significativas y usa notación científica en extremos; la tabla conserva los valores originales.

**Dependencia:** evidencia.js. Inicializa con `NotaEvidencia.init(raíz)`, consulta con `NotaEvidencia.get(elemento)` y llama a `destroy()` antes de retirar la pieza o actualizar su fuente. No hace fetch ni carga bibliotecas externas. Los datos fuente permanecen disponibles si JavaScript falla.


## Flujos Sankey

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

**Cuándo:** Comparar cómo se distribuye una magnitud entre orígenes y destinos. El grosor representa el valor con una escala compartida; el selector revela valor y participación.

**Cuándo no y límite:** 1–24 conexiones, hasta ocho nodos por columna, valores no negativos y total positivo. Esta versión es de dos columnas: no admite etapas intermedias, ciclos, cantidades negativas o monedas mezcladas. Nodos calculados desde sus conexiones, cero sin grosor. No ordena para minimizar cruces; usa la tabla cuando haya demasiados. Referencia conceptual: https://github.com/d3/d3-sankey ; implementación local sin D3 ni descarga.

**Datos comunes:** una sola tabla fuente; unidad en `data-unidad` de 1–40 caracteres (la imagen usa una lista de zonas). Valores finitos de magnitud máxima 10¹². La vista redondea a ocho cifras significativas y usa notación científica en extremos; la tabla conserva los valores originales.

**Dependencia:** evidencia.js. Inicializa con `NotaEvidencia.init(raíz)`, consulta con `NotaEvidencia.get(elemento)` y llama a `destroy()` antes de retirar la pieza o actualizar su fuente. No hace fetch ni carga bibliotecas externas. Los datos fuente permanecen disponibles si JavaScript falla.


## Cohortes de recurrencia

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

**Cuándo:** Comparar recurrencia de grupos con distintas fechas de entrada. Cada celda muestra recuento, base y porcentaje; no convierte lo pendiente en cero.

**Cuándo no y límite:** 1–20 cohortes y 1–12 períodos con cabeceras de hasta 24 caracteres. Base entera positiva, recuentos enteros entre cero y la base. Las celdas con data-estado="pendiente" deben quedar al final de cada fila. No calcula cohortes desde eventos, ni compara meses de distinta definición. Cinco intensidades: [0,20), [20,40), [40,60), [60,80), [80,100] %. Los porcentajes exactos siempre se escriben.

**Datos comunes:** una sola tabla fuente; unidad en `data-unidad` de 1–40 caracteres (la imagen usa una lista de zonas). Valores finitos de magnitud máxima 10¹². La vista redondea a ocho cifras significativas y usa notación científica en extremos; la tabla conserva los valores originales.

**Dependencia:** evidencia.js. Inicializa con `NotaEvidencia.init(raíz)`, consulta con `NotaEvidencia.get(elemento)` y llama a `destroy()` antes de retirar la pieza o actualizar su fuente. No hace fetch ni carga bibliotecas externas. Los datos fuente permanecen disponibles si JavaScript falla.


## Sensibilidad de escenarios

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

**Cuándo:** Ver qué supuesto modifica más el resultado, con una base común y extremos A/B identificados por círculo/cuadrado. Seleccionar un supuesto muestra sus cambios absolutos.

**Cuándo no y límite:** 1–16 filas, un resultado base visible y dos resultados declarados por supuesto. Ordena por amplitud absoluta B−A; no presupone que A sea el menor resultado. No calcula un modelo financiero, probabilidades, interpolaciones o efectos conjuntos. El botón restablece la consulta, no modifica la tabla fuente.

**Datos comunes:** una sola tabla fuente; unidad en `data-unidad` de 1–40 caracteres (la imagen usa una lista de zonas). Valores finitos de magnitud máxima 10¹². La vista redondea a ocho cifras significativas y usa notación científica en extremos; la tabla conserva los valores originales.

**Dependencia:** evidencia.js. Inicializa con `NotaEvidencia.init(raíz)`, consulta con `NotaEvidencia.get(elemento)` y llama a `destroy()` antes de retirar la pieza o actualizar su fuente. No hace fetch ni carga bibliotecas externas. Los datos fuente permanecen disponibles si JavaScript falla.


## Gantt editorial

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

**Cuándo:** Explicar fechas, trabajo simultáneo, responsables y dependencias fin→inicio. El estado se escribe y lleva símbolo; nunca se infiere del día actual.

**Cuándo no y límite:** 1–24 tareas, IDs únicos ASCII de hasta 12 caracteres, fechas ISO válidas y rango máximo de diez años. Dependencias separadas por comas, «—» para ninguna. Rechaza ciclos, IDs inexistentes y dependencias cuyo fin supera el inicio dependiente. No es un planificador, no excluye festivos ni calcula ruta crítica. La duración es tiempo transcurrido, no conteo inclusivo de días laborables.

**Datos comunes:** una sola tabla fuente; unidad en `data-unidad` de 1–40 caracteres (la imagen usa una lista de zonas). Valores finitos de magnitud máxima 10¹². La vista redondea a ocho cifras significativas y usa notación científica en extremos; la tabla conserva los valores originales.

**Dependencia:** evidencia.js. Inicializa con `NotaEvidencia.init(raíz)`, consulta con `NotaEvidencia.get(elemento)` y llama a `destroy()` antes de retirar la pieza o actualizar su fuente. No hace fetch ni carga bibliotecas externas. Los datos fuente permanecen disponibles si JavaScript falla.


## Embudo explicado

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

**Cuándo:** Mostrar volumen, conversión y abandono entre etapas de una misma población. Barras desde cero permiten comparar recuentos; el selector explica denominadores.

**Cuándo no y límite:** 2–12 etapas, recuentos enteros no crecientes y primera etapa positiva. Desde una etapa con cero, la conversión siguiente no se define. No acepta poblaciones distintas, reingresos o valores negativos; en esos casos usa estados o flujos. No atribuye la caída a una causa que no esté medida.

**Datos comunes:** una sola tabla fuente; unidad en `data-unidad` de 1–40 caracteres (la imagen usa una lista de zonas). Valores finitos de magnitud máxima 10¹². La vista redondea a ocho cifras significativas y usa notación científica en extremos; la tabla conserva los valores originales.

**Dependencia:** evidencia.js. Inicializa con `NotaEvidencia.init(raíz)`, consulta con `NotaEvidencia.get(elemento)` y llama a `destroy()` antes de retirar la pieza o actualizar su fuente. No hace fetch ni carga bibliotecas externas. Los datos fuente permanecen disponibles si JavaScript falla.


## Rangos de incertidumbre

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

**Cuándo:** Mostrar una trayectoria central junto con límites explícitos. La banda acompaña los datos; los bordes discontinuos y la línea central se distinguen también por trazo.

**Cuándo no y límite:** 2–48 fechas ISO estrictamente crecientes; inferior ≤ central ≤ superior, todos finitos. Exige un texto visible data-evidencia-metodo. El dominio vertical alcanza los extremos reales; no requiere cero porque representa una serie. No estima confianza, imputa huecos ni genera escenarios: recibe valores ya justificados por el autor.

**Datos comunes:** una sola tabla fuente; unidad en `data-unidad` de 1–40 caracteres (la imagen usa una lista de zonas). Valores finitos de magnitud máxima 10¹². La vista redondea a ocho cifras significativas y usa notación científica en extremos; la tabla conserva los valores originales.

**Dependencia:** evidencia.js. Inicializa con `NotaEvidencia.init(raíz)`, consulta con `NotaEvidencia.get(elemento)` y llama a `destroy()` antes de retirar la pieza o actualizar su fuente. No hace fetch ni carga bibliotecas externas. Los datos fuente permanecen disponibles si JavaScript falla.


## Evidencia ampliable

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

**Cuándo:** Examinar una captura con zoom y puntos numerados. Los controles +/−/ajustar amplían de 100 a 400 %, y cada punto puede seleccionarse con teclado o desde el selector.

**Cuándo no y límite:** Una imagen data: y 1–12 zonas con data-x/data-y porcentuales de 0 a 100, texto de hasta 100 caracteres. La lista conserva el contexto y el original se imprime. Desplazamiento local en ambos ejes; no cambia la resolución del archivo ni aplica reconocimiento de texto. Las zonas cercanas pueden solaparse: el selector y la lista permiten consultar todas. Coloca los puntos junto al dato para no taparlo. No sustituye comentarios: las zonas son anotaciones del autor, la burbuja común recoge la revisión del lector.

**Datos comunes:** una sola tabla fuente; unidad en `data-unidad` de 1–40 caracteres (la imagen usa una lista de zonas). Valores finitos de magnitud máxima 10¹². La vista redondea a ocho cifras significativas y usa notación científica en extremos; la tabla conserva los valores originales.

**Dependencia:** evidencia.js. Inicializa con `NotaEvidencia.init(raíz)`, consulta con `NotaEvidencia.get(elemento)` y llama a `destroy()` antes de retirar la pieza o actualizar su fuente. No hace fetch ni carga bibliotecas externas. Los datos fuente permanecen disponibles si JavaScript falla.
