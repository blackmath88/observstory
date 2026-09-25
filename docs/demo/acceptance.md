# Acceptance criteria: where each answer lives

| # | Question | Answer (short) | Where |
|---|---|---|---|
| 1 | What collaboration problem does Observstory solve? | Parallel (often agent-driven) work collides or stalls unseen until merge | [product-thesis.md](../definition/product-thesis.md), [problem-space.md](../discovery/problem-space.md) |
| 2 | Why doesn't GitHub itself solve it? | GitHub shows objects and feeds, not relations between different authors' *unmerged* work | [competitive-landscape.md](../discovery/competitive-landscape.md), [README](../../README.md#why-github-or-github-projects-doesnt-already-do-this) |
| 3 | What is directly observed vs inferred? | Five classes: observed, derived, heuristic, declared, unknowable. Every signal carries `basis` | [observable-signals.md](../discovery/observable-signals.md) |
| 4 | What is the typed project model? | WorkItem, Area, Lane, Signal + Evidence, Actor (no counts), Commit, Issue | [schema/snapshot-v1.json](../../schema/snapshot-v1.json), [ARCHITECTURE.md](../../ARCHITECTURE.md#typed-model-snapshot-v1) |
| 5 | Which signals matter in v1? | overlap, stale, waiting, burst (plus review_state) | [signal-specs.md](../definition/signal-specs.md) |
| 6 | How do I install it? | One workflow with `uses: blackmath88/observstory@…`; token defaults to `github.token` | [README](../../README.md#install-zero-config) |
| 7 | What useful thing appears without configuration? | Path-derived areas, default lanes, in-flight work, 4 signals, a snapshot for agents | [README](../../README.md#install-zero-config), `test_zero_config_produces_areas_and_signals` |
| 8 | How does the UI expose evidence? | Each signal opens to files, work items (linked), timestamps, and the rule with its parameters | [ui-language.md](../development/ui-language.md), [img/demo-t2.png](img/demo-t2.png) |
| 9 | How would a coding agent use the same state? | `observstory query work-near <paths>` etc. on the same snapshot; the MCP contract maps 1:1 | [agent-contract.md](agent-contract.md) |
| 10 | How does the design avoid surveillance? | Signal subjects are areas and work items only; no per-person numbers (the validator enforces it); no LLM; metadata only | [design-principles.md](../definition/design-principles.md), [risks.md](../discovery/risks.md), ADR-004 |
| 11 | What experiment shows it provides value? | E1–E6 + the demo (overlap visible before merge, then resolved) + self-observation on live data | [experiment-results.md](../development/experiment-results.md), [README](README.md), [self-observation.md](self-observation.md) |
| 12 | What should be built next? | Validate precision on real repos and with one live team, **then** the GitHub App with durable history (timeline) and MCP | [ROADMAP.md](../../ROADMAP.md) |

## Deliver: phase record

**Findings.** The v1 proof holds on fixtures and on live data. Dogfooding found one real bug
(ignore anchoring) and two presentation problems (recency scale, signal fatigue), all fixed.

**Assumptions.** A1 (WIP is pushed early) is still untested with real teams.

**Rejected alternatives.**
- Building the GitHub App now (ADR-002).
- Committing snapshot history into the observed repo (ADR-013).
- Merging per-area overlaps in the *model*. They are only grouped in the UI (ADR-016).

**Decision.** v1 ships as the Action with the radar and the query CLI.

**Evidence.** 37 passing tests; the demo scenario; a live self-observation (16 API calls).

**Uncertain.**
- Overlap precision on large or monorepo codebases.
- Whether people open the dashboard often enough, compared with a PR comment or a check annotation (a possible v1.x delivery surface).
- Whether `direct:<author>` reads as person-focused to users.
