# Efficient artifact authoring

The portable package is not the model context. Images, fonts, scripts and example artifacts can be large on disk without consuming input tokens when the agent executes the generator. Reading their full contents into the conversation is the avoidable cost.

## Default path

1. Load `SKILL.md` once. For a new artifact, read the executive voice and the relevant composition section. A follow-up edit usually needs neither again.
2. Search `scripts/catalog.py --search table --limit 8`. The index omits HTML. Load exact recipes with `--id`; English and compatibility IDs work. Multiple `--id` flags retrieve only the selected recipes in one call.
3. Write content in small source files, then run the generator. Do not hand-copy the runtime, inline fonts or sound into model output.
4. Preserve the source path, stable document ID, selected recipes and last validation in a short handoff. Future edits inspect the relevant source fragment and regenerate the same artifact.
5. Use focused validation and browser checks. Full repository maintenance tests are for changes to the library, not prose edits. Broaden after failures or changes that justify it.

Use the components that explain the work. A deep tutorial can need diagrams, examples, tables and marginal notes. Reducing repeated input and boilerplate must not remove evidence, accessibility, voice or verification.

## Measuring a claim about cost

A smaller entrypoint is a reproducible reduction in text loaded; it is **not** proof of a matching bill reduction. Compare the same task, model, cached context, source documents, requested depth and validation before/after. Record input, cached-input and output tokens from the agent's actual usage report, plus whether the result passes review. Do not infer billed tokens from ZIP size or promise a savings percentage from character counts.

Large conversation histories, repeated code dumps, broad repository scans and regenerating unchanged boilerplate can dominate the skill text itself. Use bounded searches, summary tool output and source edits before changing the model or cutting the deliverable.

The skill entrypoint routes conditional procedures to linked references. `docs/skill-reference.md` preserves extended specialist guidance and is not a default read. No cross-provider billing telemetry is collected by this change.
