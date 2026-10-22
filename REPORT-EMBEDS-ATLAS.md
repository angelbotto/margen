# Embeds del atlas: X, YouTube e Instagram — implementación

22 de octubre de 2026 · run `run_d4fd3704f129` · worktree `margen-atlas-embeds`, rebasado sobre `7e238af`. Sin push ni despliegue. Implementa la decisión de [docs/atlas-embed-compatibility.md](docs/atlas-embed-compatibility.md).

## Qué hay

| Pieza | Archivo | Qué hace |
|---|---|---|
| Runtime del artefacto | `packages/core/components/embeds.js` | Tarjetas `[data-embed]`. X: tarjeta estática, sin `widgets.js`; el enlace se reconstruye desde `data-embed-user`/`data-embed-status`; `data-embed-synthetic` elimina el enlace y rotula «Ejemplo sintético». YouTube/Instagram: botón «Cargar» explícito y enlace a la fuente siempre visible. El `href` del autor se ignora; las imágenes que no sean `data:` se retiran. `MargenEmbeds.card()` construye una tarjeta de X solo con `textContent`. API `init/get/destroy`. |
| Estilos | `packages/core/styles/embeds.css` | Contorno sutil, metadatos en mono, póster dibujado en CSS (sin miniaturas remotas), tokens del tema, 320/390/1440, movimiento y transparencia reducidos, impresión con la URL de la fuente. |
| Recetas | `packages/core/recipes/{x-post,youtube,instagram}` | Ejemplo, README con límites y `component.json` con dependencia de `embeds.js`. X es sintética con un handle imposible (`@autora.ejemplo`). YouTube e Instagram usan los IDs de ejemplo de la documentación oficial de cada proveedor; título/canal de YouTube tomados de oEmbed durante la autoría. |
| Host del portal | `portal/static/media-embeds.js`, `media-embeds.css` | Valida el mensaje, construye la URL de una tabla fija y monta el reproductor en su propio `<dialog>`. |
| Cableado mínimo | `portal/static/app.js`, `bridge.js`, `index.html`, `portal/app.py` | Operaciones `embed`, `open-source` y `external` por el canal correlacionado existente; CSP del lector; cierre al cambiar de documento. |

### Contrato del mensaje (artefacto → portal)

- Mismo filtro que hoy: `event.source === #artifact-frame.contentWindow`, `event.origin === "null"`, `bottifact: 1`, `id` ≤ 80, operación en lista blanca.
- `embed` / `open-source`: solo `{provider, id, kind?}` o `{provider:'x', user, status?}` más `version`. Claves exactas (cualquier `url`, `srcdoc`, `html` extra se rechaza), tipos y longitudes fijos. `version` debe ser la versión montada en ese momento: un mensaje tardío de otro documento o versión no abre nada.
- `external` (pie del autor y enlaces del documento): `{href, version}`; solo `https://` sin credenciales ni espacios/controles/comillas/barras invertidas (≤ 2048), o `mailto:` con dirección. El bridge solo lo envía ante un clic `isTrusted` sobre `a[href^="https://"|"mailto:"]` que no sea `data-embed-source`.
- **Activación real del lector, comprobada en el host** con `navigator.userActivation.isActive`, nunca con un booleano del mensaje. Medido con Playwright: el clic dentro del iframe sandbox activa al portal en Chromium 145 y WebKit 26; un mensaje sin clic llega con `isActive === false`. Sin activación el host rechaza las tres operaciones sin diálogo ni pestaña. Con activación: pestaña con `window.open('', '_blank')` + `opener = null` + `location.replace(url)` (consume la activación: un clic, una pestaña); si el navegador la bloquea, diálogo del portal con el destino visible y clicable. Sin API de activación: el diálogo pide confirmar con un botón del propio portal.

### Reproductor

| | YouTube | Instagram |
|---|---|---|
| URL | `https://www.youtube-nocookie.com/embed/{id}?autoplay=1&mute=1&playsinline=1&rel=0&enablejsapi=1&origin={origen del portal}` | `https://www.instagram.com/{p,reel}/{código}/embed/` (sin `rd`/`rp`, sin `embed.js`) |
| `referrerpolicy` | `strict-origin` | `no-referrer` |
| `sandbox` del proveedor | `allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox allow-presentation` (origen del proveedor, distinto del portal) | igual |
| Señales aceptadas | solo de ese `iframe.contentWindow` y origen exacto `https://www.youtube-nocookie.com`; JSON ≤ 20 000 caracteres; `onError`, `infoDelivery` (estado 1 = reproduciendo), `onReady` | solo de ese iframe y `https://www.instagram.com`; `MEASURE` con 0 < altura < 4000 (aplicada entre 200 y 3000 px), `MOUNTED`, `LOADING` |
| Sin señal en 8 s | «YouTube no respondió. El enlace abre la fuente original.» | ídem |

