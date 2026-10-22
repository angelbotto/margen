# Revisión independiente · identidad de comentarios (7d2135e)

Run `run_d4fd3704f129` · tarea `task_944a4410fdcb` · 22 oct 2026 · solo lectura de producto.
Alcance: `git diff d61743a 7d2135e` en `packages/core/components/review.js` (= `portal/static/review.js`, idénticos), `portal/app.py`, `portal/workflows.py`, `portal/static/{app,creator,reader-workspace}.js`, `docs/collaboration.md` y tests nuevos. Los archivos objetivo no cambian entre 7d2135e y HEAD (`deb3f61`). No leí `REPORT-IDENTITY.md`.

## Veredicto

**PASS con hallazgos P2/P3.** El defecto original era del cliente (base: el dueño o editor que tocaba un pin ajeno abría el composer con su propio nombre). 7d2135e lo corrige y el servidor ya registraba bien la autoría en la base. La distinción agente/humano es fiable en el lector (sufijo `· conexión de agente`), pero no en la bandeja, el creator ni el contexto exportado; ningún hallazgo es P0/P1.

## Hallazgos

### P2 · Fuera del lector, la distinción agente/humano es solo texto y cualquier invitado puede imitarla
- `portal/workflows.py:158` (`byline`) y `:172` (`'Autor: '+byline(n)`); `portal/static/app.js:760`, `creator.js:370`, `reader-workspace.js:175,328`.
- Repro (`api_probe.py`, checks «guest with agent-shaped name» y «export cannot distinguish guest from agent byline»): en un artefacto con `guests:true, comments:'readers'`, `POST /api/guest {name:'Codex (agente de Propietaria)'}` y luego comentar. En el export aparece `Autor: Codex (agente de Propietaria) · …`, igual que una entrada real de token. El evento sí lleva `verified:false` y no lleva `agent`, pero ninguna de estas superficies lo muestra.
- Clasificación: el mecanismo (nombre de invitado libre) ya existía en la base; lo nuevo es que ahora existe una forma de agente que el export, la bandeja y el creator presentan como significativa sin marca de verificación. El lector sí muestra `· invitado`. Para cumplir «el token se distingue de una cuenta humana» en estas superficies, la marca tiene que venir de `agent` y `verified`, no de la forma del texto.

### P3 · La etiqueta del token no se sanea: se aceptan saltos de línea y controles bidi
- `portal/app.py:399` (`clean(label,80)` solo hace strip) → `:680`.
- Repro A (export): con la etiqueta `"Bot\nAutor: Propietaria"`, el export contiene una línea `Autor: Propietaria (agente de Otra persona)` aparte de la real. Un agente que lea el contexto ve un autor falso.
- Repro B (UI): con una etiqueta terminada en U+202E (RLO), el resto de la línea `(agente de X) · conexión de agente · fecha` se renderiza invertido (captura: `tests/evidence/identity-independent-2026-10-22/rlo-label.png`). Así se oculta la cuenta real detrás de un nombre ajeno al principio de la línea.
- Clasificación: los nombres de invitado (`app.py:361`) ya tenían el mismo problema (preexistente). Lo introducido es el vector de la etiqueta, que antes no salía de `/api/tokens` y ahora llega a todos los lectores.

### P3 · La etiqueta del token, antes privada, ahora se expone a todos los lectores
- Antes, `GET /api/tokens` era la única forma de verla y solo para su dueño (`app.py:401-405`). Ahora queda copiada en cada evento y la ven commenters, invitados y lectores públicos. También sobrevive a la revocación (checks «token label visible to other readers» y «revoked label retained on past entries»; ambos en NO en la base).
- No hay fuga de emails (check «no email in snapshots/export»). Basta con un aviso al crear el token («esta etiqueta será visible para quien lea tus comentarios»).

### P3 · Coherencia menor
- `validate()` en `review.js:5-12` no tipa ni limita `agent`. En modo local, un JSON importado puede traer `agent` de cualquier tipo o longitud; solo afecta al texto, porque todo se pinta con `textContent`. En modo puente, el servidor siempre envía una cadena de 80 caracteres como máximo.
- Varios `aria-label` siguen usando `author` sin el agente: `app.js:793` («Respuesta a …») y `review.js:108` («Responsable del comentario de …»).

## Lo que verifiqué y pasa

| Área | Resultado | Evidencia |
|---|---|---|
| Campos `author/actor/agent/verified/time` del cliente ignorados | PASS (igual en la base) | api_probe |
| Comentarios mutuos y respuestas: cada lector ve al autor registrado | PASS | api_probe, client_probe |
| Edición ajena (dueño y editor): `create` conserva al autor; cada `edit` queda a nombre de quien edita | PASS | api_probe, client_probe |
| Pin ajeno → abre el hilo, no el composer (dueño y commenter) | PASS (en la base, NO para el dueño) | client_probe |
| «Editar» explícito → el composer muestra al autor original | PASS (en la base, NO: mostraba al lector) | client_probe |
| Entrada nueva tras editar una ajena → el composer muestra al lector | PASS | client_probe |
| Commenter: «Editar» solo en lo suyo; lector sin permiso: sin acciones | PASS | client_probe |
| El token conserva los permisos de su cuenta (no edita ni resuelve ajenos); token revocado → 401; `/api/tokens` solo desde navegador | PASS | api_probe |
| Notas privadas del agente: invisibles para el dueño del artefacto y visibles para su humano | PASS | api_probe |
| Históricos sin `agent` no se reclasifican | PASS (decisión documentada) | api_probe, client_probe |
| XSS con etiqueta `<img onerror>` | PASS (solo `textContent`) | client_probe |
| Recarga: autoría determinista desde el estado del servidor | PASS | client_probe |
| Sin emails en snapshot ni export | PASS | api_probe |

## Comandos y resultados reales

```
npm ci                                   → exit 0
npm run build                            → exit 0; no cambia ningún archivo rastreado (generated al día)
npx vitest run packages/core/review-composer.test.tsx → 13/13 passed
python -m unittest portal.test_review_identity → 3 OK
python -m unittest portal.test_app              → 15 OK
PYTHONPATH=. python tests/evidence/identity-independent-2026-10-22/api_probe.py      → api_after.json (HEAD) / api_base.json (d61743a)
python tests/evidence/identity-independent-2026-10-22/client_probe.py <root>          → client_after.json 19/19; client_base.json 4 NO (defecto original)
```
Python: `/Users/angelbotto/orca/workspaces/margen/margen-lector-voz/.venv/bin/python` (no trae pytest, así que usé unittest). En `api_*.json`, `ok:true` en los checks «export: newline…», «export cannot distinguish…» y «token label visible…» significa que **se reprodujo la debilidad**.

## Limitaciones
- Usé el puente simulado del cliente (`client_probe.py`), no el portal completo con su iframe ni el `postMessage` del host. El cliente y la API los probé por separado.
- No probé concurrencia ni varias pestañas. Del modo offline solo comprobé que carga; el modo local no tiene identidad que verificar.
- No revisé otros frentes que root está integrando, como `scripts/build_atlas.py` y `docs/atlas-delivery-plan.md`.
