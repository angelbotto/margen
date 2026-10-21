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

**Listen** is the fourth dock tool (after Comments, Share and Preferences). It offers **Listen to the entire document**, **Read selection**, **Choose where to read**, and **Show player**. The player has pause/resume, stop, speed and voice controls. Closing it stops speech. Opening another dock menu hides the player; Show player brings it back without restarting. Nothing plays on load, voice discovery, preference changes or navigation.

Select editorial text, then choose Read selection. A cloned range preserves exact start/end offsets across blocks; controls inside that range are excluded. Selected text, links, fields and code retain the native context menu. Shift + right-click also retains it. Ordinary content offers Comment here (subject to existing permissions), Read from here and Read this section. Context Menu / Shift + F10 work on focused content. Choose where to read temporarily makes visible editorial blocks keyboard reachable; Enter or a tap opens the same reading actions, and Escape cancels. Mobile long-press is unchanged.

Speech follows DOM order, not visual columns. Headings, prose, lists, captions and table cells are read once; table captions, headers and cells follow their source order (no inferred headers for complex merged cells). Navigation, controls, comments, editable content, hidden/inert content and `[data-speech-skip]` are excluded. Code blocks are announced as code in full/section reading; explicitly selecting code reads its text. Charts are not interpreted and image pixels are not transcribed. Use semantic captions or explanatory prose for those surfaces.

Known generated chapter/presentation pages (`main.multipagina > .pagina`) are included in complete reading even when inactive; the existing chapter navigation reveals each page when reached. Other hidden content remains excluded. Manually switching a page stops reading. Section reading uses the closest section/article, or the editorial root when neither exists. Read from here starts at the target block, not an inferred word under the pointer.

The current block gets an outline/background without wrapping or rewriting text. Speech does not scroll within a page or animate the highlight; moving to another generated chapter uses its existing navigation. It respects existing theme tokens and works with reduced motion. A document is split into fragments of at most 220 characters, queued one at a time. Voice/speed changes apply to the next fragment. Stop, page changes and iframe navigation invalidate late engine callbacks and clear the highlight.

### Support and privacy

| Surface | Behavior |
| --- | --- |
| Hosted current artifact | The render route injects the shared runtime before embedded modules. Speech runs in the existing opaque-origin iframe, using a direct user gesture. |
| Hosted legacy HTML | The same injection supplies Listen and the point picker even without embedded review. Existing toolbar comment actions still use the parent composer. The contextual comment action requires the embedded review runtime. |
| Newly generated standalone HTML | The generator embeds the runtime; no portal, network library or credentials are needed. Voices still depend on the browser/device. |
| Older downloaded standalone HTML | Unchanged until regenerated with this library. |
| Static preview, PDF, script-disabled embed | No voice controls. Native React recipe previews are not a document reader. |

The implementation uses only Web Speech synthesis. It adds no provider, account, server request, microphone permission, analytics or paid integration. Local voices are preferred, then the document language and browser default within that group. The selector labels the browser's `localService` flag as **Local** or **Remote service**. Remote voices may send document text to the browser's voice service. This flag is not a guarantee of offline availability; installations and browser/platform behavior vary. Speech content and voice choices are not persisted by Margen.

The [Web Speech specification](https://webaudio.github.io/web-speech-api/#tts-section) defines voice discovery, `voiceschanged`, `localService`, cancellation and pause/resume. Voice lists may initially be empty. Margen explains missing voices/API and updates when voices become available, without automatically starting. A blocked/erroring engine stops with a retry message; a 12-second startup timeout handles engines that never emit `start`. No automatic retries or silent voice-service switch occur. Native pause/resume and background/locked-screen playback remain platform dependent; Stop and a new reading are the recovery path.

Sandbox, CSP and authorization are unchanged. No speech text crosses the parent bridge. The parent can send the marked `stop-speech` lifecycle message; the iframe accepts it only from its parent. `pagehide` also cancels. The browser's speech engine is outside the document fetch API: `connect-src 'none'` must not be interpreted as a guarantee that a selected remote voice operates locally.

### Verification

- `npm run check`: extraction, selections, chunking, lifecycle, missing voices/API, engine errors/timeouts, keyboard focus and native menu preservation, plus existing tests.
- `.venv/bin/python scripts/test_reader_speech.py`: synthetic file/standalone/hosted/legacy fixtures, chapter advancement and cancellation, real DOM selection, keyboard controls, contextual review, 320/390/1280 px, Kaira light/dark, reduced motion and unchanged block geometry. The speech engine is stubbed for deterministic UI checks.
- `SPEECH_HEADED=1 SPEECH_REAL=1 .venv/bin/python scripts/test_reader_speech.py ReaderSpeech.test_real_device_voice_in_sandbox`: optional audible device-engine check; records actual browser events and explicitly skips devices without voices.

Chromium 145 on macOS was checked with real device voices inside the unchanged sandbox: start/end and pause/resume/cancel were exercised. Narrow viewport tests are browser emulation, not physical iOS/Android validation. Safari, Firefox and physical mobile engines still require a release review on those devices; do not infer cross-browser audio fidelity from stub tests. Additional synthetic screenshots remain local test output. The reviewed [before](assets/reader-speech-before.png) and [after](assets/reader-speech-after.png) mobile captures use only [this fixture](../examples/content/reader-speech.html), with no account or customer data.
