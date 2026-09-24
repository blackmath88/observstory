# v1 scope

**v1 in one line:** a zero-config GitHub Action that builds a typed snapshot of *in-flight work*
(open PRs, unmerged branches, direct pushes), groups it into areas and lanes, derives four
evidence-backed signals (overlap, stale, waiting, burst), renders a radar dashboard, and ships
a query CLI that agents can call against the same snapshot.

## MUST

- One-line install: `uses: blackmath88/observstory@v1` with only `github-token`
- Zero-config defaults: path-derived areas, default lanes, default thresholds and ignore list
- Collect in-flight evidence: open PR files and commits, unmerged branches via compare, default-branch commits in the window, issues
- Split `observations.json` (facts) from `snapshot.json` (derived); derivation is a pure function
- Snapshot v1 with work items, areas, lanes, signals, actors, provenance; validated against `schema/snapshot-v1.json` on every run
- Signals S-1…S-4 with `basis`, `confidence`, `evidence`, `rule`
- Rate-limit awareness: budget, `X-RateLimit-Remaining`, graceful degradation recorded in provenance
- Static dashboard (radar direction) where every signal links to GitHub evidence
- `observstory query …` CLI returning JSON for 5 agent questions
- Fixture-based tests for every signal and for the principles
- Dogfood on this repository

## SHOULD

- Correct lane matching (prefix/glob, not substring): fixes the v0 bug
- Declared agent authorship via commit trailers
- `observstory render` and `query` working offline from committed snapshots
- An end-to-end demo scenario reproducible from fixtures
- A README that answers the 12 acceptance questions

## NOT YET

- GitHub App and hosted state service (webhooks, durable store)
- A running MCP server (the contract is specified; the adapter comes later)
- Timeline over *persisted* history (prototype only, from fixture sequences)
- CI/check status, hunk-level overlap, duplicate-intent detection
- Multi-repo aggregation
- Any LLM interpretation

## NEVER / ANTI-GOAL

- Per-person productivity scores, rankings, leaderboards, velocity or line counts
- Per-person pages or time series; "who's online"
- Inferring ownership from authorship
- Verdicts on whose approach is correct
- Storing source file contents
- Auto-closing, auto-assigning or otherwise acting on work
