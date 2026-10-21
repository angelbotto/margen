# Interface direction

Updated September 18, 2026. Scope: shared reader, administrator library, portable and React tables, review composer and appearance. This is a code/browser review supported by public references, not a user study or measured productivity claim.

## Diagnosis

The prototype feeling came from accumulated controls with equal visual weight, inconsistent symbols and optional metadata taking over the reading surface. A hierarchy of primary, secondary and quiet actions is more important than corner radius alone. Editorial documents and product controls need distinct but compatible visual registers.

## References

[Figma UI3](https://www.figma.com/blog/behind-our-redesign-ui3/) informed grouping tools and leaving room for the document. [Linear's refresh](https://linear.app/now/behind-the-latest-design-refresh) informed quieter navigation and consistent placement. [Linear comments](https://linear.app/docs/comment-on-issues) informed a writing-first review flow. [shadcn/ui button groups](https://ui.shadcn.com/docs/components/base/button-group) informed related table actions with one perimeter. [NN/g icon usability](https://www.nngroup.com/articles/icon-usability/) supports retaining labels where a symbol is ambiguous. These are independent adaptations, not affiliations.

| Before | After | Why |
| --- | --- | --- |
| Comment type and session always visible | Author, text and send; metadata behind options | Keep writing primary |
| Large theme cards and repeated explanatory labels | Compact searchable list and separate mode control | Scale to more families |
| Disconnected table buttons | Named groups with shared borders and separators | Show related actions |
| Every action equally prominent | Primary, secondary and quiet controls | Make priorities legible |
| Mixed text symbols | Consistent decorative SVG with accessible names | Improve alignment and recognition |
| A provisional project name | Margen with explicit compatibility aliases | Establish one identity without losing work |

## Behavior

The dock contains Comments (including point creation, private notes and its open-thread badge), Share, Preferences, and Listen. There is no duplicate review or More tool. Main mobile tools have 44 px targets. Keyboard focus, arrow navigation and reduced motion are preserved. Tooltips supplement accessible labels. Comment context, optional session and entry type are disclosed; privacy stays visible. Blank submissions are disabled and failed saves retain text. The theme picker keeps the current choice visible in its header even while searching other families.

The portal keeps strict CSP and opaque artifact isolation. Shared reader styles are generated from one source. Stored artifact versions remain immutable; updating source content requires a reviewed revision. Copying context neither sends data to an agent nor changes permissions.

## Brand

The chosen name is **Margen**: **Documents, decisions and context.** The repository, portal identity and canonical skill use it. Legacy configuration paths, artifact IDs, protocol globals, package scopes and download filenames remain compatible. The old skill name explicitly forwards to Margen. See [the migration guide](migration-margen.md).

## Next validation

Observe real users finding a document, commenting on evidence and returning context to an agent. Record hesitation and required steps before adding more chrome. Prioritize explainable graph connections, context-rich review and synthetic visual regression fixtures. Never publish screenshots of production accounts as documentation.


### Review and presentation update

The reader dock exposes Appearance, one writing action, counted Comments, and Share. Privacy is selected inside the composer; existing thread types stay immutable. The count includes open threads visible to the current reader, including their own private notes, and excludes replies/resolved threads. Nearby pins group by position and open every contained thread. Share owns link/access and creator management; there is no generic More dock.

Record explorers support Table, List, Cards and Board. List reduces per-record spacing; Board groups the existing rows by the selected field (preferring a categorical status/team field initially). The portable board shows the current filtered page, with per-lane counts explicitly scoped to that page. React uses its supplied filtered dataset. Both preserve source records and selection. This is a read-only presentation, not drag-and-drop state editing or an inferred workflow. Saved portable views include presentation. Horizontal scrolling stays local to the board; print returns to a table.

## Editorial collaboration toolbar

A compact paper surface, dotted perimeter fading toward the center, ink-colored icons and restrained active underline tie the toolbar to Margen. Keep Comments, Share, existing Preferences and Listen; hide an empty comment badge. Desktop labels sit beside icons, while narrow screens stack them above labels with 44px touch targets. All positioning is scoped and resets inherited `nav` geometry. Foreign decks keep their body dimensions and existing controls. Preferences are available only when the artifact owns an appearance system.
