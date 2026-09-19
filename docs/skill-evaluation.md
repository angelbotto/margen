# Evaluate Margen across agents

A valid installation proves file integrity and discoverability, not equivalent outputs from Claude, Codex and Hermes. Test each agent in a fresh session with the same representative brief and available evidence.

## Evaluation tasks

Use an executive report, a technical explanation with exact code, a logistics table/map, a personal reading note and a revision driven by contextual comments. Include incomplete data, a narrow viewport and a request to preserve existing document identity. Keep fixtures synthetic and explicitly labeled.

## Criteria

Check correct skill/resource selection; useful component variety; executive voice; factual grounding; source/units/denominator disclosure; mobile readability; accessible controls; stable anchors; clear distinction between public comments and private notes; correct draft/publish behavior; actual session/device provenance; and preservation of the user's server/account.

Never reward fabricated metrics, decorative component count, unsupported claims of real-time data, hidden overflow or copying comments into public content. HTML validation is necessary but does not replace browser inspection or editorial review. Measuring audio state is not a listening test.

## Repeatable process

Record the brief, input evidence, agent/model version, skill version, resulting file/hash and publication state. Keep evaluation notes separate from production user content. Compare outputs against explicit criteria and document failures with reproducible examples. Improvements should update the relevant recipe, instructions or runtime and add behavior tests when warranted.

Use `scripts/test_feedback.py`, contract checks, portable installation tests and the relevant React/portal suites. Do not assert automatic agent loading without checking it on that machine. See [the skill](../SKILL.md), [executive voice](executive-voice.md) and [contribution guidance](contributing-components.md).

## Versioned fixture set

Five synthetic briefs and their evidence live in `tests/fixtures/agent-evaluation/cases.json`: executive, technical, logistics, reading and contextual revision. Run the same brief with each installed agent, recording its actual model version. Then capture repeatable checks:

```bash
python3 scripts/evaluate_artifact.py --case executive --artifact /tmp/output.html --agent Codex --model ACTUAL_MODEL --output /tmp/evaluation.json
```

The report hashes the output, checks stable identity, required evidence presence and the responsive viewport, and leaves explicit human-review fields empty. Passing string checks does not prove factual grounding, visual quality or agent equivalence. Review those fields alongside browser and privacy checks. Never publish production inputs as evaluation fixtures.
