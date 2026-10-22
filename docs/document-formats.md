# Documents, chapters and presentations

Margen supports three native HTML formats through the same generator, company identity, components and review runtime. Articles and presentations are different authored deliverables. They share collaboration infrastructure, not a reader conversion switch. Chapters organize a long document; they are not automatically slides.

| Format | Use it for | Behavior |
| --- | --- | --- |
| `document` | A memo, article or short report | One continuous page with contents and reading progress |
| `chapters` | Long reports, documentation and evidence appendices | Page navigation, per-page contents, stable deep links and browser history |
| `presentation` | A live discussion or executive briefing | Slide navigation, overview, keyboard controls and printable pages |

If omitted, format follows the source page count. A single source page can still be a presentation. `document` rejects multiple source pages instead of silently discarding them.

## Choose the deliverable before writing

```json
{
  "title": "Operational review",
  "document_id": "operations-review",
  "format": "chapters",
  "pages": [
    {"id": "decision", "title": "Decision", "content": "decision.html"},
    {"id": "evidence", "title": "Evidence", "content": "evidence.html"},
    {"id": "next-steps", "title": "Next steps", "content": "next-steps.html"}
  ]
}
```

```bash
python3 scripts/create_artifact.py --config /project/review.json --project-root /project --output /project/review.html
python3 scripts/create_artifact.py --config /project/slides.json --output /project/briefing.html
```

English configuration keys are canonical for new work; existing Spanish aliases continue to work. A separately published briefing gets a distinct document ID. A new revision of the same briefing keeps its existing ID and stable page/section IDs. A slide deck needs its own slide content and configuration. Do not reuse article prose and relabel it as a presentation.

## Dates, author footer and reactions

These options are explicit. The generator never infers a date from the build time or from file metadata, and it never adds an author's networks to other documents.

```json
{
  "date": {"published": "2026-10-01", "updated": "2026-10-22"},
  "footer": {
    "author": "Ana Autora",
    "note": "Writes about reading and data.",
    "links": [{"label": "Site", "href": "https://ana.example/", "detail": "projects and notes"}],
    "platform": true
  },
  "reactions": false
}
```

- `date`: `YYYY-MM-DD` or `{"published", "updated"}`. Invalid calendar dates, other formats and an update earlier than publication are rejected. The header shows `<time datetime>` under the title, in the measured mono 13.7 px style. A page may carry its own `date`; otherwise the document date appears on the first page only. `--date` sets it from the CLI. Historical documents keep no date unless one is supplied from a real record.
- `footer`: `author` (≤120 characters), `note` (≤280), up to eight `links` with `label` (≤60), `href` and an optional `detail` (≤80). Links accept only `https://` without credentials or `mailto:` with an address. Text is escaped and links carry `rel="noopener noreferrer"`. `platform` (default `false`) adds a separate “Hecho con Margen” line; authorship and platform never share a sentence. Without `footer`, no footer is generated. Presentations reject `footer` and `reactions`; author a closing slide if one is wanted. On a fine pointer at ≥1280 px, link details start blurred and clear on hover or focus.
- `reactions`: `true` adds three icon buttons (useful, return later, made me think). Choices are stored only in that browser under the document ID. No counts are displayed or shared, and the group says so. Print omits it.

## Presentation controls

- Previous/next buttons, a slide counter and an overview of titles and summaries.
- Arrow keys, Page Up/Down, Home and End when focus is outside interactive controls.
- Shortcuts do not interrupt typing, code, table controls, dialogs or point-comment mode.
- No Read/Present toggle: the reader cannot change the artifact’s authored format.
- Fullscreen appears only where browser/embedding policy supports it. A hosted sandbox may not offer it.
- Small screens retain readable type and natural vertical scrolling. Dense content is not scaled down to force a fixed canvas.
- Print CSS includes every slide, with landscape pages and page breaks. Long content can span printed pages; inspect the PDF before sending it.

Speaker notes are not private merely because they are visually hidden. Keep confidential presenter material in an authorized private note or a separate restricted document. HTML comments, themes, animation and interactive tables do not become native Office features in an export.

## Composition

A slide should advance one decision or claim. Prefer a conclusion, relevant evidence, comparison or next action over a page of small bullet text. Keep source, date, unit and caveats with the evidence. Put long tables and operational detail in chapters or appendices, while preserving their links. Do not invent figures to fill a slide.

The runnable samples are [chapter report](../examples/generated/project-chapters.html) and [presentation](../examples/generated/project-presentation.html), authored independently under [the example project](../examples/content/project-formats/presentation.json). All sample business content is illustrative.

For editable Office output, advanced presenter workflows or publication-quality pagination, see [the evaluated tools and integration boundaries](presentation-ecosystem.md). Those external exporters are not installed or bundled by this release.

## Existing presentations

Publish an existing HTML deck directly with `scripts/publish.py publish --file deck.html`. The portal adds the scoped collaboration toolbar and contextual review bridge. It does not run the article generator, replace the deck navigation, choose another font, or add a theme selector when the original has no appearance system. Preserve slide IDs, assets, aspect ratio, layout and existing keyboard behavior. The toolbar must not inherit broad `nav` positioning rules or add body padding to a foreign canvas.

Inspect the actual deck before changing it. Scroll-based slide canvases, paged decks and approval storyboards are distinct layouts, all supported as existing HTML. Test comments on text and visuals, keyboard behavior while typing, and the original navigation. Publishing HTML does not add native PowerPoint editing or change hosted sandbox restrictions.

## Original PDF and PowerPoint files

`portal/formats.py` defines capability contract 1 for documents, chapters, presentations, authored boards, PDF, PPTX and independent HTML. An authored board is preserved as supplied; there is no built-in board editor. Office originals are downloads, not browser-editable documents.

```bash
python3 scripts/import_document.py report.pdf --output report.html --document-id report-2026 --title 'Report'
python3 scripts/import_document.py briefing.pptx --output briefing.html --document-id briefing-2026 --title 'Briefing'
python3 scripts/publish.py publish --file report.html --title 'Report'
```

Check `publish.py --help` for account and publication flags. Import creates HTML and an adjacent `.attachments.json` sidecar; the publisher includes the original automatically. Alternatively, upload the generated HTML and original together in the portal. Keep the original named `original.pdf` or `original.pptx` in the generated link. Downloads enforce the artifact and version's permissions. Changing the original creates a distinct version even if preview HTML is identical.

PDF visual previews require Poppler (`pdfinfo`, `pdftoppm`; `pdftotext` adds searchable text). PPTX visual previews additionally require LibreOffice. Without LibreOffice, PPTX imports produce an explicitly labeled textual slide preview, not a claim of design fidelity. No Office converter runs inside the portal; conversion happens on the creator's machine. Limits: 80 pages, 12 MB of original files and the portal's total request limit. Reduce resolution or split large originals. Comment anchors identify preview pages/slides; editing the original still requires its authoring tool.
