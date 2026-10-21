# Community themes and components

The portal's **Temas y componentes** view lets verified users create and share without a GitHub account or pull request. Code contributions remain a separate path under **Developers**.

## Create and use

- Create a theme by selecting ten colors for each light/dark palette and separate heading/body fonts. The six font families are Geist, Instrument Serif, Literata, Geist Mono, Manrope and Source Serif 4. Fonts are embedded; reading does not contact a font service.
- Create a static editorial card, ordered steps or vertical flow diagram from text fields. Up to twelve lines become blocks. The diagram retains a complete accessible text list beneath its abbreviated node labels.
- Save privately, share an unlisted link immediately, or request inclusion in the public catalog. Sharing exposes the source and profile name after explicit confirmation. Only catalog inclusion requires administrator review; neither path requires a PR.
- Create a private artifact from a theme or static component. Applying a theme to an existing owned artifact prepares a draft revision; the reader publishes it explicitly. Document identity, current published version, comments and access remain unchanged until publication.
- **Crear mi versión** makes an independent copy. Visual designs retain their fields. Components without visual metadata expose a clearly labeled source editor. License, source URL and credits are retained.

The initial catalog includes sixteen bundled themes and eighty-nine component recipes. Reuse from this portal is deliberately static: supported text, tables and SVG. It does not install a recipe's JavaScript, generate interactive charts or enable third-party extensions. Use the full library recipe with an agent for its complete behavior. This distinction appears before the reuse action.

## Visibility and review

A private creation is visible only to its owner and administrators. Unlisted creations are accessible to anyone who has the link but are absent from the public catalog. Anyone can browse approved catalog entries. Only verified accounts can save, favorite or create artifacts.

Owners can revoke a link or request review. Admins approve or request changes only for author-submitted pending entries; approving a withdrawn creation requires a new author request. Administrative decisions are logged and checked against a revision number to reject stale actions. Revoking a source link does not remove independent copies or already-created artifacts.

Packages are immutable versions. The visual editor creates a new copy rather than overwriting the original. Source upload supports explicit semantic versions. Each account can have ten draft/pending creations; retiring one frees a slot. Catalog and account lists currently expose the most recent 200 community entries with a truncation notice.

## Data and isolation

Themes contain only validated hexadecimal palettes and allowlisted typography IDs, never arbitrary CSS/JavaScript. Community HTML/SVG is rebuilt through a positive grammar in `portal/community_markup.py`, with balanced tags and escaped text. It excludes scripts, styles, URLs, embedded documents, event handlers and custom runtime attributes. The original package remains available for download as source, not for execution.

Previews use sandboxed same-origin response URLs with their own restrictive CSP. Unsaved previews require their owner's verified session, expire after five minutes, and live only in a bounded in-memory cache (four per owner, 128 total). Restarting the service discards previews, not saved creations. The portal CSP is unchanged.

Three additive tables store submissions, review decisions and favorites. Existing artifact publishing handles storage, ownership, optimistic version checks and private defaults. No dependency or external service is added. Package exports use the upload schema so download/edit/reupload works.

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
