# Observstory architecture

## Core claim

Repository activity is turned into a stable, typed **project-state model** before anything renders
it or an agent reads it. The UI is a projection, and so is the agent query surface (and a future MCP
server). **The snapshot is the product boundary** (ADR-001).

## Pipeline (v1, GitHub Action)

```text
GitHub
  ├─ push / pull_request / issues events  (primary trigger)
  └─ hourly cron at :17                   (reconciliation; crons are best-effort)
        │
        ▼
src/observstory/collect.py + github.py          IMPURE · rate-limit aware · budgeted
  repo · default-branch commits (+files) · PRs (+files, +commits for open ones)
  branches without PRs (compare vs default) · issues
        │
        ▼
observstory/data/observations.json              facts only (observstory.observations/v1)
        │
        ▼
src/observstory/derive.py + signals.py          PURE: derive(observations, config, now)
  work items · areas · lanes · actors · signals (overlap, stale, waiting, burst)
        │
        ▼
observstory/data/snapshot.json                  typed state (schema/snapshot-v1.json), validated every run
        │
   ┌────┴──────────────────────────────────────────┐
   ▼                                               ▼
map_compiler.py → data/scene.json (scene v1)    query.py → `observstory query …` JSON  (MCP adapter: later)
   ▼
map_render.py → index.html  (Project Map, default)      render.py → radar.html (alternative projection)
```

| Module | Role | Pure? |
|---|---|---|
| `config.py` | Defaults and validation; every field optional | yes |
| `github.py` | REST client: call accounting, `X-RateLimit-Remaining`, reserve, retries, clear errors | no |
| `collect.py` | GitHub → observations. Degrades in a fixed order and records it in `meta.degraded` | no |
| `derive.py` | Observations → snapshot: areas, lanes, work items, actors | yes |
| `signals.py` | The four v1 signals | yes |
| `validate.py` | Stdlib JSON Schema subset, plus semantic rules (no per-person numbers) | yes |
| `map_compiler.py` | Snapshot → scene v1: zones, groups, nodes, edges, attention ([scene grammar](docs/ui/scene-grammar.md)) | yes |
| `map_render.py` | Scene → Project Map page (HTML/CSS, SVG connectors, inspector) | yes |
| `render.py` | Radar view (alternative projection) | yes |
| `query.py` | Agent questions over the snapshot | yes |
| `cli.py` | `build`, `derive`, `render`, `query`, `validate` | — |

Because derivation is pure, **fixtures are observation bundles** and every signal is tested
without the network. The same property enables replay: timeline playback is `derive` applied to
a sequence of observation bundles.

## Typed model (snapshot v1)

```text
Snapshot
 ├─ repository, window, config (thresholds echoed), summary, provenance
 ├─ work_items[]   id: pr:<n> | branch:<name> | direct:<author>
 │                  state, in_flight, paths, areas, lanes, actors, last_activity_at,
 │                  review_state, waiting_on[], agent_declared, burst
 ├─ areas[]        path prefix (container-aware: src/x, packages/y; root files are their own area)
 ├─ lanes[]        semantic groups of areas (config, defaults, or "other")
 ├─ signals[]      type, basis, confidence, subject{area|work_item}, work_items, evidence[], rule
 ├─ actors[]       id, kind (human|bot), linked, work_items   ← no counts, by design
 ├─ commits[]      default-branch commits in the window, attributed to a work item
 └─ issues[]
```

Types considered and rejected are listed in [docs/definition/README.md](docs/definition/README.md).

## API budget

`GITHUB_TOKEN` allows 1,000 requests/hour/repo. A typical run costs:

```text
5 + commits_in_window + 2 × open_prs + unproposed_branches
```

That is 15–120 calls. The client keeps a reserve (25) and a hard cap (400). When the budget runs
out it skips, in this order: commit file lists, branch comparisons, PR commit lists, PR file
lists. Each skip is recorded in `provenance.degraded`, shown on the dashboard, and emitted as a
workflow warning.

## Publishing

The default is a workflow artifact, visible only to people who can read the repo. For a hosted
page on a **public** repo:

```yaml
permissions: { contents: read, pull-requests: read, issues: read, pages: write, id-token: write }
# after the observstory step:
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with: { path: observstory }
  deploy:
    needs: observstory
    runs-on: ubuntu-latest
    environment: { name: github-pages, url: "${{ steps.d.outputs.page_url }}" }
    steps:
      - id: d
        uses: actions/deploy-pages@v4
```

## Why not MCP first?

MCP gives an agent tools and resources. It isn't a substitute for event ingestion, durable state
or webhook handling. The MCP server is a thin adapter over `query.py` reading a snapshot. See
[docs/demo/agent-contract.md](docs/demo/agent-contract.md) and
[prototypes/agent-surface/mcp-tools.json](prototypes/agent-surface/mcp-tools.json).

## Deployment evolution

1. **GitHub Action (v1, now).** Stateless: each run rebuilds from GitHub. No infrastructure.
   Limits: no history between runs, schedules are best-effort, one repo per install.
2. **GitHub App + hosted state (v2).** Webhooks go to a queue, then to the same `collect`
   normalisation, then an append-only observation log, then the same `derive` into a
   materialised snapshot. Reconciliation catches missed events. Durable history enables the
   timeline ([prototypes/timeline](prototypes/timeline/)), whose `diff()` is the event-log spec.
3. **Agent interface (v2/v3).** MCP server and REST over the stored snapshots.
4. **Richer signals (v3).** Hunk-level overlap, duplicate intent, CI state. Each must pass the
   evidence rules, and any LLM use must pass the justification test in
   [system-boundary.md](docs/definition/system-boundary.md).

## Privacy and governance

- Metadata only: paths, titles, PR bodies (truncated at 4k characters), timestamps, logins. No
  file contents.
- The Action keeps nothing between runs. Artifact retention is set in the workflow.
- There are no per-person aggregates in the model (ADR-004), and the validator rejects numeric
  fields on actors.
- The hosted service (v2) should use least-privilege App permissions (metadata, contents: read,
  pull requests: read, issues: read) and configurable retention.
