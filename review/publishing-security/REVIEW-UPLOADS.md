# Independent review: HTML, PDF and static ZIP uploads

Scope: `425579c..508ab5a` (`portal/uploads.py`, its mount in `portal/app.py`, `portal/static/upload.js`, `portal/Dockerfile`, `docs/upload-contract.md`). Review only; no product file was changed. Reader actions integration is out of scope.

Method: code reading, then adversarial inputs run in child processes with timeouts, on macOS (Python 3.14.7, Homebrew Poppler) and inside the production image built from `portal/Dockerfile` (Python 3.14.5, Alpine, Poppler 25.04, uid 1000, `--memory=2g --cpus=2`). The author tests (`portal/test_uploads.py`, 7 tests) pass and were not relied on.

Reproducers: `test_upload_security.py` (expected behaviour; `[defect]` tests fail on 508ab5a), `pdf_inputs.py` (hostile PDFs), `probe_pdf_docker.sh` (production image, real Poppler and busybox `ulimit`).

```sh
python review/publishing-security/test_upload_security.py          # 20 tests; the 9 [defect] tests fail on 508ab5a (14 failures with subtests)
sh review/publishing-security/probe_pdf_docker.sh                  # from the repository root
```

Threat model used: the attacker is any verified account. Sign-up is an emailed code to any address (`portal/auth.py:113`), so this means anyone. `POST /api/uploads/inspect` needs no artifact and stores nothing, so it is the cheapest way in. Uploaded HTML/JS executing inside `/render` is by design: it runs in an opaque-origin sandbox with `connect-src 'none'`. The upload flow is meant to keep uploads safe for the portal; it does not try to detect malware.

## Summary

| # | Severity | Finding | Practical? |
|---|---|---|---|
| F1 | **High** (blocker) | ZIP inlining allocates without bounds before the 20 MB output check: a separate `data:` copy for every reference, quadratic string splicing, and CSS `@import` fan-out | Yes: a 729-byte ZIP uses 2 GB and 44 s in the production image |
| F2 | **High** (blocker) | Quadratic regexes (`title_of`, `with_document_id`) on HTML and ZIP output hold the GIL and freeze the single uvicorn worker | Yes: 116 KB of HTML freezes the whole portal for 5.2 s, and a 1 MB file is extrapolated to about 7 min |
| F3 | Medium | Multi-page sites still publish with broken navigation: directory links, `iframe`/`frame`/`object`, meta refresh and form actions get a warning at most | Functional; this is the common static-site-generator layout |
| F4 | Medium | The UI accepts a 15 MB file plus a 12 MB original, but the JSON body (36 MiB) is over `MAX_BODY` (22 MiB), so it gets a 413 after a successful inspect | Functional |
| F5 | Low | Inlined JS escapes only `</script`. A `<!--` … `<script` inside a file puts the parser in double-escaped state and swallows the rest of the page | Functional, rare |
| F6 | Low | The document ID meta, the adopted `nota-documento` and the title are matched by regex anywhere, including inside comments and scripts | Functional |
| F7 | Low | PDF: a 0.19 MB PDF holds one of the 2 global slots for about 60 s of CPU per tool. A failure from a limit is reported as "damaged or password protected" | Feature-level DoS only |
| F8 | Info | Revision CAS is optional for unmanaged artifacts (last write wins without `expected_current`); this is the existing `publish()` rule, and the UI does send it | API clients only |
| F9 | Info (pre-existing) | The write rate limit keys on `cf-connecting-ip`, which a client can set if the origin is reachable without Cloudflare. This amplifies F1/F2 | Deployment-dependent |

## F1 — High: unbounded expansion in `Site` before the output limit

`portal/uploads.py:358` `data_uri` base64-encodes the asset again on every reference. `render()` (`:467`) applies each edit with `content = content[:start] + new + content[end:]`, so n edits copy the growing document n times. `css()` (`:369`) recurses up to depth 4, but nothing limits how many imports each level has. `LIMITS["output_bytes"]` is checked only in `zip_site` (`:503`), after everything has been built. The ZIP limits (15 MB, 50 MB, 100×) bound the input; they do not bound this output.

Measured on 508ab5a:

| Input | macOS | Production image (Linux) |
|---|---|---|
| 64 KB ZIP: `index.html` with 250× `<img src=a.png>`, 64 KB random PNG | 1.4 GB, 1.5 s | 126 MB, 0.4 s |
| same with 1,600 references | 7.4 GB, 42 s | 586 MB, 8.2 s |
| 1 MB asset × 400 references | did not finish in 45 s | (not run; output about 560 MB before the check) |
| 721-byte ZIP, 34 `@import`s per level × 4 | 3.6 s | 270 MB, 4.5 s |
| 729-byte ZIP, 60 `@import`s per level × 4 | 3 GB, 34 s | **2 GB, 44 s** |

