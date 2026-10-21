# Editorial reference and adaptation

The original inspection of [cmrg.me](https://www.cmrg.me/) was performed on September 13, 2026 with Orca browser tools. The evidence inventory is [reference.json](../tests/evidence/reference.json). It covered the current sitemap's 16 routes, their DOM and computed geometry. External destinations and the historical v1 site were outside that inspection.

Observed patterns included serif headings, handwritten marginal notes and underlines, article grids, an attention treemap, reading contents/progress, code blocks, timeline, horizontal photo galleries, shelf objects and small sound interactions. Full-page screenshots repeated the first viewport and were not accepted as complete visual evidence; viewport captures and DOM measurements supported the review.

## Adaptation

Margen uses an editorial reading grid, restrained dotted/fading frames, inline evidence and marginal annotations. Wide figures remain siblings of text blocks. Tables and charts retain accessible source values. Handwritten motion starts when seen, respects reduced motion and uses the approved font/audio assets. Gallery captions stay within images, with native scrolling and a drag affordance.

The library adds executive evidence, portable review, typed tables, themes and permission-aware hosting. These are independent product decisions, not features attributed to the reference. No claim of pixel-perfect equivalence is made. Do not reproduce personal photographs, commercial covers or private account data as public fixtures.

Fonts and approved audio have separate provenance and licenses under `licenses/`, `packages/core/assets/` and `tests/evidence/`. Keep original sound levels, pitch and duration where documented; synthesized replacements should not be described as the original recording. A measured Web Audio graph does not prove perceived sound quality.

## Validation

Inspect actual content at desktop and narrow widths, not only isolated samples. Check line wrapping, local scrolling, margins, focus, keyboard navigation, reduced motion, touch access, printing and no-JavaScript alternatives. A decorative fade must not obscure the sole copy of a conclusion or evidence. See [advanced components](advanced-components.md) and [interface direction](interface-direction.md).

## October 21 fidelity audit

The follow-up inspected all 16 current routes at 1440, 768 and 390 CSS pixels. The reduced, text-free measurements are in [the October evidence](../tests/evidence/editorial-reference-2026-10-21.json). Inspection of the public DOM/assets identifies a Next.js/React site, Tailwind utilities, React Aria controls and Shiki/rehype code output. Those observations do not establish exact dependency versions or reproduce the site's source repository.

The shared library now uses the measured reading geometry: 528 px prose, 1024 px broad figures, 24 px mobile gutters, 768 px desktop code, 15.5/24.025 px body type and 36.4/43.68 px mobile titles. Code labels stay visible; line numbers preserve blank rows; text marks survive highlighting; copying preserves source text. The code surface blurs the index behind it by 12 px. Its dashed strokes extend and fade independently of the text. Keyboard focus brings the index forward, so overlap cannot prevent navigation.

Paragraphs, headings and section boundaries use explicit 16/24/8/32 px rhythm. Archive entries are a single reading column; card grids use one/two/three columns at 640/1024 px with 8 px gaps and 16 px padding. Timeline, shelf, project titles and callout density use separate measured scales. Photo tracks keep 232 px images, 12 px vertical clearance and edge fades that follow native scroll; focus and reduced transparency remove those fades. Desktop reading ticks align at 32 px from the viewport edge and 128 px vertically.

`packages/core/styles/editorial-reference.css` is the source of the marked CSS block. `scripts/build.py` also emits hosted assets. The render-only `refresh_editorial_reference` helper recognizes real `.hoja` documents, removes older marked reference CSS and refreshes only the explicitly identified core code and editorial-pieces scripts. It leaves source revisions, custom scripts, literal examples, standalone applications and presentation roots intact. The portal must invoke that helper when rendering; shipping library files alone does not update existing hosted documents.

### Fidelity limits

This is measured reconstruction, not a verified 100% clone. The original serif is **Editorial New**; the distributed library retains **Instrument Serif**, so glyph shapes and wrapping still differ. No proprietary font was copied. Reader-selected fonts, palettes, comfortable reading, author-owned layouts and presentation canvases retain their purpose. The local conservative code tokenizer is not Shiki and does not produce identical syntax colors for every language. The website's mobile navigation/footer reveal is a separate composition from Margen's review/preferences dock. Personal photographs, covers, site identity, guestbook data and newsletter services are not fixtures or library features.

Reference performance was sampled in isolated, unthrottled desktop Chromium contexts: home LCP 888 ms / CLS 0.000053; article LCP 460 ms / CLS 0.000265, with one observed 110 ms long task. These are laboratory observations, not field Core Web Vitals or INP. They do not establish that either implementation is faster. The local reading fixtures work offline with embedded fonts, local highlighting and no additional frontend framework.

### Reproducible checks

Run `python scripts/test_editorial_reference.py`, `python scripts/test_editorial_flow.py`, `python -m unittest portal.test_reader_style` and `npm run check` in the documented Python/Node environment. Browser checks cover 300–1440 px, geometry, exact clipboard text and denied-clipboard selection fallback, literal HTML safety, blank lines, highlight preservation, repeat initialization, print, reduced motion, no JavaScript, keyboard focus, gallery scroll edges, reading preferences and upgrades of older rendered copies. Regression thresholds follow the measured rhythm; they still reject touching headings and component overflow.

### Website composition

The `web-shell` recipe (`sitio-editorial`) now supplies the separate website topology: top desktop navigation, bottom mobile navigation, direction-aware 2000 ms fade/blur, a footer behind the main surface and masked edge blur. The full-page [offline demo](../examples/generated/editorial-web.html) uses a real main landmark and one h1; the catalog specimen uses a bounded scrolling region. At 1440 px navigation is 1024 px wide at x=208/y=16; at 390 px the 342 px navigation ends 16 px above the viewport bottom. The hero begins at y=96. Keyboard focus immediately restores navigation and raises footer links; reduced motion keeps navigation visible. The original site content and service integrations are not reproduced.

Apply this composition explicitly to a web page. Standard documents keep their review/preferences dock and chapter controls rather than acquiring a competing site menu. `scripts/test_editorial_web.py` verifies both the standalone and embedded variants, footer overlap/reveal, hash focus, print, no-script and zero external requests. `editorial-reference.css` uses a CSS scope boundary for `[data-ritmo="propio"]` and `[data-presentation]`, including the boundary node itself; older browsers without CSS scope keep the baseline library rendering. Hosted refresh ignores inert template/noscript content when finding a document, module or style insertion point.
