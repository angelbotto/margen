# Revisión final acotada · delta del atlas

Run `run_d4fd3704f129` · tarea `task_da2a8a3c0b8b` · dispatch `ctx_1d197bad0e9c` · 2026-10-22. Contexto nuevo, sin subagentes, sin cambios de producto, sin deploy.

- **HEAD revisado:** `ddbdb5a` (`angelbotto/margen-atlas-main`, fast-forward). Producto = `63bb3b2` + `d2236db` y `ddbdb5a` (`media-embeds.js`) + `ad6a2dc` (caché de medidas de fuente en `chart-core.js` y assets regenerados). `29af8b7` y `db677df` solo tocan pruebas y CI.
- **Puntos intermedios:** `2e2d8bc` (identidad, medios, código, índice, puerta de gráficas), `4d2f1f7` (gráficas, impresión), `db677df` (re-ataque de medios) y `ddbdb5a` (botón central, gráficas). Entre `2e2d8bc` y `db677df` no cambian ni la identidad ni `chapters.js`/`reader.js`. Entre `4d2f1f7` y `ddbdb5a` solo cambian `portal/static/media-embeds.js` y `chart-core.js` (`ad6a2dc`).
- **Entorno:** `create_app` con BD temporal y usuarios sintéticos detrás de una ruta de Playwright (`https://portal.test`). Proveedores y hosts externos con stubs; ninguna petición sale de la máquina. Chromium y WebKit de Playwright. Capturas privadas en `~/.local/share/margen-review/atlas-final-delta-20261022/`.
- **Evidencia:** `tests/evidence/atlas-final-delta-20261022/` (probes propios y JSON/logs por HEAD).

## Veredicto

El delta acordado cumple. Encontré un defecto nuevo de seguridad (D2'): un doble clic o una tecla repetida atravesaba hasta el control del portal. Se corrigió en `d2236db` durante la revisión. Al re-atacarlo apareció el residuo del botón central (D2'-R), corregido en `ddbdb5a`, y ambos quedan verificados. Fuera del delta encontré una superposición preexistente del índice. No bloquea, pero es real.

| Área | Resultado en HEAD | Evidencia |
|---|---|---|
| D1-R / D6 / D4 identidad | ✅ 22/22 propio ×2 motores; API independiente 14/16 (fallan solo D3, D5) | `edit_provenance_browser.py`, `prior-harness-2e2d8bc/` |
| D2 / D7 / D8 medios | ✅ arnés raíz 43/43 ×2; doble clic, teclado y botón central ✅ en `ddbdb5a` (13/13 ×2) | `media_doubleclick_browser.py`, `media_keyboard_probe.py` |
| Código anidado, salto final, portapapeles | ✅ (con una nota visual) | `code_runtime_probe.py` |
| Impresión (`printReady`) | ✅ 36 bloques, capítulos ocultos, media/beforeprint/pdf | `print_probe.py` |
| Índice (umbral = scroll-padding + scroll-margin + 2) | ✅ clic, deep link en frío, documento y capítulos | `test_defects.py` 9/9 ×2, `toc_probe.py` |
| Puerta `check_component_atlas` (gráfica real) | ✅ rechaza un chart-core ausente | mutación, abajo |
| Gráficas D2/D3/D6 | ✅ `test_defects` 9/9 ×2, `test_chart_edges` OK (también en `ddbdb5a`) | `final-4d2f1f7/`, `final-ddbdb5a/` |

## Hallazgos

### D2' · Doble clic o tecla repetida activaba el control del portal (media). Corregido en `d2236db`

- **Ataque en `2e2d8bc`/`4d2f1f7`:** el artefacto pide `external` (`attacker.example`) o `embed` (otro ID de YouTube) en `mousedown`/`keydown`. `showModal()` abre el diálogo bajo el puntero y lleva el foco a la acción.
  - El segundo clic de un doble clic (60/120/250 ms) abría la pestaña del atacante o montaba el reproductor.
  - Dos pulsaciones de Espacio (desplazarse leyendo) montaban el reproductor. Dos Enter abrían la pestaña.
  - Un clic simple sí era seguro: solo mostraba la vista previa.
  - Pasaba en ambos motores, con entrada física (`final-4d2f1f7/doubleclick-*.json`, `keyboard-*.json`).
- **En `db677df`/`ddbdb5a`:** 650 ms de protección, `pointerdown` sobre el propio control después de ese plazo, `detail <= 1`, rechazo de `event.repeat` y foco inicial en «Cerrar».
  - Doble clic 60/120/250 ms: 0 peticiones y 0 pestañas.
  - Espacio/Enter ×2: el foco queda en `×` y no se carga nada.
  - Control positivo: un clic deliberado después del plazo sí abre o monta.
  - El arnés raíz pasa 43/43 ×2 y ahora verifica el foco neutro.

