# Community themes and components

The portal separates **Temas**, **Componentes** and **Developers**. Themes have their own gallery and visual creator. Components use a searchable, categorized documentation index with an inline example, preview/code controls, HTML copy, usage, dependencies and source download. Visual component creation is a secondary action; creating an artifact is not the component documentation flow. **Developers** contains code templates, package upload, personal contributions and the administrator review queue. Verified users can create visually without a GitHub account or pull request.

## Create and use

- Create a theme by selecting ten colors for each light/dark palette and separate heading/body fonts. The six font families are Geist, Instrument Serif, Literata, Geist Mono, Manrope and Source Serif 4. Fonts are embedded; reading does not contact a font service.
- Create a static editorial card, ordered steps or vertical flow diagram from text fields. Up to twelve lines become blocks. The diagram retains a complete accessible text list beneath its abbreviated node labels.
- Save privately, share an unlisted link immediately, or request inclusion in the public catalog. Sharing exposes the source and profile name after explicit confirmation. Only catalog inclusion requires administrator review; neither path requires a PR.
- Copy component HTML or download its source package. The existing API can still create a static component artifact, but documentation does not offer this as its primary flow. Create a private artifact from a theme. Applying a theme to an existing owned artifact prepares a draft revision; the reader publishes it explicitly. Document identity, current published version, comments and access remain unchanged until publication.
- **Crear mi versión** makes an independent copy. Visual designs retain their fields. Components without visual metadata expose a clearly labeled source editor. License, source URL and credits are retained.

The initial catalog includes sixteen bundled themes and eighty-nine component recipes. Bundled chart, analytics and relationship examples run reviewed local modules selected at build time in `developers-runtime.json`. Other examples and all community previews remain static. Copying HTML does not install dependencies; the documentation lists them and links to the complete library recipe. Artifact reuse through the existing API remains static.

## Visibility and review

A private creation is visible only to its owner and administrators. Unlisted creations are accessible to anyone who has the link but are absent from the public catalog. Anyone can browse approved catalog entries. Only verified accounts can save, favorite or create artifacts.

Owners can revoke a link or request review. Admins approve or request changes only for author-submitted pending entries; approving a withdrawn creation requires a new author request. Administrative decisions are logged and checked against a revision number to reject stale actions. Revoking a source link does not remove independent copies or already-created artifacts.

Packages are immutable versions. The visual editor creates a new copy rather than overwriting the original. Source upload supports explicit semantic versions. Each account can have ten draft/pending creations; retiring one frees a slot. Catalog and account lists currently expose the most recent 200 community entries with a truncation notice.

## Data and isolation

Themes contain only validated hexadecimal palettes and allowlisted typography IDs, never arbitrary CSS/JavaScript. Community HTML/SVG is rebuilt through a positive grammar in `portal/community_markup.py`, with balanced tags and escaped text. It excludes scripts, styles, URLs, embedded documents, event handlers and custom runtime attributes. The original package remains available for download as source, not for execution.

Previews use sandboxed response URLs with their own restrictive CSP and an opaque origin. Only trusted bundled IDs can select runtime sources; those frames allow scripts with exact SHA-256 CSP hashes, without `allow-same-origin`, network access or external scripts. Community packages cannot provide runtime metadata, and still receive a script-free sandbox and positive-grammar sanitization. Unsaved previews require their owner's verified session, expire after five minutes, and live only in a bounded in-memory cache (four per owner, 128 total). Restarting the service discards previews, not saved creations. The portal CSP is unchanged.

Three additive tables store submissions, review decisions and favorites. Existing artifact publishing handles storage, ownership, optimistic version checks and private defaults. No dependency or external service is added. Package exports use the upload schema so download/edit/reupload works.

Direct routes are `?view=themes`, `?view=components` and `?view=developers`. Existing `?view=developers&item=ID` shared links still resolve, including unlisted contributions. Components can also link directly with `?view=components&item=ID`.

## Build and verify

`python3 scripts/build.py` regenerates the portal catalog, CSS/font bundles and document shell when the portal source directory exists. The portable library does not require the portal. Rebuild community fonts using `scripts/community_fonts.py`; provenance and verification hashes are in `tests/evidence/community-fonts.json`, with complete OFL notices under `licenses/`.

```sh
python3 scripts/build_developers.py
python -m unittest portal.test_developers
npx vitest run portal/static/developers.test.ts
python scripts/test_community_marketplace.py
```

Browser acceptance requires Playwright Chromium and the portal test dependencies. It proxies HTTPS requests into a disposable FastAPI fixture, checks the actual portal CSP, creation/sharing/reuse, mobile widths, typography and reader controls, and adversarial SVG in a generated artifact. It never uses production accounts or content.

Before deploying, back up the persistent database/content volume and retain the previous image. Portal deployment is independent of portable skill updates. Rolling back code leaves the additive community tables intact.
