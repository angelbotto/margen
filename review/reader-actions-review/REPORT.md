# Revisión independiente · Guardar / Me gusta y pie del autor (ae6275f)

**Veredicto: NO-GO para merge tal cual.** Dos bloqueantes reproducidos contra el portal real; el backend (persistencia, permisos, revocación, CSRF) está bien.

Método: `create_app` real (app.js, index.html, reader-workspace.js reales) servido por uvicorn en HTTPS local con SQLite temporal, conducido con entrada real de Playwright (mouse/teclado) en Chromium y WebKit. Sin producción ni credenciales. Evidencia en `evidence/`; scripts para reproducir:

```sh
PY=/Users/angelbotto/orca/workspaces/margen/margen-lector-voz/.venv/bin/python
$PY review/reader-actions-review/check_reader_actions_portal.py --out /tmp/ra   # flujos + barrido de geometría (todos los ejemplos, 1280 y 390 px)
$PY review/reader-actions-review/probe_occlusion.py --out /tmp/ra-occ          # componentes anchos 1200–1920 px y temas oscuros
```

`scripts/test_reader_actions_runtime.py` pasa (4/4), pero usa un anfitrión simulado sin `reader-workspace.js`, por eso no ve B1.

## Bloqueantes

### B1 · Presentaciones y HTML propio no tienen Guardar / Me gusta en el portal real
- El dock de respaldo se agrega dentro de `#reader-dock` (`app.js:1734`). Todo render inyecta `reader-controls.js`, que envía `controls-ready`, y `reader-workspace.js:411` pone `#reader-dock.hidden = true`.
- Resultado (Chromium y WebKit, deck y HTML propio, también anónimo en público): `.reader-actions-dock` con `hidden=false`, caja 0×0 porque el padre tiene `display:none`. No hay ninguna forma de guardar ni marcar esos documentos. `evidence/portal-summary.json → fallback`.
- Arreglo sugerido: montar el dock fuera de `#reader-dock` (nodo propio fijo) o no ocultarlo en `controls-ready`; añadir un test con el portal real.

### B2 · El ancla del portal se pinta encima de contenido que cruza el hueco
- `report()` del iframe sólo comprueba los límites del viewport, nunca la oclusión. El ancla es `position:fixed; z-index:4` en el anfitrión, fuera del iframe, así que queda por encima de cualquier cosa del documento.
- Índice fijo (≥1200 px): una tabla `.amplio` pasa bajo el índice y el `elementFromPoint` del documento en el centro de los botones devuelve `td` en 13 de 25 posiciones de scroll, a 1440, 1600 y 1920 px, en los dos motores (`evidence/occlusion-chromium-table-1440.png`). Lo mismo ocurre con el ejemplo real `priorities` (`figure.amplio`, `evidence/occlusion-webkit-ex-priorities-1440.png`).
- Encabezado fijo: a 1200/1280 px y en móvil (390 px), el encabezado `header#nota-inicio.barra` (también `a.firma-editorial`) cubre el hueco en `scrollY≈230–350`, y los botones se pintan encima del encabezado. Pasa en `table`, `guide`, `chapters`, `priorities`. En `hacker` (1280 px) los tapa `span.procedencia`.
- Arreglo sugerido: en `report()`, probar con `elementFromPoint` los puntos del hueco (centros de botón o una rejilla pequeña) y enviar `visible:false` salvo que todos caigan dentro de `[data-acciones-lector]`. Ya se reprograma en cada scroll. Nota: el hecho de que el índice fijo y los `.amplio` se crucen es un problema previo del documento; el ancla lo amplifica.

