# Changelog

## 0.14.3 — Reader activity

- Add creator-controlled per-artifact activity with period-scoped Umami pageviews and estimated uniques.
- Show participants from authorized comments and replies; exclude private notes, drafts and deleted conversations.
- Keep reporting credentials server-side, filter by exact artifact path, and label unavailable unique counts explicitly.
- Add Share → Artifact activity without changing the three-action reader dock.


## 0.14.2 — Personal account ownership

- Fix My artifacts and Archive matching administrator privileges instead of actual ownership, including the legacy bookmarks query. Shared with me now requires an explicit personal or domain grant.
- Add an explicit All artifacts administration view and owner labels in the gallery, list and table. Preserve artifact owners, links, versions and audiences.
- Require an explicitly chosen email when connecting a personal token, pin the verified account ID and reject changed identities before CLI writes. Legacy connections need one-time `margen confirm-account --email YOUR_EMAIL`; changing accounts no longer inherits publishing preferences.
- Clarify per-user installation and provide a Liftit-specific team trial brief.

## 0.14.1 — Readable narrative tables

- Preserve ordinary word boundaries in table cells so short category and priority columns do not collapse around long prose.
- Accept the dense-width marker on both the scroll container and the table for compatibility with authored documents.
- Document deliberate column proportions and vertical paragraph wrapping for narrative comparisons; retain local horizontal scrolling on narrow screens.

## 0.14.0 — Verified team domains

- Share individual artifacts with exact verified email domains, with viewer or commenter roles. Make team documents discoverable in Shared, search and authorized context links.
- Preserve personal-grant precedence, private notes, drafts and management boundaries. Revoking domains takes effect on subsequent requests; Private clears all grants.
- Add domain controls to the sharing dialog and an explicit `margen share` command for agent workflows.
- Document hosted team onboarding, a reusable trial prompt, backward-compatible API behavior and session/offboarding limits.

## 0.13.2 — A considered entry experience

- Redesign the library sign-in and protected-document entry with shared light/dark surfaces and a mobile-first access form.
- Give email verification its own step, delivery feedback, resend cooldown and account recovery. Discard stale delivery responses.
- Preserve safe document, thread and version return destinations through email sign-in and cancelled Google authorization.
- Distinguish network failures from denied access, keep protected metadata private, and show the active account when it cannot open a document.

## 0.13.1 — Focused graph neighborhoods

- Restrict each knowledge lens to its matching entities and directly connected artifacts. Show an explicit empty state when no decisions, assumptions or sessions are recorded, instead of displaying unrelated documents.

## 0.13.0 — A connected creator workspace

- Promote Knowledge graph, Visits and My work to dedicated navigation destinations; render creator work inline and surface 30-day recorded opens in the library.
- Aggregate owner-scoped visit trends and rankings before row limits. Keep opens distinct from unique readers and measurement preferences explicit.
- Preserve manual tags, collections and classification in the creator graph. Add directional inspection, recorded node properties, unconnected-artifact filtering, saved lenses and stable viewport exploration.
- Discover existing spaces and topics in organization tools, enrich command-search results and support keyboard navigation.
- Simplify reader menus, theme favorites and context preparation. Copy selected feedback with evidence in one action while keeping private-note selection explicit.
- Cache graph layouts, discard stale navigation responses and adapt controls for narrow screens.

## 0.12.1 — Reject stale execution deliveries

- Bind leased draft uploads to the current unexpired assignment revision and verify idempotent retries. Preserve legacy unleased integration behavior.
- Preserve additional citations when editing the first source of an assumption in the creator form.
- Fit bar charts to their container, wrap labels and redraw after chapter/viewport changes so mobile readers can see the plot immediately.

## 0.12.0 — Evidence-backed working memory

- Add cited project continuity briefs, versioned assumptions, explicit contrast reviews, real-session summaries and decision outcome views. Keep private notes out of automatic briefs.
- Add owner-scoped evidence search and shared filter definitions without granting document access. Extend graph evidence and distinguish presentation-only changes from changed source context.
- Persist bounded operational timings, add concurrent-request benchmarks and optional owner-enabled Umami pageview collection without private titles or conversation content.
- Add opt-in execution leases, process-group cancellation acknowledgements and explicit recovery; preserve draft-only connector delivery.
- Compare artifact versions side by side, disambiguate repeated quotes with surrounding text, and organize the creator workspace for desktop and mobile with shared light/dark tokens.
- Sign monotonic release sequences and include telemetry in consistent backups. These capabilities do not claim completed real-agent or observed decision-quality evaluations.

## 0.11.1 — Connector delivery through the hosted gateway

- Identify scoped connector requests with the same Margen user agent as the existing publisher, so the hosted gateway accepts real device delivery.

