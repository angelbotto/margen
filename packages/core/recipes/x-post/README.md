## Publicación de X

<!-- nota:ejemplo x-post -->

```html
{{EXAMPLE}}
```

**Use and limits:** A static editorial card for a post on X: author, handle, date, text, source and an optional `data:` image. It never loads `widgets.js` or an X iframe, so it works offline and inside the portal sandbox. Set `data-embed-user` (1–15 letters, digits or `_`) and `data-embed-status` (digits); the runtime rebuilds the link as `https://x.com/<user>/status/<id>` and ignores the author's `href`. Write text as escaped HTML or build the card with `MargenEmbeds.card({name,user,status,text,date,media,synthetic})`, which uses DOM text only. An invented post must carry `data-embed-synthetic`: the runtime then removes any link and labels it «Ejemplo sintético»; use an impossible handle so it cannot match a real account. Never present metrics or verification you did not check. Without JavaScript, offline or in print the card, its text and the source link remain; nothing pretends to play. No remote thumbnails or provider scripts: a poster may only be a `data:` image. Runtime: `packages/core/components/embeds.js` (`MargenEmbeds.init/get/destroy`), styles `packages/core/styles/embeds.css`.