## No bloqueantes (arreglar antes o justo después)
1. **Ancla perdida tras redimensionar con el diálogo abierto.** Si se abre el diálogo, se redimensiona y se cierra con Escape, el ancla queda oculta: el iframe no reenvía una geometría que no cambió y `place()` no vuelve a correr. El foco cae en `#artifact-frame` en vez de volver a quien abrió el diálogo. Arreglo: llamar a `place()` en el handler `close` antes de restaurar el foco.
2. **Contraste con el tema del documento.** Los botones usan los tokens del portal: en documentos oscuros (`linear-dark` rgb(16,17,20), `hacker`) se ven como píldoras claras ajenas al documento (`evidence/theme-chromium-linear-dark.png`). Se leen, pero no parecen del documento.
3. **El documento puede reubicar el ancla** en cualquier punto de su propio viewport: sólo se validan los límites, no que coincida con el hueco real. El riesgo es bajo, porque el ancla sólo abre un modal del anfitrión con retardo de 650 ms. Aun así, un autor malicioso puede preparar un patrón de dos clics. Aceptable si se documenta.
4. **Me gusta duplicado tras unir alias.** Si dos alias tenían «me gusta» en el mismo artefacto, después de `merge_admin_aliases` el total sigue en 2 para una sola persona. Causa: `UPDATE OR IGNORE` deja la fila del alias viejo, y el alias viejo sigue verificado y con acceso. La migración corre en `Store.__init__` antes de la unión de alias, así que el orden es correcto. Arreglo: borrar las filas del alias viejo que hayan quedado duplicadas en `reader_saves`/`reader_likes`, o excluir en `like_count` a los usuarios unidos.
5. **El toast ignora el enlace «Ver guardados».** `toast(text)` sólo acepta texto (`app.js:81`), así que desde el dock no hay enlace a guardados.
6. **Pestaña Guardados con `/?view=saved` directo.** En la medición, `[data-view=saved]` quedó con `aria-current="false"`. Es menor: conviene verificarlo a mano.
7. **Coste de `like_count`.** Llama a `permissions()` por cada «me gusta» en cada GET y PUT, O(N) consultas por vista. Es aceptable a la escala actual; conviene ponerle un límite o cachearlo.
8. **Deriva de documentación.** `docs/document-formats.md:53` todavía dice que `platform` vale `true` por defecto y que sin `footer` se mantiene la línea «marca · título». Tampoco menciona que las presentaciones rechazan `footer`/`reactions`. `docs/design-contract.md` sí está al día.

## Verificado correcto (real, Chromium + WebKit)
- Ancla alineada con el hueco (Δ ≤ 2 px) justo bajo la `.ceja` «En esta página», en todos los ejemplos publicables, a 1280 y 390 px. No tapa controles del anfitrión. El cambio de versión vuelve a anclar.
- Mensajes forjados (`reader-actions-anchor` con claves extra, ops inventadas, `postMessage` desde la ventana superior, clic sintético `isTrusted=false`): 0 PUT y ningún diálogo.
- Retardo de intención: un clic real a los ~2 ms de abrir da 0 PUT. Un doble clic real tras el retardo da exactamente 1 PUT. Enter y Espacio sostenidos sobre el ancla dan 0 PUT, con el diálogo abierto y el foco en «Cerrar».
- Multiusuario: lectora en Chromium y segunda cuenta en WebKit dan `likes=2` para ambas y para la autora. Lo guardado es por cuenta y persiste al recargar («Guardado», «Me gusta · 2»).
- Guardados: la pestaña real navega a `/?view=saved`, la lista enlaza a `/a/<id>` y la navegación funciona.
- Revocación: el estado y el PUT dan 404, el documento desaparece de guardados y del total (2→1) y el ancla no aparece. Al volver a conceder acceso, la fila conservada reaparece (1→2).
- CSRF: el middleware exige Origin; el PUT exige `X-Margen-Reader-Action` y sesión de navegador (tokens de agente: 403). El portal tiene `frame-ancestors 'none'`.
- Pie: sin `footer` no hay pie; `platform` funciona como opt-in; las presentaciones rechazan pie y reacciones. Es un contrato razonable y los callers del repo (`build_atlas.py`, `create_artifact.py`, `check_media_embeds.py`) son compatibles. Un archivo suelto no tiene hueco y conserva sus reacciones locales.

Límites de esta revisión: 7 ejemplos (`chapters`, `checks`, `editorial-web`, `globe`, `library`, `report`, `template`) no llevan `nota-documento` y el portal los rechaza, así que no se midieron en el portal. No se probó un dispositivo táctil físico (sólo emulación móvil).