El diálogo tiene título, aviso «Al cargarlo, tu navegador se conecta con …», cierre visible y Escape. Al cerrar, retira el iframe, timers y listeners y devuelve el foco al botón del artefacto (mensaje `embed-closed`) solo si sigue montado el mismo documento y versión. `mount()` de otra versión, `pagehide` y `popstate` cierran sin avisar al documento nuevo.

### CSP

Solo `GET /a/{aid}` (el lector) cambia: `frame-src 'self' https://www.youtube-nocookie.com/embed/ https://www.instagram.com/p/ https://www.instagram.com/reel/`. Biblioteca, login, estáticos y el render del artefacto conservan la política anterior; el render sigue `sandbox allow-scripts allow-downloads`, `connect-src 'none'`, sin `frame-src` ni `allow-same-origin`/`allow-popups`. El iframe del artefacto en `index.html` no cambia.

### Fuera del portal

- HTML portátil por HTTPS (origen real): el iframe se monta en la tarjeta tras el clic, con los mismos atributos, validación de mensajes, «Quitar reproductor» y limpieza.
- `file://`: YouTube solo ofrece el enlace con una explicación breve (Error 153 medido en la investigación); Instagram se carga.
- Documento aislado sin portal (origen `null`): solo el enlace.
- Sin JavaScript, sin red o al imprimir: tarjetas, texto y enlace; el aviso de conexión y el botón están ocultos hasta que el runtime confirma que se puede cargar. No hay video fingido ni spinner.

## Comprobaciones

| Tipo | Resultado |
|---|---|
| Vitest `packages/core/components/embeds.test.tsx` | 10/10: IDs, URLs de tabla fija, señales, enlace regenerado, sintético sin enlace, ID inválido, clic sintético no carga, mensajes de otra ventana/origen/opacos ignorados, timeout honesto, limpieza, Instagram acotado, modo portal (solo proveedor+ID, foco de vuelta), tarjeta X sin HTML. |
| Vitest `portal/static/media-embeds.test.ts` | 12/12: esquema exacto (rechaza `url`/`srcdoc`/`html`, tipos, longitudes, proveedores), igualdad con la tabla del componente, versión ajena, origen/fuente del reproductor, timeout, Instagram, cierre/foco solo al mismo documento, reset y reapertura sin carreras, sin activación no abre nada, confirmación del host sin API, popup sin `opener` y diálogo si se bloquea, validación de `external`, cableado de `app.js`/`bridge.js`/`index.html`. |
| unittest `portal/test_media_embeds.py` | 4/4: `frame-src` exacto solo en el lector; biblioteca/login/estáticos sin cambios; render opaco sin `frame-src`; iframe del artefacto intacto. |
| Suites existentes | Portal Python: 208/208 OK (incluye la corrección de autoría de ediciones, commit aparte). Vitest: 127/127 OK; el archivo `packages/react/src/components.test.tsx` no resuelve `@bottifact/core` sin `npm run build` previo (no se ejecutó para no regenerar artefactos; ajeno a estos cambios). |
| Navegador real: `scripts/check_media_embeds.py` | Portal real (`portal.app`, datos temporales, HTTPS local en `https://localhost`), dos cuentas temporales (autora y lectora) sobre un artefacto `unlisted`, Chromium 145.0.7632.6 y WebKit 26.0. Resumen sin cookies ni texto de proveedores en [tests/evidence/atlas-embeds-impl-2026-10-22/results.json](tests/evidence/atlas-embeds-impl-2026-10-22/results.json). |

Resultado de la matriz (iguales en los dos motores y para las dos cuentas, salvo lo indicado):