All of these end in the correct 422 message, but only after the memory has been used. Every case is reachable through `/api/uploads/inspect` at 90 requests/min per IP. Uploads run in the default threadpool (40 threads), so a few concurrent requests reach the container memory limit and get the whole portal OOM-killed.

Recommendation: keep a running byte budget in `Site` and reject as soon as the projected output exceeds `output_bytes`. Count the base64 size of every inlined asset and every CSS/JS expansion. Cache the base64 per path (the bytes are still counted on each use). Collect the output as a list of chunks and join it once. Limit `@import` to a count per file and a total across files, as well as depth. Root acknowledged this and is fixing it. Retest with `ResourceBounds.test_defect_repeated_asset_*` and `test_defect_css_import_fanout_is_bounded`.

## F2 — High: quadratic regexes stall the event loop

- `title_of` (`:117`): `<title[^>]*>(.*?)</title>` with `re.S`, plus the `<h1` fallback. Each unclosed `<title>` scans to the end of the document. It runs on every HTML inspect and build, and on every ZIP result.
- `with_document_id` (`:126`): `<head(?:\s[^>]*)?>` behaves the same way on `<head ` with no closing `>`.

Python's `re` does not release the GIL. In a probe, a 4.3 s `title_of` call stalled another thread's 10 ms sleep loop for 4.3 s. The image runs one uvicorn worker (`CMD uvicorn ...`), so the event loop and every request stop while the regex runs.

| Input | macOS | Production image |
|---|---|---|
| 136 KB `"<title>" * 20000`, inspect | 7.8 s | — |
| 116 KB `"<title>" * 17000`, inspect | 5.5 s | **5.2 s** |
| 117 KB `"<head " * 20000`, build | 7.2 s | — |

The cost is quadratic, so the 15 MB limit allows hours of CPU per request. Recommendation: take the title from the `Tags` HTMLParser that already runs (or search a bounded window such as the first 64 KB / up to `</head>`). Bound the head regex with `[^>]{0,4096}`, or find the insertion point with the parser. Check `portal/formats.describe` and `reader_style.head_insertion_point` in the same way, since `publish()` and `/render` run them on the same content. They were not measured here.

## F3 — Medium: the single-page contract has gaps

`Site.tag` rejects linked pages only when `<a>`/`<area>` resolves to an existing `.html`. Each of the following publishes with broken navigation and at most a "missing resources" or "other pages not included" warning (`SinglePageContract`):

- `<a href="about/">`, `<a href="/about/">`, `<a href="about">` when `about/index.html` exists. This is the default output of Hugo, Astro, Jekyll and Next export.
- `<iframe src>`, `<frame src>`, `<object data>`, `<meta http-equiv=refresh content="0;url=…">`, `<form action>`, `<button formaction>`, `<link rel=next>`, `<base href>`, SVG `<a xlink:href>`.
- JS navigation (`location.href = "about.html"`) cannot be detected. Keep the warning, but name the pages.

Already rejected correctly: direct `.html` links, links with a query or fragment, and `%2F`-encoded links.

Recommendation: resolve `X/`, `/X/` and `X` to `X/index.html` / `X.html` when that page exists, and reject them like direct links. Treat `iframe|frame|object|embed` `src`/`data`, meta-refresh `url=`, `form[action]`/`formaction` and `base[href]` that resolve to an HTML page in the ZIP as navigation, and reject them. A `<base href>` that changes resolution should also be rejected or applied.

## F4 — Medium: the UI's combined size goes over the body limit

`upload.js` accepts a file up to 15 MiB plus an `original` attachment up to 12 MiB. Both are sent base64-encoded in one JSON body: (15 + 12) × 4/3 = 36 MiB, more than `MAX_BODY` = 22 MiB (`portal/app.py:36`). The middleware then returns 413 "Tamaño no permitido." after inspect has already said the file is fine. Any file over roughly 16.5 MiB combined fails. Recommendation: check the combined encoded size in the UI with an actionable message, or raise `MAX_BODY` for `/api/uploads` only. `Limits.test_defect_ui_limits_fit_the_body_limit` covers this.

## F5 — Low: inlined JS can swallow the rest of the page

`Site.tag` escapes `</script` only. A JS file containing `<!--` followed later by `<script` (for example a template string) puts the HTML parser in script double-escaped state, and everything up to the next `</script>` becomes script text. The same goes for `<script src=x.js>fallback</script>`: the inline fallback is appended to the inlined code (`script src + body` probe). Recommendation: also replace `<!--` with `<\!--`, and drop the original element body when `src` is inlined.

## F6 — Low: identity and title sniffing ignore HTML structure

