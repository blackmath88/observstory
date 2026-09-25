# Decisions

ADR-style log. Status: **accepted** unless noted. Newest decisions at the bottom.

---

## ADR-001: The typed snapshot is the product boundary
**Context.** v0 already emitted a snapshot and rendered HTML from it.
**Decision.** Keep it. Every consumer (UI, CLI, future MCP, future hosted API) reads the
snapshot. Nothing reads GitHub except the collector.
**Evidence.** Principle 3 and 5; the discovery found no reason to change it.
**Consequence.** Renderer and query code are testable offline.

## ADR-002: The GitHub Action stays the v1 delivery vehicle
**Context.** A GitHub App gives real-time webhooks and durable history, but needs hosting, auth and storage.
**Decision.** v1 ships as the composite Action. The App is v2.
**Evidence.** The v1 proof requirement (overlap visible before merge, zero-config) only needs
event-triggered runs plus in-flight evidence, and both work inside an Action.
**Uncertain.** Whether staleness between runs (up to about an hour) is acceptable for hackathons.

## ADR-003: Collect in-flight evidence, not only default-branch commits
**Context.** v0 used `GET /commits` (default branch), so overlap only showed up after merge.
**Decision.** The collector also reads open PR files and commits, and compares unmerged branches with the default branch.
**Evidence.** Discovery finding 3; F1/F4/F11 all happen before merge.
**Cost.** About 1 extra call per open PR and 2 per unproposed branch, capped (see observable-signals.md).

## ADR-004: No per-person metrics
**Context.** v0 showed a contributor table sorted by commits, with line counts.
**Decision.** Remove it. Actors appear only as authors on work items and signal evidence, sorted alphabetically. No numeric per-person fields in the snapshot.
**Evidence.** SPACE guidance against individual measurement; risks R1, R2, R4.
**Rejected alternative.** An "opt-in contributor analytics" toggle. Rejected because it would ship the capability.

