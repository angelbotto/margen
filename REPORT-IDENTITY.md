# Identidad en comentarios: comentarios ajenos que parecían del lector

Base `d61743a` (PR #47). Rama `angelbotto/margen-atlas-identidad`. Sin merge, push ni deploy.

## Causa exacta

El servidor nunca reescribió la autoría. `POST /api/artifacts/{aid}/review` guarda `author`/`actor` de la sesión al
escribir e ignora lo que mande el cliente, y `visible_events` filtra las notas privadas por `actor`. El problema
estaba en dos lugares:

1. **Composer del lector (`packages/core/components/review.js`, servido como `portal/static/review.js`).**
   `refreshComposer()` siempre pintaba el nombre y el avatar con `authorInput.value`, que en el portal es el
   **lector actual** (`remote.author`). Además, al pulsar el pin de un hilo, quien tenía `permissions.edit`
   (dueño o editor) entraba directo al editor de ese hilo (`remote.permissions.edit || actor === remote.actor`).
   Resultado: Ángel pulsa el pin de Alice y ve un composer con «ÁB · Ángel Botto» sobre el texto de Alice, como si
   fuera suyo. Lo mismo pasaba con «Editar» desde la lista.
2. **Tokens de agente (`portal/app.py`, `who()`).** Un `Bearer` resuelve a la cuenta humana dueña del token y el
   evento quedaba como `author: "Ángel Botto"`, `verified: true`, sin ninguna marca de procedencia. En el lector,
   la bandeja y el contexto exportado, un comentario del agente era indistinguible de uno escrito por Ángel
   («Ángel Botto · correo verificado»).

No existe ningún alias «Tú» en el código. Las respuestas, el JSON del snapshot y `prompt_bundle` ya usaban el
autor del evento.

## Cambios

- `review.js`: `byline(e)` muestra el autor registrado del evento (`etiqueta (agente de Nombre)` si es de agente).
  Un pin ajeno abre el hilo en el panel (`own(n)`: mismo `actor` que el lector). El editor de un hilo existente
  muestra al autor original. Un comentario nuevo sigue mostrando al lector. La meta de un comentario de agente dice
  «conexión de agente» en lugar de «correo verificado». El modo local, sin bridge, conserva su comportamiento.
- `portal/app.py`: `who()` incluye `t.label` del token; cada evento escrito con token guarda
  `agent: <label>` (máximo 80 caracteres). Es un campo nuevo y aditivo. **No cambia la autorización:** por pedido
  del coordinador revertí un primer intento de separar humano/agente en `edit`. El token conserva los permisos de
  su cuenta.
- `portal/workflows.py`: `byline()` en `prompt_bundle` (líneas `Autor:` y `<respuesta autor=…>`).
- `portal/static/app.js`, `reader-workspace.js` y `creator.js`: la bandeja, la vista de respaldo y el creator nombran
  al agente.
- La copia `portal/static/review.js`, `developers-runtime.json`/`developers-shell.html` y los módulos y hashes
  embebidos en `examples/generated/*` se actualizaron con la nueva fuente. `scripts/build.py` no produce diff
  adicional.
- `docs/collaboration.md`: nuevo párrafo sobre la autoría en la revisión conectada.

## Pruebas: antes y después

Harness real `tests/evidence/identity-2026-10-22/harness.py`: `create_app` con un store desechable, la shell del portal y
el `/render` real detrás de una ruta de Playwright (Chrome). Son tres sesiones con nombres distintos: Ángel Botto
(dueño), Alice Ruiz y Bob Pérez (comentaristas), más tokens de agente de Ángel («Codex») y de Bob («Bot de Bob»). No
se escribió nada en producción.

| | Resultado | Archivo |
|---|---|---|
| Antes (`d61743a` extraído) | **18/26** | `tests/evidence/identity-2026-10-22/before.json` |
| Después | **26/26** | `tests/evidence/identity-2026-10-22/after.json` |

Fallaban antes:
- El pin de Alice abierto por el dueño mostraba un editor con «Ángel Botto / ÁB».
- «Editar» explícito mostraba igualmente a Ángel como autor.
- El comentario del agente no tenía procedencia en el evento, en el lector (Ángel y Bob) ni en el export.
- La respuesta del bot de Bob aparecía como «Bob Pérez».

Pasan en ambos casos:
- Alice comenta, Bob la ve como Alice y responde, y Alice ve a Bob tras recargar.
- La nota privada de Alice solo la ve Alice.
- Bob no puede editar a Alice (403).
- Los `create` conservan el autor inmutable.
- El export conserva a Alice y a Bob y omite la nota ajena.
- No se filtran correos en la respuesta de revisión de un comentarista.

Unitarias:
- `portal/test_review_identity.py`, 3 pruebas. En la base, la de agente falla con `KeyError 'agent'`; las de autoría
  de servidor y privacidad ya pasaban, lo que confirma que la causa no estaba en el servidor.
- `packages/core/review-composer.test.tsx`: una prueba nueva que falla con el `review.js` de la base
  (`expected true to be false`, el editor se abría).

Suites:
- `unittest discover portal`: 197 OK.
- Vitest: 113/114. El único fallo, `components.test.tsx`, cuenta 89 recetas y espera 90; también falla en un
  checkout limpio de la base, así que no viene de este cambio.
- `test_review_store.cjs`, `validate.py`, `build.py` (sin diff), `test_contract`, `test_feedback`,
  `test_portal_shell`, `test_agent_connector`, `test_portability`, `test_release` y `validate_skill`: OK.

## Límites

- **Históricos:** los comentarios de agente escritos antes de este cambio siguen atribuidos a la cuenta, sin
  `agent`. No se reclasifican por inferencia.
- **Autorización:** un token comparte la cuenta. Atribuirlo no restringe lo que puede hacer; por ejemplo, puede
  editar entradas de su humano y viceversa, como antes.
- **Etiqueta visible:** el comentarista ve la etiqueta del token (texto elegido por el dueño), nunca correos.
- **Filtro «Asignados a mí»:** sigue comparando por nombre; dos personas homónimas se confundirían ahí. Queda fuera
  de alcance.
- **Analítica:** `portal/analytics.py` agrupa participantes por `actor`, así que el agente cuenta junto a su
  humano. No se tocó.
- **HTML descargado o local:** sigue con identidad declarada. Un JSON importado con eventos `agent` falsificados se
  mostraría como agente; el modo local nunca acreditó identidad.
