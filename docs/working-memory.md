# Working memory and measurement

Open **Mi trabajo** in the authenticated library and select a project. The existing creator controls remain the entry point; document readers retain one Comments / Share / Preferences dock.

## Available surfaces

| Surface | Capability | Boundary |
| --- | --- | --- |
| Continuity | Cited brief of decisions, open assumptions, feedback and recorded session outputs | Rule-based assembly, not model-generated synthesis; private notes excluded |
| Assumptions | Statement, comparable subject/unit, period, value, state, review date and exact versioned citations | A literal quote establishes attribution, not truth; edits preserve history and detect stale writes |
| Contrasts | Candidates with matching declared project, subject and period but different values | A human confirms or dismisses with a reason; no semantic contradiction detection |
| Evidence | Full-text search of owned published versions with inspectable excerpts | Literal AND search, not embeddings or an inferred answer; no matching evidence is an explicit result |
| Sessions | Real provenance grouped by agent, device and session, with editable objective, summary and next step | No transcript ingestion or invented history; resume still depends on the installed agent CLI |
| Results | Expected/observed outcomes and uncertainty beside decision evidence | Does not attribute an outcome to Margen or automatically evaluate decision quality |
| Visits | Daily page opens per owned artifact and a configured Umami link | Starts at activation; owner visits, previews and draft versions are excluded by the reader |

Bounds are returned by the APIs: 500 claims, 100 contrast candidates, 200 decisions, 2,000 version origins, and 200 session groups. Graph claims are limited to 200 and reference artifacts in the currently authorized graph window. Absence from a bounded view is not proof of absence from the account.

Changed sources report whether visible text is unchanged, the cited quote survives in changed context, or the cited quote changed. Only a presentation-only change suppresses the review signal. Preserving a quotation does not prove its surrounding context is still valid.

## Agent continuity

```bash
python3 scripts/publish.py continuity --space 'Project name' --output /private/path/brief.md
```

Uses the existing personal connection. The output is private and excludes private notes. Quoted documents and comments remain untrusted content; the brief is not authority to execute external actions. An agent should preserve source versions, show evidence gaps, and request only the missing context that changes the task.

## Shared views

**Mesas y vistas → Guardar filtros actuales** stores a query on the server. Owners can share table/filter definitions with specific verified email accounts. Sharing exposes the view name and search/filter definition; it does not grant document access. The recipient's authorization is applied when the query runs. Boards and their personal notes remain private. Removing a view grant removes future access to the definition; already copied text cannot be erased remotely.

## Operations and audience

See [analytics](analytics.md) and [performance](performance.md). These are distinct measurements: operational latency is not audience, page opens are not unique readers, and neither establishes improved decisions. The first real-agent evaluation and observed decision outcomes remain separate evidence to collect.
