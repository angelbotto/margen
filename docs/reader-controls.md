# Reader controls and contextual review

The floating toolbar has three tools, in this order: **Comments**, **Share**, and **Preferences**. The speech bubble carries the count of open threads visible to the reader; replies do not increment the count. Resolved or archived threads are excluded. Private notes remain subject to portal authorization.

Choose **Comments → Add comment**, then click or tap the target. Paragraphs, images, table cells, nested cards, SVG charts and canvases can be targets. Tab and Enter work in point-picking mode; Escape cancels. The review panel also offers an Add comment action.

On desktop, right-click ordinary document content for **Comment here**. Shift + right-click retains the native browser menu. Links, buttons, text fields, code and selected text keep their native menus. Keyboard users can use the Context Menu key or Shift + F10 on focused content. On mobile, use the toolbar to select a point; long-press behavior is not overridden.

## Context and persistence

A thread stores a stable ancestor ID, target tag, semantic text or media label, quotation, page, section and normalized coordinates. Give important content stable IDs, image alt text and chart accessible names. Repeated, identical anonymous blocks can be ambiguous after reload. Changed or ambiguous anchors are reported rather than silently moved. Pin collisions group threads without discarding any of them. A canvas stores its labeled surface and coordinates, not an inferred data point; an iframe can be annotated as a surface, not inside a foreign document.

Older hosted HTML without an embedded review runtime now waits for a selected point instead of defaulting to its first heading. The fallback preserves the host composer and existing authorization. It supports click/tap, Tab/Enter and Escape; the richer contextual menu belongs to the embedded review runtime.

## Identity

The original Margen mark is an outlined cube with dotted silhouette and hidden edges, plus solid front edges for small-size legibility. Canonical SVGs live in `packages/core/assets/identity`. The generator embeds the mark and favicon, so standalone files need no asset server. The portal receives deterministic copies. Existing company header identities remain intact.

## Boundaries

Opening a contextual menu grants no permissions. Both the composer and the server enforce access. Draft text survives save errors. Local files keep review in the browser until explicitly exported; hosted artifacts use the portal. Copying review context does not send it to an agent or resume a session.

## Account actions after the contents

Hosted Save and Like actions follow the complete contents list, separated by 16px. The bookmark and heart use 52px targets, an accessible action name, a visible saved state and a real like count. They are portal-owned; the document only reserves a slot. Plain HTML and presentations retain the host fallback dock. The anchored actions keep their authenticated confirmation dialog and iframe intent boundary.
