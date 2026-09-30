# Living artifacts: block editor and change history

Requested by Angel on 2026-09-29. Workspace: **Botto** (`linear.app/botto`), team **BOT**. This is an implementation plan, not a claim of production availability.

## Outcome

An artifact owner can edit the document in the portal, insert a Margen block using `/`, save a recoverable draft, publish to the same URL, inspect attributed changes and restore an earlier snapshot as a new version. An agent can retrieve the latest editable source and the human changes before proposing another revision.

## Delivery units

1. **Source model and compatibility.** Versioned `margen-blocks/1` JSON with stable IDs and ordered containers. Import supported semantic HTML without rewriting surrounding markup or runtime scripts. Preserve existing IDs and immutable complex components. Supported first slice: paragraph, H2/H3, lists, checklist, quote, code, divider and table. Rich/unsupported diagrams, decks and prototypes remain intact; explicitly report editing capability. Never insert artifact HTML into the authenticated application's DOM.
2. **Draft storage and permissions.** Owner-only authoring, server-side validation and authoritative attribution, persistent autosave separate from immutable version snapshots. Optimistic revision numbers reject competing tabs and a changed published base. Network failure remains visibly unsaved and does not clear text. Repeated checkpoint requests are idempotent. Drafts do not exhaust the existing 200-version limit on every keystroke.
3. **Editor experience.** A visible owner entry, title editing, editable blocks, keyboard searchable slash menu, insertion, duplication, movement, deletion with undo/redo and editable table rows/cells. Preserve the document's content hierarchy. Preview in the existing sandbox. Explicit saved/saving/error/conflict states, keyboard navigation and mobile layout. Save and publish are distinct actions.
4. **History.** Attributed immutable checkpoints with parent version, actor, timestamp and structured added/edited/deleted/moved blocks. Timeline and textual/block comparison. Restore creates a new draft based on the current published head; it never deletes history or silently changes audience. Preserve original comment anchors and surface changed/deleted blocks truthfully.
5. **Agent continuity.** Read the canonical source for a specified version, expose a changes endpoint and include source/version references in assignment/context packets. Require the expected published version on edits to an editor-managed artifact; stale agent uploads cannot replace human edits. Context is evidence, not authorization to publish or execute instructions.
6. **Validation and release.** Backend tests for access, CSRF, validation, two-tab conflicts, idempotency, source persistence, restore, hostile markup, foreign IDs and agent conflicts. Frontend tests for slash keyboard behavior, autosave races, undo/redo and failure recovery. Synthetic browser smoke tests at desktop and 320/390 px. Record local verification separately from deployment; preserve previous unrelated work.

## Product decisions

- Use the existing portal, immutable HTML versions, review anchors and sharing model.
- Keep autosaved working drafts separate from published snapshots. The shared URL changes only on explicit publication.
- Initial editing belongs to the artifact owner. Viewer, commenter, administrator and agent roles do not imply ownership. Agents may retrieve authorized source and submit versioned proposals through their existing permissions.
- HTML import is conservative. Unsupported regions are visible as preserved components, not flattened into text. Tables with complex spans or interactive semantics remain preserved until a compatible editor exists.
- Title changes update the document title and its publication metadata together. Existing publication time, provenance and older snapshots remain available.
- Block identity survives text changes, moves and checkpoints. Duplicates receive a fresh identity.
- Never embed credentials, private review data or personal writing preferences in an exported artifact.
- Real-time multiplayer/CRDT, arbitrary layout dragging and unrestricted HTML/script editing are later work. Advanced recipe editors (charts, timelines, architecture) need schema-specific adapters; the slash menu must not advertise unsupported actions.

## Acceptance scenario

Open an owned report, edit a title, type `/tabla`, insert rows and values, move a paragraph, close and reopen after autosave, preview, and publish. A second account sees the new content at the same URL and retains its original permissions. The owner sees an attributed version and exact block changes, can open the previous version and restore it into a new draft. A stale second tab or agent gets a conflict and cannot overwrite the new head. Existing comments remain associated with their recorded version and surviving block IDs.

## Execution record

