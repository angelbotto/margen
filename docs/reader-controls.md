# Reader controls and contextual review

The floating toolbar has four tools, in this order: **Comments**, **Share**, **Preferences**, and **Listen**. The speech bubble carries the count of open threads visible to the reader; replies do not increment the count. Resolved or archived threads are excluded. Private notes remain subject to portal authorization.

Choose **Comments → Add comment**, then click or tap the target. Paragraphs, images, table cells, nested cards, SVG charts and canvases can be targets. Tab and Enter work in point-picking mode; Escape cancels. The review panel also offers an Add comment action.

On desktop, right-click ordinary document content for **Comment here**. Shift + right-click retains the native browser menu. Links, buttons, text fields, code and selected text keep their native menus. Keyboard users can use the Context Menu key or Shift + F10 on focused content. On mobile, use the toolbar to select a point; long-press behavior is not overridden.

## Context and persistence

A thread stores a stable ancestor ID, target tag, semantic text or media label, quotation, page, section and normalized coordinates. Give important content stable IDs, image alt text and chart accessible names. Repeated, identical anonymous blocks can be ambiguous after reload. Changed or ambiguous anchors are reported rather than silently moved. Pin collisions group threads without discarding any of them. A canvas stores its labeled surface and coordinates, not an inferred data point; an iframe can be annotated as a surface, not inside a foreign document.

Older hosted HTML without an embedded review runtime now waits for a selected point instead of defaulting to its first heading. The fallback preserves the host composer and existing authorization. It supports click/tap, Tab/Enter and Escape; the richer contextual menu belongs to the embedded review runtime.

## Identity

The original Margen mark is an outlined cube with dotted silhouette and hidden edges, plus solid front edges for small-size legibility. Canonical SVGs live in `packages/core/assets/identity`. The generator embeds the mark and favicon, so standalone files need no asset server. The portal receives deterministic copies. Existing company header identities remain intact.

## Boundaries

Opening a contextual menu grants no permissions. Both the composer and the server enforce access. Draft text survives save errors. Local files keep review in the browser until explicitly exported; hosted artifacts use the portal. Copying review context does not send it to an agent or resume a session.

## Listen to a document

**Listen** is the fourth dock tool (after Comments, Share and Preferences). It offers **Listen to the entire document**, **Read selection**, **Choose where to read**, and **Show player**. The player has pause/resume, stop, speed, voice and reading-style controls. Narration requires a configured provider and explicit confirmation in the trusted portal. Closing it stops speech. Opening another dock menu hides the player; Show player brings it back without restarting. Nothing plays on load, voice discovery, preference changes or navigation.

Select editorial text, then choose Read selection. A cloned range preserves exact start/end offsets across blocks; controls inside that range are excluded. Selected text, links, fields and code retain the native context menu. Shift + right-click also retains it. Ordinary content offers Comment here (subject to existing permissions), Read from here and Read this section. Context Menu / Shift + F10 work on focused content. Choose where to read temporarily makes visible editorial blocks keyboard reachable; Enter or a tap opens the same reading actions, and Escape cancels. Mobile long-press is unchanged.

Speech follows DOM order, not visual columns. Headings, prose, lists, captions and table cells are read once; table captions, headers and cells follow their source order (no inferred headers for complex merged cells). Navigation, controls, comments, editable content, hidden/inert content and `[data-speech-skip]` are excluded. Full/section reading skips code; explicitly selecting code reads its literal text. The controls explain this omission. Charts are not interpreted and image pixels are not transcribed. Use semantic captions or explanatory prose for those surfaces.

Known generated chapter/presentation pages (`main.multipagina > .pagina`) are included in complete reading even when inactive; the existing chapter navigation reveals each page when reached. Other hidden content remains excluded. Manually switching a page stops reading. Section reading uses the closest section/article, or the editorial root when neither exists. Read from here starts at the target block, not an inferred word under the pointer.

The current block gets an outline/background without wrapping or rewriting text. Speech does not scroll within a page or animate the highlight; moving to another generated chapter uses its existing navigation. It respects existing theme tokens and works with reduced motion. A document is split into fragments of at most 1,200 characters, generated one at a time. Voice/style are fixed by the confirmed reading; speed changes playback rate. Stop, page changes and iframe navigation invalidate late callbacks and clear the highlight.

### Support and privacy

| Surface | Behavior |
| --- | --- |
| Hosted current artifact | Injected shared controls use the parent for confirmation and same-origin neural audio. Requires verified identity, version access and an enabled provider. |
| Hosted legacy HTML | Same controls and parent audio; existing contextual comment/picker behavior is preserved. No change to source HTML is required. |
| Newly generated standalone HTML | Controls explain that neural narration requires the Margen portal. No embedded credentials, external synthesis or device fallback. |
| Older downloaded standalone HTML | Unchanged until regenerated. |
| Static preview, PDF, script-disabled embed | No narration. Native React recipe previews are not a document reader. |

There is no autoplay or silent Web Speech fallback. Missing configuration, denied access, quota exhaustion or provider/playback failure has an explicit state. Narration sends the exact approved editorial text to the configured external provider; it is not an offline feature. Provider choice and quality remain unvalidated pending the [audition and operational gate](neural-narration.md). That document covers source fidelity, language/style handling, quotas, streaming, cancellation, cache/access/deletion, configuration and official provider research.

The iframe sandbox/CSP remains unchanged. Keys stay on the backend, audio stays in the parent, and the bridge only exchanges proposed text/controls and playback state. Review/private notes remain excluded. No microphone permission is requested. This work adds no visit analytics.

### Verification

- `npm run check`: extraction/selection, chunks, parent confirmation, Unicode offsets, stale navigation/session responses, pause/cancel, absent provider, exact-text matching, incomplete audio and existing reader controls.
- `.venv/bin/python -m unittest portal.test_narration -v`: disabled configuration (including Python `-O`), exact source/language/SSML escaping, access, quota reservations/concurrency, cancellation during provider opening, purge during streaming, truncation and cache. Providers are mocked; no network or consumption.
- `.venv/bin/python scripts/test_reader_speech.py`: standalone unavailable state; hosted current/legacy bridge with real parent controller and HTML audio using a synthetic WAV; chapter transitions, selection/native menu, keyboard/pickers, comments/share/preferences, 320/390/1280 px, Kaira light/dark, reduced motion and unchanged block geometry.

Chromium 145 on macOS exercised actual HTML audio playback/pause/resume/stop in the parent while the iframe retained its sandbox. The WAV has no neural speech and demonstrates no voice quality. Narrow viewports are emulation; physical mobile, Safari and Firefox remain release checks. The [before](assets/reader-speech-before.png) and [after](assets/reader-speech-after.png) captures use only the [synthetic fixture](../examples/content/reader-speech.html), with no customer/account data. The after capture uses a mock provider and is UI evidence only.
