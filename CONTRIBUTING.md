# Contributing to Margen

Thank you for improving the tools people use to explain and review their work. Small, focused changes are easier to assess. Open an issue for a large architectural change before implementing it. Bug reports should include reproduction steps using synthetic data, expected behavior and actual behavior.

## Create without code

You can create themes, static components and diagrams in the portal’s **Temas y componentes** editor, save them privately or share a link without a pull request. See [community creation and sharing](docs/community-marketplace.md). The workflow below is for contributing code to Margen itself.

## Set up

Python 3.10+ generates standalone artifacts using the standard library. Node 22.12+ is needed for the React workspace. Portal development additionally needs its pinned Python dependencies.

```bash
git clone https://github.com/angelbotto/margen.git
cd margen
npm ci
python3 scripts/build.py
npm run build
npm run dev
```

See [architecture](docs/architecture.md) before moving responsibilities between packages. See [component and theme contribution guide](docs/contributing-components.md) for the editable sources and scaffolding command.

## Change the source, regenerate the output

Recipes live in `packages/core/recipes/<id>/`; themes in `packages/core/themes/families/`; vanilla interaction modules in `packages/core/components/`; native React in `packages/react/src/components/`. Complete example HTML and the main catalog/reference are generated. New files and public APIs use English names. Preserve existing document IDs, persisted fields and legacy selectors unless the PR includes a compatible migration.

Use clear prose and minimal abstractions that serve an actual caller. Keep agent-specific orchestration outside framework-independent components. Do not add a dependency merely to rename an existing helper. A component's guidance should explain what decision it helps with, what data it needs and where it stops being useful.

## Validate

For core, skill and generation changes:

```bash
python3 scripts/build.py
python3 scripts/validate.py
python3 scripts/test_contract.py
python3 scripts/validate_skill.py
python3 scripts/test_feedback.py
python3 scripts/test_portability.py
python3 scripts/check_public_assets.py
node scripts/test_review_store.cjs
node scripts/test_themes.cjs
```

For React:

```bash
npm run check
npm run build:demo
```

For portal/API changes, in a virtual environment:

```bash
python3 -m venv .venv
.venv/bin/pip install --require-hashes -r portal/requirements.lock
.venv/bin/pip install httpx==0.28.1
.venv/bin/python -m unittest discover -s portal -t . -p 'test_*.py'
```

Use a disposable configuration and empty volumes for self-hosting checks. Never run destructive test cleanup against a production Compose project. CI boots its own instance and validates downloads and backups.

Include meaningful regression tests for behavior changes. UI changes need keyboard, narrow-screen and theme checks where applicable; use reduced motion when reviewing animations. Describe what you tested and any unverified behavior.

## Review checklist

- A focused problem statement, resulting behavior and reproduction/example.
- Sources, generated outputs, documentation and applicable tests agree.
- No secrets, personal session IDs, customer files or production screenshots.
- No new global DOM behavior in native React; effects clean up subscriptions/observers.
- Permission checks remain enforced before search, graph or feedback data is returned.
- New dependencies include justification, lockfile changes and license review.
- README and guides distinguish implemented features from roadmap ideas.

## Screenshots and security

Use only synthetic fixtures and follow [the screenshot policy](docs/screenshots.md). Security reports belong in private reporting channels described in [SECURITY.md](SECURITY.md), not public issues. Do not post tokens or single-use authentication links.

By contributing, you agree to license your contribution under the project's MIT license, while retaining the required notices for third-party material. Brand assets and fonts may have separate terms. Participation follows [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