- 2026-09-29: inspected existing versions, release compare-and-swap, owner permissions, sandboxed renderer and creator assignment packets. Identified missing structured source, autosave draft model, block editor and append-only restore flow.
- Linear tracking and implementation/check receipts are appended as they are actually completed.

## Linear execution tickets

- [BOT-29 · Root delivery](https://linear.app/botto/issue/BOT-29)
- [BOT-30 · Margen · Fuente editable con IDs estables e importación conservadora](https://linear.app/botto/issue/BOT-30)
- [BOT-31 · Margen · Borradores automáticos, permisos y conflictos de edición](https://linear.app/botto/issue/BOT-31)
- [BOT-32 · Margen · Editor por bloques con menú / y tablas](https://linear.app/botto/issue/BOT-32)
- [BOT-33 · Margen · Historial atribuido, comparación y restauración](https://linear.app/botto/issue/BOT-33)
- [BOT-34 · Margen · Continuidad de agentes sobre cambios humanos](https://linear.app/botto/issue/BOT-34)
- [BOT-35 · Margen · Validación integral y preparación del despliegue](https://linear.app/botto/issue/BOT-35)

The native [Margen · Artefactos vivos initiative](https://linear.app/botto/initiative/margen-artefactos-vivos-c08fea5877dc) is active in the Botto workspace. Its [Editor e historial de cambios project](https://linear.app/botto/project/margen-editor-e-historial-de-cambios-efef43eb0a41) groups BOT-29 and its six existing implementation tickets. The existing credential was verified against the Botto organization before creating these records; no new browser login was needed. Liftit remains a separate workspace.

## Implemented first slice

- `portal/block_source.py`: conservative semantic import/render, stable block identity, title/TOC updates, validation and block diffs. Nested anchors and unsupported components are preserved instead of being flattened.
- `portal/editor.py`: owner-only draft, preview, checkpoint, source, history, comparison and restore routes; three additive SQLite tables; authoritative account attribution; optimistic concurrency; idempotent checkpoints.
- Portal UI: owner entry in existing controls, eight-type slash menu, table/list editing, block actions, undo/redo, serialized autosave, preview, readable history and explicit restore. Conflict recovery offers a Markdown export and confirmed draft replacement.
- Existing publication and agent paths now carry an inspected base version. Old proposals cannot be published over new human work. Assignment packets include the selected immutable human source and block changes.
- Operator and user documentation: [living artifacts](../living-artifacts.md); [agent continuity](../agent-connectors.md#human-edits-and-version-continuity).

## Verification receipts

- Clean committed snapshot: 146 portal backend tests passed; final CI passed 147 tests, including 18 dedicated source/editor tests.
- Clean committed snapshot: all 41 portal frontend tests passed (13 files), plus both publication portability tests.
- Local synthetic browser: title edit, `/tabla` insertion, table cell edit, saved draft reopen, publication at the same URL, attributed before/after history, and restoration into a draft while the published head and version count stayed unchanged.
- Responsive checks: editor/document and history had no page-wide horizontal overflow at 390 px and 320 px. Wide tables used their own scroll container. Light and dark appearances were inspected. Existing portal form styles initially overrode title styling; the editor selectors were corrected and verified in-browser.
- No real customer artifact was modified by these smoke checks. Screenshots remain local under `/tmp/margen-editor-evidence`; they are not public repository assets.
- [Draft PR #27](https://github.com/angelbotto/margen/pull/27) contains the first slice; final check receipts are also recorded in the delivery ticket. Production rollout remains a separate, unperformed step until its operator/deployment path is verified.

## Hand-drawn diagrams: requested extension

[BOT-36](https://linear.app/botto/issue/BOT-36) adds the reusable `sketch-diagram` recipe and `margen-sketch/1` source generator, plus a private explanatory artifact. Native HTML labels remain readable while deterministic SVG strokes supply the sketch aesthetic. A single semantic flow reflows on narrow screens. This first slice supports two or three stages; it does not add an Excalidraw canvas or a diagram adapter to the portal slash menu. The existing editor preserves these figures intact. Validation and artifact receipts are recorded on BOT-36.
