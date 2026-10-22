# Upload review resolution

The baseline report targets 508ab5a. The integrated changes through 7e24a51 address F1–F8; F9 remains a pre-existing origin/proxy deployment concern, outside this upload change.

- F1: incremental expansion budget, cached data URIs, bounded CSS imports and element count, one output join. Independent repeated-asset and import fan-out probes now reject early.
- F2/F6: structural metadata parsing, implicit-body stop, title/head handling outside comments and script/template content; identity must agree with the existing publisher. A 15 MB unfinished-head probe completed in 0.62 seconds on the integration host.
- F3/F5: reject static multipage navigation including directory URLs, embedded pages and refresh/form targets; escape script delimiters and remove an external script element's fallback body.
- F4: the UI checks the combined base64 JSON size before sending; the 22 MiB server body cap remains. The new frontend regression checks that the oversized request is never sent. The baseline test assumed raising the server cap was the only solution, so that historical assertion is not an acceptance check for this implementation.
- F7: one 90-second conversion deadline, 384 MiB child address-space limit on Linux, bounded stdout/stderr, one page on disk at a time. The author verified the production image with 768 MiB memory and 32 MiB tmpfs. Large image/text PDFs streamed successfully; they did not reproduce the initial review's claimed Poppler RSS (that measurement included the input generator). A deterministic child allocating/touching 900 MiB failed inside the new limit without container OOM; the old limit allowed container OOM. This is subprocess-limit evidence, not a claim that every hostile PDF was tested.
- F8: revisions require `expected_current`; a blind overwrite returns 409. The historical review test expected the former last-write-wins behavior. Current endpoint tests cover rejection, stale versions and successful guarded revisions.

Integration verification: 18 applicable independent security probes passed; 242 portal tests passed (one Linux-only resource test skipped on macOS); 13 upload/reader frontend tests passed; HTML, ZIP and PDF upload flows passed in Chromium and WebKit. The prior complete frontend run passed 153 tests; the additional combined-size test also passed after integration. Linux resource checks are included in the portal CI job.

Limits remain explicit: static ZIP imports publish one entry document with its local assets; runtime JavaScript navigation cannot be inferred, so omitted pages are reported. This is validation and isolation, not malware detection. Raw authored HTML styling is preserved. No uploaded server code is executed.
