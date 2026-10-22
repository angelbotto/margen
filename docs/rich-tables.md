# Rich record tables

Margen separates a record's scalar data from its visual presentation. The React table uses TanStack Table for column ordering, visibility and selection, Radix Popover for table controls, Radix Avatar for image loading/fallback, and Radix Dialog for the inspector. Its composition follows the shadcn/ui Data Table and Popover patterns, styled with Margen tokens. It does not ship an unrelated grid theme.

Portable HTML uses semantic source tables and progressive enhancement. It supports the same column-ordering workflow without requiring React or a build step for authors. This is a compatibility implementation, not a claim that Radix runs in standalone HTML.

## Reader capabilities

- Search scalar values, combine typed conditions, and select several categorical values.
- Move columns by dragging in the Columns/Design panel or using labeled earlier/later buttons. Arrow controls work with keyboard and touch.
- Hide columns, pin columns, adjust widths, choose density, and save a named local view. Saved views retain column order, visibility, widths, pinning, filtering and presentation. Old views remain readable.
- Export scalar values in the chosen visible-column order. React offers separate exports for filtered and selected records; portable export uses selected records when a selection exists, otherwise the filtered records.
- Show people, images, status indicators and expanded related cards. Rich presentation does not add to totals or create fictitious records.
- Preserve stable row/cell IDs when changing order or presentation. Portable HTML keeps the source cells; reordering does not clone comment anchors.

Saved views are private to the browser and table, not synchronized team views. Column ordering is presentation, not editing the underlying business records. The board remains read-only. React processes the supplied dataset; portable tables are limited to 2,000 source rows and 16 columns. These are not spreadsheet editors or live operational connections.

## React composition

```tsx
import {
  DataTable, TablePerson, TableMedia, TableStatus, TableDetailCard,
} from '@bottifact/react';

<DataTable
  caption="Delivery review · supplied records"
  rows={deliveries}
  rowKey={row => row.id}
  selectable
  inspectable
  persistenceKey="delivery-review"
  columns={[
    { id: 'id', header: 'Delivery', value: row => row.id, mobile: 'primary' },
    { id: 'owner', header: 'Owner', value: row => row.owner.name,
      render: row => <TablePerson name={row.owner.name} src={row.owner.avatar} detail={row.team} /> },
    { id: 'status', header: 'Status', value: row => row.status,
      render: row => <TableStatus tone={row.status === 'Delivered' ? 'success' : 'info'}>{row.status}</TableStatus> },
    { id: 'cargo', header: 'Cargo', value: row => row.cargo.title, width: 225, mobile: 'detail',
      render: row => <TableMedia src={row.cargo.image} alt={row.cargo.description} title={row.cargo.title} /> },
  ]}
  renderExpanded={row => <div className="bf-detail-grid">
    <TableDetailCard title="Manifest">{row.manifest}</TableDetailCard>
    <TableDetailCard title="Follow-up">{row.followUp}</TableDetailCard>
  </div>}
/>
```

`value` controls search, filters, sorting and CSV. `render` controls presentation. Do not put markup into `value`. Use real data for status tones and summaries. `width` is an initial width between 100 and 480 px; readers may change it. `mobile: 'detail'` hides secondary fields in record layouts only when `inspectable` is enabled, so the inspector keeps them accessible. The column named `primary` provides the record heading. Expanded content is read-only display unless the author supplies explicit application actions.

`TablePerson` falls back to initials while its image is unavailable. `TableMedia` falls back to an image placeholder. Image helpers accept HTTP(S), root-relative paths and base64 PNG/JPEG/WebP/GIF. Use meaningful alternative text for informative thumbnails. The React demo uses local, original SVG illustrations loaded through root-relative paths; no real identities or private screenshots are included.

## Portable HTML composition

Use the `data-explorer` recipe (`data-explorador` is the stable runtime attribute). Declare `data-tipo="texto"` on rich text columns and give cells `data-valor` with the scalar value. Explicit types avoid inferring a numeric column merely because every cell has `data-valor`.

```html
<th scope="col" data-tipo="texto">Owner</th>
<!-- In the matching source row: -->
<td data-valor="Ana Rivera">
  <span class="bf-person">
    <span class="bf-avatar"><img src="data:image/png;base64,..." alt="" width="30" height="30"></span>
    <span><strong>Ana Rivera</strong><small>Operations</small></span>
  </span>
</td>
```

The shared rich-content classes are `bf-person`, `bf-avatar`, `bf-media`, `bf-status` (`data-tone`), `bf-detail-grid` and `bf-detail-card`. Put nested read-only cards inside a native `details.bf-inline-detail`; its summary remains keyboard/touch accessible. Embed approved image bytes for offline HTML. The workbench's Liftit section demonstrates this composition with explicitly fictional people, delivery records and package illustrations.

The portable identity column stays available because it owns selection and inspection controls. CSV contains `data-valor`, not image markup, hidden cards or button labels. Keep identity IDs stable when publishing another version.

## Mobile and verification

At narrow widths, records use the card presentation by default; Table remains available for comparisons with local horizontal scrolling. The React toolbar uses two columns at narrow widths, sized touch controls and collision-aware popovers. Secondary fields remain in the inspector. Lists, boards and expanded cards must not create page-wide overflow.

Test 320/390 px, keyboard and touch-compatible controls, light/dark modes, filtered selections, saved views and export order. Do not call this tested on a physical phone unless it was.

References: [shadcn Data Table](https://ui.shadcn.com/docs/components/data-table), [shadcn Popover](https://ui.shadcn.com/docs/components/radix/popover), [Radix Popover](https://www.radix-ui.com/primitives/docs/components/popover), [Radix Avatar](https://www.radix-ui.com/primitives/docs/components/avatar).

## Narrative columns

Column type controls alignment; a last column is not implicitly numeric. Text uses the reading face and left alignment. Portable text fields of at least 140 characters containing whitespace span a complete row in Cards, List and Board, so definitions do not get squeezed beside a short category. Original cells, values, search, CSV and comment anchors stay intact. Hosted Margen documents refresh the marked explorer/model modules and shared table-content CSS; arbitrary uploaded HTML keeps its own styling.
