# Compose with Margen

Margen is a portable HTML/CSS/JavaScript library and an agent skill. Its React package offers reusable product components; a published artifact does not require React. Choose components to serve the argument rather than filling a catalog checklist.

## Start with the reading task

Name the audience, question, evidence and desired next action. A short decision memo can remain a single page; an extensive report can use chapters with their own contents. Separate an executive conclusion from evidence and appendices while keeping every important limitation near the claim it qualifies.

Use the component registry and `scripts/catalog.py --id ID` to inspect recipes, dependencies and limits. The interactive guide is `examples/generated/guide.html`. The workbench provides synthetic logistics, finance and product examples. Numeric data must be real, derived transparently or explicitly labeled illustrative.

## Useful compositions

- Executive report: decision or conclusion, highlights/lowlights, evidence table/chart, risks, alternatives, owners and next steps.
- Article: thesis, grounded examples, marginal questions, definitions, references and related reading.
- Logistics: delivery summary, exceptions, route or fleet view, record explorer and operational limits.
- Finance: source and period, comparable units, reconciliation or waterfall when mathematically appropriate, assumptions and missing evidence.
- Technical documentation: exact code, terminal evidence, architecture/sequence explanation, warnings and reproducible steps.
- Prototype: problem, declared local preview, device/aspect controls, annotated changes and review questions.

## Rhythm and hierarchy

Text stays within 35rem; evidence can expand to 62/76rem. Use wide figures as siblings of narrow reading blocks. One outer dotted frame is enough. Alternate explanation, evidence and interpretation; do not replace all structure with cards. Use left/right marginal annotations for nuance, keeping critical conditions in normal text. Animation should reveal a brief secondary note when seen, with a small replay control.

## Data and interaction

Declare source, date, unit, denominator and aggregate scope. Avoid summing ratios or averaging averages without weights. Tables preserve row/cell IDs and mobile record views. Graphs require accessible values; geography requires a list/table alternative. Simulations must be labeled. Never invent results to showcase a component.

Use the shared dock and existing controls. Prefer grouped table actions, compact comment composition and progressive appearance settings. Keep creator management out of the document. Code copy buttons need clear success/fallback states; examples do not execute merely because they look like a terminal.

## Formats and project identity

Use [project profiles](project-identity.md) for company identity and preferred appearance. Choose [document, chapters or presentation](document-formats.md) for the reading task. Preserve the same source IDs across revisions, and use separate document IDs for separately published report and briefing deliverables.

## Finish

Generate with the canonical contract, validate, inspect browser behavior and preserve the document ID during revisions. Follow the saved publishing preference and deliver the appropriate published or draft URL. The skill's language is English; write the artifact in the user's requested language and voice. See [executive voice](executive-voice.md), [artifact contract](artifact-contract.md), [mobile tables](mobile-and-tables.md) and [component playbook](component-playbook.md).

## Marginal voice

Use the main column for the argument. A left note can challenge an assumption; a right note can interpret evidence or ask the next question. Alternate only when the content warrants it. Keep each annotation short and adjacent to its anchor. A line, bracket or underline points to a precise phrase. Animate once as it enters view; reveal replay on hover and keyboard focus, keep it discoverable on touch, and respect reduced motion. Do not animate essential evidence away.

## Reader controls

Mount one shared dock. Comments, Share and Preferences have distinct purposes. Reader preferences remain separate from creator management. Preserve comment context, version and session when exporting feedback; personal notes stay private unless explicitly included by their author. Keep the composer short, disclose metadata on request, and return focus after closing.

## Visual voice

Choose a family for the material: Editorial for narrative, Liftit for logistics, Tikin/Catabum for their respective brands, Blueprint for conceptual architecture and Hacker for technical evidence. Linear and Modern support compact product documentation. Light/dark/system mode is independent. Use consistent typography roles; handwritten annotation does not replace the body face. All families must support the same components and accessible state labels.

## Semantic prose spacing

In standard notes, a plain `<article>` directly inside `.hoja` (or its `.pagina`) preserves the page grid. Its direct `.ancho` and `.amplio` children use the corresponding wider measure. Plain direct sections and explicit `.prosa` sections receive paragraph and heading rhythm; classed components keep their own layout. Presentations are excluded. Keep structured components at these layout boundaries rather than nesting wide tables inside prose.

The shared source is `packages/core/styles/editorial-flow.css`; `scripts/build.py` embeds it in standalone CSS and the portal reader additions. Hosted corrections change rendering, not stored document versions. Reproduce the browser geometry check with `python scripts/test_editorial_flow.py` in an environment with Playwright and Chromium installed.
