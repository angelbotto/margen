# Creator workspace experience

Margen 0.13 separates four jobs in the main navigation. A graph is a knowledge surface, not an artifact layout option. The library keeps gallery, list and table presentations.

| Destination | Job | Route |
| --- | --- | --- |
| Library | Find, preview and organize documents | `/` |
| Knowledge graph | Explore sources, topics, decisions and recorded sessions | `/?view=brain` |
| Visits | Understand recorded opens after sharing | `/?view=insights` |
| My work | Review evidence, decisions, assignments and continuity | `/?view=work` |

The creator workspace opens inline. Reader management stays outside shared document content. Direct links to `/?view=work&section=claims`, `decisions` or `sessions` open the corresponding work section.

## Visits

The library overview links to Visits and shows the last 30 UTC days of recorded opens. Visits supports 7, 30, 90 and 365 days, scoped to an existing space. It includes a daily chart with an accessible data disclosure, a ranked list and a link to the configured Umami website. Measurement preferences remain explicit.

`GET /api/creator/analytics/summary?days=30&project=...` aggregates in SQL **before** limiting the top 100 documents. Totals and daily series cover the whole authorized owner scope, even if the ranked list is truncated. The existing raw daily endpoint remains compatible. The summary excludes future dates and old rows outside the requested period.

These are opens, not unique readers, engagement time or conversions. Zero means no recorded opens; it cannot prove nobody read a document. Measurement can be paused and cannot recover earlier traffic. Owner visits, previews, unpublished revisions, agent requests and supported browser privacy signals are excluded by the existing reader integration. Umami configuration stays on the host; it is not embedded in portable artifacts.

## Knowledge navigation

The dedicated graph uses the owner-scoped creator endpoint. Unlike the former artifact layout, it includes recorded decisions, claims and session provenance alongside spaces, manual tags, rule-based topics, collections and explicit entities. Enrichment preserves both manual metadata and automatic classification explanations.

- Start from a company/space, topic, decision, assumption or session lens.
- Select an entry point, then explore one or two connections from it.
- The inspector separates incoming references, outgoing connections and organizational membership. Directed relationships show arrows; membership does not imply causality.
- Open the exact cited version where evidence is available. Decision, claim and session inspectors expose their recorded properties and link to their work section.
- Filter for artifacts without a direct relationship to discover unfinished connections. This ignores space/topic/collection membership, so it is more specific than having no edges at all.
- Save positions, lens, relation filter, neighborhood, selected node, labels and the unconnected filter to the account. Search text and zoom are transient.
- Selection and search preserve the viewport and reuse the computed layout for an unchanged topology. The force calculation is bounded and does not run continuously.

The owner graph includes up to 150 recent artifacts, 300 membership nodes, up to 300 explicit entities with matching members, up to 200 claims and decisions each, and sessions derived from up to 2,000 versions. It reports truncation. Counts describe the loaded set. Use the project selector to narrow scope; use library search for the complete authorized document corpus. Suggestions do not become confirmed relationships automatically. No embeddings or autonomous semantic reasoning are implied.

Existing spaces and topics appear in organization tools without creating an entity first. Optional explicit entities add aliases and properties. Companies are derived from assigned spaces, not guessed from mentions in document prose. Known brand themes remain separate from ownership and permissions. A self-hosted installation does not receive the maintainer's company data.

## Reader controls

The dock retains **Comments, Share, Preferences**, in that order. Comments prioritizes adding feedback, viewing threads and preparing an AI context bundle. Personal notes disclose privacy. Sharing owns access, management and related references. Command search is available from the administrator instead of duplicating it inside every reader menu.

Menu rows combine an icon, a short action and a brief consequence. Accessible names stay concise. Theme favorites sit next to the theme search; typography and audio remain separate tabs. Selecting a theme does not change the independently selected light, dark or system mode.

The context composer lets a reader select pending shared comments, clear the selection, opt into personal notes and preview the resulting prompt. **Copy for AI** builds the authorized bundle when needed and copies it in one action. It does not send anything to an agent, reopen a session or resolve a thread. JSON download and the full prompt remain available as progressive disclosures. Every selection change invalidates the prepared preview.

## Access experience

The library sign-in and shared-document gate use the same entry surfaces, with different copy for each task. On small screens, the form comes first. Available providers come from `/api/auth/options`; deployments can enable Google, email codes or both. There is no shared-document password flow.

Email verification replaces the provider choices with a six-digit code input, delivery feedback and a resend cooldown. Browser autofill and paste work in one field. Switching email discards stale delivery polling. Google and email retain allowlisted artifact, thread and version destinations; failed Google consent retains the validated return context.

Denied access reveals no protected title or preview. An authenticated reader sees their current email and can change accounts or return to the library. Missing and unauthorized artifacts share the same gate; connection failures instead offer retry. Authentication does not grant document permissions.

## Research and next boundaries

This implementation adopts local neighborhoods, inspectable incoming links and property-driven organization from the official [Obsidian graph](https://help.obsidian.md/plugins/graph), [backlinks](https://help.obsidian.md/plugins/backlinks), [properties](https://help.obsidian.md/properties) and [Bases](https://help.obsidian.md/bases) documentation. Margen preserves its own permission model and evidence/version contracts; it does not implement an Obsidian vault or plugin API.

Further work should be evaluated through observed use, not assumed adoption:

1. Full-text evidence search can grow into hybrid retrieval with evaluated relevance, explicit sources and permission-filtered results.
2. Large graphs would benefit from server-side neighborhood expansion beyond the disclosed bounded set.
3. Presence and collaborative cursors require real-time infrastructure and clear identity; current comments are persisted conversations.
4. Review exact-source repair could become a visual workflow for moved or ambiguous anchors.
5. Sessions can become a richer timeline after end-to-end agent delivery has been measured. A copied prompt is not an executed assignment.

No usage impact, user satisfaction or concurrency SLA is claimed by this visual revision.
