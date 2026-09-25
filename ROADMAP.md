# Roadmap

## v0: repo-native proof ✅
Composite Action, typed lanes, JSON snapshot, static dashboard, path overlap on default-branch commits.

## v1: in-flight coordination state ✅ (this release)
- [x] Double Diamond research, definition and ADRs (`docs/`, `DECISIONS.md`)
- [x] Collect **in-flight** evidence: open PR files and commits, branches without PRs, direct pushes
- [x] Snapshot v1: work items, areas, lanes, signals, actors without counts, provenance
- [x] Pure derivation, with observation-bundle fixtures and tests
- [x] Signals: overlap, stale, waiting, burst (each with evidence, basis, confidence, rule)
- [x] Radar dashboard, evidence-first, light and dark
- [x] Agent query CLI (5 questions) plus an MCP tool contract
- [x] Schema validation on every run; rate-limit budget with recorded degradation
- [x] Zero-config defaults; anchored lane and ignore matching
- [x] Dogfooding on this repository; demo scenario
- [ ] Publish a tagged `v1` release so installs can pin `@v1`

## Next: validate with real teams (before building more)
- [x] Run against active public repos and label overlaps → [precision-report.md](docs/development/precision-report.md) (6 repos, 27 signals, 59% useful)
- [x] Base-aware overlap (issue #2)
- [ ] Rerun the precision study in API mode (`evals/precision/run.py`) with a second annotator
- [ ] One live hackathon team: do people act on overlaps? Does WIP get pushed early enough (assumption A1)?
- [ ] Tune default thresholds from that data

## v1.1: Project Map ✅ (issue #3)
- [x] Scene v1 contract and deterministic compiler
- [x] Project Map as the default view (HTML/CSS + SVG connectors, inspector, responsive); radar kept as `radar.html`
- [x] Demo Lab: one synthetic project at nine moments, through the real pipeline (issue #6)
- [ ] Run it with a real team for a week and see whether the attention column is what people actually open

## v1.x: cheap refinements
- [ ] Hunk-level overlap (patch ranges) to separate same-line pairs (75% useful) from same-file pairs (45%): the main remaining lever on overlap precision
- [ ] CI state on work items
- [ ] `CODEOWNERS` as *declared* ownership on areas
- [ ] Optional snapshot history via the previous run's artifact (enables `changes-since` across runs)

## v2: installable service
Install Observstory, select repositories, open the control center.
- [ ] GitHub App: webhooks, queue, append-only observation log, the same `derive`, materialised snapshots
- [ ] Scheduled reconciliation
- [ ] Timeline and playback (prototype: `prototypes/timeline/`); work-item identity across branch → PR
- [ ] Hosted dashboard with repository-scoped auth
- [ ] MCP server over stored snapshots (contract: `prototypes/agent-surface/mcp-tools.json`)

## v3: collaboration intelligence (each must pass the evidence rules)
- [ ] Duplicate-intent detection across issues and PRs
- [ ] Decision index (DECISIONS.md / ADR files / labels), linked to the areas they govern
- [ ] Multi-repo views
- [ ] Opt-in, labelled LLM annotations, only where deterministic code can't answer (see system-boundary.md)

## Never
Productivity scores, leaderboards, per-person timelines, ownership inferred from authorship.
