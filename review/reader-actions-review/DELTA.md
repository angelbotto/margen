# Revisión delta · Guardar / Me gusta (ae6275f → 4cf2f9c / efff472)

**Veredicto: GO para el delta.** Los dos bloqueantes de `REPORT.md` (B1, B2) y los no bloqueantes 1, 2, 4 y 5 quedan resueltos y verificados en el portal real, en Chromium y WebKit. El hallazgo 6 de la base era un falso positivo de mi propia sonda.

Checkout probado: `margen-publishing-main`, HEAD `d500334`. El código de producto es el de `efff472`; lo posterior sólo añade directorios `review/`. Método: el mismo `harness.Portal` (`create_app` real en HTTPS local, SQLite temporal) con entrada real de Playwright. `harness.ROOT` ahora acepta `MARGEN_ROOT`. Fueron sondas secuenciales y acotadas, sin barrido de todos los ejemplos.

```sh
PY=/Users/angelbotto/orca/workspaces/margen/margen-lector-voz/.venv/bin/python
MARGEN_ROOT=/ruta/al/checkout $PY review/reader-actions-review/check_delta.py --out /tmp/delta [--browsers chromium,webkit] [--only dock,occ,modal,theme,saved]
```

Cada motor tarda unos 4 minutos. Sale con 1 si alguna sonda falla. La evidencia está en `evidence/delta/`.

## Resultado por sonda (Chromium y WebKit: 0 fallos)

| Sonda | Qué mide | Resultado |
|---|---|---|
| `dock` | Presentación y HTML propio, a 1280 px y 390 px (táctil). El dock de respaldo tiene que ser visible, `elementFromPoint` en el centro de cada botón tiene que devolver el botón y sus cajas no pueden pisar `#reader-dock`. Además: clic real, PUT, estado en servidor y toast | 8/8 OK. El dock vive en `#reader-personal-actions`, que es fijo y ya no depende de `#reader-dock`. Un clic da 1 PUT, `aria-pressed=true` y `saved=true` en el servidor. El toast dice «Guardado en tu lista. Ver guardados» y enlaza a `/?view=saved`. Debajo del dock sólo queda `body`/`p`, ningún control del documento |
| `occ` | Tabla `.amplio`, galería y el ejemplo `priorities`, a 1280, 1440, 1920 y 390 px, en 21 posiciones de scroll. En cada posición se prueba una rejilla de 5×3 puntos **sobre cada botón del anfitrión**, mapeada al iframe | 0 posiciones con contenido debajo del ancla en 24 barridos. El ancla se ve en 10/21 posiciones (tabla a 1440/1920), 21/21 (galería) y 8/21 (`priorities`). En el resto se oculta |
| `modal` | Abrir el diálogo desde el ancla con un clic real, redimensionar 1280→1440→1280 y cerrar con Escape o con el botón «Cerrar» | El ancla reaparece y el foco vuelve al botón «Me gusta» del ancla en los dos cierres |
| `theme` | `linear-dark`, `hacker`, `linear-light` y HTML propio oscuro, con el esquema del portal claro y oscuro | El botón toma el fondo del documento: rgb(16,17,20), rgb(8,15,12) o blanco. El texto queda blanco o negro, con un contraste de 18,9 a 21:1. No depende del esquema del portal y el dock del HTML propio oscuro también lo sigue |
| `saved` | `/?view=saved` cargado directo | `button[data-view=saved]` tiene `aria-current="page"`, ninguna otra pestaña está marcada y la lista enlaza a `/a/<id>` |

**Control negativo** contra la base (`ae6275f`, Chromium, mismas sondas):

- `occ` falla en 7 barridos. Ejemplos: `td` bajo el ancla en la tabla a 1440/1920 px; `header.barra` en `priorities` a 1280 px y en la galería a 390 px; `section.apunte` en `priorities` a 1440 px.
- `dock` falla en 4/4 casos: el dock no es visible.

O sea, la sonda reproduce B1 y B2 y el delta los cierra. En la base, `saved` ya pasaba: el `aria-current="false"` del hallazgo 6 venía de que `document.querySelector('[data-view=saved]')` encuentra primero `<body data-view="saved">`. **Se retira el hallazgo 6.**

## Estado de los hallazgos de `REPORT.md`

| # | Estado | Evidencia |
|---|---|---|
| B1 · dock de respaldo oculto | **Cerrado** | `#reader-personal-actions` (`index.html`, `reader-actions.css`). Sonda `dock` |
| B2 · ancla sobre contenido | **Cerrado** | `report()` exige que el hueco entero esté en el viewport y prueba una rejilla de 3×3 con `elementFromPoint` (`editorial-pieces.js`, núcleo y copia del portal idénticos). Sonda `occ` con una rejilla más densa que la del producto |
| 1 · ancla perdida tras redimensionar | **Cerrado** | `place()` en `close`. Sonda `modal` |
| 2 · contraste con el tema | **Cerrado** | `readerActions.surface()` valida RGB entero 0–255 y deriva `--ink` blanco o negro por luminancia relativa. Sonda `theme` |
| 3 · el documento puede reubicar el ancla | Sin cambio (aceptado) | Igual que en la base: el diálogo tiene 650 ms de retardo |
| 4 · me gusta duplicado tras unir alias | **Cerrado** | `efff472`: después de `UPDATE OR IGNORE` se borran las filas del alias viejo en `reader_saves`/`reader_likes`. `python -m unittest portal.test_reader_actions` da 9/9 OK, incluida la prueba idempotente nueva |
| 5 · toast sin enlace | **Cerrado** | `toast(text, action)` sólo acepta `href === '/?view=saved'` y construye el enlace con `textContent`. Sonda `dock` |
| 6 · `aria-current` en guardados | **Retirado** (falso positivo de la sonda) | Sonda `saved` |
| 7 · coste de `like_count` | Sin cambio | Sigue siendo O(N) `permissions()`. `MAX_LISTED` sube a 2000 (= `MAX_SAVED`), así que la lista de guardados puede costar hasta 2000 comprobaciones por GET |
| 8 · deriva de docs | Cerrado según root (`efff472`, `docs/document-formats.md`) | No lo revisé a fondo: sólo confirmé que el diff existe |

## Observaciones nuevas (no bloqueantes)

1. **Sin acción de guardado mientras el ancla está oculta.** Con `anchored=true`, el dock fijo se mantiene oculto. Cuando el índice no es fijo (≤1280 px y móvil), el ancla sólo se ve al principio del documento: 1–2 de 21 posiciones. Lo mismo pasa cuando algo la tapa. Más abajo, el lector no tiene Guardar ni Me gusta hasta volver arriba. Es coherente con el diseño de «bajo En esta página». Si se quiere acceso continuo, se puede mostrar el dock cuando el ancla lleve un rato oculta.
2. **La rejilla del producto cubre x ≤ 210 px del hueco** (`[4, min(w-4,100), min(w-4,210)]`). Hoy los dos botones caben ahí: en la captura de `hacker`, «Me gusta» termina hacia los 155 px del borde izquierdo del hueco. Con un recuento largo o una fuente mayor, la parte derecha del segundo botón quedaría sin muestrear. Mi sonda sí la muestrea y no encontró casos, pero conviene derivar la rejilla de la geometría real o del ancho máximo de los botones.
3. El dock de respaldo (abajo a la derecha, `bottom:84px`) queda encima del texto del documento en ese rincón, igual que cualquier control flotante. No tapa controles del documento ni de la presentación.

Fuera del alcance: barrido de todos los ejemplos, dispositivo táctil físico y producción.
