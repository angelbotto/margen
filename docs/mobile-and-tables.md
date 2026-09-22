# Tables and mobile reading

The document is a reading surface, including on a phone. Do not shrink a desktop screenshot, hide overflowing content at the document level, or add a second toolbar.

## Choose the reading task

- **Compare values across records:** use a semantic table with units in headings, aligned numeric values and local horizontal scrolling. Readers can explicitly choose Table on a phone.
- **Review a record:** interactive tables automatically present cards at 640 CSS px or less. Each field has its column label. Table and Cards are also available on desktop. Both presentations reuse the same cells, IDs, filters and selection; comments never point at a duplicate mobile copy.
- **Explain a conclusion:** put the conclusion and denominator before the table. Do not make the reader discover the argument by filtering.

Portable tables retain pagination (10/25/50/100); cards do not render an unbounded feed. React `DataTable` supports `presentation="auto" | "table" | "cards"`; automatic is the default. React renders the supplied rows and has no pagination/virtualization. Bound its input to an appropriate dataset.

## Readable narrative columns

Long prose should grow rows vertically, not compress category or status labels into fragments. Base table cells use normal word boundaries (`overflow-wrap: break-word`), preserving the intrinsic width of ordinary words. Links and code may still wrap long tokens. Keep local horizontal scrolling when the content needs more width; do not shrink fonts or hide overflow.

For five or more prose columns, put `densa` on `.tabla-caja` (the legacy `table.densa` placement also works). When text lengths differ greatly, declare a `colgroup` with deliberate widths. For a five-column capability comparison, a starting split is 12% identifier, 38% description, 24% explanation, 16% current state and 10% priority. Inspect actual text and adjust; this is not a universal five-column rule. Keep headings and short labels intact, allow paragraphs to wrap, and retain the 58rem dense minimum for local scrolling on mobile. Avoid `overflow-wrap:anywhere` or `word-break:break-all` on every table cell.

## Portable controls

Search stays visible. **Filtros** groups distinct text values (up to 12 per column, excluding the record identifier) with source-dataset counts, plus advanced AND/OR conditions. Selected values within a facet are alternatives. The selected AND/OR mode applies to the conditions, including facets. Remove individual conditions using the chips below the toolbar; clearing filters keeps selected records.

The primary identifier column remains visible for selection and comment references.

**Diseño** groups presentation, ordering, density, grouping, visibility, pinning and width. **Vistas** saves named device-local configurations, including presentation. **Más** contains page selection and CSV export. A selection summary appears only when something is selected and declares how many selected rows are outside the filter. Exporting selection includes those rows; otherwise export covers the full filtered result, not only the visible page. CSV keeps missing numeric values empty.

Distinct-value counts deliberately refer to the complete source dataset. They are not cross-filtered or live counts. A row inspector opens all original fields, including hidden columns. No cell editing or remote data synchronization is implied.

## Compose for a small screen

1. Keep body text readable and full width within the normal gutters. Let titles wrap. Side notes follow their paragraph in the document flow.
2. Keep wide figures at the article level. Tables, code, diagrams and galleries scroll locally when comparison requires their width. Never use `body { overflow-x:hidden }` to hide a bug.
3. Use the standard reader toolbar. Its actions have 44px targets and account for the bottom safe area. On small screens the progress ruler becomes a thin line at the top, away from review controls.
4. Inputs used on a phone should be at least 16px to avoid focus zoom. Menus stay within the visible viewport; row details use a bottom sheet.
5. The fleet canvas fits the mobile viewport. Its projection compensates for narrow aspect ratios; touch orbit/zoom and the textual fallback remain available. Example vehicles are still simulated.
6. Check search, combined filters, empty results, selection across filtering, sorting in Cards, hidden columns, detail, CSV and switching back to Table. Verify the actual iframe/window width, not just a browser resize command's success response.

## Release and migration

Use the current generator to rebuild an artifact from its content. Preserve document, row and cell IDs, publish a draft, then release the reviewed revision. Historical stored HTML is immutable: installing a new skill does **not** retroactively restyle all old documents. The portal's shared reader chrome may update independently.

The native React and portable table adapters share the query model but have different control implementations. The administrator's document table remains its own interface. These improvements do not claim a migration of the administrator to the new record layout.

Try `examples/generated/workbench.html` with synthetic Liftit, Tikin and Catabum records. Mobile layout checks cover 320px and 390px frames and a 768px tablet frame; desktop comparison should also remain usable. Geometry checks complement, rather than replace, visual inspection and real-device testing.


### Review and presentation update

The reader dock exposes Appearance, one writing action, counted Comments, and Share. Privacy is selected inside the composer; existing thread types stay immutable. The count includes open threads visible to the current reader, including their own private notes, and excludes replies/resolved threads. Nearby pins group by position and open every contained thread. Share owns link/access and creator management; there is no generic More dock.

Record explorers support Table, List, Cards and Board. List reduces per-record spacing; Board groups the existing rows by the selected field (preferring a categorical status/team field initially). The portable board shows the current filtered page, with per-lane counts explicitly scoped to that page. React uses its supplied filtered dataset. Both preserve source records and selection. This is a read-only presentation, not drag-and-drop state editing or an inferred workflow. Saved portable views include presentation. Horizontal scrolling stays local to the board; print returns to a table.

## Rich records and column ordering

See [rich table composition](rich-tables.md) for reordered columns, persisted layouts, avatars, media, nested cards and mobile behavior. Scalar values remain authoritative for filtering and CSV.
