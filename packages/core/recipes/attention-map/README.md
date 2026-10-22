## Attention map

<!-- nota:ejemplo atencion -->

```html
{{EXAMPLE}}
```

**Use and limits:** Partition a positive total across 1–40 unique categories with finite nonnegative values up to 10^9. Squarified treemap (Bruls et al.) at the measured width, 380 px tall (320 px below 640 px, laid out in rows); every area is exactly proportional to its value. Labels follow the cmrg.me home map: serif 18 px name and 11.5 px mono value, abbreviated by available area (full, short, minimal or none) and never outside their cell. When the smallest tail would be too small to see or focus, it is grouped into one «Otros (n)» cell whose area is the exact sum and whose tip lists every member; the buttons, status and table still expose each category. Zero stays in controls/table with no area. Arrow keys move between cells, Enter pins the tip, Escape closes it; touch pins on tap. `data-formato="duration_min"` (or `duration`, `duration_h`) shows durations; `data-atencion-modo="particion"` keeps the previous binary layout. Needs `chart-core.js`. No productivity measurement or app connection; prefer bars for precise rankings.
