# Library rendering and filter behavior

Advanced conditions are a local draft until Apply. Cancel keeps the current query; Reset clears only the draft conditions. Existing facets stay in the applied query. Numeric zero is a valid value, empty conditions need no input, and reversed ranges are rejected. The server evaluates the query against all authorized results, not only loaded rows.

Table pagination appends rows to the existing body. It preserves the scroll container, prior row nodes, preview frames and controls. Facet options are rebuilt only for a fresh query, not each subsequent page. Gallery pagination already appended cards and retains that behavior.

The preview pool keeps at most eight live, sandboxed iframes near the viewport. It releases frames outside the eligible area, prioritizes nearby candidates, batches observer updates into an animation frame and cancels obsolete work when changing views. Document HTML remains isolated from the administrator DOM.

## Verification

A local, synthetic 60-document library was compared with the 0.15.1 administrator JavaScript. Loading from 12 to 24 table rows previously replaced the first row node; the new implementation preserves it. Filtering one of three equally populated companies returns 20 results, including unloaded records. These are behavioral checks, not production latency benchmarks.

Unit tests feed 40 eligible previews to the pool and verify that only eight frames exist, off-screen frames are released and delayed callbacks after disconnect cannot recreate them. Query tests cover cancel/apply, preserved facets, reset, numeric zero and invalid ranges. Browser checks include desktop and narrow mobile layouts. Long-session DOM growth remains proportional to the number of loaded rows/cards; this change does not implement full row virtualization or claim unlimited-scale browsing.
