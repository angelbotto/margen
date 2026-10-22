## Video de YouTube

<!-- nota:ejemplo youtube -->

```html
{{EXAMPLE}}
```

**Use and limits:** A card with title, channel and a permanent «Abrir en YouTube» link; the player only loads after the reader clicks «Cargar video». Only `data-embed-id` (11 characters `A-Z a-z 0-9 _ -`) is read; the link and the player URL are rebuilt from it. The player is `youtube-nocookie.com/embed/<id>` with `autoplay=1&mute=1` after the click (sound is the player's own control), `referrerpolicy="strict-origin"` and a sandbox limited to scripts, same-origin of the provider, popups and presentation. Inside the Margen portal the document only sends provider + ID and the portal opens its own dialog; as a standalone HTTPS page the player mounts in the card; opened as a local `file://` YouTube rejects the page (error 153), so only the link is offered. If the player gives no sign of life in 8 s the card says so; an iframe load is not treated as playback. Restricted, private or embedding-disabled videos only open at the source. The «Al cargarlo…» notice (`data-embed-notice`) starts hidden and appears only with the load button. Without JavaScript, offline or in print the card, its text and the source link remain; nothing pretends to play. No remote thumbnails or provider scripts: a poster may only be a `data:` image. Runtime: `packages/core/components/embeds.js` (`MargenEmbeds.init/get/destroy`), styles `packages/core/styles/embeds.css`.
