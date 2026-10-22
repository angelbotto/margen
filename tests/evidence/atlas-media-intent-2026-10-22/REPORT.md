# Medios · intención del portal (D2, D7, D8)

Tarea `task_20bfa9a98067` · 2026-10-22 · base `eb87698` (`angelbotto/margen-atlas-main`). Corrige D2, D7 y D8 de `REVIEW-ATLAS-IDENTITY-MEDIA.md`.

## Qué cambia

El iframe del artefacto es opaco y no es de fiar. Su activación puede venir de cualquier clic del documento, y su script puede hacer `postMessage` directo. Ningún nonce ni `isTrusted` dentro de ese mundo distingue un clic en el enlace de uno en un párrafo. Por eso la intención pasa al portal:

- **Embed y fuente.** `embed`, `open-source` y `external` ya no abren ni conectan nada. Muestran un diálogo del portal (la misma carcasa `.media-dialog`) con la vista previa sin red: tipo, sitio (`hostname`) y la dirección exacta. Lo único que sale es un control del portal que el artefacto no alcanza:
  - «Reproducir aquí» / «Cargar aquí» monta el reproductor. Su listener exige `isTrusted` en el mundo del portal y la sesión que lo mostró.
  - El enlace del portal (`target=_blank`, `rel=noopener noreferrer`, `referrerpolicy=no-referrer`) abre la pestaña de forma nativa. El portal ya no llama a `window.open`, y el popup bloqueado deja de ser un caso aparte.
- **Dos clics.** El clic en la tarjeta o en el enlace abre la vista previa al instante. El clic en el portal ejecuta. Antes del segundo clic hay 0 peticiones a proveedores o externos.
- **Sin insistencia.** Sin activación del lector no se muestra ni el diálogo, como antes. Un script que aprovecha un clic ajeno sólo consigue una vista previa que nombra su destino real (`attacker.example`) y no hace nada si nadie la confirma.
- **D7 · todos los enlaces.** `bridge.js` intercepta cualquier `a[href]` que no sea ancla interna, `javascript:` o `download`, así que el iframe nunca navega. También cubre los clics por script (sin `isTrusted`): se cancelan sin preguntar al portal. El portal clasifica el enlace:
  - `https` → «Enlace externo».
  - `http` → «Enlace http · sin cifrar», abrible con clic explícito.
  - `mailto` → «Escribir correo».
  - `tel` → «Llamar».
  - Si lleva credenciales, es relativo u otro esquema, se explica sin enlace: «Este enlace no se abre aquí» y el motivo en una línea. Con credenciales sólo muestra el host.
- **D8.** Al cerrarse el diálogo, la tarjeta borra su estado y devuelve el foco a quien lo pidió (botón de la tarjeta o enlace «Ver en X»). Un enlace `https://user:pass@…` ahora recibe respuesta visible.
- **Se mantiene igual:**
  - el sandbox del artefacto y la CSP exacta;
  - la URL, el `sandbox`, el `allow` y el `referrer` de los reproductores;
  - la prueba de vida por `postMessage` filtrada por `source`/`origin`;
  - la limpieza en Escape, `popstate`, cambio de versión y `pagehide`;
  - el rechazo de mensajes de otra versión.

Archivos: `portal/static/media-embeds.{js,css}`, `portal/static/bridge.js`, `packages/core/components/embeds.js` y `scripts/check_media_embeds.py` (flujo de dos clics). El build del artefacto lo regenera la raíz.

## Evidencia

Usa `media_intent_browser.py`, derivado del probe independiente. Corre en Chromium y WebKit de Playwright, con clics reales, `create_app` detrás de una ruta y stubs de proveedor por `postMessage`. No sale ninguna petición de la máquina.

| Probe | Antes (`eb87698`) | Después |
|---|---|---|
| Independiente `media_browser.py`, Chromium | 28/32 · D2 ×2, D7 http, D8 cred fallan | 23/31* |
| `media_intent_browser.py` Chromium / WebKit | — | **43/43 · 43/43** |

\* Los 8 fallos del probe antiguo con el código nuevo son supuestos de un solo clic que cambian a propósito:
- Seis esperan que el clic en la tarjeta monte el reproductor (YouTube ×4, Instagram ×2).
- «laundering externo» cuenta como fallo la vista previa que muestra `attacker.example` sin abrirla.
- «credentialed … not opened» exige que no haya diálogo, y eso contradice su propio check hermano de feedback visible.

El probe nuevo verifica esas mismas propiedades con la semántica de dos clics.

Lo que cubre el probe nuevo:
- D2: el clic en un párrafo más un `postMessage` del script no produce ninguna pestaña ni petición, y no llama a `window.open`. El embed con otro ID no monta reproductor ni pide nada al proveedor.
- Tarjeta → vista previa con el foco en «Reproducir aquí» y 0 peticiones. El botón del portal pide sólo la URL exacta y el stub responde «Reproduciendo».
- Escape devuelve el foco a «Cargar video». La tarjeta deja de decir «abierto» (D8). Cancelar la vista previa no carga nada.
- Varios ciclos dejan como mucho un reproductor y 0 al cerrar. Instagram acota la altura a 900. `popstate` y el cambio de versión limpian.
- Pie https: primero vista previa, después una pestaña sin `opener` ni referrer, y el diálogo se cierra. X: vista previa de `x.com`, pestaña y foco de vuelta a «Ver en X».
- D7: con `cred`, `http`, `relativo`, `tel` y `mailto`, el documento sigue montado (sin `chrome-error`), no se abren pestañas ni peticiones y el portal responde según el tipo. `http` se abre con clic explícito. `javascript:` y un clic por script sobre un relativo no navegan ni preguntan.
- 0 errores de página.

Resultados en `media-{chromium,webkit}.json`. Las capturas son privadas, fuera del repo.

HTTPS local real (`scripts/check_media_embeds.py`, con el portal en `https://localhost` sobre uvicorn) en Chromium 145 y WebKit 26: dueña y lectora contra proveedores reales, más lectora offline (`real-https.json`). Todo pasa en los 6 recorridos:
- Sin red de proveedor antes del clic. Los mensajes sin activación se ignoran.
- Vista previa sin proveedor y con el foco en el botón del portal.
- Escape, foco de vuelta, reapertura y navegación por hash.
- YouTube real: un `<video>` que avanza (≈3,7 s), silenciado y sin error 153. Instagram real muestra el medio.
- Fuente de X, fuente de YouTube y pie: 0 pestañas antes del clic en el portal, después 1 pestaña con `opener === null`, y el diálogo se cierra.
- Offline: «YouTube no respondió». Las pestañas de proveedor fallan porque la red está bloqueada a propósito; el pie sí abre.
- HTML portátil por https, `file://` y sin JS: sin cambios, y reproduce en https.

## Reproducir

```sh
PY=/Users/angelbotto/orca/workspaces/margen/margen-lector-voz/.venv/bin/python
E=tests/evidence/atlas-media-intent-2026-10-22
$PY $E/media_intent_browser.py . $E /tmp/shots chromium   # o webkit
$PY scripts/check_media_embeds.py --summary $E/real-https.json --out /tmp/real
$PY -m unittest portal.test_media_embeds
```

## Pendiente

- La raíz regenera el build del artefacto (embeds.js) y del bridge inyectado.
- D7 no cubre `<area href>` ni las navegaciones por script (`location = …`). El artefacto puede navegar su propio iframe desde siempre, y eso queda fuera de este alcance.