## 0.11.0 — Creator decisions and scoped agent assignments

- Add an owner workspace with project attention, evidence-backed decisions, review dates and append-only decision history.
- Connect selected feedback to scoped local agents, delivery receipts, draft comparisons and per-thread outcomes; keep acceptance, publication and resolution separate.
- Add approved personal writing rules, decision/session graph nodes and a shareable project review brief.
- Query the library in SQLite with indexed review projections, materialized full-text matches and bounded keyset windows; add reproducible synthetic benchmarks and administrator timing metrics.
- Preserve PDF/PPTX originals alongside page or slide previews, with version-aware authenticated downloads.
- Verify managed release signatures, support independent stable/preview channels and document self-hosted signing, local MCP and contributor contracts.


## 0.10.1 — 2026-09-18

- Treat articles and presentations as independently authored deliverables; remove the slide-to-article reader toggle and give the deck example dedicated slide content.
- Preserve existing HTML decks and document the collaboration-only publishing path.
- Restyle the shared reader toolbar with editorial paper, dotted edges and compact labeled controls. Reset inherited navigation geometry so legacy deck CSS cannot stretch the toolbar across the viewport; do not add body padding to external canvases.
- Hide empty comment badges and isolate navigation keys while editing feedback.

## 0.10.0 — 2026-09-18

- Compact cube-only Margen headers, preserving company identities and the adaptive favicon.
- Discover project identity from `.margen.json` or exact registered GitHub organizations; embed safe local company logos and declared project metadata.
- Separate project appearance from saved reader defaults with explicit CLI/configuration precedence.
- Add native presentations over chapter navigation: overview, keyboard controls, continuous reading, shared anchors and print layout.
- Add English document configuration, chapter/presentation examples, project regression tests and a sourced assessment of external Office/presentation tools.


## 0.9.0 — 2026-09-18

- Unified reader toolbar: Comments with its speech-bubble count, Share and Preferences.
- Point comments on cells, images, cards and charts; accessible contextual creation and permission checks.
- Legacy hosted comments wait for a point instead of defaulting to the first heading.
- Original dotted-cube Margen identity and embedded, adaptive SVG favicon.
- Regression coverage for media anchors, remounts, count placement, native menus and keyboard cancellation.


## 0.8.0 — 2026-09-18

- Use Radix Popover and Avatar in the React data workspace, with shared theme tokens and a compact responsive toolbar.
- Reorder columns by drag or keyboard/touch buttons. Persist order, visibility, pinning and widths in local views; retain source-cell identities in portable HTML.
- Add composable people, media, status and detail-card renderers, plus expandable React records and scalar-value filtering/export.
- Demonstrate rich fictional delivery records in the workbench and React lab. Keep 320/390 px layouts usable, with local table scrolling and inspector access for secondary React fields.
- Document the React/portable boundary, mobile composition and read-only dataset limits in English.


## 0.7.1 — 2026-09-18

- Count open threads directly from authorized host snapshots for older artifacts without an embedded review module.
- Correct workbench instructions to match the simplified reader dock.

## 0.7.0 — 2026-09-18

- Unify writing in one dock action with visible per-thread privacy. Keep access management in Share and remove the generic More dock.
- Show the current reader's open-thread count, group overlapping pins, and expose all threads at a point.
- Add List and grouped Board presentations to portable and React record explorers, preserving filtering, selection and source anchors. Boards are read-only; portable lane counts cover the current page.
- Test pin collisions, live counters, read-only reviewer capabilities and presentation changes with active filters/selection.

## 0.6.0 — 2026-09-18

- Adopt Margen as the product, repository and canonical agent skill name. Preserve document IDs, URLs, account storage, runtime APIs and legacy commands.
- Replace the crowded comment form with a compact author/draft/send composer. Disclose context, note type and session on demand; preserve failed drafts and restore controls on remount.
- Replace the large theme-card grid with a searchable list, compact mode controls and independent typography/sound tabs.
- Group table tools in portable artifacts and React with shared borders and accessible labels.
- Maintain repository guidance and recipe documentation in English while preserving localized executable examples.
- Install the `margen` command and skill entries for Codex, Claude Code and Hermes, with explicit compatibility forwarding for the old name and protection for custom installations.


## 0.5.2 — Refined controls and reader tools

- Introduce consistent SVG controls and a grouped floating reader dock with direct comment/note actions, active tool states, keyboard navigation and focus/hover hints.
- Refine the library, appearance panels and portable/React table controls with quieter surfaces, clearer hierarchy and shorter labels.
- Preserve account CSP with a generated external control stylesheet; keep permissions, private notes and historical versions intact.
- Document UX research, interface guidance and the proposed Margen brand direction without renaming packages or installations.

