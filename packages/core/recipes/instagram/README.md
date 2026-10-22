## Publicación de Instagram

<!-- nota:ejemplo instagram -->

```html
{{EXAMPLE}}
```

**Use and limits:** A card with a permanent «Abrir en Instagram» link; the post only loads after «Cargar publicación». Set `data-embed-kind` to `p` or `reel` and `data-embed-id` to the shortcode (5–40 characters). The frame is `www.instagram.com/<p|reel>/<code>/embed/` without `rd`/`rp` and with `referrerpolicy="no-referrer"`; Instagram's `embed.js` is never loaded, and only its `MEASURE` height messages from that exact frame and origin are read (bounded). Initial height 640 px. Inside the portal the post opens in a portal dialog; standalone or as a local file it mounts in the card. Stories, private, inactive or age-restricted accounts and posts with embedding disabled only open at the source. Caption and author are written by the author (or proposed from oEmbed while authoring, as plain text); provider HTML is never inserted. The «Al cargarlo…» notice (`data-embed-notice`) starts hidden and appears only with the load button. Without JavaScript, offline or in print the card, its text and the source link remain; nothing pretends to play. No remote thumbnails or provider scripts: a poster may only be a `data:` image. Runtime: `packages/core/components/embeds.js` (`MargenEmbeds.init/get/destroy`), styles `packages/core/styles/embeds.css`.
