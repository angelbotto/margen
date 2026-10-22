# Design belongs to the document

Margen has two supported paths. Choose one deliberately; installing the skill does not give it permission to redesign uploaded work.

## Compose with the library

Use `scripts/create_artifact.py` with the portable library's registry, recipes, fonts, styles and runtime. The same package is shared by Codex, Claude and Hermes. Components depend on the registry's declared modules; the generator includes what the document needs. Themes supply semantic tokens and typography, while the shared styles own spacing, code gutters, responsive behavior and accessible controls.

The editorial reader defaults to 33rem (528px) prose, 48rem (768px) code, 64rem (1024px) wide figures and 24px mobile gutters. These are reference defaults, not a mandate for presentations, boards or an author's own HTML. A deck keeps its slide navigation and a board its canvas. Do not patch individual documents to repair a shared component.

Use author-supplied publication dates and identity. A footer is optional document content: omit `footer` for none, or provide `author`, `note` and `links`. Platform credit is an explicit `platform: true` choice. Do not insert social accounts, a product manifesto or an article footer into a presentation without the author's instruction.

```json
{
  "footer": {
    "author": "Equipo de investigación",
    "note": "Preguntas y fuentes adicionales",
    "links": [{"label": "Contacto", "href": "mailto:equipo@example.com"}],
    "platform": false
  }
}
```

The portal's save and like actions are reader/account features. They are separate from author content and from standalone local reactions. Standalone HTML does not silently acquire a shared database.

## Bring your own HTML

The portal's file importer accepts HTML without Margen's classes, components or metadata. It adds a stable document ID when one is absent, and preserves authored markup and styling. It does not run the document through the generator or replace it with a theme. Network access and account access remain bounded by the reader's sandbox and Content Security Policy; a full application requiring authenticated fetches is not a static artifact.

PDFs retain their original file and receive a page preview. ZIP imports are static packages, never build jobs: no dependency installation, server functions or uploaded executable commands. The importer reports unsupported structures before publication. See [upload contract](upload-contract.md) for exact limits and rejection rules.

## Deliver and update together

`scripts/build.py` synchronizes library assets, portal preview assets and examples. `scripts/package.py` includes the skill, component recipes/registry, theme tokens, styles, runtime, fonts and validators in one checksummed package. Hosted updates additionally use a signed release manifest and monotonic version sequence. Installations preserve user connection settings outside the library.

Test a change at its source, regenerate shared outputs and verify the packaged installation. Updating the library governs subsequent generation; it does not overwrite saved HTML. Portal runtime refresh targets explicitly marked Margen modules, not arbitrary author CSS. See [installation](installation.md) and [contributing components](contributing-components.md).