- Artefacto con origen `null` y sandbox `allow-scripts allow-downloads`; ninguna petición a proveedores antes del clic (también en HTTPS portátil, `file://` y sin JS).
- Mensajes `embed`, `open-source`, `external` (incluido `javascript:` y un `url` extra) enviados por el artefacto **después** de caducar la activación, y uno desde la ventana del portal: ningún diálogo, pestaña ni petición. Nota: `evaluate()` de Playwright lleva gesto de usuario; la prueba programa el envío tras ~6,5 s para no confundirlo con un clic.
- YouTube en el diálogo del portal: `<video>` silenciado, no pausado, cuyo tiempo avanza (≈3,6 s tras 4 s de observación); estado «Reproduciendo sin sonido». Referer recibido por `youtube-nocookie.com`: solo el origen `https://localhost:<puerto>/`.
- Instagram `/p/`: contenido visible, sin muro de sesión, altura medida 744 px; Referer ausente.
- Escape cierra y retira el iframe; el foco vuelve al botón «Cargar video» dentro del artefacto; reabrir y cerrar con el botón funciona; cambiar el hash cierra el diálogo sin reproductor residual.
- Fuente de X, fuente de YouTube y enlace del pie: una pestaña con la URL exacta, `window.opener === null`, sin Referer (X y el pie se sirven con un stub local; nunca se contacta X).
- Proveedores bloqueados: a los 8 s «YouTube/Instagram no respondió. El enlace abre la fuente original.», enlace visible.
- HTML portátil por HTTPS: YouTube reproduce dentro de la tarjeta (mismo Referer de origen), «Quitar reproductor» lo retira; Instagram se muestra. `file://`: YouTube sin botón y con la explicación; Instagram se muestra. Sin JS: cuatro tarjetas y sus enlaces.
- 320/390/1440, claro y oscuro: sin desbordamiento horizontal (la primera pasada detectó 386 px a 320 por `aspect-ratio` + `min-height`; corregido). Impresión: botones ocultos y URL de la fuente impresa.

Evidencia privada (capturas por motor, cuenta y escenario; resultados completos): `~/.local/share/margen-review/atlas-embeds-impl-20261022/`.

## Wiring pendiente (fuera de mi propiedad)

`contract_artifact.py`, `build.py`, `library.py` y el generador del atlas pertenecen a otro writer. Parche listo y comprobado con `git apply --check` sobre `7e238af`: [tests/evidence/atlas-embeds-impl-2026-10-22/wiring.patch](tests/evidence/atlas-embeds-impl-2026-10-22/wiring.patch).

1. `ORDER`: `packages/core/components/embeds.js` tras `editorial-pieces.js`; `ATTRS['data-embed'] = ['packages/core/components/embeds.js']`.
2. `validate()`: ID/tipo/usuario con la misma forma que el runtime; en `[data-embed]`, `img` solo `data:`; el `href` de `[data-embed-source]` debe ser exactamente la URL reconstruida, y un sintético no lleva enlace. Ensayado: acepta las tres recetas, rechaza ID inválido, `href` ajeno, imagen remota y sintético con enlace.
3. `build.py`: bloque `("EMBEDS", embeds.css)` en `artifact.css`.
4. Después, root regenera `docs/components.md`, `registry.json`, generados y el atlas (VERSION ya cuenta 93 componentes). Las tres recetas se inicializan solas (`DOMContentLoaded` o `MargenEmbeds.init(root)` tras montar una página diferida).

Sin el punto 2, en lectura **sin JavaScript** se vería el `href` crudo del autor (la matriz lo muestra con `https://evil.example/` en una tarjeta de prueba); con JS el runtime ya lo reemplaza.

## Límites honestos

- `/reel/` no se ensayó con un reel real: no hay un ID público verificado en la documentación oficial. La ruta y la CSP siguen la documentación; el fallback cubre el fallo.
- Solo dos motores headless desde una IP doméstica; faltan Firefox, Safari real con ITP, bloqueadores, redes corporativas y la reproducción con sonido (evitada a propósito). Un desafío anti-bot o un muro de sesión no aparecieron, pero pueden aparecer: el temporizador y el enlace los cubren.
- `youtube-nocookie.com` no equivale a cero comunicaciones con Google (~90 peticiones tras el clic). El aviso lo dice en lenguaje simple.
- La activación transitoria dura unos segundos: un clic del lector en cualquier control del artefacto permite que su script pida un reproductor o una pestaña dentro de esa ventana. Es una pestaña por clic (`window.open` consume la activación) y un diálogo como máximo; no permite abrir sin clic.
- `mailto:` se abre con un ancla del host; no se puede detectar si hay cliente de correo.
- Probado con `https://localhost` y certificado autofirmado, no con `artifacts.botto.is`. Antes de desplegar: repetir la matriz contra el portal desplegado, revisión de seguridad independiente del cambio de CSP y del canal (pedida por root) y lectura entre cuentas reales.

## Reproducir

```sh
npx vitest run packages/core/components/embeds.test.tsx portal/static/media-embeds.test.ts
python -m unittest portal.test_media_embeds
/Users/angelbotto/orca/workspaces/margen/margen-lector-voz/.venv/bin/python scripts/check_media_embeds.py --browsers chromium,webkit
```
