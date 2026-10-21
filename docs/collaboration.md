# Review artifacts together

## Standalone review
Pins stay anchored to content. Local review supports a declared author, replies, assignment, open/resolved status and activity. Events live in document-scoped localStorage. Same-origin tabs can observe storage changes; separate devices exchange JSON explicitly. Standalone HTML has no remote synchronization or authenticated identity.

Events include IDs, thread, actor, timestamp and action: create, reply, edit, resolve, assign or delete. Imports are idempotent and validated before application. Different documents, conflicting IDs and orphan replies are rejected. Failed imports remove only keys created by that attempt. Storage exhaustion leaves unsaved work in memory with feedback. Exporting retains history and can expose any private text included in the local file. Limits are 2,000 events and 2 MB per import.

Projection orders by timestamp and ID. Concurrent replies survive; the latest edit/status is projected while history retains earlier events. Client clocks do not prove identity or approval. Keep exports if browser storage might be cleared.

## Stable references
Keep the document ID across revisions. Anchors include section/block identity, normalized block text, quote and relative point. Reattachment requires an unambiguous matching block. Changed or repeated text remains available as unlocated context; never fabricate a new location. Filtered-out table rows may hide their pins while their threads remain in the review list.

## Connected review
Inside the portal, an isolated bridge records identity, version, context and checked permissions. The library aggregates authorized feedback across documents. Readers may comment with permitted verified or declared guest identities. Private notes belong only to their author. Polling is approximately every 12 seconds; this is not live presence or cursor synchronization. Downloaded HTML remains standalone. Importing local JSON into shared server history is not implemented.

The compact composer shows author, text, privacy and send. Context, type and optional session are secondary. Existing entry types cannot be changed while editing. Ctrl/Command+Enter submits; errors keep the draft. The review list retains replies, history and resolution.

## Return context to an agent
Copy/export includes document URL, version, HTML SHA, section, quote, full block, author, session and replies. Select all or pending feedback and explicitly include your own private notes when appropriate. Copying does not send to a model or reopen a conversation. Comments are proposals within an authorized task, not instructions that grant external permissions.

New versions remain drafts until explicitly released. Preserve the shared URL and audience. [Portal operations](portal-operations.md), [feedback and sessions](feedback-and-sessions.md) and [the unified workspace](unified-workspace.md) describe the connected lifecycle.

## Speech and contextual review

The shared [voice reader](reader-controls.md#listen-to-a-document) excludes review panels, private notes, navigation and controls from speech extraction. Starting playback does not create a comment or change permissions. Its contextual menu adds reading actions alongside the permission-checked comment action; selection and Shift + right-click retain the native menu. Hosted legacy documents retain their existing parent composer. Speech text stays inside the document and does not enter review exports or the parent bridge. The browser voice selector distinguishes local from remote services.