## ADR-005: Work items and areas are the core units; lanes are an optional semantic layer
**Context.** v0 organised everything around lanes, which need config to mean anything.
**Decision.** A *work item* is one line of in-flight work: a PR, an unproposed branch, or a person's direct pushes to the default branch in the window. An *area* is a path prefix derived with no configuration. *Lanes* group areas using config, or defaults when there is none.
**Evidence.** Zero-config usefulness (principle 4). Overlap needs a unit smaller than a lane.
**Rejected.** Workstream (needs intent grouping, which isn't knowable); Decision and Dependency as first-class types (mostly declared, low observability in v1). `waiting_on` covers the observable part of dependency.

## ADR-006: Separate impure collection from pure derivation via an observation bundle
**Decision.** `collect()` → `observations.json` (normalised GitHub facts). `derive(observations, config, now)` → `snapshot.json`. Fixtures are observation bundles.
**Evidence.** It is the only way to test signals deterministically, and it enables replay and timeline playback.

## ADR-007: No LLM in v1
**Decision.** Every output is deterministic or a labelled heuristic. See system-boundary.md for the per-need justification test.
**Rejected.** An LLM "divergence" detector: it would state inference as fact (R3).

## ADR-008: Python standard library only
**Decision.** No pip installs in the Action. Schema validation uses a small built-in validator covering the subset of JSON Schema used by `snapshot-v1.json`.
**Tradeoff.** Less complete than `jsonschema`; in return install is instant and there's no supply-chain surface.

## ADR-009: Events first, hourly reconciliation
**Context.** v0 ran a `*/10` cron. GitHub crons are best-effort (delays of 5–30+ min, 5-min minimum) and burn minutes.
**Decision.** Trigger on push, PR and issue events. Reconcile with an hourly cron off the top of the hour (`17 * * * *`).

## ADR-010: The agent surface is a query CLI plus a JSON contract; MCP later
**Decision.** `observstory query <question>` returns structured JSON from the snapshot. The MCP tool contract in `docs/demo/agent-contract.md` maps 1:1 onto these queries, so an MCP adapter is thin.
**Evidence.** Principle 5. It proves agent usefulness without hosting.

## ADR-011: Snapshot v1 is a breaking change; v0 stays for reference
**Decision.** `schema: observstory.snapshot/v1`. `schema/snapshot-v0.json` is kept. v1 drops `contributors` (ADR-004) and restructures lanes.

## ADR-012: Area derivation is container-aware
**Decision.** An area is the first directory segment, or the first two when the first is a container (`src`, `packages`, `apps`, `services`, `lib`, `app`, `libs`, `modules`, `crates`). Root files are their own area. Configurable through `area_depth` and `containers`.
**Uncertain.** Precision on large monorepos (R11).

## ADR-013: Radar plus agent surface ship in v1; timeline waits for durable history
**Context.** Three directions were prototyped (docs/development/concept-comparison.md).
**Decision.** The radar dashboard is the human projection, and the query CLI is the machine projection. Timeline and playback are v2.
**Evidence.** Radar and query need no state across runs. Timeline needs history, which the stateless Action doesn't have.
**Rejected.** Committing snapshot history to the observed repo (noise and permissions: `contents: write`, and a risk of loops, R17).

## ADR-014: Overlap is discounted by explicit dependency
**Context.** Experiment E4: stacked PRs share ground by design and were reported as overlaps.
**Decision.** A work item whose `waiting_on` target touches the same area doesn't count towards that area's overlap. This is recorded in `rule.params.explained_by_waiting`.
**Consequence.** Declaring "Depends on #N" is also how a team *acknowledges* an overlap. This is the resolution path in the demo.

## ADR-015: Direct pushes form one work item per author
**Context.** Hackathon teams often push straight to the default branch (E6).
**Decision.** Default-branch commits that aren't attributable to a merged PR (via `(#N)` or `Merge pull request #N`) are grouped as `direct:<author>`. They take part in overlap at reduced confidence and are never stale.
**Uncertain.** Whether grouping by author reads as person-focused. The id names the stream, and the signal subject is still the area.

## ADR-016: Overlap signals stay per-area in the model and are grouped only in the UI
**Context.** Dogfooding: one branch against one push stream produced 9 per-area overlap signals.
**Decision.** The snapshot keeps one signal per area, which gives stable ids and path-level agent queries. The dashboard groups overlaps that share the same work-item set into one entry.
**Rejected.** A "pair" signal type in the model: it would duplicate evidence and break `work_near` path matching.

## ADR-017: Ignore patterns follow gitignore anchoring
**Context.** Dogfooding: the unanchored `observstory/` output entry hid `src/observstory/`.
**Decision.** A leading `/` anchors a pattern to the repo root. A trailing `/` matches directories at any depth. Globs match the path or the basename.

## ADR-018: Overlap is base-aware and pairwise (issue #2)
**Context.** v1 counted every active work item in an area. A branch created *after* a push to main was reported as overlapping that push. The self-observation's 9 overlaps were all of this kind.
**Decision.** Overlap is computed from **parallel pairs**. The collector records each open PR's and branch's merge base: compare's `merge_base_commit`, or the first commit's parent when the budget runs out (labelled `first_parent`, confidence reduced). It also records parent links for default-branch commits. A default-branch commit counts against a work item only if it isn't an ancestor of that item's merge base, which is decided from the commit graph, not timestamps. Two unmerged items are parallel unless one waits on the other. Direct pushes are never parallel to each other, because pushes to one branch are sequential. Each pair involving a landed change gets `base` evidence naming the merge-base SHA, its source, and the later commits.
**Evidence.** Fixtures b1–b7 (before/after divergence, mixed history on one file, rebase, merging main into the branch, squash merge, base before the window, unknown base). Self-observation 9 → 0.
**Consequence.** E6 (two people pushing to main) no longer produces overlap.

## ADR-019: Overlap requires a shared file by default; bot-only work doesn't take part
**Context.** Precision study (docs/development/precision-report.md).
**Decision.** A pair counts only if both sides change at least one common file (`signals.overlap_require_shared_file`, default `true`). Work items whose authors are all bots don't take part.
**Evidence.** Area-only pairs were useful in 4 of 39 labelled cases; shared-file pairs in 29 of 46. Unmerged pairs involving a bot changed the same lines 1.1% of the time.
**Cost.** About 50 useful area-only relations across six repos are given up. Area activity stays on the radar and in `work_near`.

## ADR-020: Default ignores add `CHANGELOG*`, `.changeset/`, `*.api.md`
**Evidence.** These files caused 6 of the 52 non-useful sampled pairs, including 3 of the 5 non-useful same-line pairs. Repo-specific generated files (e.g. `uv.schema.json`) belong in the repo's own `ignore` config.

## ADR-021: Stale work doesn't take part in overlap
**Decision.** Work idle for longer than `stale_hours` is left out of overlap. It's reported by the `stale` signal instead.
**Evidence.** 81.4% of all overlap pairs on the six repos involved stale work, mostly old branches with no PR.
**Cost.** 12% of those pairs changed the same lines. They're latent conflicts, now visible only as stale work.

## ADR-022: A dependency chain explains shared ground transitively
**Decision.** If A waits on B and B waits on C, A's shared ground with C is explained too.
**Evidence.** 9 of the 20 non-useful final signals came from two-level stacks (uv#21962 → #21961 → #21963; uv#21952 → #21944 → #21942). Fixture p2.

## ADR-023: Project Map is the default human view, compiled through a scene contract (issue #3)
**Context.** The radar showed that the snapshot can be projected visually, but people read it as a dashboard. The preferred direction is a calm architectural infographic that builds itself from project state.
**Decision.** Add a pure compiler (`map_compiler.py`) from snapshot v1 to **scene v1** (`schema/scene-v1.json`): zone, group, node, edge, plus attention and details. A renderer (`map_render.py`) draws it with HTML/CSS and SVG connectors. The Action writes the map to `index.html` and `data/scene.json`. The radar stays at `radar.html`.
**Rejected.** A force-directed graph (the project already has semantic order). Canvas (it loses selectable text, links and accessibility). A frontend framework (no need: one inline script of about 250 lines). BADGE, NOTE and BAND as scene types (no data needs them yet).
**Consequence.** Layout meaning is testable without a browser. Scene validation runs on every build.

## ADR-024: A work item is drawn once, in its primary area
**Decision.** A node goes in the area where the work item changes the most files (ties go to the earlier lane, then the path). Every other area it touches shows a compact reference. Landed changes appear only where they take part in a relationship.
**Why.** Drawing a work item in every area it touches multiplied a 97-file PR into 20 cards. Drawing it only once made the lanes it also changes look quiet. Self-observation showed both failures.