## 0.5.1 — Tables and mobile reading

- Consolidate portable table controls with source-value facets, removable filter chips, contextual selection actions and clearer column settings.
- Add automatic mobile record cards and explicit Table/Cards switching to portable and React tables, preserving source cells, IDs and selection.
- Improve mobile detail sheets, reader safe areas, touch targets, reading progress placement and narrow fleet projections.
- Document mobile composition and revision migration; extend the synthetic workbench and behavior tests. Historical HTML is not silently rewritten.


## 0.5.0 — Unified reading and connected context

- Add one artifact toolbar for personal appearance, review, sharing and contextual actions, with a compatible portal adapter for historical HTML.
- Introduce a shared typed table-query model, TanStack React DataTable, filter builder, row inspector, stable selection, local saved views and portable table upgrades. Include synthetic Liftit, Tikin and Catabum scenarios.
- Add authorized library conditions, account-private saved filters, explicit batch tagging/collections/archive, command search, working sets and movable private boards.
- Add personal company/project/topic entities with aliases and properties, version-pinned directional references, backlinks, literal mention suggestions, relationship filters and saved graph positions.
- Add session-output browsing and a previewable context composer with selected comments, opt-in own notes and selected reference evidence. Copy and download do not send to an agent or publish a revision.
- Keep source versions immutable, validate both endpoints of every relationship and restrict cited historical versions to confirmed references and current permissions.
- Document surface-specific capabilities and boundaries; update the canonical portable skill for Codex, Claude Code and Hermes.

## 0.4.0 — Administrator knowledge workbench

- Connect artifacts to companies/spaces, manual or automatic topics, and collections in the actual portal graph. Explain membership, explore one/two-hop neighborhoods, search nodes, pan, zoom and move nodes.
- Add searchable library facets, server-wide bidirectional column sorting, agent and pending-review filters, column visibility, density and scroll-preserving table loading.
- Add opt-in six-hour skill updates for macOS LaunchAgents and Linux user timers, preserving each installation’s chosen server and credentials. Skip unchanged downloads and lock concurrent updates.
- Document the portal/local-component distinction and update lifecycle. Add graph, cursor, privacy, filter UI and scheduler regression checks.
- The core/React package API remains at 0.3.0; this release changes the portal and portable skill.

## 0.3.0 — Component discovery and local relationship exploration

- Expand the library to 88 documented recipes with six continuity compositions.
- Add local relationship exploration: named nodes, directed explanations, search, one/two-hop focus, state/type filters, history, zoom and source tables.
- Make the visual guide searchable by need, category and composition journey; add a component playbook.
- Document 36 workbench directions while distinguishing local examples from connected portal capabilities.
- Add regression checks for graph navigation, invalid data, lifecycle and catalog discovery. The portal graph model is unchanged.

## 0.2.1 — Hosted onboarding

- Make artifacts.botto.is the primary onboarding path, with account connection, publication, review handoff and update instructions.
- Keep self-hosting and local-only installation as independent documented paths.
- Teach the shared skill to preserve the chosen service and avoid asking hosted users for server configuration.
- Correct outdated composition and review descriptions; no portal runtime changes.

## 0.2.0 — Organized sources and React adapter

- Move runtime, recipes, themes, examples, documentation and verification records into explicit English paths. Preserve published identities and legacy selectors.
- Add per-recipe manifests and a component scaffolder; split theme families into individual source files.
- Add typed core/React workspaces with eight native exports and sandbox access to the existing 82 recipes. Packages are available from source/packed tarballs, not the npm registry.
- Add a private feedback handoff bundle that preserves artifact/version/anchor/session context. Delivery remains manual.
- Document installation variables, self-hosting, architecture, graphs, React, contribution and migration. Replace historical screenshots in the current tree with a synthetic fixture.


## 0.1.0 — First open-source release

- Portable editorial library: 82 recipes, 15 theme families, light/dark/system and six typography combinations.
- Shared skill and verified installer for Claude Code, Codex and Hermes; local ZIP installation without a hosted account.
- Optional FastAPI/SQLite portal with native Google/email authentication, document permissions, comments, private notes, drafts, published versions and context exports.
- Searchable library with gallery, list, table, editable classification and shared-tag/collection relationship map.
- Generic Docker Compose deployment, private environment setup, optional HTTPS proxy and administrator bootstrap.
- Self-hosted installers remember their own update origin; authentication emails and installation links use the configured domain.
- MIT licensing for original code, third-party notices, contributor/security policies and public project documentation.

This release opens an existing working system to the community. It does not include automatic conversation synchronization, an MCP server, model training or live collaborative text editing. Historical library versions retain their dated identifiers in VERSION.json.
