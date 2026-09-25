# Collaboration definition: phase record and Checkpoint 2

[product-thesis](product-thesis.md) · [jobs-to-be-done](jobs-to-be-done.md) · [system-boundary](system-boundary.md) ·
[typed-model](typed-model.md) · [reconciliation-rules](reconciliation-rules.md) · [v1-scope](v1-scope.md) ·
[design-principles](design-principles.md) · schema [`coordination-v1.json`](../../schema/coordination-v1.json) · ADR-027–030

## Phase record
- **Findings:**
  - Four types (Session, Gate, Commitment, Decision) with `proposed`/`declared` status cover every scenario.
  - Four deterministic rules (C-linked, C-unlinked, G-freeze, G-open) cover the top two problems.
- **Assumptions:** people will confirm items after a check-in and declare link targets for the commitments that matter.
- **Rejected:** a PM-suite boundary; task statuses; OpenQuestion as a type; stored transcripts; inferred links and owners; cues mixed into repository signals.
- **Evidence:** the discovery opportunity map (Q1 = 80, Q2 = 60) and the declared-vs-observed classification.
- **Uncertain:** whether G-freeze cues feel helpful or like policing; whether storing declarations in the repository is acceptable for public repos.

## Checkpoint 2: collaboration-state v1
1. A check-in's notes go into `observstory checkin propose`. A deterministic extractor turns explicit markers into **proposed** gates, commitments and decisions, each with its source line.
2. A person reviews them and runs `observstory checkin confirm --by NAME`. Only now are they **declared**, with who confirmed and when.
3. Declared state lives in the repository (`.observstory/coordination.json`), versioned and reviewable. There's no audio and no transcript store.
4. On each run the Action reconciles declarations with the repository. It shows whether commitments have linked work (in progress, landed, not started), whether a freeze passed while its area kept changing, and whether a gate passed with committed work still open.
5. The Project Map gains a **mission rail**: NOW, check-ins, gates (next one emphasised) and commitment due times. Cues appear in the attention column under "Declared vs observed", and the inspector shows both sides.
6. No task board, no owners inferred, no people scored.
