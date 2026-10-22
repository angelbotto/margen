# Compatibilidad real de embeds en el atlas: X, YouTube e Instagram

Sonda del 22 de octubre de 2026 sobre `b382ad0`. Esto es evidencia de laboratorio, no una funcionalidad implementada: el código de producto no cambió.

**Implementación (22 de octubre, rama `margen-atlas-embeds`):** `packages/core/components/embeds.js`, `packages/core/styles/embeds.css`, recetas `x-post`, `youtube` e `instagram`, y el host `portal/static/media-embeds.js`. Difiere de esta propuesta en dos puntos: el host exige activación real del lector (`navigator.userActivation`) para montar o abrir, y la fuente se abre con `window.open` + `opener = null` o, si se bloquea, con un enlace en un diálogo del portal. Comprobaciones, matriz en Chromium y WebKit y wiring pendiente en [REPORT-EMBEDS-ATLAS.md](../REPORT-EMBEDS-ATLAS.md). Complementa la sección «Proveedores de medios» de [atlas-runtime-decisions.md](atlas-runtime-decisions.md) y el punto 3.7 de [atlas-reference-audit.md](atlas-reference-audit.md).

## Decisión

1. **X: tarjeta HTML estática propia, sin script ni iframe de X.** Autor, fecha, texto y fuente explícitos. Un ejemplo inventado lleva el rótulo «Ejemplo sintético». No hay modo «vivo».
2. **YouTube e Instagram: el portal monta el reproductor, no el artefacto.** El artefacto solo contiene una tarjeta con proveedor, ID y enlace a la fuente. Tras el clic del lector, el artefacto envía `postMessage({provider, id})`. El portal valida el mensaje, construye la URL por su cuenta y abre un `<dialog>` propio con un iframe del proveedor. El sandbox del artefacto, `connect-src 'none'` y el origen opaco no cambian.
3. **No ampliar el `frame-src` del render.** Un iframe anidado dentro del artefacto hereda el sandbox opaco. YouTube no reproduce en ese caso. Instagram sí se muestra, pero tampoco podría abrir enlaces ni medir su altura de forma fiable.
4. **No usar `embed.js` de Instagram.** Construye `…/embed/captioned/?cr=1&v=14&wp=…&rd=<origin>&rp=<pathname+search>` (hasta 200 caracteres). En el portal, eso enviaría `/a/<id>` o `/api/artifacts/<id>/render?version=<vid>` a Meta.
5. **El enlace a la fuente siempre está visible**, en la tarjeta y en la cabecera del diálogo. Dentro del portal debe abrirse a través del host: el sandbox actual bloquea `target=_blank` (ver «Enlaces»).

## Matriz medida

Chromium 145.0.7632.6 (Playwright 1.58.0, headless nuevo), es-ES, 1100×900. Cada fila carga los tres embeds solo tras un clic simulado. YouTube se carga con `mute=1`. Las cabeceras del fixture se leen en tiempo de ejecución de `portal/app.py` para no divergir. «Eco» es un proveedor simulado en otro origen (`echo.margen.test`) que informa lo que recibe y hereda.

