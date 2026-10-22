# Revisión independiente · identidad de comentarios y medios (Atlas)

Run `run_d4fd3704f129` · tarea `task_98e8270420fb` · 2026-10-22 · contexto nuevo, sin delegar.

- **Base revisada:** `d61743a..8365e1b` (rama `angelbotto/margen-atlas-review-identidad-medios`). El checkpoint de medios `7e33bd0` está integrado como `b4064a4` (range-diff idéntico).
- **Verificación de correcciones:** `angelbotto/margen-atlas-main` @ `95b1b39` (incluye `b6bef04` = `8126a1c`, `3b1ae3c` y `a11aa1d` = `cc5a339`), en un worktree temporal separado. No se cambió producto en esta rama.
- **Entorno:** `create_app` con BD temporal y usuarios sintéticos. Las peticiones del navegador pasan por una ruta de Playwright hacia el `TestClient` en `https://portal.test`. YouTube, Instagram, X y los hosts externos se sustituyen con stubs locales y ninguna petición sale de la máquina. No hubo producción, credenciales externas ni tokens en logs. Se usaron Chromium 1208 y WebKit 2248 de Playwright.
- **Prueba de vida del reproductor:** sólo se acepta un `postMessage` del stub, filtrado por `source` y `origin` exactos. Nunca se usa `iframe.onload`.

## Veredicto

| Estado | Base 8365e1b | main 95b1b39 |
|---|---|---|
| API identidad (16 pruebas) | 9 fallos | 6 fallos |
| Lector identidad Chromium / WebKit (18) | 12/18 · 12/18 | 13/18 · 13/18 |
| Medios Chromium / WebKit (32) | 28/32 · 28/32 | 28/32 · 28/32 |

El defecto alto D1 está **corregido en el servidor** en main. Queda un residuo de UI (D1-R) y un defecto medio de procedencia de las ediciones (D6). En medios, el aislamiento, la CSP, las URLs exactas, la limpieza y el fallback resisten. El hallazgo principal es que la activación del bridge no está ligada al control pulsado (D2).

## Defectos

| ID | Sev. | Estado en main | Resumen |
|---|---|---|---|
| D1 | Alta | **Corregido** (`b6bef04`, `3b1ae3c`) | Dueño/editor podía `edit` un comentario ajeno (200). El texto pasaba a ser suyo y la firma, la UI y el export seguían mostrando al autor original. |
| D1-R | Media | **Abierto** | El lector sigue ofreciendo «Editar» al dueño sobre comentarios ajenos y abre el compositor con el **nombre de la otra persona** («Alice Ruiz») sobre la sesión del dueño. Al guardar devuelve 403. Además, `portal/static/review.js` (el que se inyecta en `/render`) no recibió la proyección de `3b1ae3c`. Sólo la recibieron `packages/core/components/review.js` y `reader-workspace.js`, y los eventos heredados ajenos siguen proyectándose en el iframe hasta el build. |
| D6 | Media | **Abierto** | Una edición entre humano y agente de la **misma cuenta** (mismo `actor`) se permite, pero no deja rastro visible. El texto actual escrito por el token «Codex» se exporta y se muestra bajo «Propietaria · correo verificado». A la inversa, el texto humano sigue firmado como «Codex (agente de Propietaria)». El historial sí lo registra, pero ni la byline ni la línea `Autor:` lo hacen. |
| D2 | Media | **Abierto** (Chromium y WebKit) | La activación es la del documento, no la del enlace o botón. Tras un clic real en un párrafo cualquiera, el script del artefacto envía `op:'external'` con `https://attacker.example/phish` y el portal abre la pestaña. También sirve `op:'embed'` con otro ID de YouTube: monta ese reproductor y conecta con el proveedor sin que se haya pulsado su tarjeta. `bridge.js` comprueba `isTrusted` sólo en su propio listener, pero el artefacto puede hacer `postMessage` directo. |
| D7 | Media (preexistente, no regresión) | Abierto | Los enlaces `http://`, relativos y `tel:` no se interceptan. En Chromium navegan el iframe del artefacto, la CSP del portal lo bloquea y el lector queda en `chrome-error://chromewebdata/`: se pierden el documento y la revisión. En WebKit no hay efecto visible. |
| D4 | Baja | Abierto | El nombre de invitado se guarda crudo (`clean` no quita controles). `GET /api/review/export` → `items[].thread.author` conserva `‮` y `\n`. El campo `text` sí está saneado. Además, el nombre elegido puede imitar la insignia: «Alice Ruiz · correo verificado · invitado». Sólo la caja de la insignia distingue lo real. |
| D5 | Baja | Abierto | La etiqueta de un token es texto libre y puede ser el nombre de otra persona: «Alice Ruiz (agente de Propietaria)». Está marcada como agente, pero el primer nombre que se lee es el de otra persona. |
| D3 | Baja | Abierto | Dos cuentas verificadas con el mismo nombre son indistinguibles en el lector y en el export (`Identidad (metadatos del servidor)` idéntica). Los permisos sí se separan por `actor`. |
| D8 | Baja | Abierto | Tras cerrar el diálogo, la tarjeta sigue diciendo «El reproductor está abierto en una ventana del portal.». Un `https://user:pass@…` se rechaza en silencio (el `.catch(()=>{})` del bridge), sin feedback. |
| D9 | Baja (observación de código) | Abierto | `/auth/login` usa la parte local del correo como nombre si el JWT no trae `name` (`portal/app.py`, `store.user(..., claims['email'].split('@')[0])`). Esa parte local queda publicada como autor de comentarios. |

