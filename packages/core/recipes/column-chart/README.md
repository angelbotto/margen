## Column chart

<!-- nota:ejemplo columnas -->

```html
{{EXAMPLE}}
```

**Use and limits:** Compare amounts across ordered categories (periods, stages) in one unit. Grouped by default; `data-apilado="si"` stacks series when their sum is a real total (counts, money, hours), never for ratios or percentages. Stacking rejects negative values. Up to eight series and 40 categories; long category names are abbreviated in the axis and stay complete in the tip and table. A missing cell is drawn as a flat mark and its column total is reported as incomplete, not as zero. Needs `chart-core.js` before `charts.js`. For many categories or long names prefer horizontal bars.
