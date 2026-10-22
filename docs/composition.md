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

Editorial prose defaults to 33rem (528px), code to 48rem (768px), and wide evidence to 64rem (1024px), with 24px mobile gutters. Use wide figures as siblings of narrow reading blocks. One outer dotted frame is enough. Alternate explanation, evidence and interpretation; do not replace all structure with cards. Use left/right marginal annotations for nuance, keeping critical conditions in normal text. Animation should reveal a brief secondary note when seen, with a small replay control.

## Reports need an argument, not just formatted prose

When the request is for a developed report, preserve its depth. A title, several paragraphs and a repeated three-column table are not a substitute for explaining what the evidence means. Plan the reading path before generating: the decision, the supporting evidence, the interpretation, the uncertainty, and the next action. Use chapters when each initiative or evidence family needs its own explanation; keep a brief overview with links to the detail. A requested short memo should stay short.

For each substantive section, explain the situation and consequence, present the relevant evidence, and interpret it. Distinguish current results from proposed targets and historical context. If the source supplies definitions but no observations, build a measurement specification rather than an invented dashboard. Preserve all supplied facts; identify missing baselines, denominators, sources and owners instead of adding fictional numbers to make a chart possible.

Choose a form for the reading task:

| Reader task | Composition |
| --- | --- |
| Compare a few definitions or alternatives | Wide semantic table, descriptive caption, deliberate column widths and comfortable multiline cells |
| Search or inspect a record collection | `data-explorer`, stable row IDs, typed columns, meaningful default view and details for long descriptions |
| Understand a process | `steps` or a sequence diagram, followed by dependencies and failure conditions |
| Judge measured change | Chart with units, period, source and denominator; preserve a table alternative |
| Understand an unknown or historical limitation | Adjacent callout or note; never present an old number as current performance |
| Act on a recommendation | Decision and action list with the real owner, timing and verification criterion; mark unassigned fields |

Do not add charts, filters, cards or length merely to meet a quota. Explain why a component helps the reader. Use the registry's actual recipes and capabilities; do not hand-roll a plain table when the reader needs record inspection. Conversely, a seven-row comparison does not automatically need a data explorer.

### Tables with narrative cells

Put `.tabla-caja` inside a direct `.ancho` or `.amplio` sibling of prose. Do not bury it in a narrow paragraph container. Reserve `.densa` for short scalar cells; paragraphs, measurement definitions and limitations need normal density, a wide description column, top alignment and line wrapping. Preserve complete text and comment anchors. On mobile use a labeled local scroller or the explorer's record view; never shrink all text until a desktop table fits.

Before publication, check the longest cell at 390px and at desktop width, the difference between the overview and detail, and whether every section adds explanation or evidence. Run `validate_artifact.py --strict-composition` on authored reports and address its structural warnings. Passing that check does not establish editorial depth: read the report as its intended recipient.

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

## Shared reading rhythm

All theme families use the same spacing tokens: paragraph 18px, heading-before 36px, heading-after 14px, section 28px and eyebrow 10px. The shared source is `packages/core/styles/editorial-flow.css`; the build embeds it in standalone CSS and the hosted reader. Legacy `.hoja` documents receive the same rules. Hosted corrections change rendering, not stored source, versions or audience.

Plain semantic containers, nested prose, lists and canonical recipe text hosts receive reading rhythm. A plain `<article>` directly inside `.hoja` or `.pagina` preserves the page grid, including direct `.ancho` and `.amplio` figures. Keep wide evidence beside prose rather than inside its text column. Custom classed text containers should include `.prosa`, at any nesting depth. The generator and validator warn about unknown classed prose; `validate_artifact.py --strict-composition FILE` treats these warnings as failures.

Grid/flex components retain their own gaps. Do not add `.prosa` to a layout grid or control group. `data-ritmo="propio"` opts a custom layout and its descendants out of automatic reading rhythm. Inline-styled containers also retain their layout; use an explicit prose child when needed. Data interfaces, navigation and presentations are excluded.

The `editorial-layout` CI job runs these checks on every pull request. From a repository checkout, run `python scripts/test_editorial_flow.py` in an environment with Playwright and Chromium installed. The suite checks all recipe examples at 320/390/1440px, 16 theme families in light/dark mode, nested text, article grids, long identifiers, print visibility, excluded components and hosted stylesheet ordering. A historical downloaded HTML embeds its old CSS; regenerate it with the same document ID to update that offline copy.
