# Upload contract: HTML, PDF and static ZIP

`portal/uploads.py` turns one uploaded file into one self-contained HTML version and hands it to the existing `publish()`. Uploads therefore get the same account checks, private default, version history, `expected_current` compare-and-set, format description and sandboxed `/render` as any other publication. Uploaded HTML and JavaScript are never served from the portal origin: only through `/render` (`sandbox allow-scripts allow-downloads`, opaque origin, `connect-src 'none'`, images/fonts/media only as `data:`). Original PDFs go through the existing attachment endpoint (`application/octet-stream`, `sandbox` CSP, version ACL).

Both endpoints require a verified account (portal cookie or agent Bearer token). The portal middleware still applies the `Origin` rule, the 22 MB body limit and the write rate limit.

## `POST /api/uploads/inspect`

Request: `{"name": "site.zip", "data": "<base64>", "entry": "optional/page.html"}`. Nothing is stored.

Response 200:

```json
{
  "kind": "html | pdf | zip",
  "name": "site.zip",
  "title": "Extracted <title>, first <h1>, PDF title or file name",
  "size": 12345,
  "sha256": "…",
  "entry": "index.html",
  "pages": 12,
  "preview": "visual | none",
  "document_id": "existing nota-documento or null",
  "files": [{"path": "css/main.css", "size": 812, "type": "text/css", "role": "entry | page | asset | unused | skipped | original"}],
  "warnings": ["…"],
  "limits": {"upload_bytes": 15728640, "…": 0}
}
```

`entry` is set for ZIP only; `pages` and `preview` for PDF only (`preview: "none"` means the server lacks Poppler and publishing will fail). Every rejection is 422 with `{"detail": "<actionable message in Spanish>"}`; 413 above the body limit; 503 when two PDFs are already being processed.

## `POST /api/uploads`

Request: the same `name`, `data`, `entry`, plus optional `title` (default: inspected title), `space` (default `Personal`), `artifact` (revision target), `expected_current` (required for revisions; compare-and-set: 409 when it is not the current version), `source` (`{agent, session, label, device}`), `mode` (`draft | published`) and, for HTML/ZIP only, `attachments` (`[{name, data}]` PDF/PPTX originals validated by the existing publish rules; link them with `data-margen-original`). `visibility` is rejected: uploads are private; change access from Share.

Response: exactly the publish response `{id, version, url, visibility, state, preview_url}`.

The file is decoded and validated again on publish; an inspect result is never trusted.

## Kinds

| Kind | Accepted | Result |
| --- | --- | --- |
| HTML (`.html`, `.htm`) | UTF-8, at most 15 MiB | Stored byte for byte. Only `<meta name="nota-documento">` is inserted after `<head>` when absent. No generator, theme or restyling. |
| PDF (`.pdf`, `%PDF-`) | At most 12 MiB and 80 pages | Page images (JPEG, 1400 px up to 20 pages, 1000 px above) plus each page's text, `margen-format=pdf`, and `original.pdf` as a downloadable version attachment. |
| ZIP (`.zip`) | Compiled static site | Local assets of the entry page are inlined as `data:` or inline `<style>`/`<script>`. |

### Document identity and revisions

- New upload: an existing `nota-documento` in the HTML is kept; otherwise `upload-<24 random hex>` is assigned.
- Revision (`artifact`): the artifact's document ID is inserted when absent. An upload that declares a different ID gets 409. The artifact ID never changes, permissions are kept, and HTML/ZIP revisions do not inherit an earlier PDF original.

### PDF processing

Poppler (`pdfinfo`, `pdftoppm`, `pdftotext`) runs as a child process: a temporary folder, an empty environment, its own process group killed on timeout (30 s for metadata, 120 s for rendering), `ulimit` CPU 60 s, file size, 64 descriptors and 1 GiB address space, at most two conversions at a time. Generated output is capped at 200 MiB on disk and 20 MiB of HTML. No code from the PDF is executed. The portal image installs `poppler-utils`.

Two upload jobs may run concurrently; additional jobs receive 503 and can be retried. Metadata title/head extraction uses a bounded window.

### ZIP rules

- At most 15 MiB compressed, 400 entries, 50 MiB uncompressed, 20 MiB per entry; any entry over 1 MiB and the archive as a whole may not expand more than 100×. Each entry is read up to its declared size and its CRC is verified.
- Rejected: encrypted entries, symbolic links and special files, absolute paths, `..`, backslashes, drive letters, control characters, names repeated ignoring case and Unicode form, compression other than stored/deflate.
- Allowed types: HTML, CSS, JS/MJS, JSON, TXT, SVG, PNG, JPEG, GIF, WebP, AVIF, ICO, WOFF/WOFF2, TTF/OTF, MP3, MP4, WebM. Everything else is rejected, including nested archives, server code (PHP, Python, shell…), dotfiles, `node_modules`, `package.json`, lock files, `netlify.toml`, `_redirects`, `_headers`, `.htaccess`, `vercel.json`. `__MACOSX/`, `.DS_Store` and `Thumbs.db` are skipped and reported.
- A ZIP of a single folder uses that folder as the site root.
- Entry page: `entry`, else `index.html`, else the only HTML file; otherwise 422 listing the pages.
- Expansion is budgeted before allocating repeated resources: 20 MiB conservative work/output budget, cached data URIs, at most 128 CSS imports and 30 000 HTML elements. Repeated references consume budget too; files below the input limit can therefore be rejected.
- Inlined: `<link rel=stylesheet>` (with nested `@import` up to four levels and CSS `url()`), `<script src>` (`</script` escaped), `img`/`source` `src` and `srcset`, media `src`/`poster`, icons, SVG `image`/`use`, `style` attributes and `<style>` blocks. Local links to non-HTML files become `data:` links.
- Remote URLs are left untouched and never fetched by the server; the reader CSP blocks most of them, and inspect warns.
- One artifact is one page. If the entry links another HTML page in the ZIP, the upload is rejected with the linked pages named, rather than publishing broken navigation. Unlinked extra pages and unreferenced files are not published and are listed in `warnings`.

## Known limits

- JavaScript that loads files at runtime (`fetch`, dynamic `import`, computed paths) cannot reach ZIP files: the reader has no network. Module scripts that import other files are reported.
- `<link rel=stylesheet>` keeps only its `media` attribute when inlined.
- PowerPoint uploads are not part of this endpoint; use `scripts/import_document.py` on the creator's machine.
- The original ZIP is not stored; the published HTML is the self-contained result.