| Escenario | Artefacto | YouTube (`youtube-nocookie.com/embed/M7lc1UVf-VE`) | Instagram (`/p/fA9uwTtkSN/embed/`) | Eco: origen del iframe · Referer | Popup desde el artefacto |
|---|---|---|---|---|---|
| `file://` sin cabeceras | origen `null`, sin CSP | **Error 153** («Error de configuración del reproductor de video») | se muestra | real · ninguno | sí |
| http local, render con **CSP exacta** como documento superior | opaco, sin cookie/almacenamiento, fetch bloqueado | **bloqueado por CSP** (`default-src 'none'`) | bloqueado | — | no |
| http local, CSP exacta + `frame-src` exacto | opaco | iframe 200, el JS carga y falla: **pantalla negra, sin `<video>`** (`error_204` bloqueado por ORB) | se muestra | `null` (hereda sandbox) · ninguno, aun con `referrerpolicy=strict-origin` | no |
| host https equivalente: portal → artefacto (**CSP actual**) | opaco | bloqueado por CSP | bloqueado | — | no |
| host https: portal → artefacto + `frame-src` exacto (anidado) | opaco | negro, como arriba | se muestra | `null` · ninguno | no |
| **host https: el portal monta el iframe** (`frame-src` exacto en el portal, `referrerpolicy=strict-origin`) | **opaco, fetch bloqueado** | **reproduce**: `<video>`, `currentTime≈7 s`, `muted`, no pausado; 31 mensajes del reproductor | se muestra; 37 mensajes (`MEASURE`) | real · `https://artifacts.margen.test:<puerto>/` (solo origen) | sí, mediado por el host |
| el portal monta con `referrerpolicy=no-referrer` | opaco | **Error 153** | se muestra | real · ninguno | sí, mediado |
| el portal monta **sin** ampliar `frame-src` | opaco | bloqueado (`frame-src 'self'`) + aviso visible | bloqueado + aviso | — | sí, mediado |
| el portal monta, red de proveedores bloqueada | opaco | página de error de red; a los 6 s: «YouTube no respondió…» y enlace visible | igual | sin cambios | sí, mediado |
| host https sin cabeceras (HTML portátil fuera del portal) | origen real | reproduce (`currentTime≈7 s`) | se muestra | real · solo origen | sí |

La tarjeta X se dibujó en todas las filas sin peticiones a X: la sonda aborta `x.com` y no hubo recursos externos. No apareció un desafío anti-bot ni un muro de inicio de sesión en ningún proveedor; la sonda los habría marcado como fallo (`bot`/`login`). Que cargue el iframe no basta como evidencia de YouTube: «funciona» exige un `<video>` en reproducción.

Conclusiones verificadas:

- **Referer.** El `Referrer-Policy: no-referrer` del documento se anula por iframe con el atributo `referrerpolicy`. Con `strict-origin` el proveedor recibe solo el origen, nunca la ruta ni el ID del artefacto. Sin Referer, YouTube responde con el Error 153 (filas `file://` y `no-referrer`). Instagram funciona sin Referer.
- **Sandbox heredado.** Desde un documento opaco, Chromium no envía Referer, aunque se pida explícitamente. El iframe hijo recibe origen `null`, sin cookies, almacenamiento ni popups. Mantener el aislamiento del artefacto y permitir allí un YouTube funcional son, por tanto, incompatibles.
- **CSP.** Solo cuenta el `frame-src` del documento que contiene el iframe. Con el montaje por el host se amplía el portal, no el render; el render conserva `default-src 'none'` y `connect-src 'none'`.

## Arquitectura para implementar

**Contenido (contrato).** El contrato sigue prohibiendo `<iframe>` (`scripts/contract_artifact.py:87`, `:159`). Se añaden piezas declarativas, sin script del proveedor:

```html
<figure class="embed" data-embed="youtube" data-embed-id="M7lc1UVf-VE">
  <button type="button" data-embed-load>Cargar video de YouTube</button>
  <figcaption>Título · Canal. <a href="https://www.youtube.com/watch?v=M7lc1UVf-VE" data-embed-source>Abrir en YouTube</a></figcaption>
</figure>
```

El validador acepta solo `youtube` con un ID `^[A-Za-z0-9_-]{11}$` e `instagram` con un shortcode `^[A-Za-z0-9_-]{5,40}$` y tipo `p` o `reel`. El `href` se regenera a partir del ID, nunca se copia del autor. El póster se dibuja en CSS, o como imagen `data:` si el autor la aporta: el render no permite cargar `img.ytimg.com`, y así debe seguir. El título y el autor los escribe el autor, o se toman de oEmbed durante la autoría (ver abajo), como texto escapado.

