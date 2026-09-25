# Definition: phase record and Checkpoint 2

| Doc | Purpose |
|---|---|
| [product-thesis.md](product-thesis.md) | Problem / claim / non-goal / proof requirement |
| [jobs-to-be-done.md](jobs-to-be-done.md) | Primary and secondary JTBDs, plus the job we decline |
| [system-boundary.md](system-boundary.md) | Layer ownership and the LLM justification test |
| [signal-specs.md](signal-specs.md) | S-1 overlap, S-2 stale, S-3 waiting, S-4 burst, plus review_state |
| [v1-scope.md](v1-scope.md) | MUST / SHOULD / NOT YET / NEVER |
| [design-principles.md](design-principles.md) | The seven principles turned into checkable rules |
| [`../../schema/snapshot-v1.json`](../../schema/snapshot-v1.json) | Typed model |
| [`../../DECISIONS.md`](../../DECISIONS.md) | ADR-001…012 |

## Phase record

**Findings.** The minimal model that supports the claim has seven types: **WorkItem, Area, Lane, Signal (with Evidence), Actor, Commit, Issue**. Of the brief's candidate types:
Observation became the separate `observations.json` bundle. Change became Commit. Branch and PullRequest folded into WorkItem.kind. Dependency became `WorkItem.waiting_on`. Confidence became a field on Signal. Workstream, Decision, OpenLoop, Handoff and Artifact were **rejected** as types:
- Workstream isn't observable.
- Decision is declared only.
- OpenLoop is a view (signals of type stale or waiting).
- Handoff is `review_state`.
- Artifact is a path.

**Assumptions.** Path areas approximate subsystems (A2). Four signals are enough to prove value.

**Rejected alternatives.**
- Lane-centric model (needs config).
- Contributor-centric model (surveillance).
- A divergence signal (not knowable).
- An LLM summary layer.

**Decision.** v1 = in-flight work items + areas + four signals, zero-config, Action-delivered, no LLM.

**Evidence.** Opportunity map: P1 (80), P2 (75), P3 (60) and P4 (48) are all covered by overlap, open loops, areas and the query CLI.

**Uncertain.** Area precision on monorepos; stale threshold defaults; whether the direct-push work item (one per author) is a good proxy for hackathon teams that push straight to main.

## Checkpoint 2: the exact v1 product

1. One workflow line: `uses: blackmath88/observstory@v1` with `github-token`. No config required.
2. Each run collects **in-flight work**: open PRs (files and commits), unmerged branches without a PR, and direct pushes to the default branch in the last 48 h.
3. It derives a typed **snapshot v1** made of work items, path-derived areas, lanes (from config or defaults), actors (with no counts), and signals.
4. Four signals, each with evidence, basis and confidence: **overlap** (areas touched by ≥2 in-flight items), **stale** (idle > 72 h, including branches without a PR), **waiting** (stacked or declared dependency), **burst** (machine-paced change streams, folded).
5. It renders a calm **radar dashboard** in which every mark links back to GitHub evidence, with no people rankings.
6. It ships `observstory query` (changes-since, work-near, overlaps, open-loops, handoff) that returns JSON from the same snapshot, so agents and humans share one source of truth.
7. The snapshot is schema-validated on every run. Rate-limit degradation is recorded in provenance.
