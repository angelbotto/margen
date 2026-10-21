## Editorial web shell

<!-- nota:ejemplo sitio-editorial -->

```html
{{EXAMPLE}}
```

**Use and limits:** This is a website composition, separate from artifact review controls. The embedded specimen scrolls inside its own region. For a full page, move `web-editorial` and `data-editorial-web` to the document body; use a `main` element for `.web-contenido`. Keep the header, edge decoration, main and footer as siblings. Do not add this shell around a chapter/presentation reader or its comment/preferences dock. `examples/generated/editorial-web.html` demonstrates the full-page topology offline.

Desktop navigation sits at the top; below 640 px it sits 16 px above the bottom safe area. Scroll direction reveals it; keyboard focus always restores it immediately. The footer reveals beneath the main surface. Reduced motion disables directional hiding and animated transitions; reduced transparency removes edge blur. Without JavaScript every link and section remains usable. Keep anchor IDs unique, preserve the skip link and accessible region name, and replace only the illustrative copy and real destinations. This pattern reproduces structure and motion, not the original site's identity or proprietary serif.
