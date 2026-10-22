# Upload contract: HTML, PDF and static ZIP

`portal/uploads.py` turns one uploaded file into one self-contained HTML version and hands it to the existing `publish()`. Uploads therefore get the same account checks, private default, version history, `expected_current` compare-and-set, format description and sandboxed `/render` as any other publication. Uploaded HTML and JavaScript are never served from the portal origin: only through `/render` (`sandbox allow-scripts allow-downloads`, opaque origin, `connect-src 'none'`, images/fonts/media only as `data:`). Original PDFs go through the existing attachment endpoint (`application/octet-stream`, `sandbox` CSP, version ACL).

Both endpoints require a verified account (portal cookie or agent Bearer token). The portal middleware still applies the `Origin` rule, the 22 MiB body limit (`MAX_BODY`) and the write rate limit. File and original travel base64-encoded in one JSON body, so together they can use about 16.5 MiB; the upload dialog checks the encoded size before sending and asks to remove the original or use a lighter file.

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

`entry` is set for ZIP only; `pages` and `preview` for PDF only (`preview: "none"` means the server lacks Poppler and publishing will fail). Every rejection is 422 with `{"detail": "<actionable message in Spanish>"}`; 413 above the body limit; 503 when another PDF is already being processed or two uploads are in flight.

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

- The title, an existing `nota-documento` and the `<head>` position are read with an HTML parser: comments and the contents of `script`, `style` and `template` are ignored. The title is the first closed `<title>`, else the first closed `<h1>`, else the file name.
- New upload: an existing `nota-documento` in the HTML is kept; otherwise `upload-<24 random hex>` is inserted right after the real `<head>` (after the doctype, or at the start, when there is none).
- `publish()` reads the first textual `nota-documento`. When that would differ from the parsed identity (a copy in a comment or script before the real one, or a meta the portal cannot read), the upload gets 422 and asks to move the meta into `<head>` or remove it.
- Revision (`artifact`): the artifact's document ID is inserted when absent. An upload that declares a different ID gets 409. The artifact ID never changes, permissions are kept, and HTML/ZIP revisions do not inherit an earlier PDF original.

### PDF processing

Poppler (`pdfinfo`, `pdftoppm`, `pdftotext`) runs as a child process: a temporary folder, an empty environment, its own process group killed on timeout, `ulimit` CPU (at most 60 s and never past the deadline), file size, 64 descriptors and 384 MiB address space per child, one conversion at a time. One 90-second deadline covers the whole conversion, metadata included (inspect: 30 s for metadata). The memory cap keeps a child well inside the production 768 MiB container next to the portal: a child that needs more fails alone instead of triggering the container OOM killer. Each page is rendered, charged against the 20 MiB HTML output budget, and deleted before the next one. Child output files (stdout and stderr) are limited to 4096 shell file-size blocks; at most 64 KiB of extracted text is retained per page. This keeps temporary files within the production 32 MiB tmpfs. No code from the PDF is executed. The portal image installs `poppler-utils`.

Errors are distinct: a child stopped by a limit (signal, CPU, file size or memory) gets "too heavy to preview"; the deadline gets "took too long (90 s)"; any other failure gets "damaged or password protected". ulimit `-v` is ignored on macOS, so the memory cap only applies in Linux (the production image).

Two upload jobs may run concurrently; additional jobs receive 503 and can be retried. Metadata extraction parses incrementally and stops at the body.

### ZIP rules

- At most 15 MiB compressed, 400 entries, 50 MiB uncompressed, 20 MiB per entry; any entry over 1 MiB and the archive as a whole may not expand more than 100×. Each entry is read up to its declared size and its CRC is verified.
- Rejected: encrypted entries, symbolic links and special files, absolute paths, `..`, backslashes, drive letters, control characters, names repeated ignoring case and Unicode form, compression other than stored/deflate.
- Allowed types: HTML, CSS, JS/MJS, JSON, TXT, SVG, PNG, JPEG, GIF, WebP, AVIF, ICO, WOFF/WOFF2, TTF/OTF, MP3, MP4, WebM. Everything else is rejected, including nested archives, server code (PHP, Python, shell…), dotfiles, `node_modules`, `package.json`, lock files, `netlify.toml`, `_redirects`, `_headers`, `.htaccess`, `vercel.json`. `__MACOSX/`, `.DS_Store` and `Thumbs.db` are skipped and reported.
- A ZIP of a single folder uses that folder as the site root.
- Entry page: `entry`, else `index.html`, else the only HTML file; otherwise 422 listing the pages.
- Expansion is budgeted before allocating repeated resources: 20 MiB conservative work/output budget, cached data URIs, at most 128 CSS imports and 30 000 HTML elements. Repeated references consume budget too; files below the input limit can therefore be rejected.
- Inlined: `<link rel=stylesheet>` (with nested `@import` up to four levels and CSS `url()`), `<script src>` (`</script` and `<!--` escaped as `<\/script` and `<\!--`; the element's own fallback body is dropped), `img`/`source` `src` and `srcset`, media `src`/`poster`, icons, SVG `image`/`use`, `style` attributes and `<style>` blocks. Local links to non-HTML files become `data:` links.
- Remote URLs are left untouched and never fetched by the server; the reader CSP blocks most of them, and inspect warns.
- One artifact is one page. If the entry navigates to another HTML page in the ZIP, the upload is rejected with the pages named, rather than publishing broken navigation. Navigation covers `a`/`area` `href` (and SVG `xlink:href`), `iframe`/`frame`/`embed` `src`, `object` `data`, `form` `action`, `button`/`input` `formaction`, meta refresh `url=` and `link rel=next|prev|alternate`. A reference resolves to a page directly (`about.html`) or as a directory or clean URL (`about/`, `/about/`, `about` → `about.html` or `about/index.html`). Links to the entry itself are fine. `<base href>` is rejected unless it points at the entry's own folder. Unlinked extra pages and unreferenced files are not published and are listed in `warnings`.

## Known limits

- Navigation done by JavaScript (`location.href = …`) cannot be detected; the unlinked-pages warning names the pages left out.
- JavaScript that loads files at runtime (`fetch`, dynamic `import`, computed paths) cannot reach ZIP files: the reader has no network. Module scripts that import other files are reported.
- `<link rel=stylesheet>` keeps only its `media` attribute when inlined.
- PowerPoint uploads are not part of this endpoint; use `scripts/import_document.py` on the creator's machine.
- The original ZIP is not stored; the published HTML is the self-contained result.
