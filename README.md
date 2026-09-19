<div align="center">

# Margen

**Turn evidence into an artifact people can read, explore and improve.**

An open-source component library, portable agent skill and optional self-hosted review workspace.

[![Validation](https://github.com/angelbotto/margen/actions/workflows/validate.yml/badge.svg)](https://github.com/angelbotto/margen/actions/workflows/validate.yml)
[![Self-host test](https://github.com/angelbotto/margen/actions/workflows/selfhost.yml/badge.svg)](https://github.com/angelbotto/margen/actions/workflows/selfhost.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/angelbotto/margen?style=flat)](https://github.com/angelbotto/margen/stargazers)

[Use artifacts.botto.is](#use-artifactsbottois) · [Self-host](docs/self-hosting.md) · [React](#use-components-in-react) · [Documentation](docs/README.md)

</div>

![Margen React showcase with illustrative data and an editorial theme](docs/assets/react-showcase.png)

*This screenshot comes from the synthetic local demo. No customer documents, accounts, comments or session identifiers are shown.*

Margen brings together **88 component recipes**, **15 theme families with light/dark/system modes**, a shared skill for **Claude Code, Codex and Hermes**, and a portal you can run on your own server. Generate standalone HTML without an account. Add the portal when you need shared comments, private notes, permissions, versions and a searchable library.

> Renamed from Bottifact in v0.6.0. Existing documents, links and commands remain compatible. See the [migration guide](docs/migration-margen.md).

## Project identity and formats

A [project profile](docs/project-identity.md) selects company logo, theme, mode and typography. Exact registered GitHub organizations can supply defaults; reader themes never replace company identity. Generic headers use the compact Margen cube.

Create a continuous document, a chapter report or a presentation with the [same generator](docs/document-formats.md). Articles and presentations are authored separately. Native slides include navigation, overview and contextual review; existing decks retain their own design and navigation. See the [tool and skill assessment](docs/presentation-ecosystem.md) for optional Office/export directions and their limits.

## Choose how to use Margen

| Path | Who operates the server? | What you install | Configuration |
| --- | --- | --- | --- |
| **[Use artifacts.botto.is](docs/hosted-service.md)** | Botto operates the existing service | The agent skill, if you want to create/publish from an agent | Sign in and connect your personal token; no `.env` |
| **[Self-host](docs/self-hosting.md)** | You operate your own instance | Portal + optional agent skill | Docker, domain, environment variables, authentication, backups |
| **[Local only](docs/installation.md#local-only-skill)** | No server | The agent skill | No account, token or environment variables |
| **[React integration](docs/react.md)** | Your application | Core/React packages | Node 22.12+, React 18.3 or 19 |

## Use artifacts.botto.is

This is the shortest route to an existing library with accounts, shared review and versions. **You do not need Docker, a NAS, Google Cloud credentials or environment variables.**

1. Open [artifacts.botto.is](https://artifacts.botto.is), sign in, and open **Conectar un agente** to create a personal token. Readers can use a shared artifact link without installing the skill; the document's access policy determines whether sign-in is required.
2. Install the shared skill for Claude Code, Codex and Hermes:

```bash
curl -fsSL https://artifacts.botto.is/install.sh -o /tmp/bottifact-install.sh
# Review the downloaded script before running it.
bash /tmp/bottifact-install.sh
```

3. Connect through the CLI's masked token prompt:

```bash
margen connect --server https://artifacts.botto.is
margen status
```

If the command is not found, add `~/.local/bin` to PATH. Reload your agent's skill discovery and ask it to use **Margen**. Installing a skill does not itself sign in or publish files.

4. Create an artifact with your agent, then publish it when ready:

```bash
margen publish --file /path/to/brief.html --title 'Decision brief' \
  --visibility private --agent codex --session SESSION_ID --device DEVICE_LABEL
margen comments --artifact-id ARTIFACT_ID --open
margen update
```

Replace the path and origin metadata with your actual values; omit unknown session IDs rather than inventing them. New artifacts are private by default. Share from the portal according to the audience you intend. Tokens and private artifacts are not included in the open-source repository or portable skill.

[Complete hosted-service guide: browser use, agent connection, first publication, review and troubleshooting →](docs/hosted-service.md)

## Install locally without a service

The independent installation needs **no account, token or environment variables**:

```bash
git clone https://github.com/angelbotto/margen.git
cd margen
python3 scripts/package.py
python3 scripts/update.py --package dist/bottifact-portable.zip
```

This installs one shared library in `~/.local/share/bottifact/library`, links it into `~/.agents/skills`, `~/.claude/skills` and `~/.hermes/skills`, and creates `~/.local/bin/margen` (with `bottifact` retained as an alias). Existing independent skill directories are preserved. Add `~/.local/bin` to your `PATH` if necessary. Restart or reload your agent's skill discovery and ask it to use **Margen**. Agent versions control how skills are discovered; this is not an installer for the ChatGPT website.

For hosted installation and updates, follow the section above. For an independent ZIP installation, update the checkout, rebuild the ZIP and repeat the local command. Downloadable ZIPs and checksums are attached to [GitHub releases](https://github.com/angelbotto/margen/releases).

Generate your first artifact from the checkout:

```bash
python3 scripts/create_artifact.py \
  --content examples/content/standard-content.html \
  --title 'Decision brief' --document-id decision-brief \
  --theme linear --mode system --output /tmp/decision-brief.html
python3 scripts/validate_artifact.py /tmp/decision-brief.html
```

Keep the same `--document-id` when revising a document. Generation embeds fonts, styles and needed runtime modules. Three.js visualizations additionally load a pinned CDN dependency. [Installation details and troubleshooting →](docs/installation.md)

## Host your own workspace

Self-hosting is an independent path for people who want to operate their own instance. Follow the **[self-hosting guide](docs/self-hosting.md)** for Docker Compose, every environment variable, domain/HTTPS, Google and email setup, administrator bootstrap, backups and upgrades. The starting configuration is [`.env.example`](.env.example).

Your own instance has separate users, tokens and data. A botto.is token does not sign in to another instance. Point the skill at the server you choose; installing the open-source library does not require using the hosted service.

## Publish, review and return feedback to your session

Sign in to your portal, create an agent token under **Conectar un agente**, then connect through the masked prompt:

```bash
margen connect --server https://artifacts.botto.is
margen publish --file /tmp/decision-brief.html --title 'Decision brief' \
  --visibility private --agent codex --session SESSION_ID --device DEVICE_LABEL
```

Supply the actual agent session ID and a device label you are comfortable storing. Publication records artifact identity, version and source context. Tokens remain outside the shared skill.

- **Standalone HTML:** floating comments stay in that browser; export/import them to exchange a review.
- **Connected portal:** authenticated comments, replies, states and private notes are stored centrally, subject to document and note permissions.
- **Feedback export:** includes the artifact link, version/hash, anchored section or quote, discussion and available source session/device. An outdated anchor remains identifiable as outdated.

```bash
margen comments --artifact-id ARTIFACT_ID --open --kind all
margen feedback --artifact-id ARTIFACT_ID --output /tmp/bottifact-feedback
```

`feedback` creates a private `feedback.md` + `context.json` bundle. Open the original agent session and ask it to read those files. If the origin is missing or ambiguous, supply `--agent` and `--session` explicitly. **Copying a bundle does not deliver it.** The optional [scoped connector](docs/agent-connectors.md) can receive selected assignments and explicitly run a locally installed agent, returning a draft and per-thread explanations. It never edits conversation-history files or publishes on its own. Review changes, publish a new version, then resolve the relevant threads. [Complete feedback/session workflow →](docs/feedback-and-sessions.md)

## Search and graph connections

The portal offers a searchable library with list/gallery/table views, previews, tags, collections and a relationship graph. Search indexes document text as well as titles. Local classification rules suggest categories and tags and expose the matched terms. Graph edges explain shared tags or collections; they are computed only from documents the requester may access.

This is an explainable local graph, not embedding search or automatic knowledge of your chat history. It does not upload conversations or train a model. [Graph model, limits and extension points →](docs/graphs.md)

## Discover the components

The [visual guide](examples/generated/guide.html) shows every recipe with live examples, usage limits and copyable HTML. Search by need and combine family and composition-journey filters. The [component playbook](docs/component-playbook.md) explains how to choose and combine pieces.

New continuity recipes include a local relationship explorer, session brief, context bundle, evidence ledger, review queue and version comparison. These are portable components, not new persistent project/session entities in the portal. [Knowledge workbench directions →](docs/knowledge-workbench.md)

## Use components in React

The source workspace includes `@bottifact/core` and `@bottifact/react`. These package names are **not yet published to npm**. Run the working showcase:

```bash
npm ci
npm run build
npm run dev
```

```tsx
import { Artifact, Callout, MarginNote, RecipePreview } from '@bottifact/react';
import '@bottifact/react/styles.css';

export function Brief() {
  return (
    <Artifact theme="linear" mode="system">
      <h1>A decision with its evidence</h1>
      <MarginNote side="right" note="Check the denominator.">
        <p>Write the finding, source and limitation here.</p>
      </MarginNote>
      <Callout title="Decision needed">Define the next experiment.</Callout>
      <RecipePreview id="bar-chart" theme="linear" mode="dark" />
    </Artifact>
  );
}
```

There are **8 native React exports**: `Artifact`, `Callout`, `MarginNote`, `Timeline`, `CardGrid`, `DataTable`, `ArtifactFrame` and `RecipePreview`. The last provides access to **all 88 existing recipes inside sandboxed frames**. This is not a claim that all 88 have been rewritten as native React components. Full shared review and publication remain portal capabilities. [Using packed packages in another app, API and limitations →](docs/react.md)

## Repository map

```text
packages/
  core/
    components/       Framework-independent interaction modules
    recipes/          One directory per component: HTML, guidance, manifest
    themes/families/   One file per theme family
    brands/           Brand configuration
    styles/           Editorial styles and embedded fonts
    registry/         Generated catalog, compatibility and aliases
    src/              Typed core API and generated data
  react/src/          Native React components and scoped styles
portal/               Authentication, storage, review, search, graph, worker
examples/
  content/            Editable document content
  generated/          Complete generated HTML artifacts
  react/              Synthetic interactive React showcase
scripts/              Build, validation, installation, publishing, scaffolding
agents/               Agent integration metadata
licenses/             Third-party licenses and provenance
docs/                 Architecture, guides, operations and migration notes
tests/evidence/       Dated verification records; not current guarantees
```

[Architecture and boundaries](docs/architecture.md) · [Migration from v0.1](docs/migration-0.2.md) · [Source vs generated files](docs/contributing-components.md)

## Contribute

Improve a recipe in `packages/core/recipes/<id>/`, or scaffold one:

```bash
python3 scripts/new_component.py --id release-brief \
  --title 'Release brief' --category reports
python3 scripts/build.py
python3 scripts/validate.py
npm run check
```

Read [CONTRIBUTING.md](CONTRIBUTING.md) for the complete checks, contribution boundaries and review criteria. We welcome accessibility fixes, clearer examples, theme improvements and native React ports. Public screenshots must come from synthetic fixtures; see [screenshot policy](docs/screenshots.md).

## Status and boundaries

Margen is an early-stage project. The standalone generator, portal, skill and React layer have different runtime requirements. There is no npm release yet, multi-replica database support, automatic conversation-history import or an embedding-based graph model. [Roadmap](ROADMAP.md) tracks future work; [changelog](CHANGELOG.md) records shipped changes.

MIT for project code. Fonts, approved reference sounds and geographic inputs retain their own terms in [NOTICE](NOTICE) and [licenses/](licenses). Brand names and logos do not imply endorsement or grant trademark rights. The editorial reference is credited in [design documentation](docs/editorial-reference.md).

Please report vulnerabilities privately through [SECURITY.md](SECURITY.md). Community participation follows the [Code of Conduct](CODE_OF_CONDUCT.md).

## Keep your agents current

After installation, `margen update --if-changed` updates from your configured server. Opt into a six-hour per-user check with `margen update --auto enable`; inspect it with `--auto status` or stop it with `--auto disable`. This updates the shared skill used by Codex, Claude and Hermes on that computer, without changing credentials. See [automatic updates](docs/automatic-updates.md), [administrator graphs](docs/graphs.md), and [tables and filters](docs/connected-library.md).

## Unified workspace

[Reader controls, advanced tables, private boards, entities, references and AI review bundles](docs/unified-workspace.md) · [Live synthetic table examples](examples/generated/workbench.html).

## A creator workspace for decisions

**Mi trabajo** connects project feedback, evidence-backed decisions, review dates, agent assignments and approved personal writing rules. A source changing marks dependent decisions for review. A returned proposal keeps its source session, base version and explanation per thread; accepting is separate from publishing. The contextual graph connects artifacts, companies, projects, topics, decisions and recorded sessions. [Creator workflow](docs/creator-workspace.md) · [Local agents and MCP](docs/agent-connectors.md) · [Release verification](docs/release-security.md) · [Performance measurements](docs/performance.md).
