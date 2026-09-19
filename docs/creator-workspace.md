# A working memory for decisions

Margen connects a creator's artifacts, feedback, agent sessions and decisions. Open **Mi trabajo** in the authenticated library. Choose a project before reviewing its work. A project is an organizational scope, not an access grant.

## The loop

1. **Attention:** inspect unresolved feedback and decisions whose review date has arrived or whose cited published version changed. Quotes, artifact links and anchor status keep feedback attributable.
2. **Decisions:** record the choice, rationale, alternatives, uncertainty, expected outcome, evidence and review date. Accepting requires owned evidence; optional literal quotes must exist in that version. Changes append a history record. Updating evidence is explicit; a new draft does not invalidate a published reference.
3. **Assignments:** select an artifact and individual threads, instructions and a connector. Private notes require a separate opt-in. Inspect or copy the exact packet before dispatch. Rules approved for the project are included.
4. **Delivery:** `prepared → queued → received → working → proposed`. Failures and cancellation remain visible. A receipt means that the connector received the job, not that the agent completed it.
5. **Review:** inspect the draft and textual comparison. Every selected thread requires one explanation: addressed, blocked or unchanged. Accepting a proposal does not publish it or resolve feedback. Publish from the existing version controls only after review.
6. **Learning:** explicitly approve an editable writing rule, optionally with source artifacts. Export or delete rules at any time. This is personal retrieval and prompting, not shared model training.

## Context graph

The creator graph adds decisions and real recorded sessions to artifact, company, project and topic relationships. Evidence edges identify changed sources. Confirmed links preserve their quote and version; shared topics only indicate similarity. Selecting a project scopes the view to owned artifacts. Use search, a local neighborhood and the adjacent session/output list instead of trying to read every edge simultaneously.

The current view is bounded to 150 artifacts, 200 decisions and the latest 2,000 version origins; the UI reports the scope. The creator dashboard lists at most 200 jobs and decisions. It does not silently infer causal relationships or import entire chat histories. Source provenance must come from the creating agent or an explicit user reference.

## Privacy and authority

The creator workspace is owner-specific even when an administrator can inspect the broader library. Other people cannot read personal rules, decisions or assignments. Private notes enter a packet only when selected and explicitly included. Connector credentials are hashed at rest, shown once, revocable, and separate from publishing tokens. They cannot list the library or publish a version. Existing broad personal publishing tokens remain a separate compatibility interface.

Cancellation stops further portal state changes; it does not terminate an already-running local agent process. A changed published base is flagged during comparison. A text diff does not assess visual differences; open the proposed artifact before publication.
