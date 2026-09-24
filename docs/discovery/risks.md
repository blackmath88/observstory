# Product risks

> Phase: DISCOVER. Each risk has a severity, a likelihood and the mitigation adopted.

| # | Risk | Severity | Likelihood | Mitigation (decision) |
|---|---|---|---|---|
| R1 | **Productivity scoring**: counts per person turn into rankings | High | High (v0 already sorts contributors by commits) | Remove per-person leaderboards and line counts from the UI. Actors appear only as evidence on work items and areas. ADR-004 |
| R2 | **Employee surveillance**: managers use it to watch people | High | Medium | No per-person pages, no per-person time series, no "online now". Document the anti-goal. The tool observes *work in flight*, not people |
| R3 | **False inference presented as fact** | High | High | Every heuristic signal carries `basis`, `confidence` and `evidence[]`. The UI labels heuristics. No LLM text in v1 |
| R4 | **Gaming**: people split commits or avoid pushing WIP to avoid showing up | Medium | Medium | Nothing to win: no scores. Signals are about areas, so gaming only makes coordination worse for the person doing it |
| R5 | **API rate limits** (1,000/h for GITHUB_TOKEN) | Medium | Medium on large repos | Caps per call class; read `X-RateLimit-Remaining`; degrade gracefully and record the degradation in `provenance.limits` |
| R6 | **Private repos**: the dashboard leaks content | High | Medium | The artifact is uploaded as a workflow artifact by default (visible only to repo readers). Pages publishing is opt-in, with a warning in the README. Only metadata is stored: paths, titles, never file contents |
| R7 | **Data retention** | Medium | Low | The Action keeps nothing between runs. Artifact retention is set by the workflow (default 7 days). Snapshot history is opt-in |
| R8 | **Contributor identity**: unlinked emails, multiple accounts | Low | High | Use the login when present. Otherwise `name` with `linked: false`. Never merge identities heuristically |
| R9 | **Bots vs humans; agents under human tokens** | Medium | High | `kind: bot` from API type or `[bot]` suffix. Agent authorship only when declared (trailer or label). Never guessed |
| R10 | **Generated commits and files** (lockfiles, dist, snapshots) | Medium | High | A default `ignore` list (lockfiles, `dist/`, `build/`, `*.min.*`, `observstory/`), configurable |
| R11 | **Monorepos**: top-level dirs too coarse | Medium | Medium | Zero-config area depth is 2 for known container dirs (`packages/`, `apps/`, `services/`, `src/`); configurable lanes override |
| R12 | **Squash merges**: branch history disappears | Low | High | Overlap is computed on *open* work. Merged work only counts as recent history |
| R13 | **Rebases / force pushes** change shas | Low | Medium | No cross-run sha identity in v1. Work items are keyed by PR number or branch name |
| R14 | **Branch-heavy teams** (hundreds of branches) | Medium | Low–Medium | Only branches with commits inside the window are considered, capped (default 20) |
| R15 | **Schedule reliability** | Low | High | Crons are best effort, delayed 5–30+ min under load, with a 5-min minimum. Event triggers are primary and the cron only reconciles (hourly, off the :00 mark) |
| R16 | **Signal fatigue**: too many overlaps | Medium | Medium | Overlap only between *distinct work items* and *in flight*; ignore list; sort by number of work items |
| R17 | **Self-referential noise**: committing the dashboard triggers a run | Low | Medium | Default output is the artifact, not a commit; `observstory/` is in the ignore list |

## Sources

- GitHub Docs: [Rate limits for the REST API](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api) (GITHUB_TOKEN: 1,000 requests/hour/repository)
- [GitHub community discussion on delayed cron workflows](https://github.com/orgs/community/discussions/156282)
- Swarmia: [DORA, SPACE and DX Core 4](https://www.swarmia.com/blog/comparing-developer-productivity-frameworks/), and SPACE guidance against individual-level measurement ([getdx](https://getdx.com/blog/space-metrics/))
