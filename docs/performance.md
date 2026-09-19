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

`GET /api/operations/performance` is available only to authenticated administrators. It reports p50/p95 and server-error counts for the latest 2,000 requests in that process, grouped by route template. It stores no query strings, user identifiers or content and resets on restart. Add external availability monitoring for long-term operational measurements.

`MARGEN_MAX_ARTIFACTS` defaults to 10,000 per owner. Existing limits remain: 200 versions per document, 2,000 review events per artifact and bounded graph neighborhoods. SQLite WAL and the application lock support one service instance. Do not scale this deployment by adding replicas against a shared NAS SQLite file. Move to PostgreSQL when measured concurrent write contention or multi-instance availability requirements justify the migration. A NAS backup is not high availability; test restoration separately.

Static preview HTML remains sanitized and bounded in the existing in-process cache. Original files and versions remain access-controlled. No shared public preview cache is introduced for private documents.