### D2'-R · Doble clic con botón central abría el enlace externo (baja). Corregido en `ddbdb5a`

- **Reproducción** (`media_doubleclick_browser.py`, Chromium y WebKit): el artefacto pide `external` en un `mousedown` del botón central. El segundo clic central cae sobre `.media-source` y abre `https://attacker.example/phish` en otra pestaña.
- **Causa:** `auxclick` no pasa por `intended()`.
- **Alcance:** el botón «Reproducir aquí» no se ve afectado.
- **En `ddbdb5a`:** `auxclick` pasa por el mismo `intended()`. El doble clic central ya no abre nada, el clic deliberado después del plazo sigue funcionando y el arnés raíz da 43/43 ×2 (`final-ddbdb5a/`).

### Índice tapado por las notas al margen (media‑baja, preexistente, fuera del delta)

- **Reproducción:** Lectura a 1440 px (también a 1328), con `#apuntes-ejemplo` en vista. `.apunte izquierda`, `.mano-caracter` y el `summary` «Ver y copiar el HTML» de `#fuente-apuntes` pintan sobre el carril del índice fijo. En el hit‑test quedan cubiertos 9 de 14 enlaces y Playwright no puede hacerles clic (`toc_cover_probe.py`, `final-4d2f1f7/toc-cover-*.json`). Captura privada: `toc-cover-final-chromium.png`.
- **Comparación:** idéntico en `2e2d8bc`, así que no es una regresión de este delta.
- **Contradice** el «ningún rótulo del índice pinta sobre contenido» de `REVIEW-ATLAS-UI-RUNTIME.md`. Ese hit‑test buscaba controles del contenido sobre el carril, no enlaces del índice tapados.
- Por esto `toc_probe.py` falla en «clic en cada enlace». Los casos de clic que sí se pueden ejecutar y el deep link en frío marcan bien `aria-current`.

### Nota · El salto final deja una fila visible sin número (baja, aceptada)

`const a = 1;\nconst b = 2;\n` ya no numera una tercera línea. La fila final sin número sigue ocupando una línea: el `pre` mide 98 px frente a 76 px sin el `\n`, en ambos motores. Es el compromiso documentado para que la copia sea exacta, y `test_defects` solo cuenta las filas con `data-numero`. No pido cambio.

## Verificación por cambio

**Identidad (`280ab18`)**

Mi probe `edit_provenance_browser.py` da 22/22 en Chromium y WebKit.

- Ni la dueña ni su agente pueden editar a Alice (403).
- El `author`, `agent` y `verified` forjados en el body se ignoran.
- Después de una edición del token «Codex» de Alice:
  - La lista muestra «Alice Ruiz» como autora original y «Última edición: Codex (agente de Alice Ruiz)», tanto a la dueña como a Alice.
  - «Editar» aparece solo para Alice.
- La edición humana real (clic en Editar → compositor «Alice Ruiz» → guardar) deja «Última edición: Alice Ruiz» y desaparece «Codex».
- El export trae:
  - `Autor:` = último editor;
  - `Autor original:`;
  - `Última edición:`;
  - la identidad de la edición en metadatos (`"tipo": "agente"`).
- No hay correos en el frame ni en el export.
- `portal/static/review.js` está sincronizado con `packages/core/components/review.js`, y la proyección `last_edit` está en las tres capas.

Arnés independiente previo, en HEAD:

- API 14/16.
- Lector 14/17 ×2.
- Solo fallan D3 (nombres que colisionan), la insignia imitada en el nombre de invitado y D5 (etiqueta libre de agente), que son las limitaciones aceptadas.
- D1-R pasa: la dueña no tiene «Editar» en un comentario ajeno.

**Medios (`02442f3`/`ebfbe6a`/`d2236db`)**

- El arnés raíz `media_intent_browser.py` da 43/43 ×2 en `2e2d8bc`, `db677df` y `ddbdb5a`. Sale con código distinto de 0 si algo falla.
- El arnés independiente antiguo da 23/31 en `2e2d8bc`. Los 8 fallos son los supuestos de un solo clic que el diseño de dos pasos cambia a propósito. Comprobé el más sensible: el lavado de activación hacia `attacker.example` solo produce la vista previa, sin pestaña ni petición.
- D7 y D8 están cubiertos por el arnés raíz. El enlace con credenciales ahora da un aviso visible.

**Código (`1a4a2e4`, `a531697`) y salto final**

`code_runtime_probe.py` da 13/14 en Chromium y 12/13 en WebKit. El único fallo es la nota de altura.

