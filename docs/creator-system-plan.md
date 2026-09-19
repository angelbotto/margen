# Creator workspace implementation plan

This working plan tracks the accepted product scope. Completion requires implementation and verification, not only documentation.

- [x] Creator inbox with project context and feedback-to-revision tracking.
- [x] Evidence-backed decisions, review dates, dependencies and change-impact signals.
- [x] Inspectable agent assignments, scoped connectors, delivery receipts and draft results.
- [x] Agent tools and local adapters, preserving actual session/device provenance.
- [x] Approved, editable, exportable writing preferences with source feedback.
- [x] SQL-first authorized library queries, bounded graph neighborhoods and measured load tests.
- [x] Versioned format capabilities and original-file handling for independently authored formats.
- [x] Release verification, compatibility, contributor contracts and repeatable evaluations.
- [x] Browser/mobile/access checks, portable installation tests and documented operating limits.

Deployment and device rollout are verified separately against the tagged release; local test completion alone is not a production deployment.

Product invariant: each suggestion identifies its evidence, scope and next action. Private context remains private. Publishing, resolving feedback, accepting decisions and learning a preference are separate recorded actions.

Implementation boundaries are recorded in [creator workspace](creator-workspace.md), [connectors](agent-connectors.md), [formats](document-formats.md), [performance](performance.md) and [release security](release-security.md). Personal rules are approved prompting context, not model fine-tuning. Agent execution is opt-in on each device.
