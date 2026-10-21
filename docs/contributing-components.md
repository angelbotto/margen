# Contributing components and themes

A contribution should improve a reader's ability to understand evidence or make a decision. Each recipe has an editable specimen, a manifest and guidance. The generated reference and examples are outputs, not editing surfaces.

For creation without code or a PR, use the portal’s [visual theme and component editor](community-marketplace.md). This guide covers changes to the library source and interactive runtime.

## Edit an existing recipe

1. Find its English folder under `packages/core/recipes/` (for example `bar-chart`). `component.json` preserves its original identifier under `legacyId`.
2. Change `example.html`. Keep semantic structure, stable IDs and illustrative data. Wide figures must be siblings of normal reading blocks, not nested inside a narrow paragraph wrapper.
3. Update `README.md`: when to use it, when not to, required data, keyboard/touch behavior, failure states and limitations. The `{{EXAMPLE}}` placeholder is replaced in the generated reference.
4. If behavior changes, edit the relevant module in `packages/core/components/`. Declare required modules in the component manifest. Reuse base controls instead of copying them.
5. Run the build and applicable checks below. Include desktop and narrow-screen evidence from synthetic fixtures.

## Add a recipe

```bash
python3 scripts/new_component.py --id release-brief \
  --title 'Release brief' --category reports
```

Categories: `publications`, `reading`, `reports`, `charts`, `tables`, `prototypes`, `expression`, `settings`. The scaffolder creates the folder, registers its order/alias and updates the component count. English kebab-case IDs are required and duplicates are refused. Internal category values retain legacy identifiers for compatibility.

Replace the placeholder example and write its guidance before submitting. Metadata now controls chapter placement, labels and dependencies; you do not need to append a new ID to a giant chapter list. Existing chapters remain an editorial navigation choice. Additional runtime modules must be imported into complete library demonstrations where they are needed; test both a standalone artifact and the catalog preview.

Add new React-native components in `packages/react/src/components/`, export their types from `src/index.ts`, and add them to the synthetic showcase when useful. A recipe addition does not automatically create a native React implementation.

## Add or improve a theme

Edit one file in `packages/core/themes/families/`. Each family defines light and dark appearance. `system` chooses between these modes; it is not a third palette. The theme index supplies family order and preserved aliases. Adding a family also requires registering that family in the index and VERSION metadata. Run theme validation and inspect body text, secondary text, code, selection, focus, comments, tables and charts in both modes.

Do not copy licensed brand assets without permission. Keep provenance and terms in `NOTICE`/`licenses`. Brand data belongs in `packages/core/brands`; it is distinct from a generic color theme.

## Source and generated files

| Edit | Rebuilt output |
| --- | --- |
| Recipe `README.md`, `example.html`, `component.json`, recipe index | `docs/components.md`, catalog registry, guide/library HTML |
| Theme family files and index | `themes.json`, theme control markup and demo pages |
| Core JS/CSS and example content/builders | Complete HTML under `examples/generated` |
| Core catalog/styles/modules | `packages/core/src/generated-*` (ignored), package `dist` |
| React TSX/styles | React package `dist` (ignored) |

Generated HTML and the main registry are committed for Python-only users. TypeScript generated data and package builds are not committed. Run the same build twice and check that the second run is unchanged.

## Checks

```bash
python3 scripts/build.py
python3 scripts/validate.py
python3 scripts/test_contract.py
python3 scripts/validate_skill.py
python3 scripts/test_feedback.py
python3 scripts/test_portability.py
node scripts/test_review_store.cjs
node scripts/test_themes.cjs
npm ci
npm run check
npm run build:demo
```

Run relevant portal tests for API, identity, publication, storage or permission changes; see [CONTRIBUTING.md](../CONTRIBUTING.md). Tests should verify behavior or a contract, not duplicate a CSS implementation. Check keyboard access, reduced motion, empty/error states, mobile overflow and both theme modes when your change affects them.

## English filenames, compatible data

New files use English names. Do not rename persisted IDs, CSS classes, JSON keys or published document IDs merely to translate them: migrate the consumers and prove old artifacts/reviews still work. Guidance and artifact content may use the reader's language. A clean file tree must not erase compatibility.