- `<mark><a>` conserva el enlace y un clic físico navega a `#s1`.
- `<a><mark>` conserva el `mark`.
- `textContent` exacto.
- `x\n\n` mantiene numerada la línea vacía real.
- `selection.toString()` conserva el `\n` final, con numeración y sin ella.
- El botón copiar escribe los bytes exactos en el portapapeles real (Chromium).
- `pendientes()`/`esperando()`: sus únicos consumidores son el arnés de runtime.

**Impresión (`63bb3b2`)**

`print_probe.py` usa 3 capítulos, 2 de ellos ocultos, con 36 bloques y uno de 3000 líneas a medio colorear.

- En `emulate_media('print')`, `beforeprint` y `page.pdf()` (Chromium) los 36 quedan en estado `listo`, con la numeración igual a las líneas reales y el texto exacto.
- Al volver a pantalla y abrir los capítulos no hay duplicados.
- 0 errores y 0 peticiones de red.
- `test_code_syntax` da 9/9 ×2.

**Índice (`d2dd5df`, `2e2d8bc`)**

- `test_defects.py` da 9/9 en Chromium y WebKit, incluidos los dos tests nuevos de deep link en frío (capítulos) y de clic en formato documento.
- Sobre el atlas real de HEAD, el caso original (deep link en frío a `#receta-glosario`) queda como actual a 1440 y 1328 en ambos motores.

**Puerta de gráficas (`check_component_atlas`)**

Hice una mutación sobre `git archive` de `2e2d8bc`: quité `chart-core.js` de `ORDER` en `contract_artifact.py` y reconstruí con `--render`.

- Control positivo: `passed: true`, 162 comprobaciones, 26 «chart rendered».
- Mutante: exit 1 y 12 «chart rendered» fallidos (lectura, reportes, gráficas) antes de abortar.
- Nota menor: si una figura no produce ni SVG ni error, la puerta falla por un timeout de 30 s (`probe completed`) en vez de por un diagnóstico propio. Sigue fallando, que es lo que importa.

**Gráficas (`d85e0a1`/`63af447`)**

- `test_defects` (calor constante, meta negativa) pasa ×2.
- `scripts/test_chart_edges.py` da OK en `4d2f1f7` y `ddbdb5a`. El cambio de `ad6a2dc` (vaciar la caché de anchos con `loadingdone`) es acotado y no lo ataqué aparte.
- No repetí la matriz de 432 comprobaciones del root.

## No cubierto

- No hay CI de PR48 propia.
- La matriz completa 432×2 no la repetí.
- Medios reales en `https://localhost` (`real-https.json` del root): no los repetí.
- Ni Safari ni Chrome de escritorio, ni táctil.

## Reproducir

```sh
PY=/Users/angelbotto/orca/workspaces/margen/margen-lector-voz/.venv/bin/python
E=tests/evidence/atlas-final-delta-20261022
$PY $E/edit_provenance_browser.py . $E/out chromium            # o webkit
$PY $E/media_doubleclick_browser.py . $E/out chromium          # D2' y D2'-R (exit 0 en ddbdb5a)
$PY $E/media_keyboard_probe.py . $E/out chromium
MARGEN_BROWSER=webkit $PY $E/code_runtime_probe.py . $E/out
MARGEN_BROWSER=webkit $PY $E/print_probe.py . $E/out
python3 scripts/build_atlas.py --output-dir /tmp/a --render
$PY $E/toc_probe.py chromium /tmp/a/atlas.html $E/out; $PY $E/toc_cover_probe.py chromium /tmp/a/atlas.html 1440
(cd review/atlas-ui-runtime && MARGEN_BROWSER=webkit $PY test_defects.py)
```

## Coordinator disposition · index occlusion

The independent centre-point finding is retained above. Wide surfaces intentionally cover the fixed index, matching the reference and preventing index text from painting through content; moving the whole index above them would restore the original visual defect. The visible left edge remains available and keyboard focus raises the index onto opaque paper. A separate real-click probe (`toc_visible_edge_probe.py`) verified all 14 links at 1440 and 1328 px in Chromium and WebKit, including the cold deep link. Results are in `toc-visible-edge-{chromium,webkit}.json`. This partial occlusion is accepted as reference behavior, not described as an unobstructed index. At that checkpoint no product code had changed after the reviewed `ddbdb5a`.

## Post-review Linux compatibility correction

CI reproduced a 29 px page overflow at 320 px / Kaira / dark in WebKitGTK. Isolation traced it to the native select in image-evidence controls: hiding the prototype menu did not change the overflow; removing the evidence select did. Native option text contributed to ancestor scroll geometry despite `overflow:hidden`. Adding `contain:layout` to that select reduced page width from 349 to 320 without clipping the control or its focus outline. The existing complete-atlas CI gate covers this exact combination. A bounded independent follow-up reviews native keyboard selection and responsive behavior; its result is recorded in Orca run `run_d4fd3704f129` and private release evidence.
