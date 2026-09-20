# Margen design system

Creators browse documents and revisions throughout a working day on desktop and mobile. The interface follows their light/dark preference; previews retain the document's identity.

## Visual language
The administrator uses Geist, 11–13 px labels, 15 px card headings and 28 px page headings. Instrument Serif is reserved for the wordmark. Warm OKLCH neutrals and a terracotta accent are defined in `portal/static/library.css`. Use a second surface for navigation and selection, subtle 1 px borders, 8 px controls and 14–16 px floating panels.

The reader inherits document tokens. Its three-tool dock contains Comments with the count on its speech bubble, Share, and Preferences, in that order. See [reader controls](reader-controls.md) for contextual actions and point anchoring. Comments use a compact writing surface with author, privacy and send; optional type, session and anchor context are disclosed. Appearance uses a 400 px panel with a searchable single-column theme list, independent mode control and separate typography/sound tabs.

## Composition
Desktop navigation is 226 px; below 850 px it becomes horizontally scrollable. Gallery, list and table share library search and permissions. Knowledge graph, Visits and My work are dedicated destinations with project scoping. Wide tables scroll locally. Group related table actions in one perimeter; keep their names. Do not place creator management inside shared document content.

## Interaction
Use 120 ms color/surface transitions, reduced motion, explicit focus and 44 px main reader tools on mobile. Hover must not be required. Menus remain within the viewport; focus returns to the invoking control. Previews are isolated static frames loaded near the viewport. Graphs retain keyboard controls and a list alternative.

[Interface direction](interface-direction.md) records rationale and references. [Tables and mobile](mobile-and-tables.md) defines data behavior. The account UI uses external CSS under a strict CSP; do not relax it for cosmetic changes.

## Workspace navigation

[Workspace experience](workspace-experience.md) documents the dedicated graph, inline creator work and aggregate visit metrics. Keep graph controls progressively disclosed, preserve the viewport on selection, and use a readable source inspector. Search results show title, space and a text excerpt with arrow-key navigation.
