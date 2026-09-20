# Performance and scaling

The library uses SQLite authorization, full-text search, typed filters, keyset windows and indexed review counters. Classification is recomputed only for dirty artifacts. Full-text matches are materialized once per query instead of repeating an FTS scan per document. Only returned records are hydrated into Python objects. Unmigrated external bookmarks retain the older compatibility path until imported.

Reproduce a synthetic test independently of production:

```bash
python3 scripts/benchmark_library.py --sizes 100 1000 5000 --samples 20
```

Measured on the maintainer's local Mac, Python 3.14, September 19, 2026. Each query returns at most 60 records. Warm filesystem cache; 20 serial samples; no HTTP, network, browser rendering or concurrent writes included. These figures are not a production SLA.

| Owned artifacts | Recent p95 | Full-text p95 | Project filter p95 |
| --- | ---: | ---: | ---: |
| 100 | 2.73 ms | 3.36 ms | 2.03 ms |
| 1,000 | 8.27 ms | 16.55 ms | 8.04 ms |
| 5,000 | 46.35 ms | 74.54 ms | 28.72 ms |

The initial classification projection took 4.85 seconds at 5,000 synthetic artifacts. Subsequent queries use the stored projection. Large first migrations should be scheduled with a backup and maintenance window.

`GET /api/operations/performance` is available only to authenticated administrators. It reports p50/p95 and server-error counts for up to 50,000 requests from the last 30 days, grouped by route template. A separate SQLite WAL file persists across restarts and is included in new backups. It stores no query strings, user identifiers or content. Failed telemetry writes do not block reader responses. Add external availability monitoring for long-term operational measurements.

`MARGEN_MAX_ARTIFACTS` defaults to 10,000 per owner. Existing limits remain: 200 versions per document, 2,000 review events per artifact and bounded graph neighborhoods. SQLite WAL and the application lock support one service instance. Do not scale this deployment by adding replicas against a shared NAS SQLite file. Move to PostgreSQL when measured concurrent write contention or multi-instance availability requirements justify the migration. A NAS backup is not high availability; test restoration separately.

Static preview HTML remains sanitized and bounded in the existing in-process cache. Original files and versions remain access-controlled. No shared public preview cache is introduced for private documents.

## Concurrent ASGI baseline

Run `python3 scripts/benchmark_http.py --size 1000 --samples 40 --concurrency 1 4 8 --output results.json` with portal dependencies installed. The disposable fixture never contacts production. Results on the local Mac, Python 3.14.7, September 20, 2026 UTC:

| Concurrent requests | Samples | p50 | p95 | Errors |
| --- | ---: | ---: | ---: | ---: |
| 1 | 40 | 19.02 ms | 24.19 ms | 0 |
| 4 | 40 | 68.75 ms | 90.87 ms | 0 |
| 8 | 40 | 134.13 ms | 162.94 ms | 0 |

Includes ASGI authorization, alternating recent/full-text library requests, SQL and telemetry. Excludes external network, browser rendering and concurrent writes. The fixture creates separate request clients. This is an initial regression baseline, not a production SLA or a benchmark of concurrent editing.