- `with_document_id('<!-- <head> --><html><head>…')` puts the meta inside the comment. `publish()` still accepts it, because its regex also matches inside comments, but the reader DOM has no `nota-documento`.
- A page whose script contains `'<meta name="nota-documento" content="ejemplo">'` (a Margen tutorial, for example) adopts `ejemplo` as its document ID. A later revision then gets a confusing 409.
- `<script>const t="<title>pwn</title>"</script><title>Real</title>` gets the title `pwn`.

Recommendation: read the title, meta and head position from the `HTMLParser` pass, skipping comments and the contents of script, style and template elements.

## F7 — Low: PDF resource use (real Poppler, production image)

`ulimit` works in the image: busybox reports CPU 60 s, file size 131072 blocks of 512 bytes (64 MiB), 64 descriptors and 1 GiB address space. A 70 MB write was cut at 64 MiB, and a 2 GiB allocation raised `MemoryError`. The process-group kill on timeout works. Poppler turns control characters in `Title` into `?`, so a fake `Pages:` line cannot get past the 80-page limit (tested with a literal, a UTF-16 newline and a CR).

| `pdf_inputs.py` case | PDF | Result |
|---|---|---|
| `image`: 30000×30000 gray image | 0.8 MB | ok, 4.5 s, child RSS 901 MB (close to the 1 GiB cap) |
| `image80`: 8000² image on 80 pages | 0.1 MB | ok, 26 s CPU |
| `text`: about 400 MB of text operators | 1.1 MB | ok, 14 s |
| `text80`: about 60 MB shared by 80 pages | 0.19 MB | rejected at 60 s CPU, with "No se pudo leer el PDF; puede estar dañado o protegido" |

Each tool gets its own 60 s CPU limit and its own wall timeout (30 + 120 + 60 s). One request can therefore use about 2.5 CPU-minutes and hold one of the two global `PDF_SLOTS`, so two requests every few minutes deny PDF uploads to everyone. The rest of the portal is not affected, because `communicate()` releases the GIL. The temp disk used is at most 64 MiB per file. On the macOS dev host, `ulimit -v` is silently ignored; this affects development only.

Recommendation: set one CPU and wall budget for the whole conversion (for example 30–45 s), pass `-l <pages>` to `pdftoppm`/`pdftotext` as a second guard, give each account its own slot, and return a distinct "the PDF is too heavy to preview" message when a limit kills the process (signal or exit code 152/153).

## F8 / F9 — Info

- F8: `publish()` enforces `expected_current` only when it is sent or when the artifact is editor-managed. An API client that leaves it out overwrites concurrent work. This is consistent with `POST /api/artifacts/{id}/versions`. Consider requiring it on `/api/uploads` revisions, since the UI always sends it.
- F9: the rate limit and the e-mail send limit key on `cf-connecting-ip` without `--proxy-headers` trust. If the origin is reachable outside the tunnel, a client can rotate the header. Not new.

## Verified safe

These are covered by the passing tests in `test_upload_security.py`, plus code reading.

- **ZIP paths:** `..`, absolute paths, drive letters, backslashes, `.`/empty segments, C0 and DEL characters, case- and NFC-insensitive duplicates, symlinks and special files, encryption, and compression other than stored/deflate are all rejected. Lying declared sizes and bad CRCs are rejected. The per-entry 100× ratio, 400 entries, 50 MB total and 20 MB per entry limits hold. Archive contents never touch disk, so path traversal cannot write files.
- **Code insertion through the build:** rebuilt attributes are escaped, and inlined `<style>` escapes `</style`. PDF title, metadata and text are HTML-escaped (`<img onerror>` in `Title`, `<script>` in page text). The original PDF bytes are preserved. Uploaded markup runs only in the sandboxed `/render` (opaque origin, `connect-src 'none'`).
- **Arbitrary HTML is preserved:** CRLF, a doctype, attributes on `<head>`, inline handlers and SVG survive byte for byte, apart from the inserted meta.
- **Auth and CSRF:** `Origin: null`, a suffix-lookalike origin and an http downgrade all get 403. An invalid Bearer gets 401. A guest gets 401 on both endpoints. No CORS middleware is present.
- **Malformed fields:** bad base64, an empty file, a non-string or traversal name, a bad extension, a non-string `entry` or `title`, an oversized `space`, a bad `mode`, any `visibility`, and a PDF extension on HTML bytes all get 422 with nothing stored.
- **Private default and revisions:** uploads are created private. An uppercase, wrong-length or someone else's `artifact` gets 404, a stale `expected_current` gets 409, and a revision keeps the artifact ID.
- **Production image:** builds; Poppler 25.04 is present and runs as uid 1000; the PDF tests pass inside it.
- **Not testable in the image:** the image has no `httpx`, so HTTP tests (the author's and this review's) run only in a dev environment.

## Recommended order

1. F1 and F2 before release (any account can deny service).
2. F3 and F4 (the contract promises they cannot happen, and users will hit them).
3. F5–F7 as hardening; F8/F9 are decisions.