**Puente.** `bridge.js` envía una operación nueva, `embed`, con `{provider, id}`, y otra, `open-source`, con `{provider, id | path}`. `app.js` la acepta en la lista blanca existente (`portal/static/app.js:1797`), con las mismas condiciones que hoy: `event.source === #artifact-frame.contentWindow` y `event.origin === "null"`. La URL la construye el portal a partir de una tabla fija:

| Proveedor | iframe en el `<dialog>` del portal | `referrerpolicy` | Señal de vida (mensaje aceptado solo si `e.source === iframe.contentWindow` y `e.origin` coincide exactamente) |
|---|---|---|---|
| YouTube | `https://www.youtube-nocookie.com/embed/{id}?autoplay=1&mute=1&playsinline=1&rel=0&enablejsapi=1&origin={origen del portal}` | `strict-origin` | `https://www.youtube-nocookie.com`; tras `load`, el portal envía `{"event":"listening"}` |
| Instagram | `https://www.instagram.com/{p,reel}/{código}/embed/` (sin `rd` ni `rp`) | `no-referrer` (probado) | `https://www.instagram.com`; acepta `MEASURE` con `0 < height < 4000` para la altura |

El iframe del proveedor lleva `sandbox="allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox allow-presentation"`. `allow-same-origin` se aplica aquí al origen del proveedor, que ya es distinto del portal; el artefacto nunca lo recibe. También lleva `allow="autoplay; encrypted-media; picture-in-picture; fullscreen"`, un tamaño mínimo de 200×200 y una relación 16:9. Para Instagram, la altura inicial es fija (640 px), un título accesible indica el proveedor y el control de cierre es visible. El diálogo nunca toma HTML del proveedor ni ejecuta su script en el DOM de la cuenta.

**CSP del portal.** Solo para la vista del lector:
`frame-src 'self' https://www.youtube-nocookie.com/embed/ https://www.instagram.com/p/ https://www.instagram.com/reel/`. No cambian `script-src`, `connect-src` ni la CSP del render. La sonda confirma que las rutas exactas bastan para los documentos iniciales de `/p/`; `/reel/` sigue la documentación oficial, pero no se ensayó. Chromium no comprueba la ruta tras una redirección, así que esto limita lo que el portal pide, no lo que el proveedor sirve.

**Fallback.** El enlace a la fuente se muestra antes, durante y después de la carga. Si no llega una señal de vida en unos 8 s, el diálogo dice «<Proveedor> no respondió. El enlace abre la fuente original». Así se cubren red bloqueada, CSP ausente y Error 153. Error 153 sí envía mensajes, pero el portal no lee el DOM del proveedor: el texto visible del reproductor y el enlace cubren ese caso. Fuera del portal (HTML portátil), el runtime del atlas crea el iframe en el mismo documento si este no está en sandbox y, si `self.origin === "null"`, solo ofrece el enlace. En `file://` YouTube solo ofrece el enlace (Error 153 medido); Instagram se puede cargar.

**Enlaces.** El render tiene `sandbox allow-scripts allow-downloads` sin `allow-popups`. Chromium registra: «Blocked opening 'https://x.com/…' in a new window because … 'allow-popups' permission is not set». Esto afecta hoy a cualquier enlace externo con `target=_blank` dentro de un artefacto del portal, no solo a los embeds. La operación `open-source` del host abrió la ventana con `window.open(url, "_blank", "noopener,noreferrer")` desde el manejador de `message`: la activación del clic en el iframe se propaga al portal. Recomendación: abrir por el host solo destinos de una lista exacta (`x.com/{usuario}[/status/{id}]`, `www.youtube.com/watch?v={id}`, `www.instagram.com/{p,reel}/{código}/`), en lugar de añadir `allow-popups` al artefacto.

## Instagram oEmbed y autoría

