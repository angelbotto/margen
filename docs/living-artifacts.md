# Editing living artifacts

Implementation: owner editing for editorial documents, with eight insertable block types. Production availability depends on deploying the portal revision that includes this feature; installing the agent skill alone does not update the server.

## Edit and publish

As the document owner, choose **Editar contenido** in the artifact's sharing menu or owner controls. Change the document title or content directly. In an empty text block, type `/`, search for Texto, Título, Lista, Checklist, Tabla, Cita, Código or Separador, and press Enter. The `+` beside a block opens the same menu. Block actions let you move, duplicate or remove a block; Deshacer/Rehacer also work with the keyboard.

Tables support cell editing, a caption, adding rows/columns and removing the last row/column. The initial limit is 100 rows and 12 columns. Wide tables scroll within the editor. Lists support numbered or bulleted items; checklists retain their checked state.

**Guardado** means the private working draft has reached the server. It does not change the shared artifact. **Vista previa** renders the saved draft in an isolated frame. **Publicar cambios** creates an immutable version, records the actual account author and changes, and updates the existing artifact URL. Audience and comments are preserved.

## History and recovery

**Historial de cambios** lists the version author, date, publication state and before/after block content. You can open each immutable version. **Restaurar como borrador** explicitly replaces the working draft; it does not rewrite history or change the shared URL. Publish that draft to make the restored content the new current version.

If another tab or agent changes the draft or published version, the editor rejects the stale save and keeps your local text. **Descargar mis cambios** exports a readable Markdown copy. After preserving any desired changes, **Continuar desde la versión publicada** asks you to confirm replacement of the shared working draft. You can then apply the changes you want to keep. Automatic conflict merging is not implemented.

Connection failures display **No guardado** and leave the editor open. Reconnection plus another edit or the save keyboard shortcut retries. Do not close the browser while there are unsaved changes; the browser receives an unload warning. Autosave is server-backed, not an offline browser database.

## Compatibility and boundaries

- Only the owning account can edit or restore. Being an administrator or invited editor does not confer ownership. Invited editors retain their existing proposal/source permissions.
- Existing paragraph/heading IDs remain intact. Newly inserted and duplicated blocks get unique IDs. Removed blocks remain available in their original version; existing review tooling reports missing anchors.
- Unsupported components retain their exact original HTML and appear as **Componente conservado**. This includes complex tables, independently anchored nested content and custom diagrams. Decks and prototypes retain their own editing workflow.
- Surrounding styles, theme, document identity, runtime, audience and comments are retained. Editing does not assign Angel's identity or writing preferences to another account.
- Charts, timelines, architecture adapters, drag-to-reorder, a formatting toolbar and simultaneous real-time collaboration are not included in this first slice.

See the [implementation plan](plans/living-artifacts.md) and [agent continuity contract](agent-connectors.md#human-edits-and-version-continuity).

## Operating the change

The server initializes three additive SQLite tables: `editor_sources`, `editor_drafts`, `editor_checkpoints`. No prior version is rewritten or deleted. Back up the database and content volume before deploying, then restart the portal on the new revision. Existing deployment health and authentication checks still apply. Verify with a private synthetic document before using a real artifact.

A complete backup includes the database (editable sources, private working drafts, attribution) and content files (immutable HTML and attachments). Avoid an older-server rollback after users start editing: it lacks the stale-base guard and could overwrite their work. Restore a consistent pre-release backup only through the operator's explicit recovery process.
