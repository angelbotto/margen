## Heatmap

<!-- nota:ejemplo calor -->

```html
{{EXAMPLE}}
```

<a id="recetas-tablas"></a>

**Use and limits:** Compare intensity across two discrete dimensions. SVG matrix with row and column axes at the measured width; the coloured table stays as the accessible mode. `data-umbrales` declares 3–6 increasing boundaries (2–5 levels), with the maximum included in the final level; without it, boundaries are data quantiles and the legend says so. `data-centro` makes a diverging scale around a declared midpoint. Out-of-domain data produces an error while preserving the source table, never silent saturation. Missing cells are hatched and labelled «Sin dato ≠ 0». Up to 31×31 cells without page scroll: values print inside cells only when they fit, otherwise the tip (arrows move by row and column) gives them. Each cell retains its value; no hidden row-specific scales or gradient encoding.
