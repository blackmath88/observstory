# Observstory architecture

## Core claim

Repository activity should be transformed into a stable **project-state model** before it is rendered for humans or exposed to agents.

The UI is a projection. MCP is a projection. The typed snapshot is the product boundary.

## State pipeline

```text
GitHub
  |-- push / PR / issue / workflow events
  |-- periodic reconciliation
  v
Collector
  |-- commits
  |-- changed files
  |-- pull requests
  |-- issues
  |-- contributors
  |-- checks
  v
Normalizer
  v
Typed Snapshot
  |-- repository
  |-- contributors
  |-- activity
  |-- lanes
  |-- overlaps
  |-- pull_requests
  |-- issues
  |-- provenance
  +-------------------+
  |                   |
  v                   v
Human dashboard     API / MCP
```

## Why not MCP first?

MCP is excellent for giving an agent tools and contextual resources. It is not a substitute for event ingestion, durable state or webhook handling.

An Observstory MCP server should eventually offer tools such as:

- `project.snapshot`
- `project.changes_since`
- `project.lanes`
- `project.overlaps`
- `project.contributor_activity`
- `project.open_loops`
- `project.handoff`

Those tools should read the same state that powers the dashboard.

## Deployment evolution

### Stage 1 — reusable GitHub Action

A repository includes one workflow. Push/PR/issue events trigger immediately; a schedule reconciles state.

Pros:
- trivial to understand
- no external service required
- works with GitHub permissions
- ideal for proving the model

Limits:
- no durable cross-run state by default
- each repository owns deployment
- schedules are best-effort
- harder to aggregate multiple repositories

### Stage 2 — GitHub App + hosted service

A user installs Observstory on selected repositories.

The App receives webhooks and places normalized events on a queue. A worker updates project state in durable storage. A periodic reconciliation job detects missed events and refreshes derived state.

```text
GitHub App
   |
 webhooks
   v
event queue ---> normalizer ---> project store ---> web UI
                       ^              |
                       |              +--> REST/GraphQL
                 reconciliation       +--> MCP
```

This is the actual "add it to my repo and it builds itself" product.

### Stage 3 — collaboration intelligence

Derived modules can be added without changing the ingestion contract:

- overlapping work / likely merge collisions
- stalled work
- orphaned tasks
- PR dependency graph
- ownership drift
- decision-to-code trace
- handoff readiness
- activity heat
- parallel-agent work visibility

These should remain explainable signals, not opaque productivity scores.

## Typed lane model

A lane is a semantic grouping of work, not a hardcoded UI column.

Example:

```json
{
  "id": "verify",
  "label": "Verify",
  "description": "Tests, evaluations and evidence",
  "signals": {
    "paths": ["tests/", "evals/"],
    "labels": ["validation", "qa"]
  }
}
```

Different repositories can define different lanes. Future adapters may infer proposed lane mappings, but repository configuration remains authoritative.

## Snapshot contract

The current MVP emits `observstory/data/snapshot.json`.

Version the schema. Renderers and MCP consumers should depend on the schema rather than GitHub's raw API representation.

## Persistence

For the Action MVP, the dashboard represents current state plus activity reconstructed from GitHub history.

For the hosted service, persist append-only observations and materialize current project state. This allows true ten-minute snapshots, historical playback and "what changed since the last sync?" without committing generated telemetry back into the observed repository.

## Privacy and governance

For private repositories, the hosted service should use least-privilege GitHub App permissions. Repository source should not be retained unless a feature explicitly requires it. Prefer metadata and derived signals; make retention configurable.