Comprobado el 22 de octubre: `GET https://graph.facebook.com/v26.0/instagram_oembed?url=https://www.instagram.com/p/fA9uwTtkSN/` **sin token** respondió HTTP 200. Devolvió `version`, `provider_name`, `provider_url`, `type: rich`, `width: 658` y un `html` de 6433 caracteres: `blockquote.instagram-media` + `embed.js`, sin `thumbnail_url` ni `author_name`. YouTube oEmbed (`https://www.youtube.com/oembed?url=…&format=json`) respondió 200 con `title`, `author_name` y `thumbnail_url`. Uso permitido: solo en el CLI o el agente al **crear** el artefacto, para proponer título y autor como texto. Nunca desde el render ni el portal en tiempo de lectura (`connect-src 'none'`). Nunca insertar su `html` ni almacenarlo para analítica. No se comprobó el límite de cuota sin token; si Meta lo restringe, la tarjeta se llena a mano y funciona igual.

`embed.js` observado: `https://www.instagram.com/embed.js`, 65.124 bytes, SHA-256 `b1fd0290dc5d1ee7c3f962be19dcb5b7dfdfadc9669c29fb7c8437e732dee02c`. Construye los parámetros `rd` y `rp` citados arriba y acepta `MEASURE`, `LOADING` y `MOUNTED` desde `instagram.com`. Esos mensajes son los que el portal reutiliza sin el script.

## Límites reales

- Lo que puede quedar embebido: videos públicos de YouTube con la inserción permitida por el propietario, y publicaciones y reels públicos de Instagram. Lo que requiere abrir el proveedor: historias, cuentas privadas, inactivas o con restricción de edad, inserción desactivada, Shorts o listas que el propietario no permita insertar, cualquier publicación de X y todo en `file://` para YouTube.
- `youtube-nocookie.com` reduce cookies, pero no elimina comunicaciones con Google: la fila del portal registró unas 90 peticiones a dominios del proveedor tras el clic. Instagram contacta con `cdninstagram`/`fbcdn`. El texto del botón debe decir que la carga conecta con el proveedor.
- Solo se probó Chromium headless desde una IP doméstica. Faltan Safari/WebKit y Firefox, una sesión con bloqueadores, redes corporativas y la reproducción con sonido; esta última se evitó a propósito. Un desafío anti-bot o un muro de sesión no aparecieron, pero pueden aparecer; el fallback los cubre porque no hay señal de vida.
- La prueba de host usa `artifacts.margen.test` con un certificado autofirmado y las mismas cabeceras. Antes de activar la función hace falta repetir la fila «el portal monta» contra el portal real, más una prueba de lectura entre cuentas y una revisión de seguridad del cambio de CSP, como pide atlas-runtime-decisions.md.

## Reproducir

```sh
/Users/angelbotto/orca/workspaces/margen/margen-lector-voz/.venv/bin/python \
  tests/evidence/atlas-embeds-2026-10-22/probe_embeds.py
```

- `tests/evidence/atlas-embeds-2026-10-22/probe_embeds.py`: servidor HTTP/HTTPS con las cabeceras exactas del portal, shell, artefacto sintético, eco y la sonda. Montaje por el host con validación de `source`, `origin` e ID.
- `tests/evidence/atlas-embeds-2026-10-22/results.json`: resumen sin texto de los proveedores.
- Privado, sin comprometer: `~/.local/share/margen-review/atlas-embeds-20261022/`. Contiene `private-results.json` (consola y red, sin cookies ni tokens), las capturas `<escenario>-<proveedor>.png`, `oembed-ig.json`, `yt-oembed.json` y `embedjs.js`.

Fuentes primarias: [parámetros del reproductor de YouTube](https://developers.google.com/youtube/player_parameters) (200×200, Referer, Error 153), [privacidad mejorada](https://support.google.com/youtube/answer/171780?hl=en), [Instagram oEmbed](https://developers.facebook.com/documentation/instagram-platform/oembed) (v26.0, publicaciones públicas y reels, sin historias ni cuentas privadas). Los IDs de prueba son los ejemplos de esas mismas documentaciones.
