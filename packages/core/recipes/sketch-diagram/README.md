## Sketch diagram

<!-- nota:ejemplo sketch-diagram -->

```html
{{EXAMPLE}}
```

**When:** Explain a short directed flow in an Excalidraw-like hand-drawn style. Use two or three stages per diagram. Separate an overview, a history example and an agent handoff when each answers a different question. This is a native Margen recipe, not the Excalidraw editor or its file format.

**Source:** Copy `source.json` from this recipe. Schema `margen-sketch/1` requires a unique diagram `id`, `title`, two or three `nodes` with stable `id`, `title`, `body`, and exactly one `transitions` label between each consecutive pair. `note` is optional. Node order is the directed reading order. Labels are plain text, never HTML. Preserve the JSON outside the published HTML for later revisions.

```bash
python3 scripts/sketch_diagram.py --source /path/flow.json --output /path/flow.html
```

Insert the generated figure as a sibling of `.prosa`, then compose the complete document with `scripts/create_artifact.py`. Give every figure a unique ID. Styles are included in the canonical `artifact.css` by `scripts/build.py`; no extra runtime or remote assets are needed. Do not paste a screenshot of the figure.

**Reading and accessibility:** Real HTML text and an ordered list carry the meaning; decorative SVG borders/arrows are hidden from assistive technology. Connections name their destination in reading order. The same DOM reflows vertically below an 820px figure width. Labels retain their CSS font sizes and text wraps instead of scaling or clipping. Light/dark colors follow the current theme. There are no animations or keyboard-only interactions; all content is available without JavaScript. Print uses the vertical flow. No color encodes a required distinction.

**Limits:** This first recipe supports linear flows, not branching architectures, free-positioned canvas editing, numerical charts, Excalidraw import/export, or real-time collaboration. Split larger processes, or select `relationship-map` for an explorable graph. The block editor conservatively preserves this figure as an opaque component; it does not yet expose editable diagram nodes in its slash menu. The source generator fails closed on invalid schema, duplicate IDs, missing transitions and oversize content. Always inspect the actual standalone artifact on desktop and mobile, in light and dark mode. Drawing paths alone do not prove legibility or accessibility conformance.