### Reproducción

```sh
PY=/Users/angelbotto/orca/workspaces/margen/margen-lector-voz/.venv/bin/python
E=tests/evidence/atlas-identity-media-independent-2026-10-22
SH=~/.local/share/margen-review/atlas-identity-media-independent-20261022
$PY -m unittest $E/test_identity_api.py                     # D1 D1b D3 D4 D4b D5 D6 D6b legacy (fallos esperados = defectos)
$PY $E/identity_browser.py . $E $SH chromium                # o webkit · D1/D1-R D3 D4 D5 en el lector
$PY $E/media_browser.py    . $E $SH chromium                # o webkit · D2 D7 D8 y controles de medios
# Contra otra revisión: pasar su checkout como REPO (1.er argumento); para la API, ejecutar desde ese checkout.
```

Resultados JSON: `identity-{chromium,webkit}.json` y `media-{chromium,webkit}.json` (base), y `main-3b1ae3c/` (main). Las capturas privadas están en `~/.local/share/margen-review/atlas-identity-media-independent-20261022/` y no se suben al repo.

### Corrección sugerida (no aplicada)

- **D1-R:** ocultar «Editar» cuando `!own(note)`, también con `permissions.edit`. Regenerar `portal/static/review.js` con la proyección por actor.
- **D6:** guardar y mostrar «editado por Codex (agente de …)» cuando el `agent` del último `edit` difiera del `create`. Lo mismo en `prompt_bundle`.
- **D2:** el bridge solo debería aceptar `external`, `embed` y `open-source` si los acompaña un token de un solo uso. Ese token lo genera el portal al recibir el clic en `[data-embed-load]` / `a[data-embed-source]` / `a[href]`. Alternativa: en `external`, abrir siempre el diálogo de confirmación del portal en vez de `window.open` directo.
- **D7:** interceptar cualquier `a[href]` que no sea ancla interna y responder con el fallback o un aviso.
- **D4:** aplicar `identity_text` al registrar invitados y en `items` del export.
- **D3:** añadir un discriminador estable (por ejemplo, el dominio verificado o un sufijo corto del actor) cuando colisionen nombres.

## Controles que resisten (base y main, Chromium y WebKit)

**Identidad**

- El cliente no puede forjar `author`, `actor`, `verified` ni `agent`.
- La gemela con el mismo nombre no puede editar a Alice.
- El invitado se etiqueta «invitado».
- El token se registra como «X (agente de Cuenta)».
- La etiqueta con bidi o salto de línea se sanea al crearla y al publicarla.
- La respuesta queda atribuida a quien la escribió después de recargar.
- Las notas privadas no se filtran.
- No aparecen correos de participantes en `/review` ni en el export.
- Tras el fix, el texto del dueño nunca aparece bajo la firma de Alice.

**Medios**

- La CSP del lector es exacta: `frame-src 'self' https://www.youtube-nocookie.com/embed/ https://www.instagram.com/p/ https://www.instagram.com/reel/`.
- El iframe del artefacto sigue con `sandbox="allow-scripts allow-downloads"` y origen `null`, sin acceso al portal.
- No hay red hacia proveedores ni externos antes del clic. La imagen remota de la tarjeta la bloquea la CSP `img-src data: blob:`.
- Un `embed` por script sin activación se rechaza.
- URL exacta del reproductor: `https://www.youtube-nocookie.com/embed/M7lc1UVf-VE?autoplay=1&mute=1&playsinline=1&rel=0&enablejsapi=1&origin=https%3A%2F%2Fportal.test`, con su `sandbox`, `allow` y `referrerpolicy` exactos.
- Las señales falsas que envía el artefacto se ignoran.
- Escape desmonta el reproductor y devuelve el foco al botón de la tarjeta.
- Abrir y cerrar repetidamente o mandar mensajes dobles deja ≤1 reproductor, y 0 al cerrar.
- La altura de Instagram queda acotada: 5000 se ignora y 900 se aplica.
- `popstate` y el cambio de versión cierran el diálogo y lo limpian.
- Un mensaje de otra versión se rechaza.
- Un enlace https del pie abre una sola pestaña con `opener === null` y referrer vacío.
- Con el popup bloqueado aparece un diálogo con el enlace exacto, `_blank` y `noopener`, que recibe el foco y abre la pestaña al clic.
- El `href` de X se regenera desde el ID; el `href` del autor se ignora.
- `mailto` no rompe el lector.
